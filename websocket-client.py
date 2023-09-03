import websocket
import json

def on_message(ws, message):
    # Handle incoming WebSocket messages here
    data = json.loads(message)
    print(f"Received message: {data}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    # WebSocket connection is established
    print("WebSocket connection established")

    # Send a message to the Django server
    message_to_send = {
        "type": "send_message",
        "message": "Hello, Django WebSocket!"
    }
    ws.send(json.dumps(message_to_send))

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://your-django-server-url/", on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
