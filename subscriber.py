import redis

# Connect to the Redis server
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Subscribe to a channel
pubsub = redis_client.pubsub()
pubsub.subscribe('my_channel')

# Listen for messages
for message in pubsub.listen():
    if message['type'] == 'message':
        print(f"Received message: {message['data'].decode('utf-8')}")
