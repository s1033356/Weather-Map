#weather_map
from picamera.array import PiRGBArray
from picamera import PiCamera
from functools import partial
from pymongo import MongoClient
from gps import *
from time import *

import numpy as np
import multiprocessing as mp
import time
import cv2
import pymongo
import os
import io
import threading
import time
import pigpio
import pygame
import sys
import math
import serial
import pynmea2
import requests
import picamera
import json
import argparse
import base64
import googleapiclient.discovery

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

MONGO_HOST = 'mongodb://bigmms:bigmms1413b@140.138.145.77'
MONGO_PORT = 27017
MONGO_DB = 'weather'
MONGO_USER = 'bigmms'
MONGO_PASS = 'bigmms1413b'

#ser =serial.Serial("/dev/ttyUSB0",9600,timeout=0.5)

resX = 320
resY = 240

cx = resX / 2
cy = resY / 2

pygame.init()
lcd = pygame.display.set_mode((320, 240))
pygame.mouse.set_visible(False)

panX = 19.2
panY = 19.2

pi = pigpio.pi()
pi.set_mode(4, pigpio.OUTPUT)
pi.set_PWM_frequency(4, 50)
pi.set_PWM_dutycycle(4, panX)

pi.set_mode(17, pigpio.OUTPUT)
pi.set_PWM_frequency(17, 50)
pi.set_PWM_dutycycle(17, panY)

camera = picamera.PiCamera()
camera.resolution = (resX, resY)
camera.rotation=180
camera.framerate = 60

rawCapture = PiRGBArray(camera, size=(resX, resY))
#rawCapture = io.BytesIO()

font = pygame.font.SysFont("monospace", 15)
t_start = time.time()

fps = 0
count=0
labels='None'

 # [START authenticate]
service = googleapiclient.discovery.build('vision', 'v1')

gpsd = None 



class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
      
def get_mongo_db():
    con=MongoClient('mongodb://bigmms:bigmms1413b@140.138.145.77:27017')
    db=con[MONGO_DB]
    
    return db
def get_GPS_data():
    send_url = 'http://freegeoip.net/json'
    r = requests.get(send_url)
    j = json.loads(r.text)
    lat = j['latitude']
    lon = j['longitude']
    return (lat,lon)
def get_GPS_net():
    send_url = 'http://freegeoip.net/json'
    r = requests.get(send_url)
    j = json.loads(r.text)
    lat = j['latitude']
    lon = j['longitude']
    return lat,lon

def insert_data(db,lat,lng,rain,fog,snow):
#def insert_data(db,vision):
    #global gpsd
    db.weather.insert_one({'TIME':time.time(),'GPS':[lat,lng],'rain_score':rain,'fog_score':fog,'snow_score':snow})
   # db.weather.insert_one(vision)
def get_vision_result(photo_file):
    """Run a label request on a single image"""

    global service
    # [END authenticate]

    # [START construct_request]
    with open(photo_file, 'rb') as image:
        image_content = base64.b64encode(image.read())
        service_request = service.images().annotate(body={
            'requests': [{
                'image': {
                    'content': image_content.decode('UTF-8')
                },
                'features': [{
                    'type': 'LABEL_DETECTION',
                    'maxResults': 10
                }]
            }]
        })
        # [END construct_request]
        # [START parse_response]
        response = service_request.execute()
        labels = response['responses'][0]['labelAnnotations'][0]['description'] 
        return response,labels
        #json.dumps(response,indent=4,sort_keys=True)
        # [END parse_response]

	
	
