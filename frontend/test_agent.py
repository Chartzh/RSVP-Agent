import asyncio
from uagents import Agent, Context
from models import ChatMessage, RSVPResponse
import logging
import sys

logging.basicConfig(level=logging.INFO)

# Update dengan alamat agent.py Anda yang baru (akan digenerate saat Anda jalankan agent.py)
MAIN_AGENT_ADDRESS = "agent1qw3c3kh4lxthjqsht28luml9lk6wrf67rasfs37x8za8d2cvkzfmktm5ekf"  # Ganti dengan address dari agent.py
TEST_MESSAGE = "Tolong buatkan event 'Hackathon Afterparty' tanggal 24 Agustus 2025 jam 8 malam di 'Rooftop Cafe'. Deskripsinya 'Perayaan selesai hackathon'."

agent = Agent(
    name="final_simple_tester",
    seed="final_simple_tester_seed",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"]
)

@agent.on_event("startup")
async def setup(ctx: Context):
    ctx.logger.info(f"🧪 Test Agent started")
    ctx.logger.info(f"🔗 Test Agent address: {agent.address}")

@agent.on_event("startup")
async def send_test_message(ctx: Context):
    """Kirim pesan tes sederhana saat startup."""
    await asyncio.sleep(2)  # Wait a bit for other agents to be ready
    ctx.logger.info(f"📤 Mengirim pesan ke {MAIN_AGENT_ADDRESS}")
    await ctx.send(
        MAIN_AGENT_ADDRESS,
        ChatMessage(message=TEST_MESSAGE, sender_address=agent.address)
    )

@agent.on_message(model=RSVPResponse)
async def handle_final_response(ctx: Context, sender: str, msg: RSVPResponse):
    """Handle balasan akhir dari agen utama."""
    ctx.logger.info("✅ BERHASIL MENERIMA BALASAN AKHIR!")
    ctx.logger.info(f"📊 Success Status: {msg.success}")
    ctx.logger.info(f"💬 Message: {msg.message}")
    if msg.data:
        ctx.logger.info(f"📄 Data: {msg.data}")
    # Don't stop immediately to see all logs
    await asyncio.sleep(1)
    ctx.logger.info("🏁 Test completed successfully!")
    sys.exit()

if __name__ == "__main__":
    print("🧪 Starting Test Agent...")
    print(f"🔗 Test Agent address: {agent.address}")
    agent.run()