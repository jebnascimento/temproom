import streams
from mqtt import mqtt
from wireless import wifi
import math
import adc     


from espressif.esp8266wifi import esp8266wifi as wifi_driver
wifi_driver.auto_init()

VCC = 3.3   # NodeMCU on board 3.3v vcc
R2 = 10000  # 10k ohm series resistor
adcRes = 1023 #10-bit adc

A = 0.001129148 
B = 0.000234125
C = 0.0000000876741


streams.serial()


# use the wifi interface to link to the Access Point
# change network name, security and password as needed
print("Establishing connection")
try:
    # FOR THIS EXAMPLE TO WORK, "Network-Name" AND "Wifi-Password" MUST BE SET
    # TO MATCH YOUR ACTUAL NETWORK CONFIGURATION
    wifi.link("your wifi network",wifi.WIFI_WPA2,"password")
except Exception as e:
    print("connection failed :(", e)
    while True:
        sleep(1000)

# define MQTT callbacks
def is_sample(data):
    if ('message' in data):
        return (data['message'].qos == 1 and data['message'].topic == "desktop/samples")
    return False

def print_sample(client,data):
    message = data['message']
    print("sample received: ", message.payload)

def print_other(client,data):
    message = data['message']
    print("topic: ", message.topic)
    print("payload received: ", message.payload)

def send_sample(obj):
    print("publishing: ", obj)
    client.publish("temp/random", str(obj))

def publish_to_self():
    client.publish("desktop/samples","hello! "+str(random(0,10)))


try:
    # set the mqtt id to "zerynth-mqtt"
    client = mqtt.Client("zerynth-mqtt",True)
    # and try to connect to "test.mosquitto.org"
    for retry in range(10):
        try:
            client.connect("test.mosquitto.org", 60)
            break
        except Exception as e:
            print("connecting...")
    print("connected.")
 
    client.subscribe([["desktop/samples",1]])
    client.subscribe([["desktop/others",2]])
   
    client.on(mqtt.PUBLISH,print_sample,is_sample)
   
    client.loop(print_other)
   

    while True:
        sleep(3000)
        value = adc.read(A0)
        print(value)
        Vout = (value * VCC) / adcRes
        Rth = (VCC * R2 / Vout) - R2
        temperature = (1 / (A + (B * math.log(Rth)) + (C * math.pow((math.log(Rth)),3))))
        temperature = temperature - 292.15
        temperature = -1*(temperature)
        
        print(temperature)
        send_sample(temperature)
        if temperature%10==0:
            publish_to_self()
except Exception as e:
    print(e)
