from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators import gzip
from django.contrib.auth import authenticate
from django.contrib.auth.models import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
import RPi.GPIO as GPIO
from rpi_rf import RFDevice
import dht11
import cv2
import time
from app.models import Lights, Temp_And_Hum
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px


def login(request):
    if request.method == 'POST':
        login = request.POST['login']
        password = request.POST['password']

        user = authenticate(username=login, password=password)
        if user is not None:
            auth.login(request , user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid login or password')
            return redirect('/login')

    return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return render(request, 'logout.html')

@login_required(login_url='/login')
def home(request):
    temp, hum, water_status, fire_status = read_home_variables()
    context = {'temp' : temp, 'hum' : hum, 'water_status' : water_status, 'fire_status' : fire_status} 
    return render(request, 'home.html', context)

def home_variables(request):
    temp, hum, water_status, fire_status = read_home_variables()
    context = {'temp' : temp, 'hum' : hum, 'water_status' : water_status, 'fire_status' : fire_status}
    return JsonResponse(context)

def read_home_variables():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    temp_hum_channel = 4
    fire_channel = 20
    water_channel = 21

    instance = dht11.DHT11(pin = temp_hum_channel)
    result = instance.read()
    temp = "{0:0.1f}".format(result.temperature)
    hum = "{0:0.1f}".format(result.humidity) 

    if temp is None:
        temp = 'No temperature sensor'
    else:
        temp = temp + " °C"
    
    if hum is None:
        hum = 'No humditi sensor'
    else:
        hum = hum + " %"

    GPIO.setup(fire_channel, GPIO.IN)
    GPIO.setup(water_channel, GPIO.IN)

    if GPIO.input(water_channel):
        water_status = "Flowers not watered"     	   
    else:
        water_status = "Watered flowers"
			
    if GPIO.input(fire_channel):
        fire_status = "Fire Detected" 
    else:
        fire_status = "Not Fire Detected"

    return temp, hum, water_status, fire_status


@login_required(login_url='/login')
def camera(request):
    return render(request, 'camera.html')

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.first_frame = None
    def __del__(self):
        self.video.release()

    def get_frame(self):
        ret, image = self.video.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)
        if self.first_frame is None:
            self.first_frame = gray
        delta_frame = cv2.absdiff(self.first_frame, gray)
        thresh_frame = cv2.threshold(delta_frame, 30, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

        (cnts, _) = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in cnts:
            if cv2.contourArea(contour) < 1000:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(image, (x, y), (x+w, y+h), (5, 122, 5), 3)
        
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield(b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@gzip.gzip_page
def camera_streaming(request):
    try:
        return StreamingHttpResponse(gen(VideoCamera()),content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        print("aborted")
    
@login_required(login_url='/login')
def sockets(request):
    return render(request, 'sockets.html')


def socketsON(request, socket_no):
    if socket_no == "all":     
        rfdevice = RFDevice(22)
        rfdevice.enable_tx()
        rfdevice.tx_repeat = 100
        rfdevice.tx_code(15642210, 1, 314)
        rfdevice.cleanup()

    return HttpResponse()

def socketsOFF(request, socket_no):
    if socket_no == "all":
        rfdevice = RFDevice(22)
        rfdevice.enable_tx()
        rfdevice.tx_repeat = 100
        rfdevice.tx_code(15642209, 1, 314)
        rfdevice.cleanup()
        
    return HttpResponse()

def get_light_info():
    red = Lights.objects.get(name='red')
    green = Lights.objects.get(name='green')
    yellow = Lights.objects.get(name='yellow')
    light = Lights.objects.get(name='light')
    return red, green, yellow, light

@login_required(login_url='/login')
def lights(request):
    red, green, yellow, light = get_light_info()
    red = red.turn_on
    green = green.turn_on
    yellow = yellow.turn_on
    light = light.turn_on

    if red and green and yellow and light:
        all_led = True
    else:
        all_led = False
    context = {'red' : red, 'green' : green, 'yellow': yellow, 'light' : light, 'all_led' : all_led }
    return render(request, 'lights.html', context)

def lightsON(request, diode):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    red, green, yellow, light = get_light_info()

    if diode == "all":
        GPIO.setup([18,17,15], GPIO.OUT)
        GPIO.output([18,17,15],  GPIO.LOW)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14,  GPIO.HIGH)
        red.turn_on  = True
        red.save()
        green.turn_on  = True
        green.save()
        yellow.turn_on  = True
        yellow.save()
        light.turn_on  = True
        light.save()
         
    elif diode == "red":
        GPIO.setup(17, GPIO.OUT)
        GPIO.output(17,  GPIO.LOW)
        red.turn_on  = True
        red.save()

    elif diode == "green":
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18,  GPIO.LOW)
        green.turn_on  = True
        green.save()

    elif diode == "yellow":
        GPIO.setup(15, GPIO.OUT)
        GPIO.output(15,  GPIO.LOW)
        yellow.turn_on  = True
        yellow.save() 

    elif diode == "light":
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14,  GPIO.HIGH)
        light.turn_on  = True
        light.save()

    return HttpResponse()

