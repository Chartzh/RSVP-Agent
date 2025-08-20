# File: frontend/test_agent.py
import asyncio
from uagents import Agent, Context
from models import NaturalLanguageRequest, RSVPResponse
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize test agent
tester_agent = Agent(
    name="llm_tester_agent",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"]
)

# Target agent address
TARGET_AGENT_ADDRESS = "agent1qduet3vnuswx0ep09szc94u2lrmrn9ws9mrxq0990dwh5cxgzktt2j6jknz"

@tester_agent.on_interval(period=5.0)
async def send_message_on_interval(ctx: Context):
    # Create a natural language request
    nl_request = NaturalLanguageRequest(
        message="I want to RSVP for a Python Workshop on August 25th 2025 at 2 PM in the Jakarta Digital Hub"
    )
    
    try:
        await ctx.send(TARGET_AGENT_ADDRESS, nl_request)
        ctx.logger.info(f"Mengirim pesan natural language ke {TARGET_AGENT_ADDRESS}")
    except Exception as e:
        ctx.logger.error(f"Error sending message: {str(e)}")

@tester_agent.on_message(model=RSVPResponse)
async def handle_response(ctx: Context, sender: str, msg: RSVPResponse):
    ctx.logger.info(f"Received response: {msg.status}")
    ctx.logger.info(f"Message: {msg.message}")

if __name__ == "__main__":
    tester_agent.run()