def get_data(img,lat,lng):	  
    global labels
    rain_score=0
    fog_score=0 
    snow_score=0
    data_base=get_mongo_db()
    cv2.imwrite( 'label.jpg', img ) 
    if  int((time.time() - t_start)%5) == 0:
      #lat,lng=get_GPS_data()
      vision_result,labels=get_vision_result('label.jpg')
      #print len(vision_result['responses'][0]['labelAnnotations'])
      #print vision_result['responses'][0]['labelAnnotations'][0]['description']
      #print vision_result['responses'][0]['labelAnnotations'][0]['score']
      for i in range(0,len(vision_result['responses'][0]['labelAnnotations'])):        
        if vision_result['responses'][0]['labelAnnotations'][i]['description'] == "rain":
            rain_score = vision_result['responses'][0]['labelAnnotations'][i]['score']
        if vision_result['responses'][0]['labelAnnotations'][i]['description'] == "fog":
            fog_score = vision_result['responses'][0]['labelAnnotations'][i]['score']
        if vision_result['responses'][0]['labelAnnotations'][i]['description'] == "snow":
            snow_score = vision_result['responses'][0]['labelAnnotations'][i]['score']  
      #print rain_score,fog_score,snow_score
      #lat_net,lon_net=get_GPS_net()
      if (rain_score+fog_score+snow_score) != 0 :
        insert_data(data_base,lat,lng,rain_score,fog_score,snow_score)
      #insert_data(data_base,vision_result)
    return labels
    

def draw_frame(frame):
    global panX
    global panY
    global fps
    global time_t

    fps = fps + 1
    sfps = fps / (time.time() - t_start)
    lfps = font.render("FPS: " + str(sfps), 1, (255, 0, 0))
    #edge = font.render("EDGE:"+str(edges),1,(255, 0, 0))
    #showhaze = font.render("HAZE:"+str(haze),1,(255, 0, 0))
    #llabel=font.render("LABEL:"+label,1,(255,0,0))

    
    cv2.imwrite( 'tmp.jpg', frame )
    img = pygame.image.load( 'tmp.jpg' )
    lcd.blit(img, (0, 0))
    lcd.blit(lfps, (0, 0))
    #lcd.blit(edge,(0,20))
    #lcd.blit(showhaze,(0,40))
    #lcd.blit(llabel,(0,20))
    pygame.display.update()


### Main ######################################################################

if __name__ == '__main__':
    pool = mp.Pool(processes=4)
    fcount = 0
    
    gpsp = GpsPoller() # create the thread
    
    camera.capture(rawCapture, format='bgr')
    
    try:
        gpsp.start() # start it up
      #It may take a second or two to get good data
      #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc    
        r1 = pool.apply_async(get_data, args=(rawCapture.array,gpsd.fix.latitude,gpsd.fix.longitude,))
        r2 = pool.apply_async(get_data, args=(rawCapture.array,gpsd.fix.latitude,gpsd.fix.longitude,))
        r3 = pool.apply_async(get_data, args=(rawCapture.array,gpsd.fix.latitude,gpsd.fix.longitude,))
        r4 = pool.apply_async(get_data, args=(rawCapture.array,gpsd.fix.latitude,gpsd.fix.longitude,))
    
        label1 = r1.get()
        label2 = r2.get()
        label3 = r3.get()
        label4 = r4.get()
    
        rawCapture.truncate(0)
    
        for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
            
            image = frame.array
           
            if fcount == 1:
                r1 = pool.apply_async(get_data, args=(image,gpsd.fix.latitude,gpsd.fix.longitude,))
                #label2 = r2.get()
                draw_frame(image)
    
            elif fcount == 2:
                r2 = pool.apply_async(get_data, args=(image,gpsd.fix.latitude,gpsd.fix.longitude,))
                #label3 = r3.get()          
                draw_frame(image)
    
    
            elif fcount == 3: 
                r3 = pool.apply_async(get_data, args=(image,gpsd.fix.latitude,gpsd.fix.longitude,))
                #label4 = r4.get()           
                draw_frame(image)
    
    
            elif fcount == 4:  
                r4 = pool.apply_async(get_data, args=(image,gpsd.fix.latitude,gpsd.fix.longitude,))
                #label1 = r1.get()            
                draw_frame(image)
    
    
                fcount = 0
            fcount += 1
    
            rawCapture.truncate(0)
    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
      print "\nKilling Thread..."
      gpsp.running = False
      gpsp.join()
      pi.stop()
      pygame.quit()
      pool.close()
      sys.exit()
    



