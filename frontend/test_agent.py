# File: frontend/test_agent.py
import asyncio
from uagents import Agent, Context
from models import AgentRSVPRequest, AgentRSVPResponse
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize test agent
tester_agent = Agent(
    name="tester_agent",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"]
)

# Define the target agent's address
RSVP_AGENT_ADDRESS = "agent1qduet3vnuswx0ep09szc94u2lrmrn9ws9mrxq0990dwh5cxgzktt2j6jknz"

@tester_agent.on_interval(period=5.0)
async def send_test_message(ctx: Context):
    request = AgentRSVPRequest(
        event_name="Test Event",
        date="2025-08-20",
        time="14:00",
        location="Test Location",
        description="Test Description"
    )
    await ctx.send(RSVP_AGENT_ADDRESS, request)
    ctx.logger.info(f"Sent test request to {RSVP_AGENT_ADDRESS}")

@tester_agent.on_message(model=AgentRSVPResponse)
async def handle_response(ctx: Context, sender: str, msg: AgentRSVPResponse):
    ctx.logger.info(f"Received response: {msg.dict()}")

if __name__ == "__main__":
    tester_agent.run()