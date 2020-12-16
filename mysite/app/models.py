from django.db import models
from django.conf import settings
from django.db import models

class Lights(models.Model):
    name = models.TextField()
    turn_on = models.BooleanField()

class Sockets(models.Model):
    name = models.TextField()
    turn_on = models.BooleanField()

class Temp_And_Hum(models.Model):
    temp = models.TextField()
    hum = models.TextField()
    date = models.DateField()
    time = models.TimeField()

class Motion_Detector(models.Model):
    user_fkey= models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    phone = models.TextField()
    email = models.TextField()
    accept_sms = models.BooleanField()
    accept_email = models.BooleanField()
    send = models.BooleanField()