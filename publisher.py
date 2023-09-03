import time

import redis

# Connect to the Redis server
redis_client = redis.Redis(host='192.168.1.103', port=6379, db=0)

# Publish messages to a channel
while True:
    message = input("Enter a message to publish (or 'exit' to quit): ")
    if message.lower() == 'exit':
        break
    redis_client.publish('script_agent', message)
