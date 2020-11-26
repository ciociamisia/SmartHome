from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home_variables', views.home_variables, name='home_variables'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('camera', views.camera, name='camera'),
    path('camera_streaming', views.camera_streaming, name='camera_streaming'),
    path('sockets', views.sockets, name='sockets'),
    path('sockets/on/<socket_no>', views.socketsON, name='socketsON'),
    path('sockets/off/<socket_no>', views.socketsOFF, name='socketsOFF'),
    path('lights', views.lights, name='lights'),
    path('lights/on/<diode>', views.lightsON, name='lightsON'),
    path('lights/off/<diode>', views.lightsOFF, name='lightsOFF'),
    path('temperatures', views.temperatures, name='temperatures'),
    path('humidity', views.humidity, name='humidity'),

]