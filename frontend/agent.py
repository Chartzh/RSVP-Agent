import asyncio
from typing import Optional
from uagents import Agent, Context, Bureau, Model
from models import (
    ChatMessage, 
    StructuredOutputRequest, 
    StructuredOutputResponse, 
    RSVPResponse,
    RSVPRequest,
    AgentRSVPRequest,
    AgentRSVPResponse,
    ActionType,
    EventInput,
    RSVPInput,
    chat_protocol,
    structured_output_protocol,
    rsvp_response_protocol,
    NaturalLanguageRequest
)
from rsvp_service import RSVPService
import logging
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the agent
agent = Agent(
    name="rsvp_manager_agent",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"]
)

# LLM Agent address for structured output
LLM_AGENT_ADDRESS = "agent1qvk7q2av3e2y5gf5s90nfzkc8a48q3wdqeevwrtgqfdl0k78rspd6f2l4dx"

# Include protocols untuk hackathon eligibility
agent.include(chat_protocol, publish_manifest=True)
agent.include(structured_output_protocol, publish_manifest=True)
agent.include(rsvp_response_protocol, publish_manifest=True)

# Global RSVP service instance
rsvp_service = None

@agent.on_event("startup")
async def setup(ctx: Context):
    """Setup service saat agent start"""
    global rsvp_service
    rsvp_service = RSVPService()
    ctx.logger.info("🚀 RSVP Manager Agent started successfully!")
    ctx.logger.info(f"Agent address: {agent.address}")
    ctx.logger.info("Ready to handle RSVP requests!")

@agent.on_event("shutdown")
async def cleanup(ctx: Context):
    """Cleanup saat agent shutdown"""
    global rsvp_service
    if rsvp_service and hasattr(rsvp_service, 'session') and rsvp_service.session:
        await rsvp_service.session.close()
    ctx.logger.info("👋 RSVP Manager Agent shutdown complete!")

