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
from app.models import Lights, Sockets, Temp_And_Hum, Motion_Detector
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px


def login(request):
    ''' login view '''
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
    ''' logout view '''
    auth.logout(request)
    return render(request, 'logout.html')

@login_required(login_url='/login')
def home(request):
    ''' home site view '''
    temp, hum, water_status, fire_status = read_home_variables()
    context = {'temp' : temp, 'hum' : hum, 'water_status' : water_status, 'fire_status' : fire_status} 
    return render(request, 'home.html', context)

def home_variables(request):
    ''' get temp, hum, water_status, fire_status from read_home_variables() and return in JSON '''
    temp, hum, water_status, fire_status = read_home_variables()
    context = {'temp' : temp, 'hum' : hum, 'water_status' : water_status, 'fire_status' : fire_status}
    return JsonResponse(context)

def read_home_variables():
    ''' get temp, hum, water_status, fire_status and return '''
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

def get_user_object(request):
    '''get Motion Detector object for logged user '''
    user = request.user
    user_object = Motion_Detector.objects.get(user_fkey_id = user.id)
    return user_object

@login_required(login_url='/login')
def motion_detector(request):
    '''motion detector view '''
    user_object = get_user_object(request)
    accept_sms, accept_email, phone, email, send  = get_motion_detector_details(user_object)
    info = ''
    if request.method == 'POST':
        if "change_email" in request.POST:
            try:
                email = request.POST['email']
                user_object.email = email
                info = 'success'
            except:
                info = 'error'
        if "change_phone" in request.POST:
            try:
                phone = request.POST['phone']
                user_object.phone = phone
                info = 'success'
            except:
                info = 'error'
        if "reset" in request.POST:
            try:
                user_object.send = False
                send = False
                info = 'success'
            except:
                info = 'error'

        user_object.save()
    context = {'accept_sms' : accept_sms , 'accept_email' : accept_email,
     'phone': phone, 'email' : email, 'send' : send, 'info' : info}
    return render(request, 'motion_detector.html', context)

def get_motion_detector_details(user_object):
    ''' get motion detector details '''
    accept_sms = user_object.accept_sms
    accept_email =  user_object.accept_email
    phone = user_object.phone
    email = user_object.email
    send = user_object.send 
    return accept_sms, accept_email, phone, email, send 

def motion_detector_turn(request, turn, alert):
    ''' accepting or resigning from sharing sms or email '''
    user_object = get_user_object(request)
    if turn == "on":
        status = True
    else:
        status = False
    if alert == 'sms':
        user_object.accept_sms = status
    elif alert == 'email':
        user_object.accept_email = status
    user_object.save()
    return HttpResponse()

@login_required(login_url='/login')
def camera(request):
    ''' camera view '''
    return render(request, 'camera.html')

