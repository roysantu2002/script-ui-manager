from RedisMessenger import RedisMessenger

def main():
    room_name = "script_run"  # Specify the room name you want to send messages to
    messenger = RedisMessenger(room_name)

    while True:
        message = input("Enter the message to send (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        messenger.send_message(message)

if __name__ == "__main__":
    main()