@agent.on_message(model=ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages dari users"""
    ctx.logger.info(f"📨 Received chat from {sender}: {msg.message}")
    
    try:
        # Kirim ke LLM agent untuk structured extraction
        structured_request = StructuredOutputRequest(
            message=msg.message,
            user_address=sender
        )
        
        ctx.logger.info(f"🤖 Sending to LLM agent: {LLM_AGENT_ADDRESS}")
        await ctx.send(LLM_AGENT_ADDRESS, structured_request)
        
    except Exception as e:
        ctx.logger.error(f"❌ Error processing chat message: {str(e)}")
        # Send error response back to user
        error_response = RSVPResponse(
            success=False,
            message=f"Maaf, terjadi error saat memproses pesan Anda: {str(e)}",
            data=None
        )
        await ctx.send(sender, error_response)

@structured_output_protocol.on_message(model=StructuredOutputResponse)
async def handle_structured_output(ctx: Context, sender: str, msg: StructuredOutputResponse):
    """Handle structured output dari LLM agent"""
    ctx.logger.info(f"🧠 Received structured output from LLM: {msg.action}")
    
    try:
        # Parse the action
        action = ActionType(msg.action.lower()) if msg.action else ActionType.UNKNOWN
        
        # Create RSVP request from structured output
        rsvp_request = RSVPRequest(
            action=action,
            event_input=EventInput(**msg.event_input) if msg.event_input else None,
            rsvp_input=RSVPInput(**msg.rsvp_input) if msg.rsvp_input else None,
            event_name=msg.event_name,
            rsvp_id=msg.rsvp_id,
            user_query=msg.user_query
        )
        
        # Process the request
        response = await process_rsvp_request(ctx, rsvp_request)
        
        # Send response back to original user
        user_address = getattr(msg, 'user_address', sender)
        await ctx.send(user_address, response)
        
    except Exception as e:
        ctx.logger.error(f"❌ Error processing structured output: {str(e)}")
        # Send error response
        error_response = RSVPResponse(
            success=False,
            message=f"Error memproses permintaan: {str(e)}",
            data=None
        )
        await ctx.send(sender, error_response)

async def process_rsvp_request(ctx: Context, request: RSVPRequest) -> RSVPResponse:
    """Process RSVP request dan return response"""
    global rsvp_service
    
    try:
        # Create session untuk service jika belum ada
        if not hasattr(rsvp_service, 'session') or not rsvp_service.session:
            rsvp_service.session = __import__('aiohttp').ClientSession()
        
        result = None
        action_str = request.action.value
        
        # Process berdasarkan action type
        if request.action == ActionType.CREATE_EVENT and request.event_input:
            ctx.logger.info(f"🎪 Creating event: {request.event_input.name}")
            result = await rsvp_service.create_event(request.event_input)
            
        elif request.action == ActionType.ADD_RSVP and request.rsvp_input:
            ctx.logger.info(f"✏️ Adding RSVP: {request.rsvp_input.participant_name} -> {request.rsvp_input.event_name}")
            result = await rsvp_service.add_rsvp(request.rsvp_input)
            
        elif request.action == ActionType.LIST_EVENTS:
            ctx.logger.info("📅 Listing all events")
            result = await rsvp_service.list_events()
            
        elif request.action == ActionType.LIST_RSVPS:
            ctx.logger.info("📋 Listing all RSVPs")
            result = await rsvp_service.list_rsvps()
            
        elif request.action == ActionType.LIST_RSVPS_BY_EVENT and request.event_name:
            ctx.logger.info(f"📋 Listing RSVPs for event: {request.event_name}")
            result = await rsvp_service.list_rsvps_by_event(request.event_name)
            
        elif request.action == ActionType.GET_RSVP and request.rsvp_id:
            ctx.logger.info(f"🔍 Getting RSVP: {request.rsvp_id}")
            result = await rsvp_service.get_rsvp(request.rsvp_id)
            
        elif request.action == ActionType.CANCEL_RSVP and request.rsvp_id:
            ctx.logger.info(f"❌ Cancelling RSVP: {request.rsvp_id}")
            result = await rsvp_service.cancel_rsvp(request.rsvp_id)
            
        elif request.action == ActionType.GET_EVENT_BY_NAME and request.event_name:
            ctx.logger.info(f"🔍 Getting event: {request.event_name}")
            result = await rsvp_service.get_event_by_name(request.event_name)
            
        elif request.action == ActionType.HEALTH_CHECK:
            ctx.logger.info("🏥 Health check")
            result = await rsvp_service.health_check()
            
        else:
            return RSVPResponse(
                success=False,
                message="🤔 Maaf, saya tidak mengerti permintaan Anda. Coba tanyakan tentang membuat event, RSVP, atau melihat daftar event/RSVP.",
                data=None
            )
        
        if result:
            # Format response message
            formatted_message = rsvp_service.format_response_message(result, action_str)
            
            return RSVPResponse(
                success=result.success,
                message=formatted_message,
                data=result.data
            )
        else:
            return RSVPResponse(
                success=False,
                message="❌ Tidak dapat memproses permintaan Anda.",
                data=None
            )
            
    except Exception as e:
        ctx.logger.error(f"❌ Error in process_rsvp_request: {str(e)}")
        return RSVPResponse(
            success=False,
            message=f"❌ Error: {str(e)}",
            data=None
        )

# Handler untuk direct RSVP responses (jika diperlukan)
@rsvp_response_protocol.on_message(model=RSVPResponse)
async def handle_rsvp_response(ctx: Context, sender: str, msg: RSVPResponse):
    """Handle RSVP response messages"""
    ctx.logger.info(f"📬 Received RSVP response: {msg.success} - {msg.message}")
    # Bisa digunakan untuk logging atau forwarding ke user lain jika diperlukan

# Handler untuk agent RSVP requests - using the correct model
@agent.on_message(AgentRSVPRequest)
async def handle_agent_rsvp_request(ctx: Context, sender: str, msg: AgentRSVPRequest):
    try:
        ctx.logger.info(f"Processing RSVP request from {sender}")
        ctx.logger.debug(f"Request details: {msg.dict()}")
        
        # Create response
        response = AgentRSVPResponse(
            status="confirmed",
            message=f"RSVP confirmed for {msg.event_name} on {msg.date}"
        )
        
        # Send response back
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"Error processing request: {str(e)}")
        await ctx.send(sender, AgentRSVPResponse(
            status="error",
            message="Failed to process RSVP request"
        ))

def parse_natural_language(message: str) -> RSVPRequest:
    # Extract date using regex (format: Month DD YYYY)
    date_match = re.search(r'(\w+ \d{1,2}(?:st|nd|rd|th)? \d{4})', message)
    # Extract time (format: X PM/AM)
    time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))', message)
    # Extract location (after "in" or "at")
    location_match = re.search(r'(?:in|at)\s+the\s+(.+?)(?:\.|$)', message)
    
    # Get event name (assume it's the first capitalized phrase)
    event_match = re.search(r'for\s+(?:a|an)\s+([A-Z][a-zA-Z\s]+?)(?:\son|at|in|\.)', message)
    
    return RSVPRequest(
        event_name=event_match.group(1) if event_match else "Unnamed Event",
        date=date_match.group(1) if date_match else "",
        time=time_match.group(1) if time_match else "",
        location=location_match.group(1) if location_match else "",
        description="Created from natural language request"
    )

@agent.on_message(model=NaturalLanguageRequest)
async def handle_natural_language(ctx: Context, sender: str, msg: NaturalLanguageRequest):
    try:
        # Parse the natural language request
        rsvp_request = parse_natural_language(msg.message)
        ctx.logger.info(f"Parsed request: {rsvp_request.dict()}")
        
        # Create response
        response = RSVPResponse(
            status="confirmed",
            message=f"RSVP confirmed for {rsvp_request.event_name} on {rsvp_request.date} at {rsvp_request.time} in {rsvp_request.location}"
        )
        
        await ctx.send(sender, response)
    except Exception as e:
        ctx.logger.error(f"Error processing natural language request: {str(e)}")
        await ctx.send(sender, RSVPResponse(
            status="error",
            message=f"Failed to process natural language request: {str(e)}"
        ))

# Fungsi helper untuk testing
async def test_direct_message():
    """Test function untuk mengirim direct message"""
    test_message = ChatMessage(
        message="Buat event baru dengan nama 'Tech Meetup Jakarta' pada tanggal '2024-03-15' dengan deskripsi 'Meetup teknologi bulanan' dan maksimal 50 peserta",
        sender_address="test_user"
    )
    
    # Simulate receiving message
    ctx = Context()  # Mock context untuk testing
    await handle_chat_message(ctx, "test_user", test_message)

if __name__ == "__main__":
    # Untuk development, bisa jalankan agent secara standalone
    print("🚀 Starting RSVP Manager Agent...")
    print(f"Agent address: {agent.address}")
    print("Ready to handle RSVP requests!")
    
    # Create bureau dan run agent
    bureau = Bureau(port=8001, endpoint="http://localhost:8001/submit")
    bureau.add(agent)
    
    # Run the bureau
    bureau.run()