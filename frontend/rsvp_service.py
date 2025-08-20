import aiohttp
import cbor2
import json
from typing import Optional, List, Dict, Any
from models import RSVP, Event, RSVPInput, EventInput, ServiceResult

class RSVPService:
    def __init__(self, canister_id: str = None, gateway_url: str = "http://127.0.0.1:4943"):
        self.gateway_url = gateway_url
        self.canister_id = canister_id or "uxrrr-q7777-77774-qaaaq-cai"  # Default local canister ID
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _call_canister(self, method_name: str, args: Any = None) -> ServiceResult:
        """Memanggil method di canister dengan format ICP HTTP Gateway v2"""
        try:
            # Prepare the call payload
            call_payload = {
                "request_type": "call",
                "canister_id": self.canister_id,
                "method_name": method_name,
                "arg": cbor2.dumps(args) if args is not None else cbor2.dumps(()),
                "sender": "2vxsx-fae",  # Anonymous caller
            }
            
            # Encode to CBOR
            cbor_data = cbor2.dumps(call_payload)
            
            # Make the request
            url = f"{self.gateway_url}/api/v2/canister/{self.canister_id}/call"
            headers = {
                "Content-Type": "application/cbor",
            }
            
            async with self.session.post(url, data=cbor_data, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.read()
                    decoded_response = cbor2.loads(response_data)
                    
                    # Handle different response formats
                    if isinstance(decoded_response, dict):
                        if "status" in decoded_response and decoded_response["status"] == "replied":
                            result = decoded_response.get("reply", {}).get("arg", None)
                            if result:
                                decoded_result = cbor2.loads(result)
                                return ServiceResult(
                                    success=True,
                                    message="Success",
                                    data=decoded_result
                                )
                    
                    return ServiceResult(
                        success=True,
                        message="Success",
                        data=decoded_response
                    )
                else:
                    error_text = await response.text()
                    return ServiceResult(
                        success=False,
                        message=f"HTTP {response.status}: {error_text}",
                        data=None
                    )
                    
        except Exception as e:
            return ServiceResult(
                success=False,
                message=f"Error calling canister: {str(e)}",
                data=None
            )
    
    async def _query_canister(self, method_name: str, args: Any = None) -> ServiceResult:
        """Query method di canister (read-only operations)"""
        try:
            # Prepare the query payload
            query_payload = {
                "request_type": "query",
                "canister_id": self.canister_id,
                "method_name": method_name,
                "arg": cbor2.dumps(args) if args is not None else cbor2.dumps(()),
                "sender": "2vxsx-fae",  # Anonymous caller
            }
            
            # Encode to CBOR
            cbor_data = cbor2.dumps(query_payload)
            
            # Make the request
            url = f"{self.gateway_url}/api/v2/canister/{self.canister_id}/query"
            headers = {
                "Content-Type": "application/cbor",
            }
            
            async with self.session.post(url, data=cbor_data, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.read()
                    decoded_response = cbor2.loads(response_data)
                    
                    # Handle query response format
                    if isinstance(decoded_response, dict):
                        if "status" in decoded_response and decoded_response["status"] == "replied":
                            result = decoded_response.get("reply", {}).get("arg", None)
                            if result:
                                decoded_result = cbor2.loads(result)
                                return ServiceResult(
                                    success=True,
                                    message="Success",
                                    data=decoded_result
                                )
                    
                    return ServiceResult(
                        success=True,
                        message="Success",
                        data=decoded_response
                    )
                else:
                    error_text = await response.text()
                    return ServiceResult(
                        success=False,
                        message=f"HTTP {response.status}: {error_text}",
                        data=None
                    )
                    
        except Exception as e:
            return ServiceResult(
                success=False,
                message=f"Error querying canister: {str(e)}",
                data=None
            )
    
    async def create_event(self, event_input: EventInput) -> ServiceResult:
        """Membuat event baru"""
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