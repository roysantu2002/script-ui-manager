# script_manager.py
import asyncio
import json
import os
import threading
import redis
import websockets
from datetime import datetime
from disk_space_checker import DiskSpaceChecker
from network_interface_checker import NetworkInterfaceChecker

# Lock to control access to the execution status
execution_lock = threading.Lock()
hostnames = ["192.168.1.23", "192.168.1.100"]  # Add more hosts as needed
timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
today_folder = timestamp.split('_')[0:3]  # Extract dd, mm, yyyy

folder_path = "/Users/santuroy/script-manager-network/script-drivers/" + \
    "_".join(today_folder)

print(folder_path)

# Define a dictionary to map script names to their execution functions
SCRIPT_EXECUTORS = {
    "disk_space_checker": DiskSpaceChecker.check_disk_space,
    "network_interface_checker": NetworkInterfaceChecker.check_network_interfaces,
    # Add more scripts and corresponding execution functions here
}

async def async_execute_script(script_name, hostname):
    if script_name in SCRIPT_EXECUTORS:
        print(f"Executing '{script_name}' on {hostname}")
        await publish_websocket_message(f"Executing '{script_name}' on {hostname}")
        await SCRIPT_EXECUTORS[script_name](hostname)
        await publish_websocket_message(f"Finished executing '{script_name}' on {hostname}")
    else:
        print(f"Unknown script '{script_name}'")

 async def publish_websocket_message(message):
    # Define the WebSocket URL for your Django Channels WebSocket consumer
    websocket_url = "ws://192.168.1.103:8000/ws/scriptchat/run_script/"

    message_data = {
        "message": message,
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
        except websockets.exceptions.WebSocketTimeoutError as timeout_error:
            # Handle the timeout error
            print(f"WebSocket Timeout Error: {timeout_error}")
        except websockets.exceptions.WebSocketError as ws_error:
            # Handle other WebSocket errors
            print(f"WebSocket Error: {ws_error}")
        except Exception as e:
            # Handle other exceptions that may occur
            print(f"An error occurred: {e}")

        if attempt < max_retries - 1:
            # Sleep for a specified duration before retrying the connection
            await asyncio.sleep(retry_delay)
        else:
            print("Maximum retry attempts reached, giving up.")
                   

async def listen_to_redis_messages():
    try:
        redis_client = redis.Redis(
            host='192.168.1.103', port=6379, db=0, socket_timeout=60)

        pubsub = redis_client.pubsub()
        pubsub.subscribe('script_agent')

        for message in pubsub.listen():
            if message['type'] == 'message':
                message_text = message['data'].decode('utf-8').strip()
                message_text = message_text.replace('"', '')
                print(message_text)

                # Check if the received message is "run"
                if message_text.lower() == 'run':
                    print(message_text)
                    # Add your logic here to determine the script name and hostname
                    script_name = "disk_space_checker"  # Example script name
                    hostname = "192.168.1.23"  # Example hostname

                    if script_name and hostname:
                        print(f"Received command to execute '{script_name}' on '{hostname}'")
                        asyncio.create_task(async_execute_script(script_name, hostname))
                    else:
                        print("Invalid message format. Expected 'script_name,hostname'")
                elif message_text.lower() == 'executed':
                    print(f"Received 'executed' message.")
                    # Add your logic here to handle the "executed" message as needed
                else:
                    # Handle other message types or formats if needed
                    print(f"Received an unrecognized message: {message_text}")
    except ConnectionError as e:
        print(f"ConnectionError: {e}")
    except Exception as ex:
        print(f"An error occurred: {ex}")

if __name__ == "__main__":
    asyncio.run(listen_to_redis_messages())
