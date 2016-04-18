##------------------------------------------
##--- Author: Pradeep Singh
##--- Date: 2nd April 2016
##--- Version: 1.0
##--- WD MY Cloud Firmware: WDMyCloud v04.04.02-105 : Core F/W
##--- Python Ver: 2.7
##--- Description: This python code will listen on MQTT and shutdown WD MY Cloud
##--- This file includes print statements to make it easy to troubleshoot the connection
##------------------------------------------

import requests
import xml.etree.ElementTree as ET
import time
import paho.mqtt.client as mqtt
import os, socket

##==================================================##
##---------------- SET VARIABLES -------------------##
##==================================================##
##--- Change following 3 variables ---
USER_NAME = "put UI User Name Here" 
PASSWORD = "put UI User Password Here"
MQTT_TOPIC = "put MQTT Topic here"

MQTT_HOST = "iot.eclipse.org"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
INTERNET_CONNECTION_TEST_URL = 'http://www.google.com/'
##==================================================##


##==================================================================================##
##----- Test Internet Connection Before Proceeding Further -----##
##----- As we are using public MQTT Broker, Internet connectivity is Must -----##
##==================================================================================##
def is_connected_to_internet(url, timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
		pass
    return False

while True:
	if (is_connected_to_internet(INTERNET_CONNECTION_TEST_URL)):
		break
	else:
		time.sleep(60)
##==================================================================================##



##==================================================================================##
##-----GET IP ADDRESS OF LOCAL SYSTEM (Used Internally by 'get_System_Details')-----##
##==================================================================================##
if os.name != "nt":
    import fcntl
    import struct

def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip
#=====================================================================================

# Get the WD MY Cloud IP to make REST Calls
WD_MY_CLOUD_HOST_NAME = get_lan_ip()

#=====================================================================================


##==================================================##
##---------------- REST URLs -----------------------##
##==================================================##
login_URL = "http://" + WD_MY_CLOUD_HOST_NAME + "/api/2.1/rest/local_login?username=" + USER_NAME + "&password=" + PASSWORD
logout_URL = "http://" + WD_MY_CLOUD_HOST_NAME + "/api/2.1/rest/logout"
usb_Drive_URL = "http://" + WD_MY_CLOUD_HOST_NAME +  "/api/2.1/rest/usb_drives"
usb_UnMount_Base_URL = "http://" + WD_MY_CLOUD_HOST_NAME + "/api/2.1/rest/usb_drive/"
restart_URL = "http://" + WD_MY_CLOUD_HOST_NAME +  "/api/2.1/rest/shutdown?state=reboot"
shutdown_URL = "http://" + WD_MY_CLOUD_HOST_NAME +  "/api/2.1/rest/shutdown?state=halt"
system_State_URL = "http://" + WD_MY_CLOUD_HOST_NAME +  "/api/2.1/rest/system_state"
##==================================================##


##==================================================##
##---------------- INITIALIZE ---------------##
##==================================================##
## Disable Warning for HTTPS requests 
requests.packages.urllib3.disable_warnings()

#Initialize Login Session
login_Session = requests.session()
##==================================================##


##==================================================##
##---------------- HTTP REST REQUEST ---------------##
##==================================================##
def http_REST_REQUEST(url, type):
	
	Response = None
	ErrorMsg = None
	
	try:
		if type == "GET":
			Response = login_Session.get(url)
		elif type == "PUT":
			Response = login_Session.put(url)			
		elif type == "DELETE":
			Response = login_Session.delete(url)
			
	except requests.exceptions.ConnectionError:
		ErrorMsg = "Connection Error. Please check the Network Connectivity and verify WD My Cloud Host-Name/IP Address."
		return Response, ErrorMsg
	except requests.exceptions.HTTPError:
		ErrorMsg = "HTTP Error, Error occurred during HTTP" + type + "Request."
		return Response, ErrorMsg
	except requests.exceptions.Timeout:
		ErrorMsg = "Request Timed Out, while trying HTTP" + type + "Request."
		return Response, ErrorMsg		
	except:
		ErrorMsg = "Error in HTTP" + type + "Request."
		return Response, ErrorMsg
		
	return Response, ErrorMsg	
##==================================================##



##==================================================##
##-------------------LOGIN METHOD-------------------##
##==================================================##
def login():
	
	global login_URL
	
	login_Response, ErrorMsg = http_REST_REQUEST(login_URL, "GET")
	if login_Response != None and ErrorMsg == None:
		try:
			xml_Tree = ET.fromstring(login_Response.text)
			node = xml_Tree.find('status')
			if node.text != 'success':
				ErrorMsg = "Failed to Login to WD My Cloud at " + WD_MY_CLOUD_HOST_NAME
				return login_Response, ErrorMsg
		except:
			try:
				node = xml_Tree.find('error_message')
				if node.text == 'Unauthenticated login':
					ErrorMsg = "Failed to Login to WD My Cloud. Invalid User Name or Password."
					return login_Response, ErrorMsg
			except:
				ErrorMsg = "Error: Invalid response or Response XML has got changed. XML Response: " + (login_Response.text if login_Response != None else "None") 

	return login_Response, ErrorMsg
##==================================================##	
	

##==================================================##
##-------------------LOGOUT METHOD-------------------##
##==================================================##
def logout():
	
	global logout_URL
	
	logout_Response, ErrorMsg = http_REST_REQUEST(logout_URL, "GET")
	if logout_Response != None and ErrorMsg == None:
		try:
			xml_Tree = ET.fromstring(logout_Response.text)
			node = xml_Tree.find('status')
			if node.text != 'success':
				ErrorMsg = "Failed to Logout from WD My Cloud at " + WD_MY_CLOUD_HOST_NAME
				return logout_Response, ErrorMsg
		except:
			try:
				node = xml_Tree.find('error_message')
				ErrorMsg = "Error: " + node.text + ". " + " XML Response: " + (logout_Response.text if logout_Response != None else "None") 
				return logout_Response, ErrorMsg
			except:
				ErrorMsg = "Error: Invalid response or Response XML has got changed. XML Response: " + (logout_Response.text if logout_Response != None else "None") 

	return logout_Response, ErrorMsg
##==================================================##		
	
	
##==================================================##
##----------------CHECK USB METHOD------------------##
##==================================================##
def check_USB():
	
	usb_Handle = "-1"
	global usb_Drive_URL
	
	check_USB_Response, ErrorMsg = http_REST_REQUEST(usb_Drive_URL, "GET")

	if check_USB_Response != None and ErrorMsg == None:
		try:	
			xml_Tree = ET.fromstring(check_USB_Response.text)
			usb_List = xml_Tree.find('usb_drive')
			handle = usb_List.find('handle')
			usb_Handle = handle.text
			
			if usb_Handle != None:
				return check_USB_Response, ErrorMsg, usb_Handle
			else:
				ErrorMsg = "Error: Unable to find USB Drive"
				return check_USB_Response, ErrorMsg, usb_Handle				
		except:
			ErrorMsg = "Error: Unable to parse USB XML. XML Response: " + (check_USB_Response.text if check_USB_Response != None else "None")
			return check_USB_Response, ErrorMsg, usb_Handle
	
	return check_USB_Response, ErrorMsg, usb_Handle	
##==================================================##	
	
	
	
##==================================================##
##---------------UNMOUNT USB METHOD-----------------##
##==================================================##	
def unmount_USB(usb_Handle):

	global usb_UnMount_Base_URL
	usb_UnMount_URL = usb_UnMount_Base_URL + usb_Handle
	
	unmount_Response, ErrorMsg = http_REST_REQUEST(usb_UnMount_URL, "DELETE")
	
	if unmount_Response != None and ErrorMsg == None:
		try:
			xml_Tree = ET.fromstring(unmount_Response.text)
			node = xml_Tree.find('status')
			if node.text != 'success':
				ErrorMsg = "Error: Failed to un-mount the USB Drive"
				return unmount_Response, ErrorMsg
			else:
				time.sleep(2)
		except:
			try:
				node = xml_Tree.find('error_message')
				if node.text == 'Drive not found':
					ErrorMsg = "Error: Invalid USB Drive Handle. Drive Not Found."
					return unmount_Response, ErrorMsg
			except:
				ErrorMsg = "Error: Invalid response or Response XML has got changed. XML Response: " + (unmount_Response.text if unmount_Response != None else "None")

	return unmount_Response, ErrorMsg			
	
##==================================================##	
	

	
##==================================================##
##-----------------RESTART METHOD-------------------##
##==================================================##	
def restart():
	
	global restart_URL

	restart_Response, ErrorMsg = http_REST_REQUEST(restart_URL, "PUT")
	print restart_Response.text
	if restart_Response != None and ErrorMsg == None:
		try:
			xml_Tree = ET.fromstring(restart_Response.text)
			node = xml_Tree.find('status')
			if node.text != 'success':
				ErrorMsg = "Failed to submit Restart Command." + (restart_Response.text if restart_Response != None else "None")
				return restart_Response, ErrorMsg
		except:
			try:
				node = xml_Tree.find('error_message')
				ErrorMsg = "Error: " + node.text + ". " + (restart_Response.text if restart_Response != None else "None")
				return restart_Response, ErrorMsg
			except:
				ErrorMsg = "Error: Invalid response or Response XML has got changed. XML Response: " + (restart_Response.text if restart_Response != None else "None")

	return restart_Response, ErrorMsg
##==================================================##



##==================================================##
##----------------SHUTDOWN METHOD-------------------##
##==================================================##	
def shutdown():
	
	global shutdown_URL
	
	shutdown_Response, ErrorMsg = http_REST_REQUEST(shutdown_URL, "PUT")
	
	if shutdown_Response != None and ErrorMsg == None:
		try:
			xml_Tree = ET.fromstring(shutdown_Response.text)
			node = xml_Tree.find('status')
			if node.text != 'success':
				ErrorMsg = "Failed to submit Shutdown Command." + (shutdown_Response.text if shutdown_Response != None else "None")
				return shutdown_Response, ErrorMsg
		except:
			try:
				node = xml_Tree.find('error_message')
				ErrorMsg =  "Error: " + node.text + ". " + (shutdown_Response.text if shutdown_Response != None else "None")
				return shutdown_Response, ErrorMsg
			except:
				ErrorMsg = "Error: Invalid response or Response XML has got changed. XML Response: " + (shutdown_Response.text if shutdown_Response != None else "None")

	return shutdown_Response, ErrorMsg
##==================================================##



##==================================================##
##----------------SYSTEM STATE METHOD-------------------##
##==================================================##	
def system_State():
	
	global system_State_URL
	Status = ''
	Temperature = ''
	Reported_Status = ''
	Smart = ''
	Volume = ''
	FreeSpace = ''
	
	system_State_Response, ErrorMsg = http_REST_REQUEST(system_State_URL, "GET")
	
	if system_State_Response != None and ErrorMsg == None:
		try:
			xml_Tree = ET.fromstring(system_State_Response.text)
			node = xml_Tree.find('status')
			Status = node.text
			node = xml_Tree.find('temperature')	
			Temperature = node.text
			node = xml_Tree.find('reported_status')			
			Reported_Status = node.text
			node = xml_Tree.find('smart')	
			Smart =  node.text
			node = xml_Tree.find('volume')	
			Volume =  node.text
			node = xml_Tree.find('free_space')	
			FreeSpace =  node.text			
			return system_State_Response, ErrorMsg, Status, Temperature, Reported_Status, Smart, Volume, FreeSpace
			
		except:
			try:
				node = xml_Tree.find('error_message')
				ErrorMsg =  "Error: " + node.text + ". " + (system_State_Response.text if system_State_Response != None else "None")
				
				return system_State_Response, ErrorMsg, Status, Temperature, Reported_Status, Smart, Volume, FreeSpace
			
			except:
				ErrorMsg = "Error: Invalid response or Response XML has got changed. XML Response: " + (system_State_Response.text if system_State_Response != None else "None")

	return system_State_Response, ErrorMsg, Status, Temperature, Reported_Status, Smart, Volume, FreeSpace
##==================================================##


	
##==================================================##
##----------------- STEP METHOD---------------------##
##==================================================##	
Step = 0
def counter():
	global Step
	Step = Step + 1
	return ('Step ' + str(Step) + ': ')
##==================================================##



##==================================================##
##---------------- Task/Activities -----------------##
##==================================================##

##==================================================##
def task_Login():
	# Login to WD My Cloud	
	print counter() + "Logging into WD My Cloud" + " @ " + WD_MY_CLOUD_HOST_NAME + "..." 
	login_Response, login_Error = login()

	if login_Error == None:
		print "Successfully Logged into WD My Cloud..."
	else:
		print "Error: " + "Failed to login to WD My Cloud..."
		print "Error Message: "
		print login_Error
		raise SystemExit
##==================================================##

##==================================================##
def task_Logout():
	# Login to WD My Cloud	
	print counter() + "Logging Out from WD My Cloud" + " @ " + WD_MY_CLOUD_HOST_NAME + "..." 
	logout_Response, logout_Error = logout()

	if logout_Error == None:
		print "Successfully Logged Out from WD My Cloud..."
	else:
		print "Error: " + "Failed to Logout from WD My Cloud..."
		print "Error Message: "
		print logout_Error
##==================================================##


##==================================================##
def task_UnMount_USB_Drive():

	# Check if External USB Drive is connected to WD My Cloud
	print counter() + "Checking external USB Drive..."
	usb_List_Response, usb_Check_Error, usb_Handle = check_USB()

	# If External USB Drive is connected, Unmount it.
	if usb_Check_Error == None and usb_Handle != "-1":
		print "Found USB Drive connected with USB 3.0 Port..."
		print counter() + "Trying to Un-mount the external USB Drive..."
		unmount_Response,unmount_Error = unmount_USB(usb_Handle)
		if unmount_Error == None:
			
			print "Successfully un-mounted external USB Drive..."
		else:
			print "Failed to un-mount external USB Drive..."
			print "Error Message: "
			print unmount_Error
	else:
		print "No USB Device Found..."
##==================================================##


##==================================================##
def task_Restart():
	#Restart WD My Cloud
	print counter() + "Trying to Restart WD My Cloud..."
	restart_Response, restart_Error = restart()
	
	if restart_Error == None:
		print "Successfully issued Restart Command to WD My Cloud..."
	else:
		print "Error: " + "Failed to Restart WD My Cloud..."
		print "Error Message: "
		print restart_Error
##==================================================##


##==================================================##
def task_Shutdown():
	print counter() + "Trying to Shutdown WD My Cloud..."
	shutdown_Response, shutdown_Error = shutdown()

	if shutdown_Error == None:
		print "Successfully issued Shutdown Command to WD My Cloud..."
	else:
		print "Error: " + "Failed to Shutdown WD My Cloud..."
		print "Error Message: "
		print shutdown_Error
##==================================================##

##==================================================##
def task_System_State():
	print counter() + "Trying to get WD My Cloud system state..."
	system_State_Response, system_State_Error, Status, Temperature, Reported_Status, Smart, Volume, FreeSpace = system_State()

	if system_State_Error == None:
		print "-----------------------------------"
		print "Current System State:"
		print "-----------------------------------"
		print "Status: " + Status
		print "Reported Status: " + Reported_Status
		print "Temperature: " + Temperature
		print "Smart: " + Smart
		print "Volume: " + Volume
		print "Free Space: " + FreeSpace
		print "-----------------------------------"
	else:
		print "Error: " + "Failed to check WD My Cloud system state..."
		print "Error Message: "
		print system_State_Error
##==================================================##

##==================================================##
##--------------ACTION-TASK SEQUENCE ---------------##
##==================================================##	

def my_Cloud_UnMount_USB():
	task_Login()
	task_UnMount_USB_Drive()
	task_Logout()
	
def my_Cloud_Restart():
	task_Login()
	task_UnMount_USB_Drive()
	task_Restart()
	
def my_Cloud_Shutdown():
	task_Login()
	task_UnMount_USB_Drive()
	task_Shutdown()
	
def my_Cloud_System_State():
	task_Login()
	task_System_State()
	task_Logout()
	
##==================================================##



##==================================================##
##----------- INVOKE ACTION USING MQTT  ------------##
##==================================================##	

# Define on connect event function
# We shall subscribe to our Topic in this function
def on_connect(mosq, obj, rc):
	try:
		mqttc.subscribe(MQTT_TOPIC, 0)
	except:
		pass

# Define on_message event function. 
def on_message(mosq, obj, msg):
	try:
		if (str(MQTT_TOPIC) == str(msg.topic)):
			if (str(msg.payload) == "Shutdown"):
				my_Cloud_Shutdown()
			elif (str(msg.payload) == "Restart"):
				my_Cloud_Restart()
			elif (str(msg.payload) == "Unmount"):
				my_Cloud_UnMount_USB()
	except:
		pass
 
 # Initiate MQTT Client
mqttc = mqtt.Client()

# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

# Continue monitoring the incoming messages for subscribed topic
mqttc.loop_forever()
##==================================================##
