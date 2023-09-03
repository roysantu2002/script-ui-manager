import os
import threading  # Import the threading module

import redis

from disk_space_checker import DiskSpaceChecker

# Lock to control access to the execution status
execution_lock = threading.Lock()


def check_space_and_publish():
    with execution_lock:
        check_space()
        # Check if the file exists after execution is complete
        if os.path.exists('192.168.1.23_disk_space.txt'):
            # Publish "executed" if the file exists
            redis_client.publish('script_agent', 'executed')


def check_space():
    hostnames = ["192.168.1.23", "192.168.1.100"]  # Add more hosts as needed

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
