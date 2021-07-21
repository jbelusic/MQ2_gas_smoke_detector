import wifimgr
from   time import sleep
import machine
import gc
from machine import Timer, ADC, Pin

import mqtt_config_data
from mqtt import MQTTClient

#import esp
#print(esp.flash_id()) 

gc.collect()

def restart_and_reconnect():
  print('Reconnecting...')
  sleep(1)
  machine.reset()

def set_web_server():
  try:
    print("Starting web server after 5 sec...")
    sleep(5)
    for _ in range(5):
      print('.', end='')
      web_server_started = wifimgr.set_web_server()
      if web_server_started:
        restart_and_reconnect()
  except:
    print("general exception in set_web_server")

btn_set_web_server = False # web server activate button
#btn_set_web_server = Pin(14, Pin.IN, Pin.PULL_UP) #GPIO 14 -> D5 - web server activate button
# Try to check and wait 5 seconds to start web server if button pressed
if btn_set_web_server:
  sleep(5)
  set_web_server()

led_board = Pin(2, Pin.OUT) #GPIO 2 -> D4 # Pin is HIGH on BOOT, boot may failure if pulled LOW

is_reconnected = False

def connect_to_wlan():
  try:
    set_ap = False
    print("Trying to connect...")
    wlan = wifimgr.get_connection(set_ap)
    if not wlan:
      print("wlan not found and not connected.")
      return False
    print("Connected to wlan!")
    return True
  except:
    print("general exception in connect_to_wlan")
    return False

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
is_wlan = connect_to_wlan()
print("ESP Connected to wlan!" if is_wlan else "ESP Not connected to wlan!")

#************* MQTT *************#
gc.collect()

my_mqtt_data  = mqtt_config_data.get_data_tuple()
my_broker     = str(my_mqtt_data[0])
my_brokeruser = str(my_mqtt_data[1])
my_brokerpass = str(my_mqtt_data[2])
my_brokerport = int(my_mqtt_data[3])
my_client_id  = str(my_mqtt_data[4])
my_sub_topic  = str(my_mqtt_data[5])
my_pub_topic  = str(my_mqtt_data[6])
my_pub_status = str(my_mqtt_data[7])
my_keepalive  = int(my_mqtt_data[8])

print("Memory free:",gc.mem_free())
gc.collect()

# ######################### Get MQTT message (operational) ##############################
def connect_and_subscribe():
  global my_client_id, my_broker, my_brokerport, my_brokeruser, my_brokerpass, my_keepalive, my_pub_status, my_sub_topic
  try:
    print("Initiate MQTTClient...")
    client = MQTTClient(client_id = my_client_id,
                        server    = my_broker,
                        port      = my_brokerport,
                        user      = my_brokeruser,
                        password  = my_brokerpass,
                        keepalive = my_keepalive)
    print("MQTTClient initiated.")
    #client.set_callback(sub_cb) # U mojem slučaju nema callback nego samo senzor radi publish
    #client.settimeout = settimeout
    client.set_last_will(topic=my_pub_status, msg=b"OFFLINE", retain=True)
    print("Connecting to MQTTClient...")
    try:
      client.connect()
      #client.subscribe(topic = my_sub_topic)
      print('Connected to MQTT broker: %s, subscribed to topic: %s' % (my_broker, my_sub_topic))
      print("Sending status AVLB")
      client.publish(topic=my_pub_status, msg=b"AVLB", retain=False)
      sleep(1)
    except:
      print("Mqtt broker offline, cannot connect!")
      return False

    return client
  except:
    print("connect_and_subscribe general exception")
    return False

def mqtt_reconnect(mqtt_client):
  try:
    print("mqtt_reconnect started")
    try:
      mqtt_client.disconnect()
    except:
      print("Error mqtt client disconnecting")
      sleep(0.5)
    mqtt_client = connect_and_subscribe()   
    sleep(1)
    if mqtt_client:
        print("Client Reconnected")
        return True, mqtt_client
    print("Client not reconnected")
    return False, mqtt_client
  except:
    print("Error mqtt client reconnecting")
    return False, mqtt_client

gc.collect()

try:
  print("Starting program...")
  mqtt_client = connect_and_subscribe()
  if is_wlan:
    print("Program started Online.")
  else:
    print("Program started Offline.")
  led_board.value(1)
except OSError as e:
  print("OSError in starting program")
except:
  print("Other exception")
#************* END MQTT *************#


#************** Reading sensor status ***************#
gas = Pin(12, Pin.IN) #Pin12 -> GPIO12 -> D6
    
# Heating sensor...
print("Sensors is heating and starting up, pleas wait for 20 seconds...")
for i in range(20, 0, -1):
  print(i, end=",")
  sleep(1)
#if gas.value() == 0:
#    mqtt_client.publish(topic=my_pub_status, msg="ON", retain=True)

# ########################### MAIN LOOP ###################################
cnt = 0
is_connected = True
last_reading_value = 1
gas_value = 1
gas_status = "OFF"
print("")
print("Main LOOP...")
while True:
  cnt += 1
  try:
    if gc.mem_free() < 102000:
      gc.collect()

    try:
        mqtt_client.check_msg()
        mqtt_client.ping()
        
        #mqtt_client.publish(topic=my_pub_status, msg=b"AVLB", retain=False)
        gas_value = gas.value()
        if gas_value == 0:
            gas_status = "ON" # When 0 is readed then there is a gas leaking
        if gas_value == 1:
            gas_status = "OFF"
        #print(gas_status)
        #print("last_reading_value",last_reading_value,"gas_value",gas_value)
        if last_reading_value != gas_value:
            print("Gas or smoke", gas_status)
            mqtt_client.publish(topic=my_pub_status, msg=gas_status, retain=True)
            #last_reading_value = gas_value
        #mqtt_client.publish(topic=my_pub_status, msg=gas_status, retain=True)
        last_reading_value = gas_value    
    except Exception as e:
        print("Error reading gas status,",str(e))
        if "Errno 104" in str(e) or "Errno 103" in str(e):
            is_connected = False
            print("Broker is unavailable, trying to connect to broker...")
            is_connected, mqtt_client = mqtt_reconnect(mqtt_client)
        
    sleep(1)
    
  except OSError as e:
    print("General error", str(e))
    pass

try:
  mqtt_client.disconnect()
except:
  print("Problem disconnecting client on program end")

print("End program!")
