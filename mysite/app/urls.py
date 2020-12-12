from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home_variables', views.home_variables, name='home_variables'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('motion_detector', views.motion_detector, name='motion_detector'),
    path('motion_detector/<turn>/<alert>', views.motion_detector_turn, name='motion_detector_turn'),
    path('camera', views.camera, name='camera'),
    path('camera_streaming', views.camera_streaming, name='camera_streaming'),
    path('sockets', views.sockets, name='sockets'),
    path('sockets/<turn>/<socket_no>', views.sockets_turn, name='sockets_turn'),
    path('lights', views.lights, name='lights'),
    path('lights/<turn>/<diode>', views.lights_turn, name='lightsON'),
    path('temperatures', views.temperatures, name='temperatures'),
    path('humidity', views.humidity, name='humidity'),

]