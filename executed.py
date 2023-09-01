import redis

# Connect to the Redis server
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Subscribe to the same channel
pubsub = redis_client.pubsub()
pubsub.subscribe('my_channel')

# Listen for messages containing "executed"
for message in pubsub.listen():
    if message['type'] == 'message':
        message_text = message['data'].decode('utf-8')

        # Check if the received message is "executed"
        if message_text.lower() == 'executed':
            print(f"Received 'executed' message.")
            # Add your logic here to handle the "executed" message as needed
