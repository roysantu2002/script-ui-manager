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


# Define a dictionary to map script names to their execution functions
SCRIPT_EXECUTORS = {
    "disk_space_checker": DiskSpaceChecker.get_disk_space,
    "network_interface_checker": NetworkInterfaceChecker.get_network_interfaces,
    # Add more scripts and corresponding execution functions here
}

# Define your constants and configuration here
MAX_RETRIES = 2
RETRY_DELAY = 5
WEBSOCKET_URL = "ws://192.168.1.103:8000/ws/scriptchat/run_script/"


# Define a function to continuously check for the "stop" message
# Define a function to continuously check for the "stop" message
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

# Create a thread to check for the "stop" message
# stop_check_thread = threading.Thread(target=check_for_stop_message)
# stop_check_thread.start()

# Define a class to encapsulate the script execution logic
class ScriptExecutor:
    def __init__(self):
        self.websocket = None
        self.execution_status = {}  # D
        self.socket = None  # Initialize WebSocket connection attribut
       

    # async def connect_to_websocket(self, websocket_url):
    #     self.websocket_url = websocket_url
    #     try:
    #         async with websockets.connect(websocket_url, timeout=5) as self.socket:
    #             await self.start_listening()
    #     except asyncio.TimeoutError as e:
    #         logging.error(f"WebSocket Timeout Error: {e}")
    #     except websockets.WebSocketException as e:
    #         logging.error(f"WebSocket Error: {e}")

    # async def start_listening(self):
    #     if hasattr(self, 'socket'):
    #         async for message in self.socket:
    #             # Handle incoming WebSocket messages here
    #             print(f"Received message: {message}")
    #     else:
    #         print("WebSocket connection is not established.")
    
    async def publish_websocket_message(self, message, script_name, ip_address):
        global stop_execution
        if stop_execution:  # Check if stop flag is set
            print("WebSocket publishing stopped.")
            return  # Skip publishing

        # Define the WebSocket URL for your Django Channels WebSocket consumer
        websocket_url = "ws://192.168.1.103:8000/ws/scriptchat/run_script/"
        # message_data = f"{message} '{script_name}' on {ip_address}"

        message_data = {
                "message":  f"{message}, {script_name}, {ip_address}",
            
            }

        for attempt in range(MAX_RETRIES):
            try:
                async with websockets.connect(websocket_url, timeout=5) as socket:
                    # Serialize the dictionary to JSON
                    message_json = json.dumps(message_data)
                    # Send the JSON data as a string
                    await socket.send(message_json)
                    response = await socket.recv()
                    # Receive WebSocket messages
                    # while True:
                    #     response = await socket.recv()
                    #     print(response)

                    # # Check if the received message indicates a "stop" command
                    # if response.strip().lower() == 'stop':
                    #     print("Received 'stop' message from WebSocket. Stopping execution.")
                    #     stop_execution = True
                    #     return  # Terminate execution

                    # break  # Exit the loop if the connection 

                    # break  # Exit the loop if the connection and message send are successful
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

    async def execute_scripts(self):
        global stop_execution
        if stop_execution:  # Check if stop flag is set
            print("WebSocket publishing stopped.")
            return  # Skip publishing

        script_count = len(SCRIPT_EXECUTORS)  # Get the script count
        completed_scripts = 0
     
        try:
            for script_name in SCRIPT_EXECUTORS:
                for ip_address in ip_addresses:
                    if stop_execution:  # Check if stop flag is set
                        print("Execution stopped.")
                        return  # Terminate execution
                    ip_folder_path = os.path.join(today_folder_path,  ip_address, script_name)
                    file_util_common.create_folder_if_not_exists(ip_folder_path)
                    print(f"Received command to execute '{script_name}' on '{ip_address}'")
                    print(f"Executing '{script_name}' on {ip_address}")
                    await self.publish_websocket_message("start", script_name, ip_address)
                    await self.publish_websocket_message("executing", script_name, ip_address)
                    # websocket_connections.append(websocket)
                    # ... Your script execution code ...
                    print(f"Finished executing '{script_name}' on {ip_address}")
                    await self.publish_websocket_message("done", script_name, ip_address)
                    # websocket_connections.append(websocket)

                    # Close the websocket connection for this script execution
                    # await self.close_websocket_connection(ip_address)
                    completed_scripts += 1

                  
                    #  # Update the execution status
                    # self.execution_status[ip_address].add(script_name)
                    # completed_scripts += 1
                    # print(self.execution_status)
                    #  # Update the execution status

                    # # Update the execution status
                    # self.execution_status[ip_address].discard(script_name)
                        # Check if all scripts have been executed for all IP addresses
        except Exception as e:
            print(f"An error occurred: {e}")
        print(completed_scripts)
        print(script_count * len(ip_addresses))
        if completed_scripts == script_count * len(ip_addresses):
            await self.publish_websocket_message("alldone", "all", "all")
            # websocket_connections.append(websocket)
            # for websocket in websocket_connections:
            #     await websocket.close()


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
    # print('indide listen')
    # extracted_ips = await get_ip_addresses_from_endpoint()
    # print(extracted_ips)
    # ip_addresses.extend(extracted_ips)
    # await script_executor.execute_scripts()
    # return

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
                   # Parse the data using ast.literal_eval
                    # data_list = ast.literal_eval(message_text)

                    # # Extract IP addresses using regular expression
                    # extracted_ips = [item['ip_address'] for item in data_list]

                    # Access the "message" field
                    # message_text = data.get("message", "")
                    # Handle other messages and IP address extraction
                    # extracted_ips = [item["ip_address"] for item in data]
                    extracted_ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', message_text)
                    ip_addresses.extend(extracted_ips)
                    print(extracted_ips)
                    await script_executor.execute_scripts()
                  
    except ConnectionError as e:
        print(f"ConnectionError: {e}")
    except Exception as ex:
        print(f"An error occurred: {ex}")



