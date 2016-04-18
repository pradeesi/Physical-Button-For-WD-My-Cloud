------------------------------------------
--- Author: Pradeep Singh
--- Date: 2nd April 2016
--- Version: 1.0
--- NodeMCU Firmware: nodemcu_float_0.9.6-dev_20150704.bin
--- Description: This is sample code to send MQTT msg to WD My Cloud NAS to shut it down.
------------------------------------------


-----------------------------------------------
--- Variables Block ---
-----------------------------------------------
--- WIFI CONFIGURATION ---
WIFI_SSID = "joker"
WIFI_PASSWORD = "avengers"
WIFI_SIGNAL_MODE = wifi.PHYMODE_N

--- WiFi IP CONFIG (Leave blank to use DHCP) ---
ESP8266_IP=""
ESP8266_NETMASK=""
ESP8266_GATEWAY=""


--- MQTT Configuration ---
MQTT_BROKER = "iot.eclipse.org"
MQTT_BROKER_PORT = "1883"
MQTT_BROKER_SECURE = 0

MQTT_PUBLISH_TOPIC = "/india/karnataka/bangalore/ecity/ajmera/avenye/7"
MQTT_PUBLISH_MESSAGE = "Shutdown"
MQTT_PUBLISH_TOPIC_QoS = 0
MQTT_PUBLISH_TOPIC_RETAIN = 0

MQTT_CLIENT_ID = (wifi.sta.getmac())
MQTT_CLIENT_USER = "username"
MQTT_CLIENT_PASSWORD = "password"
MQTT_CLIENT_KEEPALIVE_TIME = 45

MQTT_RECONNECT =1


--- GPIO PIN Configuration ---
BUTTON_GPIO_PIN = 3
LED_PIN = 4


--- Reserved Variables (Don Not Change) ---
IS_WIFI_READY = 0
STATUS_CHECK_COUNTER = 0
STOP_AFTER_ATTEMPTS = 45
MAX_LED_BLINKS = 4
-----------------------------------------------


-----------------------------------------------
--- Code Block ---
-----------------------------------------------

--- Connect to the wifi network ---
wifi.setmode(wifi.STATION) 
wifi.setphymode(WIFI_SIGNAL_MODE)
wifi.sta.config(WIFI_SSID, WIFI_PASSWORD) 
wifi.sta.connect()

if ESP8266_IP ~= "" then
 wifi.sta.setip({ip=ESP8266_IP,netmask=ESP8266_NETMASK,gateway=ESP8266_GATEWAY})
end


--- Check WiFi Connection Status ---
function get_WiFi_Status()
   ip_Add = wifi.sta.getip()
     if ip_Add ~= nill then
          print('Connected with WiFi. IP Add: ' .. ip_Add)
          IS_WIFI_READY = 1
          tmr.stop(0)
          initiate_MQTT_Session()
          print ("Registered with MQTT Broker")
     end
end


--- Initiate MQTT Session with Broker ---
function initiate_MQTT_Session()
     --- Initiate MQTT Client ---
     mqtt_Client = mqtt.Client(MQTT_CLIENT_ID, MQTT_CLIENT_KEEPALIVE_TIME, MQTT_CLIENT_USER, MQTT_CLIENT_PASSWORD)

     --- On Connect Event ---
     mqtt_Client:on("connect", function(con) end)

     --- On Message Recieve Event ---
     mqtt_Client:on("message", function(conn, topic, data)
     	if data == MQTT_PUBLISH_MESSAGE then
     		led_Blinker()
        end
     end)

     --- Connect with MQTT Broker ---
     mqtt_Client:connect(MQTT_BROKER, MQTT_BROKER_PORT, MQTT_BROKER_SECURE, MQTT_RECONNECT, function(conn) 
          -- Subscribe to Topic ---
          mqtt_Client:subscribe(MQTT_PUBLISH_TOPIC,MQTT_PUBLISH_TOPIC_QoS, function(conn) end) 
    end)
end



-- Interrupt Call/Function ---
function onChange()
     if IS_WIFI_READY == 1 then
         if gpio.read(BUTTON_GPIO_PIN) == 0 then
               -- Publish to MQTT Topic ---
               mqtt_Client:publish(MQTT_PUBLISH_TOPIC, MQTT_PUBLISH_MESSAGE, MQTT_PUBLISH_TOPIC_QoS, MQTT_PUBLISH_TOPIC_RETAIN, function(conn) end)
         end
     end
end


-- Configure GPIO Interrupt for GPIO_PIN1 ---
gpio.mode(BUTTON_GPIO_PIN, gpio.INT, gpio.PULLUP)
gpio.trig(BUTTON_GPIO_PIN, 'down' , onChange)


-- Configure LED Pin and Pull it Down ---
gpio.mode(LED_PIN, gpio.OUTPUT)
gpio.write(LED_PIN, gpio.LOW)


--- Check WiFi Status before starting anything ---
tmr.alarm(0, 1000, 1, function() 
     
     get_WiFi_Status()
     tmr.delay(1000)

     --- Stop from getting into infinite loop ---
     STATUS_CHECK_COUNTER = STATUS_CHECK_COUNTER + 1
     if STOP_AFTER_ATTEMPTS == STATUS_CHECK_COUNTER then
          tmr.stop(0)
     end  
end)

--- LED Blinker ---
function led_Blinker()
	Counter = 0
	tmr.alarm(1, 300, 1, function()
		if gpio.read(LED_PIN) == gpio.LOW then
			gpio.write(LED_PIN, gpio.HIGH)
		else
			gpio.write(LED_PIN, gpio.LOW)
		end 

	    Counter = Counter +1
	    if Counter == MAX_LED_BLINKS then
	    	tmr.stop(1)
	    	gpio.write(LED_PIN, gpio.LOW)
	    end  
	end)
end
-----------------------------------------------
