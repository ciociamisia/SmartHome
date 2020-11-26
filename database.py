import psycopg2
import dht11
import RPi.GPIO as GPIO

def q_run(querry):
    ''' execute querry'''
    username = 'pi'
    password = 'Misia123'
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

def get_temp_hum():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    temp_hum_channel = 4

    instance = dht11.DHT11(pin = temp_hum_channel)
    result = instance.read()
    temp = "{0:0.1f}".format(result.temperature)
    hum = "{0:0.1f}".format(result.humidity)
    return temp, hum

temp, hum = get_temp_hum()
if temp != '0' and hum != '0':
    query = "INSERT INTO app_temp_and_hum(temp, hum, date, time) VALUES ('{}', '{}', now(), now())".format(temp, hum)
    q_run(query)
