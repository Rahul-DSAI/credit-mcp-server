import asyncio
import logging

from mcp.client.sse import sse_client
from mcp.types import JSONRPCRequest

logging.basicConfig(level=logging.DEBUG)

async def main():
    url = "http://localhost:8000/sse"

    async with sse_client(url) as (read_stream, write_stream):
        # Send an `initialize` message
        init_message = JSONRPCRequest(
            jsonrpc="2.0",
            id=1,
            method="tools/call",
            params={"name":"get_time",
                "arguments":{}
            }
        )
        await write_stream.send(init_message)
        print("[CLIENT] Sent initialize message")

        # Now invoke a tool method
        request = JSONRPCRequest(
            jsonrpc="2.0",
            id=2,
            method="tools/call",  # Change this to the tool you want to invoke
            params={
                "name":"get_restaurants_nearby",
                "arguments":{
                    "latitude": 22.5726, 
                    "longitude": 88.3639
                }
            }
        )
        await write_stream.send(request)
        print("[CLIENT] Sent get_time request")

        # Listen for responses from the server
        try:
            while True:
                message = await read_stream.receive()
                print("[CLIENT] Received:", message)
        except asyncio.CancelledError:
            print("[CLIENT] Cancelled")
        except Exception as e:
            print("[CLIENT] Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
