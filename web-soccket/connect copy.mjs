import WebSocket from "ws";

// WebSocket server URL (replace with your WebSocket server URL)
const serverUrl = "ws://192.168.1.103:8000/ws/scriptchat/run_script/";

// Create a WebSocket connection
const socket = new WebSocket(serverUrl);

// Function to send a message to the server
function sendMessage(message) {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ message }));
  } else {
    console.error("WebSocket is not open. Unable to send the message.");
  }
}

// WebSocket connection event handlers
socket.addEventListener("open", () => {
  console.log("WebSocket connection established");

  // Create a message object with the message content
  const messageToSend = {
    message: "Run script!",
  };

  // Send the initial message to the server
  sendMessage(messageToSend);

  // Continuously send messages at an interval (e.g., every 5 seconds)
  setInterval(() => {
    const message = "Continuously sending messages!";
    sendMessage(message);
  }, 5000); // Adjust the interval as needed
});

socket.addEventListener("message", (event) => {
  console.log("Received message:", event.data);

  // Handle received messages here, if needed
});

socket.addEventListener("close", (event) => {
  console.log(
    `WebSocket connection closed with code ${event.code}: ${event.reason}`
  );
});

socket.addEventListener("error", (error) => {
  console.error("WebSocket error:", error.message);
});
