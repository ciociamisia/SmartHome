from django.db import models

class Lights(models.Model):
    name = models.TextField()
    turn_on = models.BooleanField()

class Temp_And_Hum(models.Model):
    temp = models.TextField()
    hum = models.TextField()
    date = models.DateField()
    time = models.TimeField()
