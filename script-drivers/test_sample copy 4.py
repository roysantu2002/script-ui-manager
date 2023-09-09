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

# Create an instance of FileUtils
file_util_common = FileUtils()
# Access the folder path
today_folder_path = file_util_common.today_folder_path

# Generate a timestamp with seconds
timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")

# Lock to control access to the execution status
execution_lock = threading.Lock()
ip_addresses = []
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
channelName = 'scripts'; 
WEBSOCKET_URL = f"ws://192.168.1.103:8000/ws/scriptchat/run_script/?channel=${channelName}"

def check_for_stop_message():
    global stop_execution
    try:
        async def receive_messages():
            async with websockets.connect(WEBSOCKET_URL, timeout=5) as socket:
                while True:
                    message = await socket.recv()
                    if message:
                        message_text = message.lower()
                        print(f"Received WebSocket message: {message_text}")
                        if message_text == 'stop':
                            print("Received 'stop' command. Stopping execution...")
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
        if stop_execution:
            print("WebSocket publishing stopped.")
            return
        
        script_count = len(SCRIPT_EXECUTORS)  # Get the script count
        completed_scripts = 0

        try:
            threads = []

            for script_name in SCRIPT_EXECUTORS:
                for ip_address in ip_addresses:
                    if stop_execution:
                        print("Execution stopped.")
                        return

                    executor = SCRIPT_EXECUTORS[script_name]
                    if executor:
                        class_name = executor.__qualname__.split('.')[0]
                        func_name = executor.__qualname__.split('.')[1]
                    # Create an instance of the class
                        run_obj = globals()[class_name](ip_address)

                        # Create a separate thread to execute the script
                        script_thread = threading.Thread(target=self.execute_script_thread, args=(run_obj, func_name))
                        script_thread.start()
                        # Wait for the script thread to complete
                        script_thread.join()
                        print(f"Thread for '{func_name}' on {ip_address} has completed.")

                        # Publish a message indicating the execution is done
                        await self.publish_websocket_message("done", func_name, ip_address)

                    else:
                        print(f"No executor found for script '{script_name}'")

                # Publish a message indicating the execution is done
            #     await self.publish_websocket_message("done", func_name, ip_address)
            # else:

                    # # Call the method using the function name
                    # result = getattr(run_obj, func_name)()

                    # # Print the result or use it as needed
                    # print(result)

                    # run_script(script_name, ip_address)

                    # thread = threading.Thread(target=execute_script, args=(self, script_name, ip_address))
                    # thread.start()
                    # threads.append(thread)

                    # # script_entry = SCRIPT_EXECUTORS.get(script_name)
                    # execution_function = SCRIPT_EXECUTORS[script_name]

                    # # Execute the method with the IP address as an argument
                    # execution_function(ip_address)
                    # if script_entry:
                    #     # Extract the class and method names
                    #     script_class, script_method = script_entry
                    #     script_instance = script_class(ip_address)
                    #     result = script_instance()

                    # execution_function = SCRIPT_EXECUTORS[script_name]
                   
                    # script_name()
                     # Create and start a thread for each script execution, passing the IP address as an argument
                    # thread = threading.Thread(target=SCRIPT_EXECUTORS[script_name], args=(ip_address,))
                    # thread.start()
                    # threads.append(thread)

                    # # Create and start a thread for each script execution
                    # thread = threading.Thread(target=self.execute_script, args=(script_name, ip_address))
                    # thread.start()
                    # threads.append(thread)

            # Wait for all threads to complete
            # for thread in threads:
            #     thread.join()
            #     completed_scripts += 1

            # print(completed_scripts)
            # print(script_count * len(ip_addresses))
            
            if completed_scripts == script_count * len(ip_addresses):
                await self.publish_websocket_message("alldone", "all", "all")

        except Exception as e:
            print(f"An error occurred: {e}")

    # async def execute_scripts(self):
    #     global stop_execution
    #     if stop_execution:  # Check if stop flag is set
    #         print("WebSocket publishing stopped.")
    #         return  # Skip publishing

    #     script_count = len(SCRIPT_EXECUTORS)  # Get the script count
    #     completed_scripts = 0
     
    #     try:
    #         for script_name in SCRIPT_EXECUTORS:
    #             for ip_address in ip_addresses:
    #                 if stop_execution:  # Check if stop flag is set
    #                     print("Execution stopped.")
    #                     return  # Terminate execution
    #                 ip_folder_path = os.path.join(today_folder_path,  ip_address, script_name)
    #                 file_util_common.create_folder_if_not_exists(ip_folder_path)
    #                 print(f"Received command to execute '{script_name}' on '{ip_address}'")
    #                 print(f"Executing '{script_name}' on {ip_address}")
    #                 await self.publish_websocket_message("start", script_name, ip_address)
    #                 await self.publish_websocket_message("executing", script_name, ip_address)
    #                 print(f"Finished executing '{script_name}' on {ip_address}")
    #                 await self.publish_websocket_message("done", script_name, ip_address)
                  
    #                 completed_scripts += 1

    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #     print(completed_scripts)
    #     print(script_count * len(ip_addresses))
    #     if completed_scripts == script_count * len(ip_addresses):
    #         await self.publish_websocket_message("alldone", "all", "all")
        

async def get_ip_addresses_from_endpoint():
    try:
        response = requests.get("http://192.168.1.103:8000/api/scripts/network-devices/list/")
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

    #remove
    print('indide listen')
    extracted_ips = await get_ip_addresses_from_endpoint()
    print(extracted_ips)
    ip_addresses.extend(extracted_ips)
    await script_executor.execute_scripts()
    return

    try:
        redis_client = redis.Redis(host='192.168.1.103', port=6379, db=0, socket_timeout=60)
        pubsub = redis_client.pubsub()
        pubsub.subscribe('script_agent')

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
    # Define the WebSocket URL for your Django Channels WebSocket consumer
    websocket_url = "ws://192.168.1.103:8000/ws/scriptchat/run_script/"
    # message_data = f"{message} '{script_name}' on {ip_address}"

    message_data = {
            "message":  f"{message}, {script_name}, {ip_address}",
           
        }

    for attempt in range(max_retries):
        try:
            async with websockets.connect(websocket_url, timeout=5) as socket:
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