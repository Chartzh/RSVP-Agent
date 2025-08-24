import aiohttp
import cbor2
import json
from typing import Optional, List, Dict, Any
from models import RSVP, Event, RSVPInput, EventInput, ServiceResult
import logging
import time

class RSVPService:
    def __init__(self, canister_id: str = None, gateway_url: str = "http://127.0.0.1:4943"):
        self.gateway_url = gateway_url
        self.canister_id = canister_id or "uxrrr-q7777-77774-qaaaq-cai"  # Pastikan ID ini benar
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _call_canister(self, method_name: str, args: Any = None) -> ServiceResult:
        """Memanggil method di canister dengan format CBOR dan payload yang lengkap"""
        try:
            # BARU: Membuat timestamp kedaluwarsa 5 menit dari sekarang
            expiry_time = int((time.time() + 300) * 1_000_000_000)

            candid_arg_bytes = b''
            if isinstance(args, dict):
                if all(k in args for k in ['name', 'description', 'date', 'max_participants']):
                    candid_arg_bytes = self._encode_event_input(args)
                elif all(k in args for k in ['event_name', 'participant_name', 'participant_email']):
                    candid_arg_bytes = self._encode_rsvp_input(args)
            elif isinstance(args, str):
                candid_arg_bytes = self._encode_text(args)

            inner_payload = {
                "request_type": "call",
                "canister_id": self.canister_id,
                "method_name": method_name,
                "arg": candid_arg_bytes,
                "ingress_expiry": expiry_time, # <-- BARU: Menambahkan expiry
                "sender": b'\x04' # <-- DIUBAH: Menggunakan sender anonim yang benar
            }

            final_payload = {"content": inner_payload}
            cbor_payload = cbor2.dumps(final_payload)

            url = f"{self.gateway_url}/api/v2/canister/{self.canister_id}/call"
            headers = {"Content-Type": "application/cbor"}

            async with self.session.post(url, data=cbor_payload, headers=headers) as response:
                if response.status == 200:
                    response_bytes = await response.read()
                    return ServiceResult(success=True, message="Success", data=cbor2.loads(response_bytes))
                else:
                    error_text = await response.text()
                    return ServiceResult(success=False, message=f"HTTP {response.status}: {error_text}", data=None)
        except Exception as e:
            self.logger.error(f"Error calling canister: {str(e)}")
            return ServiceResult(success=False, message=f"Error calling canister: {str(e)}", data=None)

    async def _query_canister(self, method_name: str, args: Any = None) -> ServiceResult:
        """Query method di canister dengan format CBOR dan payload yang lengkap"""
        try:
            # BARU: Membuat timestamp kedaluwarsa 5 menit dari sekarang
            expiry_time = int((time.time() + 300) * 1_000_000_000)

            candid_arg_bytes = b''
            if isinstance(args, str):
                candid_arg_bytes = self._encode_text(args)

            inner_payload = {
                "request_type": "query",
                "canister_id": self.canister_id,
                "method_name": method_name,
                "arg": candid_arg_bytes,
                "ingress_expiry": expiry_time, # <-- BARU: Menambahkan expiry
                "sender": b'\x04' # <-- DIUBAH: Menggunakan sender anonim yang benar
            }
            
            final_payload = {"content": inner_payload}
            cbor_payload = cbor2.dumps(final_payload)
            
            url = f"{self.gateway_url}/api/v2/canister/{self.canister_id}/query"
            headers = {"Content-Type": "application/cbor"}
            
            async with self.session.post(url, data=cbor_payload, headers=headers) as response:
                if response.status == 200:
                    response_bytes = await response.read()
                    response_data = cbor2.loads(response_bytes)
                    if response_data.get("status") == "replied":
                        decoded_arg = cbor2.loads(response_data['reply']['arg'])
                        return ServiceResult(success=True, message="Success", data=decoded_arg)
                    else:
                        return ServiceResult(success=False, message=f"Query failed: {response_data.get('reject_message')}", data=None)
                else:
                    error_text = await response.text()
                    return ServiceResult(success=False, message=f"HTTP {response.status}: {error_text}", data=None)
        except Exception as e:
            self.logger.error(f"Error querying canister: {str(e)}")
            return ServiceResult(success=False, message=f"Error querying canister: {str(e)}", data=None)
    
    def _encode_event_input(self, event_data: dict) -> bytes:
        """Encode EventInput to Candid format"""
        try:
            # Simple Candid encoding for EventInput record
            # This is a basic implementation - in production you'd use a proper Candid library
            candid_data = b'DIDL\x01\x6c\x04'  # Record with 4 fields
            candid_data += b'\x00\x01\x02\x03'  # Field indices
            candid_data += b'\x71\x71\x71\x7f'  # Types: text, text, text, nat
            
            # Encode field values
            name = event_data.get('name', '').encode('utf-8')
            description = event_data.get('description', '').encode('utf-8')
            date = event_data.get('date', '').encode('utf-8')
            max_participants = event_data.get('max_participants', 0)
            
            # Add lengths and data
            candid_data += len(name).to_bytes(4, 'little') + name
            candid_data += len(description).to_bytes(4, 'little') + description  
            candid_data += len(date).to_bytes(4, 'little') + date
            candid_data += max_participants.to_bytes(8, 'little')
            
            return candid_data
        except Exception as e:
            self.logger.error(f"Error encoding event input: {e}")
            return b'DIDL\x00\x00'  # Return empty record on error
    
    def _encode_rsvp_input(self, rsvp_data: dict) -> bytes:
        """Encode RSVPInput to Candid format"""
        try:
            # Simple Candid encoding for RSVPInput record
            candid_data = b'DIDL\x01\x6c\x03'  # Record with 3 fields
            candid_data += b'\x00\x01\x02'  # Field indices
            candid_data += b'\x71\x71\x71'  # Types: text, text, text
            
            # Encode field values
            event_name = rsvp_data.get('event_name', '').encode('utf-8')
            participant_name = rsvp_data.get('participant_name', '').encode('utf-8')
            participant_email = rsvp_data.get('participant_email', '').encode('utf-8')
            
            # Add lengths and data
            candid_data += len(event_name).to_bytes(4, 'little') + event_name
            candid_data += len(participant_name).to_bytes(4, 'little') + participant_name
            candid_data += len(participant_email).to_bytes(4, 'little') + participant_email
            
            return candid_data
        except Exception as e:
            self.logger.error(f"Error encoding RSVP input: {e}")
            return b'DIDL\x00\x00'  # Return empty record on error
    
    def _encode_text(self, text: str) -> bytes:
        """Encode simple text to Candid format"""
        try:
            text_bytes = text.encode('utf-8')
            candid_data = b'DIDL\x00\x01\x71'  # Text type
            candid_data += len(text_bytes).to_bytes(4, 'little') + text_bytes
            return candid_data
        except Exception as e:
            self.logger.error(f"Error encoding text: {e}")
            return b'DIDL\x00\x00'  # Return empty record on error
        
    async def create_event(self, event_input: EventInput) -> ServiceResult:
        """Membuat event baru"""
        self.logger.info(f"📤 Creating event: {event_input.name}")
        
        # Convert EventInput to dict format expected by canister
        args = {
            "name": event_input.name,
            "description": event_input.description,
            "date": event_input.date,
            "max_participants": event_input.max_participants
        }
        
        return await self._call_canister("create_event", args)
    
    async def add_rsvp(self, rsvp_input: RSVPInput) -> ServiceResult:
        """Menambahkan RSVP baru"""
        args = {
            "event_name": rsvp_input.event_name,
            "participant_name": rsvp_input.participant_name,
            "participant_email": rsvp_input.participant_email
        }
        return await self._call_canister("add_rsvp", args)
    
    async def list_rsvps(self) -> ServiceResult:
        """Mendapatkan semua RSVP"""
        return await self._query_canister("list_rsvps")
    
    async def list_rsvps_by_event(self, event_name: str) -> ServiceResult:
        """Mendapatkan RSVP berdasarkan nama event"""
        return await self._query_canister("list_rsvps_by_event", event_name)
    
    async def list_events(self) -> ServiceResult:
        """Mendapatkan semua event"""
        return await self._query_canister("list_events")
    
    async def get_rsvp(self, rsvp_id: str) -> ServiceResult:
        """Mendapatkan RSVP berdasarkan ID"""
        return await self._query_canister("get_rsvp", rsvp_id)
    
    async def cancel_rsvp(self, rsvp_id: str) -> ServiceResult:
        """Membatalkan RSVP"""
        return await self._call_canister("cancel_rsvp", rsvp_id)
    
    async def get_event_by_name(self, event_name: str) -> ServiceResult:
        """Mendapatkan event berdasarkan nama"""
        return await self._query_canister("get_event_by_name", event_name)
    
    async def health_check(self) -> ServiceResult:
        """Health check"""
        return await self._query_canister("health")
    
    def format_response_message(self, result: ServiceResult, action: str) -> str:
        """Format response message untuk user"""
        if not result.success:
            return f"❌ Error: {result.message}"
        
        if action == "create_event":
            return f"✅ {result.data if isinstance(result.data, str) else 'Event berhasil dibuat!'}"
        
        elif action == "add_rsvp":
            return f"✅ {result.data if isinstance(result.data, str) else 'RSVP berhasil ditambahkan!'}"
        
        elif action == "list_events":
            if isinstance(result.data, list) and result.data:
                events_text = "\n📅 **Daftar Event:**\n"
                for event in result.data:
                    events_text += f"• **{event.get('name', 'N/A')}**\n"
                    events_text += f"  📝 {event.get('description', 'N/A')}\n"
                    events_text += f"  🗓️ {event.get('date', 'N/A')}\n"
                    events_text += f"  👥 {event.get('current_participants', 0)}/{event.get('max_participants', 0)} peserta\n\n"
                return events_text
            else:
                return "📅 Tidak ada event yang ditemukan."
        
        elif action == "list_rsvps" or action == "list_rsvps_by_event":
            if isinstance(result.data, list) and result.data:
                rsvps_text = "\n📋 **Daftar RSVP:**\n"
                for rsvp in result.data:
                    status_emoji = "✅" if rsvp.get('status') == "confirmed" else "❌" if rsvp.get('status') == "cancelled" else "⏳"
                    rsvps_text += f"• **{rsvp.get('participant_name', 'N/A')}** {status_emoji}\n"
                    rsvps_text += f"  📧 {rsvp.get('participant_email', 'N/A')}\n"
                    rsvps_text += f"  🎪 Event: {rsvp.get('event_name', 'N/A')}\n"
                    rsvps_text += f"  📊 Status: {rsvp.get('status', 'N/A')}\n\n"
                return rsvps_text
            else:
                return "📋 Tidak ada RSVP yang ditemukan."
        
        elif action == "get_rsvp":
            if result.data:
                rsvp = result.data
                status_emoji = "✅" if rsvp.get('status') == "confirmed" else "❌" if rsvp.get('status') == "cancelled" else "⏳"
                return f"📋 **RSVP Details:**\n• **{rsvp.get('participant_name', 'N/A')}** {status_emoji}\n📧 {rsvp.get('participant_email', 'N/A')}\n🎪 Event: {rsvp.get('event_name', 'N/A')}\n📊 Status: {rsvp.get('status', 'N/A')}"
            else:
                return "❌ RSVP tidak ditemukan."
        
        elif action == "cancel_rsvp":
            return f"✅ {result.data if isinstance(result.data, str) else 'RSVP berhasil dibatalkan!'}"
        
        elif action == "get_event_by_name":
            if result.data:
                event = result.data
                return f"📅 **Event Details:**\n• **{event.get('name', 'N/A')}**\n📝 {event.get('description', 'N/A')}\n🗓️ {event.get('date', 'N/A')}\n👥 {event.get('current_participants', 0)}/{event.get('max_participants', 0)} peserta"
            else:
                return "❌ Event tidak ditemukan."
        
        elif action == "health_check":
            return f"🟢 {result.data if isinstance(result.data, str) else 'Service is running healthy!'}"
        
        else:
            return f"✅ Operasi berhasil: {result.message}"