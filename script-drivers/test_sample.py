import asyncio
import json
import os
import threading
import redis
import websockets
import requests  # Import the requests library
from datetime import datetime
from disk_space_checker import DiskSpaceChecker
from get_network_interfaces import NetworkInterfaceChecker
import socket
import re
from datetime import datetime
from file_util import FileUtils
import logging
import ast
from LogSender import LogSender

# Create an instance of FileUtils
file_util_common = FileUtils()
# Access the folder path
today_folder_path = file_util_common.today_folder_path

# Generate a timestamp with seconds
timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")

# Lock to control access to the execution status
execution_lock = threading.Lock()
ip_addresses = []
ip_to_process = None
global_done_ip_list = []
websocket_connections = []

# Global flag to indicate whether executions should be stopped
stop_execution = False

# Function to assign or extend the ip_addresses dictionary
def assign_or_extend_ip_addresses(new_addresses):
    global ip_addresses
    ip_addresses.update(new_addresses)


# def run_script(script_name, *args):
#     print(script_name)
#     if script_name in SCRIPT_EXECUTORS:
#         executor = SCRIPT_EXECUTORS[script_name]
#         # Get the class name
#         class_name = executor.__qualname__.split('.')[0]
#         run_obj = class_name()
#         print(class_name)
#         executor(*args)
#     else:
#         print(f"Script '{script_name}' not found in SCRIPT_EXECUTORS")

# # Define a dictionary to map script names to their execution functions
SCRIPT_EXECUTORS = {
    "disk_space_checker": DiskSpaceChecker.get_disk_space,
    "network_interface_checker": NetworkInterfaceChecker.get_network_interfaces,
    # Add more scripts and corresponding execution functions here
}
# Define a dictionary to map script names to a tuple containing class and method names
# SCRIPT_EXECUTORS = {
#     "disk_space_checker": (DiskSpaceChecker, "get_disk_space"),
#     # Add more scripts and corresponding classes/methods here
# }

# Define your constants and configuration here
MAX_RETRIES = 2
RETRY_DELAY = 5
channelName = 'scripts'
WEBSOCKET_URL = f"ws://localhost:8000/ws/netgeni/scripts/"
API_URL = "http://localhost:8000/api/scripts/network-devices/list/"

def check_for_stop_message():
    global stop_execution
    global ip_to_process
    global global_done_ip_list
    print(ip_to_process)

    try:
        async def receive_messages():
           
            print('receive_messages')
            async with websockets.connect(WEBSOCKET_URL, timeout=5) as socket:
                while True:
                    message = await socket.recv()
                    if message:
                        message_dict = json.loads(message)
                        message_text = message_dict.get("message", "").lower()
                        print(message_text)
                        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
                        ip_match = re.search(ip_pattern, message_text)
                 
                        if ip_match:
                            ip_address = ip_match.group()
                            print(ip_address)
                            global_done_ip_list.append(ip_address)
                        print(global_done_ip_list)

                        # print(message_text["message"])
                        # Convert the dictionary to a JSON-formatted string
                        # json_string = json.dumps(message_text)

                        # print(json_string)
                        # print('check_for_stop_message')
                        # print(json_string)
                        # print(f"Received WebSocket message: {message_text}")
                        if 'stop' in message_text:
                            print("Received 'stop' command. Stopping execution...")
                            stop_execution = True
                        elif "done" in message_text:
                            print("Post processing...")
                            await publish_websocket_message("preparing logs", "", "")
                            
                            data_sender = LogSender()
                            data_sender.iterate_folders_and_send_to_api(global_done_ip_list)
                            stop_execution = True
                            break
                        # else:
                        #     stop_execution = False

        asyncio.run(receive_messages())
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed unexpectedly.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Define a class to encapsulate the script execution logic
class ScriptExecutor:
    def __init__(self):
        self.websocket = None
        self.execution_status = {}  # D
        self.socket = None  # Initialize WebSocket connection attribut
    
    async def publish_websocket_message(self, message, script_name, ip_address):
        global stop_execution
        if stop_execution:  # Check if stop flag is set
            print("WebSocket publishing stopped.")
            return  # Skip publishing

        # Define the WebSocket URL for your Django Channels WebSocket consumer
        # websocket_url = "ws://192.168.1.103:8000/ws/scriptchat/run_script/"
        # message_data = f"{message} '{script_name}' on {ip_address}"

        message_data = {
                "message":  f"{message}, {script_name}, {ip_address}",
            
            }
        print(message_data)

        for attempt in range(MAX_RETRIES):
            try:
                async with websockets.connect(WEBSOCKET_URL, timeout=5) as socket:
                    # Serialize the dictionary to JSON
                    message_json = json.dumps(message_data)
                    # Send the JSON data as a string
                    await socket.send(message_json)
                    response = await socket.recv()
               
            except asyncio.TimeoutError as timeout_error:
                print(f"WebSocket Timeout Error: {timeout_error}")
            except websockets.exceptions.WebSocketError as ws_error:
                print(f"WebSocket Error: {ws_error}")
            except Exception as e:
                print(f"An error occurred: {e}")

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print("Maximum retry attempts reached, giving up.")
            if socket and not socket.closed:
                await socket.close()

    # Define a function to execute a single script on a single IP address
    async def execute_script(self, script_name, ip_address):
        print(script_name, ip_address)
        global stop_execution
    
        if stop_execution:
            print(f"WebSocket publishing stopped for '{script_name}' on '{ip_address}'.")
            return
        
        try:
            if not stop_execution:
                ip_folder_path = os.path.join(today_folder_path, ip_address, script_name)
                file_util_common.create_folder_if_not_exists(ip_folder_path)
                print(f"Received command to execute '{script_name}' on '{ip_address}'")
                print(f"Executing '{script_name}' on {ip_address}")
                await self.publish_websocket_message("start", script_name, ip_address)
                await self.publish_websocket_message("executing", script_name, ip_address)
                print(f"Finished executing '{script_name}' on {ip_address}")
                await self.publish_websocket_message("done", script_name, ip_address)
        except Exception as e:
            print(f"An error occurred: {e}")

    # Your existing execute_scripts function with added threading
    async def execute_scripts(self):
        global stop_execution
        global ip_to_process
        if stop_execution:
            print("WebSocket publishing stopped.")
            return
        
        script_count = len(SCRIPT_EXECUTORS)  # Get the script count
        completed_scripts = 0

        try:
            # threads = []

            for script_name in SCRIPT_EXECUTORS:
                for ip_address in ip_addresses:
                    
                    if stop_execution:
                        print("Execution stopped.")
                        return

                    executor = SCRIPT_EXECUTORS[script_name]
                    if executor:
                        ip_to_process = ip_address
                        class_name = executor.__qualname__.split('.')[0]
                        func_name = executor.__qualname__.split('.')[1]
                    # Create an instance of the class


                        print(class_name, func_name)
                        class_instance = globals()[class_name](ip_address)
                        func = getattr(class_instance, func_name)

                        # Run the function
                        func()

                        # reseult = run_obj

                        # func = getattr(class_instance, func_name)
                        # result = func()  # Assuming your function takes no arguments


                        # Create a separate thread to execute the script
                        # script_thread = threading.Thread(target=self.execute_script_thread, args=(run_obj, func_name))
                        # script_thread.start()
                        # Wait for the script thread to complete
                        # script_thread.join()
                        print(f"Thread for '{func_name}' on {ip_address} has completed.")

                        # Publish a message indicating the execution is done
                        await self.publish_websocket_message("done", func_name, ip_address)

                    else:
                        print(f"No executor found for script '{script_name}'")

            
            if completed_scripts == script_count * len(ip_addresses):
                await self.publish_websocket_message("alldone", "all", "all")

        except Exception as e:
            print(f"An error occurred: {e}")


