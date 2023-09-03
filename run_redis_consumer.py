import asyncio
import json

import redis

from redis_consumer import \
    RedisConsumer  # Replace with your actual module path


async def run_consumer():
    room_name = "run_script"  # Specify the room name you want to listen to
    consumer = RedisConsumer(room_name)
    await consumer.connect()

    try:
        while True:
            message = input("Enter a message to send to the WebSocket: ")
            await consumer.receive(json.dumps({"message": message}))
    finally:
        # No need to define disconnect here; it should be defined in the RedisConsumer class
        pass

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_consumer())
