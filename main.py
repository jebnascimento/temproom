
################################################################################
# Universidade Federal do Rio de Janeiro
# Date: 10/dezembro/2018
# Disciplina: Linguagens de Programação
# Professor: Cláudio Miceli
# Autores: José Eduardo Batista e William Barbosa
################################################################################

import streams
from mqtt import mqtt
from wireless import wifi
import math
import adc     

# from broadcom.bcm43362 import bcm43362 as wifi_driver
# from espressif.esp32net import esp32wifi as wifi_driver
from espressif.esp8266wifi import esp8266wifi as wifi_driver

# init the wifi driver!
# The driver automatically registers itself to the wifi interface
# with the correct configuration for the selected device
wifi_driver.auto_init()


#valores de tensão e do resistor que faz um divisor resistivo com o termistor

VCC = 3.3   # NodeMCU on board 3.3v vcc
R2 = 10000  # 10k ohm series resistor
adcRes = 1023 #10-bit adc #resolução do conversor analógico digital

#constantes do termistor usado
A = 0.001129148 
B = 0.000234125
C = 0.0000000876741

#habilita o uso de fluxo de dados através da UART do microcontrolador
streams.serial()


# use the wifi interface to link to the Access Point
# change network name, security and password as needed
print("Establishing Link...")
try:
    # FOR THIS EXAMPLE TO WORK, "Network" AND "Password" MUST BE SET
    # TO MATCH YOUR ACTUAL NETWORK CONFIGURATION
    wifi.link("Network",wifi.WIFI_WPA2,"Password")
except Exception as e:
    print("ooops, something wrong while linking :(", e)
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

def send_sample(obj):#função que publica os dados de temperatura
    print("publishing: ", obj)
    client.publish("temp/room", str(obj))

def publish_to_self():
    client.publish("desktop/samples","hello! "+str(random(0,10))) #quando não consegue enviar dado de temperatura.


try:
    # define a identificação do cliente mqtt que no caso é nosso ESP8266
    client = mqtt.Client("zerynth-mqtt",True)
    # and try to connect to "test.mosquitto.org"
    #aqui tentamos se conectar ao servidor mqtt(broker) através da url abaixo e a porta 60
    for retry in range(10):
        try:
            client.connect("test.mosquitto.org", 60)
            break
        except Exception as e:
            print("connecting...")
    print("connected.")
 
    #aqui o ESP8266 assina os tópicos abaixo
    client.subscribe([["desktop/samples",1]])
    client.subscribe([["desktop/others",2]])
   
    #habilita a publicação de dados
    client.on(mqtt.PUBLISH,print_sample,is_sample)
   
    client.loop(print_other)
   
#dentro desse loop medimos a tensão que o sensor fornece para entrada analógica do ESP8266 e convertemos num valor de temperatura.
    while True:
        sleep(3000)
        value = adc.read(A0)
        print(value)
        Vout = (value * VCC) / adcRes
        Rth = (VCC * R2 / Vout) - R2
        temperature = (1 / (A + (B * math.log(Rth)) + (C * math.pow((math.log(Rth)),3))))
        temperature = temperature - 292.15
        temperature = -1*(temperature)
        
        #printamos o valor pela serial e logo em seguida enviamos o valor calculado para o Broker MQTT Mosquitto
        print(temperature)
        send_sample(temperature)
        if temperature%10==0:
            publish_to_self()#caso ocorra alguma exceção ou erro, a temperatura publicada é um valor aleatório de 0 a 10
except Exception as e:
    print(e)
      
