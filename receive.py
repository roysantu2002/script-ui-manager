from RedisMessenger import RedisMessenger


def main():
    room_name = "script_run"  # Specify the room name you want to listen to
    messenger = RedisMessenger(room_name)

    print(f"Listening for messages in room: {room_name}")

    try:
        while True:
            message = messenger.receive_messages()
            print(f"Received message: {message}")
    except KeyboardInterrupt:
        print("Stopped listening for messages.")


if __name__ == "__main__":
    main()