class VideoCamera(object):
    def __init__(self):
        ''' capturing video '''
        self.video = cv2.VideoCapture(0)
        self.first_frame = None

    def __del__(self):
        ''' releasing camera '''
        self.video.release()

    def get_frame(self):
        ''' extracting frames and catching motion '''
        ret, image = self.video.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)
        if self.first_frame is None:
            self.first_frame = gray
        delta_frame = cv2.absdiff(self.first_frame, gray)
        thresh_frame = cv2.threshold(delta_frame, 30, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

        (cnts, _) = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #drawing a square on the differences from the first frame
        for contour in cnts:
            if cv2.contourArea(contour) < 1000:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(image, (x, y), (x+w, y+h), (5, 122, 5), 3)

        #encode frame
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield(b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@gzip.gzip_page
def camera_streaming(request):
    ''' video streaming view '''
    try:
        return StreamingHttpResponse(gen(VideoCamera()),content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        print("aborted")

def get_sockets_info():
    ''' get sockets object '''
    socket_no1 = Sockets.objects.get(name='socket_no1')
    socket_no2 = Sockets.objects.get(name='socket_no2')
    socket_no3 = Sockets.objects.get(name='socket_no3')
    return socket_no1, socket_no2, socket_no3

@login_required(login_url='/login')
def sockets(request):
    ''' sockets view '''
    socket_no1, socket_no2, socket_no3 = get_sockets_info()
    socket_no1 = socket_no1.turn_on
    socket_no2 = socket_no2.turn_on
    socket_no3 = socket_no3.turn_on

    if socket_no1 and socket_no2 and socket_no3:
        all_sockets = True
    else:
        all_sockets  = False
    context = {'socket_no1' : socket_no1, 'socket_no2' : socket_no2, 'socket_no3': socket_no3, 'all_sockets' : all_sockets}
    return render(request, 'sockets.html', context)


def sockets_turn(request, turn, socket_no):
    ''' turn on or turn of sockets '''
    socket_no1, socket_no2, socket_no3 = get_sockets_info()
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    if turn == 'on':
        if socket_no == "all": 
            code =  15642210
            socket_no1.turn_on = True
            socket_no2.turn_on = True
            socket_no3.turn_on = True
        elif socket_no == "1":
            code = 15642223
            socket_no1.turn_on = True
        elif  socket_no == "2":
            code = 15642221
            socket_no2.turn_on = True
        elif socket_no == "3":
            code = 15642219
            socket_no3.turn_on = True
    else:
        if socket_no == "all": 
            code = 15642222 
            socket_no1.turn_on = False
            socket_no2.turn_on = False
            socket_no3.turn_on = False
        elif socket_no == "1":
            code = 15642222
            socket_no1.turn_on = False
        elif  socket_no == "2":
            code = 5642220
            socket_no2.turn_on = False
        elif socket_no == "3":
            code = 15642218
            socket_no3.turn_on = False
    try:
        rfdevice = RFDevice(22)
        rfdevice.enable_tx()
        rfdevice.tx_repeat = 200
        rfdevice.tx_code(code, 1, 315)
        rfdevice.cleanup()
        socket_no1.save()
        socket_no2.save()
        socket_no3.save()
        info = 'success'
    except:
        info = 'error'
    context = {'info' : info}
    return JsonResponse(context)

def get_light_info():
    ''' get lights object '''
    red = Lights.objects.get(name='red')
    green = Lights.objects.get(name='green')
    yellow = Lights.objects.get(name='yellow')
    light = Lights.objects.get(name='light')
    return red, green, yellow, light

@login_required(login_url='/login')
def lights(request):
    ''' lights view '''
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

def lights_turn(request, turn, diode):
    ''' turn on or turn of lights '''
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    if turn == "on":
        status = True
        state_diode = GPIO.LOW
        state_light = GPIO.HIGH
    else:
        status = False
        state_diode = GPIO.HIGH
        state_light = GPIO.LOW
    red, green, yellow, light = get_light_info()

    if diode == "all":
        GPIO.setup([18,17,15], GPIO.OUT)
        GPIO.output([18,17,15],  state_diode)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, state_light)
        red.turn_on = status
        red.save()
        green.turn_on = status
        green.save()
        yellow.turn_on = status
        yellow.save()
        light.turn_on = status
        light.save()
         
    elif diode == "red":
        GPIO.setup(17, GPIO.OUT)
        GPIO.output(17, state_diode)
        red.turn_on  = status
        red.save()

    elif diode == "green":
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18, state_diode)
        green.turn_on  = status
        green.save()

    elif diode == "yellow":
        GPIO.setup(15, GPIO.OUT)
        GPIO.output(15, state_diode)
        yellow.turn_on  = status
        yellow.save() 

    elif diode == "light":
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, state_light)
        light.turn_on = status
        light.save()

    return HttpResponse()

@login_required(login_url='/login')
def temperatures(request):
    ''' temperatures chart view '''
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
    ''' humidity chart view '''
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
    ''' create graph '''
    data = go.Scatter(
        x = xAxis,
        y = yAxis,
        name = nameGraph)   
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

