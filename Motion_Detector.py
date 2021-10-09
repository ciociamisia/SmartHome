#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import psycopg2
from smsapi.client import SmsApiPlClient
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.IN)        


def q_run(querry):
    ''' execute querry'''
    username = 'pi'
    password = '****'
    host = '127.0.0.1'
    kport = "5432"
    kdb = "postgres"
    cs = "dbname=%s user=%s password=%s host=%s port=%s" % (kdb, username, password, host, kport)
    conn = None
    conn = psycopg2.connect(str(cs))
    cur = conn.cursor()
    cur.execute(querry)
    try:
        result = cur.fetchall()
        return result
    except:
        pass
    conn.commit()
    cur.close()
        
def send_email(email):
    sender_email = "*****"
    receiver_email = email
    password = '****'

    message = MIMEMultipart("alternative")
    message["Subject"] = "Smart Home: Motion Detector!"
    message["From"] = sender_email
    message["To"] = receiver_email
    text = """<p>Hello!<br> Your sensor has detected movement. If it's not you, check the camera on the smart home app.</p>
            <p>This e-mail was generated automatically. Please don't answer.</p>"""
    part = MIMEText(text, "html")
    message.attach(part)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def send_sms(phone):
    token = "lV3Iqs8dHGTziNLacNelDwirCs5zXw6xmbJIFgNG"
    phone_number = phone
    message = "Your sensor has detected movement. If it's not you, check the camera on the smart home app."
    client = SmsApiPlClient(access_token=token)
    send_results = client.sms.send(to=phone, message=message)
    
def check_motion_sensor(): 
    while True:
        query = "SELECT accept_sms, accept_email, phone, email, id FROM app_motion_detector WHERE send = false "
        users_list = q_run(query)
      
        i = GPIO.input(16)
        if i == 0:  
            time.sleep(5)
        elif i == 1: 
            for user in users_list:
                user_id = user[4]
                accept_sms = user[0]
                accept_email = user[1]
                if accept_sms:
                    send_sms(user[2])
                if accept_email:
                    send_email(user[3])
                if accept_sms or accept_email:
                    query = "UPDATE app_motion_detector set send = true WHERE id = '{}';".format(user_id)
                    q_run(query)
            time.sleep(5)
                    
check_motion_sensor()

