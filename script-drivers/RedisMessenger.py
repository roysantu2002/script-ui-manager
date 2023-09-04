import redis


class RedisMessenger:
    def __init__(self, room_name):
        self.room_name = room_name
        self.redis_conn = redis.StrictRedis(
            host='192.168.1.103', port=6379, db=0)

    def send_message(self, message):
        try:
            self.redis_conn.publish(self.room_name, message)
            print(f"Published message in room {self.room_name}: {message}")
        except redis.exceptions.ConnectionError:
            print("Error publishing to Redis.")

    def receive_messages(self):
        pubsub = self.redis_conn.pubsub()
        pubsub.subscribe(self.room_name)

        for message in pubsub.listen():
            print(message)
            if message['type'] == 'message':
                print(
                    f"Received message in room {self.room_name}: {message['data']}")
