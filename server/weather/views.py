from django.shortcuts import render
from django.http import HttpResponse
from math import sin,asin,cos,radians,fabs,sqrt


import time

EARTH_RADIUS=6378
TIME_REFRESH = 6000000


def mymap(request):
    return render(request, 'weather_map.html', {'time_refresh': TIME_REFRESH})


def getmarker(request):
    import requests
    import json
    collection = getcollection()
    '''collection=[
        {"Latitude":24.968604,"Longitude":121.250969,"Time":0,"Speed":100},
        {"Latitude": 24.968604, "Longitude": 121.250969, "Time": 0, "Speed": 100},
        #{"Latitude": "", "Longitude": "", "Time": "", "Speed": ""},
        #{"Latitude": "", "Longitude": "", "Time": "", "Speed": ""},
        #{"Latitude": "", "Longitude": "", "Time": "", "Speed": ""},
        #{"Latitude": "", "Longitude": "", "Time": "", "Speed": ""},
        #{"Latitude": "", "Longitude": "", "Time": "", "Speed": ""},
        #{"Latitude": "", "Longitude": "", "Time": "", "Speed": ""},
        #{"Latitude": "", "Longitude": "", "Time": "", "Speed": ""}
    ]'''
    marker = []
    time_S = []
    Voting = []
    for item in collection.find():   #filter
        if (time.time() - item['TIME']) < 5:
            time_S.append(item)


    b_V=time_S
    #print (len(b_V))
    #print(b_V)
    #
    for i in range(0,len(b_V)):
        if b_V[i] not in Voting:
             Voting.append(b_V[i])
             for j in range(i+1,len(b_V)):
                #print(b_V[i]['GPS'][0])
                if get_distance(b_V[i]['GPS'][0],b_V[i]['GPS'][1],b_V[j]['GPS'][0],b_V[j]['GPS'][1]) < 0.005 and b_V[j] not in Voting:
                    #print(get_distance(b_V[i]['GPS'][0],b_V[i]['GPS'][1],b_V[j]['GPS'][0],b_V[j]['GPS'][1]))
                    Voting.append(b_V[j])
    Voting.extend({"0"})


    count=0
    mark=[]
    rain_total=0
    fog_total=0
    snow_total=0

    for i in range(len(Voting)):
        if Voting[i] != "0":
            count+=1

            if float(Voting[i]['rain_score'])>0.7:
                #Voting[i]["rain_score"]=1;
                rain_total+=1
            #else:
            #    Voting[i]["rain_score"]=0;
            if float(Voting[i]['fog_score'])>0.7:
                #Voting[i]["fog_score"]=1;
                fog_total+=1
            #else:
            #    Voting[i]["fog_score"]=0;
            if float(Voting[i]['snow_score'])>0.7:
                #Voting[i]["snow_score"]=1;
                snow_total+=1
            #else:
            #    Voting[i]["snow_score"]=0;
        elif Voting[i] is "0":
            rain_voting=float(rain_total)/float(count)
            fog_voting=float(fog_total)/float(count)
            snow_voting=float(snow_total)/float(count)
            rain_total=0
            fog_total=0
            #snow_total=0
            print(rain_voting,fog_voting)
            if rain_voting>0.6:
                mark.append({"LAT":Voting[i-count]["GPS"][0],"LON":Voting[i-count]["GPS"][1],"weather":"rain"})
            if fog_voting>0.6:
                mark.append({"LAT":Voting[i-count]["GPS"][0],"LON":Voting[i-count]["GPS"][1],"weather":"fog"})
            if snow_voting>0.6:
                mark.append({"LAT":Voting[i-count]["GPS"][0],"LON":Voting[i-count]["GPS"][1],"weather":"snow"})

    #print(mark)
    for tamp in mark:

        if tamp["weather"]=="rain":
            marker.append({'addr':[float(tamp['LAT']), float(tamp['LON'])],'icon': {'url': '/static/img/rain.png', 'scaledSize': [48, 48]}})
        if tamp["weather"]=="fog":
            marker.append({'addr':[float(tamp['LAT']), float(tamp['LON'])],'icon': {'url': '/static/img/fog.png', 'scaledSize': [48, 48]}})
        if tamp["weather"]=="snow":
            marker.append({'addr':[float(tamp['LAT']), float(tamp['LON'])],'icon': {'url': '/static/img/snow.png', 'scaledSize': [48, 48]}})

    '''
    for i in range(0,len(time_S)):
        marker.append({'addr': [float(time_S[i]['GPS'][0]), float(time_S[i]['GPS'][1])],'icon': {'url': '/static/img/rain.png', 'scaledSize': [48, 48]}})
    '''
    import json
    data = json.dumps(marker)
    response = HttpResponse()
    response.write(data)
    return response

def getcollection():
    import pymongo
    db = pymongo.MongoClient("mongodb://bigmms:bigmms1413b@140.138.145.77:27017")


    return db['weather']['weather']

def hav(theta):
    s=sin(theta/2)
    return s*s

def get_distance(lat0,lng0,lat1,lng1):
    lat0=radians(lat0)
    lat1=radians(lat1)
    lng0=radians(lng0)
    lng1=radians(lng1)

    dlng =fabs(lng0-lng1)
    dlat= fabs(lat0-lat1)
    h=hav(dlat)+cos(lat0)*cos(lat1)*hav(dlng)
    distance = 2*EARTH_RADIUS*asin(sqrt(h))

    return distance