def lightsOFF(request, diode):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    red, green, yellow, light = get_light_info()
    
    if diode == "all":
        GPIO.setup([18,17,15], GPIO.OUT)
        GPIO.output([18,17,15],  GPIO.HIGH)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14,  GPIO.LOW)
        red.turn_on  = False
        red.save()
        green.turn_on  = False
        green.save()
        yellow.turn_on  = False
        yellow.save()
        light.turn_on  = False
        light.save()

    elif diode == "red":
        GPIO.setup(17, GPIO.OUT)
        GPIO.output(17,  GPIO.HIGH)
        red.turn_on = False
        red.save()

    elif diode == "green":
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18,  GPIO.HIGH)
        green.turn_on  = False
        green.save()

    elif diode == "yellow":
        GPIO.setup(15, GPIO.OUT)
        GPIO.output(15,  GPIO.HIGH)
        yellow.turn_on  = False
        yellow.save()

    elif diode == "light":
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14,  GPIO.LOW)
        light.turn_on  = False
        light.save()   
    
    return HttpResponse()

@login_required(login_url='/login')
def temperatures(request):
    date_max = date.today()
    date_min = date_max - timedelta(days=7)
    if request.method == 'POST':
        date_min = request.POST['date_min']
        date_max = request.POST['date_max']
    temp = list(Temp_And_Hum.objects.exclude(date__gt=date_max).exclude(date__lt=date_min).values_list('temp', flat=True))
    time = list(Temp_And_Hum.objects.exclude(date__gt=date_max).exclude(date__lt=date_min).values_list('time', flat=True))
    timeGraph = createGraph(time, temp, 'Temperatures')
    date_max = str(date_max)
    date_min = str(date_min)
    context = {'timeGraph' : timeGraph, 'date_max' : date_max, 'date_min' : date_min}
    return render(request, 'temperatures.html', context)

@login_required(login_url='/login')
def humidity(request):
    date_max = date.today()
    date_min = date_max - timedelta(days=7)
    if request.method == 'POST':
        date_min = request.POST['date_min']
        date_max = request.POST['date_max']
    hum = list(Temp_And_Hum.objects.exclude(date__gt=date_max).exclude(date__lt=date_min).values_list('hum', flat=True))
    time = list(Temp_And_Hum.objects.exclude(date__gt=date_max).exclude(date__lt=date_min).values_list('time', flat=True))
    timeGraph = createGraph(time, hum, 'Humidity')
    date_max = str(date_max)
    date_min = str(date_min)
    context = {'timeGraph' : timeGraph, 'date_max' : date_max, 'date_min' : date_min}
    return render(request, 'humidity.html', context)

def createGraph(xAxis, yAxis, nameGraph):
    data = go.Scatter(
        x = xAxis,
        y = yAxis,
        name = nameGraph)   
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

