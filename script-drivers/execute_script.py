import os
import threading
import redis

# Lock to control access to the execution status
execution_lock = threading.Lock()

def execute_script_on_device(script_name, hostname):
    try:
        with execution_lock:
            execute_script(script_name, hostname)
    except Exception as e:
        print(f"An error occurred for {hostname}: {e}")

def execute_script(script_name, hostname):
    print(f"Executing '{script_name}' on {hostname}")

    # Add logic to execute the specified script on the device here.
    # You can use if statements to determine which script to run.

    if script_name == "disk_space_checker":
        # Execute disk space checking script for the device
        pass  # Replace with the actual code for disk space checking
    elif script_name == "network_interface_checker":
        # Execute network interface checking script for the device
        pass  # Replace with the actual code for network interface checking
    else:
        print(f"Unknown script '{script_name}'")

def listen_to_redis_messages():
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

                # Split the message into script name and hostname
                parts = message_text.split(',')
                if len(parts) == 2:
                    script_name, hostname = parts
                    script_name = script_name.strip()
                    hostname = hostname.strip()

                    # Check if the received message is valid
                    if script_name and hostname:
                        print(f"Received command to execute '{script_name}' on '{hostname}'")
                        execution_thread = threading.Thread(
                            target=execute_script_on_device,
                            args=(script_name, hostname))
                        execution_thread.start()
                    else:
                        print("Invalid message format. Expected 'script_name,hostname'")
                else:
                    print("Invalid message format. Expected 'script_name,hostname'")
    except ConnectionError as e:
        print(f"ConnectionError: {e}")
        # Handle the connection error, e.g., by logging or taking corrective action
    except Exception as ex:
        print(f"An error occurred: {ex}")
        # Handle other exceptions as needed

if __name__ == "__main__":
    listen_to_redis_messages()
