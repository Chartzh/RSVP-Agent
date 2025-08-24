import asyncio
from typing import Optional
from uagents import Agent, Context, Bureau
from models import (
    ChatMessage,
    StructuredOutputRequest,
    StructuredOutputResponse,
    RSVPResponse,
    EventInput,
    RSVPInput,
    ActionType
)
from rsvp_service import RSVPService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize agent
agent = Agent(
    name="rsvp_manager_agent",
    port=8000,
    seed="rsvp_manager_secret_seed",
    endpoint=["http://127.0.0.1:8000/submit"]
)

# Mini LLM Agent address
MINI_LLM_ADDRESS = "agent1qtjgj0cex59qhfjg7zulxtd9t89j5dzjjgluqacvhv3eydq2fyn37scacsc"


@agent.on_event("shutdown")
async def cleanup(ctx: Context):
    """Cleanup saat agent shutdown"""
    ctx.logger.info("👋 RSVP Manager Agent shutdown complete!")

@agent.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"📨 Received chat from {sender}: {msg.message}")
    
    # Forward to Mini LLM agent for processing
    ctx.logger.info(f"🤖 Sending to Mini LLM agent: {MINI_LLM_ADDRESS}")
    await ctx.send(
        MINI_LLM_ADDRESS,
        StructuredOutputRequest(message=msg.message, user_address=sender)
    )

@agent.on_message(StructuredOutputResponse)
async def handle_structured_output(ctx: Context, sender: str, msg: StructuredOutputResponse):
    ctx.logger.info(f"🧠 Received structured output from LLM: {msg.action}")
    
    try:
        # Ensure we have an active session for RSVP service
        async with RSVPService() as service:
            result = None
            
            if msg.action == "create_event" and msg.event_input:
                ctx.logger.info(f"🎪 Creating event: {msg.event_input.get('name', 'Unknown')}")
                
                # Convert dict to EventInput
                event_input = EventInput(
                    name=msg.event_input.get('name', ''),
                    description=msg.event_input.get('description', ''),
                    date=msg.event_input.get('date', ''),
                    max_participants=msg.event_input.get('max_participants', 50)
                )
                
                result = await service.create_event(event_input)
                formatted_message = service.format_response_message(result, "create_event")
                
                response = RSVPResponse(
                    success=result.success,
                    message=formatted_message,
                    data=result.data
                )
                
            elif msg.action == "add_rsvp" and msg.rsvp_input:
                ctx.logger.info(f"📝 Adding RSVP for event: {msg.rsvp_input.get('event_name', 'Unknown')}")
                
                # Convert dict to RSVPInput
                rsvp_input = RSVPInput(
                    event_name=msg.rsvp_input.get('event_name', ''),
                    participant_name=msg.rsvp_input.get('participant_name', ''),
                    participant_email=msg.rsvp_input.get('participant_email', '')
                )
                
                result = await service.add_rsvp(rsvp_input)
                formatted_message = service.format_response_message(result, "add_rsvp")
                
                response = RSVPResponse(
                    success=result.success,
                    message=formatted_message,
                    data=result.data
                )
                
            elif msg.action == "list_events":
                ctx.logger.info("📅 Listing all events")
                result = await service.list_events()
                formatted_message = service.format_response_message(result, "list_events")
                
                response = RSVPResponse(
                    success=result.success,
                    message=formatted_message,
                    data=result.data
                )
                
            elif msg.action == "list_rsvps":
                ctx.logger.info("📋 Listing all RSVPs")
                result = await service.list_rsvps()
                formatted_message = service.format_response_message(result, "list_rsvps")
                
                response = RSVPResponse(
                    success=result.success,
                    message=formatted_message,
                    data=result.data
                )
                
            elif msg.action == "health_check":
                ctx.logger.info("🏥 Health check")
                result = await service.health_check()
                formatted_message = service.format_response_message(result, "health_check")
                
                response = RSVPResponse(
                    success=result.success,
                    message=formatted_message,
                    data=result.data
                )
                
            else:
                ctx.logger.warning(f"⚠️ Unknown action: {msg.action}")
                response = RSVPResponse(
                    success=False,
                    message=f"Unknown action: {msg.action}",
                    data=None
                )
        
        # Send response back to original user
        ctx.logger.info(f"📤 Sending response to {msg.user_address}")
        await ctx.send(msg.user_address, response)
        
    except Exception as e:
        ctx.logger.error(f"❌ Error in process_rsvp_request: {str(e)}")
        error_response = RSVPResponse(
            success=False,
            message=f"Error processing request: {str(e)}",
            data=None
        )
        await ctx.send(msg.user_address, error_response)

if __name__ == "__main__":
    print("🚀 Starting RSVP Manager Agent...")
    print(f"🔗 Agent will run on address: {agent.address}")
    agent.run()