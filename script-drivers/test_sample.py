import asyncio
import json
import os
import threading
import redis
import websockets
import requests  # Import the requests library
from datetime import datetime
# from disk_space_checker import DiskSpaceChecker
# from network_interface_checker import NetworkInterfaceChecker
import socket
import re
# Lock to control access to the execution status
execution_lock = threading.Lock()
ip_addresses = []

# Function to assign or extend the ip_addresses dictionary
def assign_or_extend_ip_addresses(new_addresses):
    global ip_addresses
    ip_addresses.update(new_addresses)


# Define a dictionary to map script names to their execution functions
SCRIPT_EXECUTORS = {
    "disk_space_checker": "DiskSpaceChecker.check_disk_space",
    "network_interface_checker": "NetworkInterfaceChecker.check_network_interfaces",
    # Add more scripts and corresponding execution functions here
}

# WebSocket configuration
websocket_url = "ws://192.168.1.103:8000/ws/scriptchat/run_script/"
max_retries = 3
retry_delay = 5


async def get_ip_addresses_from_endpoint():
    # global ip_addresses
    try:
        response = requests.get("http://192.168.1.103:8000/api/scripts/network-devices/list/")
        if response.status_code == 200:
            data = response.json()
            ip_addresses = [device['ip_address'] for device in data]
            return ip_addresses
        else:
            print(f"Failed to retrieve IP addresses from the endpoint. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while fetching IP addresses: {e}")
    return []

async def async_execute_script(script_name, ip_address):
    try:
        print(f"Executing '{script_name}' on {ip_address}")
        await publish_websocket_message(f"Executing '{script_name}' on {ip_address}")
        # ... Your script execution code ...
        print(f"Finished executing '{script_name}' on {ip_address}")
        await publish_websocket_message(f"Finished executing '{script_name}' on {ip_address}")
    except Exception as e:
        print(f"An error occurred: {e}")

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

      
async def execute_scripts():
    print(ip_addresses)
    for script_name in SCRIPT_EXECUTORS:
        for ip_address in ip_addresses:
            print(f"Received command to execute '{script_name}' on '{ip_address}'")
            print(f"Executing '{script_name}' on {ip_address}")
            await publish_websocket_message("start", script_name, ip_address)
            # ... Your script execution code ...
            print(f"Finished executing '{script_name}' on {ip_address}")
            await publish_websocket_message("done", script_name, ip_address)

async def listen_to_redis_messages():
    global ip_addresses
    try:
        redis_client = redis.Redis(
            host='192.168.1.103', port=6379, db=0, socket_timeout=60)

        pubsub = redis_client.pubsub()
        pubsub.subscribe('script_agent')

        # ip_addresses = await get_ip_addresses_from_endpoint()
        # print(ip_addresses)  # Print the result here

        for message in pubsub.listen():
            if message['type'] == 'message':
                message_text = message['data'].decode('utf-8').strip()
                message_text = message_text.replace('"', '')
                print(message_text)

                if message_text.lower() == 'run':
                    ip_addresses = await get_ip_addresses_from_endpoint()
                    print(message_text)
                    await execute_scripts()
                   

                    # for script_name in SCRIPT_EXECUTORS:
                    #     for ip_address in ip_addresses:
                    #         print(f"Received command to execute '{script_name}' on '{ip_address}'")
                    #         print(f"Executing '{script_name}' on {ip_address}")
                    #         await publish_websocket_message("start", script_name, ip_address)
                    #         # ... Your script execution code ...
                    #         print(f"Finished executing '{script_name}' on {ip_address}")
                    #         await publish_websocket_message("done", script_name, ip_address)

                            # asyncio.create_task(async_execute_script(script_name, ip_address))
                elif message_text.lower() == 'executed':
                    print(f"Received 'executed' message.")
                else:
                  
                
                    extracted_ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', message_text)
                    ip_addresses.extend(extracted_ips)
                    print(extracted_ips)
                    # assign_or_extend_ip_addresses(ip_addresses)
                    await execute_scripts()
                    print(f"Received an unrecognized message: {message_text}")
    except ConnectionError as e:
        print(f"ConnectionError: {e}")
    except Exception as ex:
        print(f"An error occurred: {ex}")

if __name__ == "__main__":
    asyncio.run(listen_to_redis_messages())