async def get_ip_addresses_from_endpoint():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            ip_addresses = [device['ip_address'] for device in data if device.get('status') is True]
            return ip_addresses
        else:
            print(f"Failed to retrieve IP addresses from the endpoint. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while fetching IP addresses: {e}")
    return []

async def listen_to_redis_messages(script_executor):
    global ip_addresses
    global stop_execution

    # #remove
    print('indide listen')
    extracted_ips = await get_ip_addresses_from_endpoint()
    print(extracted_ips)
    ip_addresses.extend(extracted_ips)
    await script_executor.execute_scripts()
    return

    try:
        redis_client = redis.Redis(host='192.168.64.2', port=6379, db=0, socket_timeout=60)
        pubsub = redis_client.pubsub()

        clients = redis_client.client_list()
        # Extract unique channel names from the client list
        channel_names = set()
        for client in clients:
            print(client)
            if 'name' in client and 'subscription' in client:
                if client['subscription'] != 0:
                    channel_names.add(client['name'].decode('utf-8'))

       

        # Test the connection by sending a PING command
        try:
            response = redis_client.ping()
            print(response)
            if response == b'PONG':
                print("Redis connection is active.")
            else:
                print(f"failed {response}")
        except redis.exceptions.ConnectionError as e:
            print(f"Redis connection failed: {str(e)}")

        # Get all the channel names
        channel_names = redis_client.pubsub_channels()

        # Print the channel names
        for channel_name in channel_names:
            print(channel_name)

        pubsub.subscribe('scripts')

        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                message_text = message['data'].decode('utf-8').strip()
                message_text = message_text.replace('"', '')
                print(f"all {message_text}")

                if message_text.lower() == 'run':
                    # Handle the 'run' command
                    ip_addresses = await get_ip_addresses_from_endpoint()
                    await script_executor.execute_scripts()
                elif message_text.lower() == 'executed':
                    print(f"Received 'executed' message.")
                elif message_text.lower() == 'stop':
                    print("Received 'stop' message. Stopping executions and WebSocket publishing.")
                    stop_execution = True
                    return

                else:
                    stop_execution = False
                
                    extracted_ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', message_text)
                    ip_addresses.extend(extracted_ips)
                    print(extracted_ips)
                    await script_executor.execute_scripts()
                  
    except ConnectionError as e:
        print(f"ConnectionError: {e}")
    except Exception as ex:
        print(f"An error occurred: {ex}")


async def publish_websocket_message(message, script_name, ip_address):

    message_data = {
            "message":  f"{message}, {script_name}, {ip_address}",
           
        }

    for attempt in range(MAX_RETRIES):
        try:
            async with websockets.connect(WEBSOCKET_URL, timeout=5) as socket:
                # Serialize the dictionary to JSON
                message_json = json.dumps(message_data)
                # Send the JSON data as a string
                await socket.send(message_json)
                response = await socket.recv()
                print(response)
                break  # Exit the loop if the connection and message send are successful
        except asyncio.TimeoutError as timeout_error:
            print(f"WebSocket Timeout Error: {timeout_error}")
        except websockets.exceptions.WebSocketError as ws_error:
            print(f"WebSocket Error: {ws_error}")
        except Exception as e:
            print(f"An error occurred: {e}")

        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
        else:
            print("Maximum retry attempts reached, giving up.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)  # Set logging level to ERROR
    # asyncio.run(main())

    script_executor = ScriptExecutor()

    # Create and start the "check_for_stop_message" thread
    stop_check_thread = threading.Thread(target=check_for_stop_message)
    stop_check_thread.start()

    # Create and run the asyncio event loop
    asyncio.run(listen_to_redis_messages(script_executor))

    # Wait for all threads to finish
    stop_check_thread.join()