# async def get_ip_addresses_from_endpoint():
#     # global ip_addresses
#     try:
#         response = requests.get("http://192.168.1.103:8000/api/scripts/network-devices/list/")
#         if response.status_code == 200:
#             data = response.json()
#             ip_addresses = [device['ip_address'] for device in data]
#             return ip_addresses
#         else:
#             print(f"Failed to retrieve IP addresses from the endpoint. Status code: {response.status_code}")
#     except Exception as e:
#         print(f"An error occurred while fetching IP addresses: {e}")
#     return []

# async def async_execute_script(script_name, ip_address):
#     try:
#         print(f"Executing '{script_name}' on {ip_address}")
#         await publish_websocket_message(f"Executing '{script_name}' on {ip_address}")
#         # ... Your script execution code ...
#         print(f"Finished executing '{script_name}' on {ip_address}")
#         await publish_websocket_message(f"Finished executing '{script_name}' on {ip_address}")
#     except Exception as e:
#         print(f"An error occurred: {e}")

# async def async_execute_script(script_name, ip_address):
#     print(script_name)
#     if script_name in SCRIPT_EXECUTORS:
#         print(f"Executing '{script_name}' on {ip_address}")
#         await publish_websocket_message(f"Executing '{script_name}' on {ip_address}")
#         await SCRIPT_EXECUTORS[script_name](ip_address)
#         await publish_websocket_message(f"Finished executing '{script_name}' on {ip_address}")
#     else:
#         print(f"Unknown script '{script_name}'")

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

      
# async def execute_scripts():
#     print(ip_addresses)
#     for script_name in SCRIPT_EXECUTORS:
#         for ip_address in ip_addresses:
#             ip_folder_path = os.path.join(today_folder_path,  ip_address, script_name)
#             file_util_common.create_folder_if_not_exists(ip_folder_path)
#             print(f"Received command to execute '{script_name}' on '{ip_address}'")
#             print(f"Executing '{script_name}' on {ip_address}")
#             await publish_websocket_message("start", script_name, ip_address)
#             # ... Your script execution code ...
#             print(f"Finished executing '{script_name}' on {ip_address}")
#             await publish_websocket_message("done", script_name, ip_address)

# async def listen_to_redis_messages():
#     global ip_addresses
#     try:
#         redis_client = redis.Redis(
#             host='192.168.1.103', port=6379, db=0, socket_timeout=60)

#         pubsub = redis_client.pubsub()
#         pubsub.subscribe('script_agent')

#         # ip_addresses = await get_ip_addresses_from_endpoint()
#         # print(ip_addresses)  # Print the result here

#         #remove

#         ip_addresses = await get_ip_addresses_from_endpoint()
#         await execute_scripts()

#         for message in pubsub.listen():
#             if message['type'] == 'message':
#                 message_text = message['data'].decode('utf-8').strip()
#                 message_text = message_text.replace('"', '')
#                 print(message_text)

            

#                 if message_text.lower() == 'run':
#                     ip_addresses = await get_ip_addresses_from_endpoint()
#                     print(message_text)
#                     await execute_scripts()
                   

#                     # for script_name in SCRIPT_EXECUTORS:
#                     #     for ip_address in ip_addresses:
#                     #         print(f"Received command to execute '{script_name}' on '{ip_address}'")
#                     #         print(f"Executing '{script_name}' on {ip_address}")
#                     #         await publish_websocket_message("start", script_name, ip_address)
#                     #         # ... Your script execution code ...
#                     #         print(f"Finished executing '{script_name}' on {ip_address}")
#                     #         await publish_websocket_message("done", script_name, ip_address)

#                             # asyncio.create_task(async_execute_script(script_name, ip_address))
#                 elif message_text.lower() == 'executed':
#                     print(f"Received 'executed' message.")
#                 else:
                  
                
#                     extracted_ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', message_text)
#                     ip_addresses.extend(extracted_ips)
#                     print(extracted_ips)
#                     # assign_or_extend_ip_addresses(ip_addresses)
#                     await execute_scripts()
#                     print(f"Received an unrecognized message: {message_text}")
#     except ConnectionError as e:
#         print(f"ConnectionError: {e}")
#     except Exception as ex:
#         print(f"An error occurred: {ex}")

# Usage example:
# async def main():
#     script_executor = ScriptExecutor()
    
#     # Connect to the WebSocket
#     await script_executor.connect_to_websocket()
    
#     # Start listening for WebSocket messages
#     await script_executor.start_listening()

    # # Create tasks for WebSocket listening and Redis message listening
    # websocket_task = asyncio.create_task(script_executor.start_listening())
    # redis_task = asyncio.create_task(listen_to_redis_messages(script_executor))
    
    # # Concurrently run WebSocket listening and Redis message listening
    # await asyncio.gather(websocket_task, redis_task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)  # Set logging level to ERROR
    # asyncio.run(main())

    script_executor = ScriptExecutor()
    # asyncio.run(listen_to_redis_messages(script_executor))

    # Create and start the "check_for_stop_message" thread
    stop_check_thread = threading.Thread(target=check_for_stop_message)
    stop_check_thread.start()

    # Create and run the asyncio event loop
    asyncio.run(listen_to_redis_messages(script_executor))

    # Wait for all threads to finish
    stop_check_thread.join()

    # asyncio.run(main())
    # asyncio.run(script_executor.connect_to_websocket(WEBSOCKET_URL))
    # asyncio.run(listen_to_redis_messages(script_executor))
