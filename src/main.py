import asyncio
import sys
from src.classes.relay import Relay
from src.classes.eddn_listener import EddnListener

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    # Initialize components
    relay = Relay(port=9600)
    listener = EddnListener(relay)

    # Create tasks
    relay_task = asyncio.create_task(relay.start())
    listener_task = asyncio.create_task(listener.start())

    # Wait for both tasks
    try:
        await asyncio.gather(relay_task, listener_task)
    except KeyboardInterrupt:
        listener.stop()

if __name__ == "__main__":
    asyncio.run(main())
