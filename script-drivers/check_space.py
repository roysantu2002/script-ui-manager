import asyncio
import json
import os
import threading  # Import the threading module
from datetime import datetime

import redis
import websockets

from disk_space_checker import DiskSpaceChecker

# Lock to control access to the execution status
execution_lock = threading.Lock()
hostnames = ["192.168.1.23", "192.168.1.100"]  # Add more hosts as needed
timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
today = timestamp.split('_')[0:3]  # Extract dd, mm, yyyy
# Check if text files exist for all hostnames with today's date stamp
all_files_exist = False
max_retries = 3
retry_delay = 5
# Create the folder with today's date if it doesn't exist
today_folder = timestamp.split('_')[0:3]  # Extract dd, mm, yyyy

folder_path = "/Users/santuroy/script-manager-network/script-drivers/" + \
    "_".join(today_folder)

print(folder_path)


def check_files_for_hostnames(hostnames, folder_path):

    all_files_exist = False  # Default to False

    if not os.path.exists(folder_path):
        return all_files_exist  # Return False if the folder doesn't exist

    for hostname in hostnames:

        filename = f"{hostname}_{today}_disk_space.txt"
        print(filename)
        file_path = os.path.join(folder_path, filename)
        print(file_path)

        if not os.path.exists(file_path):
            return all_files_exist  # Return False if any file is missing

    all_files_exist = True  # Set to True only if all files are found
    return all_files_exist


def check_space_and_publish():

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the asynchronous function within the event loop
    # Run the asynchronous function within the event loop
    loop.run_until_complete(async_check_space_and_publish())

    # with execution_lock:
    #     check_space()
    # redis_client.publish('script_agent', 'executed')
    # publish_websocket_message('executed')  # Use
    # all_files_exist = check_files_for_hostnames(hostnames, folder_path)

    # # hostnames = ["192.168.1.23", "192.168.1.100"]  # Add more hosts as needed
    # # Check if the file exists after execution is complete
    # if all_files_exist:
    #     print("all files found")

    #     redis_client.publish('script_agent', 'executed')


async def async_check_space_and_publish():
    with execution_lock:
        check_space()
    await publish_websocket_message('executed')
    redis_client.publish('script_agent', 'executed')


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

    # # Prepare the WebSocket message
    # message_data = {
    #     "message": message,
    # }

    # try:
    #     print(f"Inside publish_websocket_message: {message_data}")

    #     # Establish a WebSocket connection
    #     async with websockets.connect(websocket_url) as ws:
    #         # Send the message
    #         await ws.send(json.dumps(message_data))

    # except websockets.exceptions.WebSocketException as e:
    #     print(f"WebSocket error: {e}")

    # except Exception as ex:
    #     print(f"An error occurred: {ex}")


def check_space():

    for hostname in hostnames:
        print(hostname)
        disk_checker = DiskSpaceChecker(hostname)
        disk_checker.get_disk_space()


# Connect to the Redis server
try:
    redis_client = redis.Redis(
        host='192.168.1.103', port=6379, db=0, socket_timeout=60)

    # Subscribe to a channel
    pubsub = redis_client.pubsub()
    pubsub.subscribe('script_agent')

    # Listen for messages
    for message in pubsub.listen():
        if message['type'] == 'message':

            message_text = message['data'].decode('utf-8').strip()
            # Remove double quotes from the received message
            message_text = message_text.replace('"', '')
            print(message_text)

            # Check if the received message is "run"
            if message_text.lower() == 'run':
                print(message_text)
                # Execute check_space_and_publish() in a separate thread
                execution_thread = threading.Thread(
                    target=check_space_and_publish)
                execution_thread.start()
            elif message_text.lower() == 'executed':
                print(f"Received 'executed' message.")
                # Add your logic here to handle the "executed" message as needed
except ConnectionError as e:
    print(f"ConnectionError: {e}")
    # Handle the connection error, e.g., by logging or taking corrective action
except Exception as ex:
    print(f"An error occurred: {ex}")
    # Handle other exceptions as needed
