import json
import os
from datetime import datetime
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol
from typing import Set, Callable, Any, Optional

class WebSocketServer:
    def __init__(self):
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.host: str = 'localhost'
        self.port: int = 8765
        self.server: Any = None
        self.message_handler: Callable[[str], None] = lambda _: None
        self.current_websocket: Optional[WebSocketServerProtocol] = None
    def initialize(self, host: str = None, port: int = None) -> None:
        """Initialize server with environment variables or provided values"""
        self.host = host or os.getenv('WS_HOST', 'localhost')
        self.port = port or int(os.getenv('WS_PORT', '8765'))

    async def handle_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Handle new client connections and messages"""
        self.connected_clients.add(websocket)
        self.current_websocket = websocket 
        try:
            async for message in websocket:
                    # Try to parse the message as JSON
                try:
                    message = json.loads(message)
                    if not isinstance(message, dict) or "text" not in message:
                        raise ValueError("Invalid message format: must be a JSON object with 'text'")
                    # Ensure the timestamp is included
                    if "timestamp" not in message:
                        message["timestamp"] = datetime.now().isoformat()
                except (json.JSONDecodeError, ValueError):
                    # Handle plain string message
                    message= {
                        "text": message,
                        "timestamp": datetime.now().isoformat()
                    }                
                if asyncio.iscoroutinefunction(self.message_handler):
                    await self.message_handler(message)
                else:
                    self.message_handler(message)
        finally:
            self.connected_clients.remove(websocket)

    async def send_message(self, message: str) -> None:
        """Send message to all connected clients"""
        if self.connected_clients:
           # message_json = json.dumps({"text":message})
            await asyncio.gather(
                *[client.send(message) for client in self.connected_clients]
            )

    def set_message_handler(self, handler: Callable[[str], None]) -> None:
        """Set the function to handle incoming messages"""
        self.message_handler = handler

    async def start(self) -> None:
        """Start the WebSocket server"""
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port
        )
        print(f"Server started on ws://{self.host}:{self.port}")
    async def wait_for_client_response(self) -> str:
        return await self.current_websocket.recv()
    async def stop(self) -> None:
        """Stop the WebSocket server"""
        self.server.close()
        await self.server.wait_closed()

# Singleton instance for easy import
server = WebSocketServer()

# Exported functions
def initialize_server(host: str = None, port: int = None) -> None:
    server.initialize(host, port)

async def send_message(message: str) -> None:
    await server.send_message(message)

def set_message_handler(handler: Callable[[str], None]) -> None:
    server.set_message_handler(handler)

async def start_server() -> None:
    await server.start()

async def stop_server() -> None:
    await server.stop()

async def wait_for_client_response() -> str:
    return await server.wait_for_client_response()
