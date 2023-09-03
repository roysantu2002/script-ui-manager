import asyncio
import json

import redis

class RedisConsumer:
    def __init__(self, room_name):
        self.room_name = room_name
        self.redis_conn = None

    async def connect(self):
        while True:
            try:
                self.redis_conn = redis.StrictRedis(
                    host='192.168.1.103', port=6379, db=0)
                await asyncio.sleep(0.1)
                print(f"Connected to room: {self.room_name}")
                break  # Connection successful, break out of the retry loop
            except redis.exceptions.ConnectionError:
                print("Error connecting to Redis. Retrying...")
                await asyncio.sleep(2)  # Retry after a delay

    async def disconnect(self, close_code=None):
        if self.redis_conn is not None:
            self.redis_conn.close()
        print(f"Disconnected from room: {self.room_name}")

    async def receive(self, text_data):
        if self.redis_conn is None:
            print("Not connected to Redis. Reconnecting...")
            await self.connect()
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        try:
            self.redis_conn.publish(self.room_name, message)
            print(
                f"Received and published message in room {self.room_name}: {message}")
        except redis.exceptions.ConnectionError:
            print("Error publishing to Redis. Reconnecting...")
            await self.connect()
