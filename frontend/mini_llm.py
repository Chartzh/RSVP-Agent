from uagents import Agent, Context
from models import StructuredOutputRequest, StructuredOutputResponse

mini_llm = Agent(
    name="mini_llm_simulator",
    port=8004,
    seed="mini_llm_simulator_secret_seed",
    endpoint=["http://127.0.0.1:8004/submit"] 
)

@mini_llm.on_event("startup")
async def setup(ctx: Context):
    ctx.logger.info("🤖 Mini LLM Simulator started")
    ctx.logger.info(f"🔗 Mini LLM address: {mini_llm.address}")

@mini_llm.on_message(model=StructuredOutputRequest)
async def handle_request(ctx: Context, sender: str, msg: StructuredOutputRequest):
    ctx.logger.info(f"🧠 Simulator LLM menerima pesan dari {sender}: '{msg.message}'")
    
    # Simple parsing logic untuk demo
    message_lower = msg.message.lower()
    
    if "event" in message_lower and ("buat" in message_lower or "create" in message_lower):
        # Mock event creation
        mock_response = StructuredOutputResponse(
            action="create_event",
            event_input={
                "name": "Hackathon Afterparty from Simulator",
                "description": "Perayaan selesai hackathon",
                "date": "2025-08-24",
                "max_participants": 50
            },
            user_address=msg.user_address
        )
    elif "rsvp" in message_lower and ("daftar" in message_lower or "add" in message_lower):
        # Mock RSVP creation
        mock_response = StructuredOutputResponse(
            action="add_rsvp",
            rsvp_input={
                "event_name": "Hackathon Afterparty",
                "participant_name": "Test User",
                "participant_email": "test@example.com"
            },
            user_address=msg.user_address
        )
    elif "list" in message_lower and "event" in message_lower:
        # Mock list events
        mock_response = StructuredOutputResponse(
            action="list_events",
            user_address=msg.user_address
        )
    elif "health" in message_lower:
        # Mock health check
        mock_response = StructuredOutputResponse(
            action="health_check",
            user_address=msg.user_address
        )
    else:
        # Default to event creation for testing
        mock_response = StructuredOutputResponse(
            action="create_event",
            event_input={
                "name": "Default Test Event",
                "description": "Event created from default parsing",
                "date": "2025-08-25",
                "max_participants": 30
            },
            user_address=msg.user_address
        )
    
    ctx.logger.info(f"🤖 Simulator LLM mengirim balasan terstruktur: {mock_response.action}")
    await ctx.send(sender, mock_response)

if __name__ == "__main__":
    print(f"🤖 Starting Mini LLM Simulator...")
    print(f"🔗 Address: {mini_llm.address}")
    mini_llm.run()