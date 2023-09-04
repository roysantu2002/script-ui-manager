import redis

from DataSenderToDjangoAPI import DataSenderToDjangoAPI

# Connect to the Redis server
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Subscribe to the same channel
pubsub = redis_client.pubsub()
pubsub.subscribe('script_agent')


# Listen for messages containing "executed"
for message in pubsub.listen():
    if message['type'] == 'message':
        message_text = message['data'].decode('utf-8')

        # Check if the received message is "executed"
        if message_text.lower() == 'executed':
            # Usage example:
            root_folder = "/Users/santuroy/script-manager-network/02_09_2023"
            # data_sender = DataSenderToDjangoAPI(root_folder, "api_endpoint")
            # data_sender.iterate_folders_and_send_to_api()
            print(f"Received 'executed' message.")

            # Create an instance of the class
            data_sender = DataSenderToDjangoAPI(root_folder, "api_endpoint")

            # Specify the list of IP addresses to process
            # Replace with your IP addresses
            ips_to_process = ["192.168.1.23", "192.168.1.100"]

            # Call the method to iterate through folders and send data to the API
            data_sender.iterate_folders_and_send_to_api(ips_to_process)

            # Add your logic here to handle the "executed" message as needed
