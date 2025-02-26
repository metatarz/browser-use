from langchain_openai import ChatOpenAI
from datetime import datetime
from browser_use import Agent, Controller
import asyncio
from dotenv import load_dotenv
from browser_use.browser.browser import Browser, BrowserConfig
from websocket_server import initialize_server, start_server, set_message_handler, send_message
import os
from typing import Optional, Dict

os.environ["ANONYMIZED_TELEMETRY"] = "false"

load_dotenv()
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
llm = ChatOpenAI(model=model_name)

cdp_url = os.getenv("BROWSER_CDP_URL", "ws://localhost:9223")
browser = Browser(
    config=BrowserConfig(
        cdp_url=cdp_url,
    )
)
controller = Controller()

# Lock to ensure only one agent runs at a time
agent_lock = asyncio.Lock()
last_task_completed_timestamp: Optional[datetime] = None 
async def handle_websocket_message(message_object: Dict[str, str]):
    """Handle incoming WebSocket messages as tasks for the agent."""
    global last_task_completed_timestamp

    # Extract the timestamp and message from the object
    message_timestamp = datetime.fromisoformat(message_object["timestamp"])
    message = message_object["text"]

    # Discard the message if it is older than the last completed task
    if last_task_completed_timestamp and message_timestamp < last_task_completed_timestamp:
        print(f" Discarding outdated message: {message} (received at {message_timestamp})")
        return

    # Acquire the lock to ensure one task at a time
    async with agent_lock:
        print(f"Received task: {message} (received at {message_timestamp})")
        agent = Agent(
            task=message,
            llm=llm,
            browser=browser,
            controller=controller,
            save_conversation_path="logs/conversation"
        )
        await send_message("Processing...")        
        result = await agent.run()
        print(f"Task result: {result}")
        response_text = f"{result.final_result()} 🚀"

        await send_message(response_text)
        await browser.close()

async def main():
    # Initialize and start WebSocket server
    initialize_server()
    
    # Set the message handler to process tasks
    set_message_handler(handle_websocket_message)
    
    # Start the WebSocket server
    await start_server()
    
    # Keep the server running
    await asyncio.Future()  # Run forever

if __name__ == '__main__':
    asyncio.run(main())
