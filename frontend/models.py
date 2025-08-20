from pydantic import BaseModel
from typing import Optional, Literal, List
from uagents import Model, Protocol
from enum import Enum

# Base Models yang sesuai dengan smart contract
class RSVPInput(BaseModel):
    event_name: str
    participant_name: str
    participant_email: str

class RSVP(BaseModel):
    id: str
    event_name: str
    participant_name: str
    participant_email: str
    timestamp: int
    status: Literal["confirmed", "pending", "cancelled"]

class EventInput(BaseModel):
    name: str
    description: str
    date: str
    max_participants: int

class Event(BaseModel):
    name: str
    description: str
    date: str
    max_participants: int
    current_participants: int
    created_at: int

# Request Models untuk komunikasi dengan LLM
class ActionType(str, Enum):
    CREATE_EVENT = "create_event"
    ADD_RSVP = "add_rsvp"
    LIST_RSVPS = "list_rsvps"
    LIST_EVENTS = "list_events"
    GET_RSVP = "get_rsvp"
    CANCEL_RSVP = "cancel_rsvp"
    LIST_RSVPS_BY_EVENT = "list_rsvps_by_event"
    GET_EVENT_BY_NAME = "get_event_by_name"
    HEALTH_CHECK = "health_check"
    UNKNOWN = "unknown"

class RSVPRequest(BaseModel):
    action: ActionType
    event_input: Optional[EventInput] = None
    rsvp_input: Optional[RSVPInput] = None
    event_name: Optional[str] = None
    rsvp_id: Optional[str] = None
    user_query: Optional[str] = None

# Protocol Messages - These need to inherit from Model for uAgents
class ChatMessage(Model):
    message: str
    sender_address: str

class StructuredOutputRequest(Model):
    message: str
    user_address: str

class StructuredOutputResponse(Model):
    action: str
    event_input: Optional[dict] = None
    rsvp_input: Optional[dict] = None
    event_name: Optional[str] = None
    rsvp_id: Optional[str] = None
    user_query: Optional[str] = None

class RSVPResponse(Model):
    success: bool
    message: str
    data: Optional[dict] = None

# Agent communication models - using Model base class
class AgentRSVPRequest(Model):
    event_name: str
    date: str
    time: str
    location: str
    description: Optional[str] = None

class AgentRSVPResponse(Model):
    status: str
    message: str

# Response Models
class ServiceResult(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# Protocol definitions
chat_protocol = Protocol("Chat")
structured_output_protocol = Protocol("StructuredOutput")
rsvp_response_protocol = Protocol("RSVPResponse")

from uagents import Model
from typing import Optional

class NaturalLanguageRequest(Model):
    message: str

class RSVPRequest(Model):
    event_name: str
    date: str
    time: str
    location: str
    description: Optional[str] = None