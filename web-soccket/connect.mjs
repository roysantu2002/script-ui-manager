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
socket.on("open", () => {
  console.log("WebSocket connection established");

  // Create a message object with the message content
  const messageToSend = {
    message: "Run script!",
  };

  // Send the initial message to the server
  sendMessage(messageToSend);

  // Start listening for user input
  process.stdin.on("data", (data) => {
    const userInput = data.toString().trim();
    sendMessage(userInput);
  });
});

socket.on("message", (data) => {
  if (typeof data === "string") {
    console.log("Received text message:", data);
    // Handle received text messages here, if needed
  } else if (data instanceof Buffer) {
    // Handle binary messages here
    console.log("Received binary message:", data.toString());
  }
});

socket.on("close", (event) => {
  console.log(
    `WebSocket connection closed with code ${event.code}: ${event.reason}`
  );

  // Close the standard input stream
  process.stdin.pause();
});

socket.on("error", (error) => {
  console.error("WebSocket error:", error.message);
});
