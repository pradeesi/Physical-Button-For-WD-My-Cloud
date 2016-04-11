-----------------------------------------------
--- Set Variables ---
-----------------------------------------------
--- Change Following three Variables ---
WIFI_SSID = "your wifi network name"
WIFI_PASSWORD = "your wifi password"
MQTT_PUBLISH_TOPIC = "your MQTT topic which you selected while configuring WD My Cloud Step # 10"
-----------------------------------------------

--- GPIO Config ---
local int BUTTON_GPIO_PIN = 3
--- MQTT Configuration ---
MQTT_BROKER = "iot.eclipse.org"
MQTT_BROKER_PORT = 1883
MQTT_BROKER_SECURE = 0
MQTT_PUBLISH_MESSAGE = "Shutdown"
MQTT_CLIENT_ID = (wifi.sta.getmac())
-----------------------------------------------

--- Connect to the wifi network ---
wifi.setmode(wifi.STATION) 
wifi.sta.config(WIFI_SSID,WIFI_PASSWORD)
wifi.sta.connect()

--- Initiate MQTT Client ---
mqtt = mqtt.Client(MQTT_CLIENT_ID, 45, "username", "password")

--- Connect to MQTT Broker ----
mqtt:connect(MQTT_BROKER, MQTT_BROKER_PORT, MQTT_BROKER_SECURE, function(conn) end)

-- Interrupt Call/Function (For Posting Status of GPIO Pin)
function onChange()
    if gpio.read(BUTTON_GPIO_PIN) == 0 then
          -- Publish to MQTT Topic ---
          mqtt:publish(MQTT_PUBLISH_TOPIC, MQTT_PUBLISH_MESSAGE, 0, 0, function(conn) end)
    end
end

-- Configure GPIO Interrupt for GPIO_PIN1
gpio.mode(BUTTON_GPIO_PIN, gpio.INT, gpio.PULLUP)
gpio.trig(BUTTON_GPIO_PIN, 'down' , onChange)