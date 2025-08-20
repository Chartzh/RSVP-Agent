# File: frontend/test_agent.py (Versi Final Sederhana)
import asyncio
from uagents import Agent, Context
from models import ChatMessage, RSVPResponse # Kita tidak perlu chat_protocol di sini
import logging

logging.basicConfig(level=logging.INFO)

# Ganti dengan alamat agent.py Anda yang sedang berjalan
MAIN_AGENT_ADDRESS = "agent1qduet3vnuswx0ep09szc94u2lrmrn9ws9mrxq0990dwh5cxgzktt2j6jknz"
TEST_MESSAGE = "Tolong buatkan event 'Hackathon Afterparty' tanggal 24 Agustus 2025 jam 8 malam di 'Rooftop Cafe'. Deskripsinya 'Perayaan selesai hackathon'."

agent = Agent(
    name="final_simple_tester",
    seed="final_simple_tester_seed",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"]
)

@agent.on_event("startup")
async def send_test_message(ctx: Context):
    """Kirim pesan tes sederhana saat startup."""
    ctx.logger.info(f"Mengirim pesan ke {MAIN_AGENT_ADDRESS}")
    await ctx.send(
        MAIN_AGENT_ADDRESS,
        ChatMessage(message=TEST_MESSAGE, sender_address=agent.address)
    )

@agent.on_message(model=RSVPResponse)
async def handle_final_response(ctx: Context, sender: str, msg: RSVPResponse):
    """Handle balasan akhir dari agen utama."""
    ctx.logger.info("✅ BERHASIL MENERIMA BALASAN AKHIR!")
    ctx.logger.info(f"Success Status: {msg.success}")
    ctx.logger.info(f"Message: {msg.message}")
    await ctx.stop()

if __name__ == "__main__":
    agent.run()