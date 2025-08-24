import Map "mo:base/HashMap";
import Text "mo:base/Text";
import Array "mo:base/Array";
import Result "mo:base/Result";
import Time "mo:base/Time";
import Debug "mo:base/Debug";
import Iter "mo:base/Iter";
import Nat "mo:base/Nat";

persistent actor RSVPManager {
    // Type definitions
    public type RSVP = {
        id: Text;
        event_name: Text;
        participant_name: Text;
        participant_email: Text;
        timestamp: Int;
        status: Text; // "confirmed", "pending", "cancelled"
    };

    public type RSVPInput = {
        event_name: Text;
        participant_name: Text;
        participant_email: Text;
    };

    public type Event = {
        name: Text;
        description: Text;
        date: Text;
        max_participants: Nat;
        current_participants: Nat;
        created_at: Int;
    };

    public type EventInput = {
        name: Text;
        description: Text;
        date: Text;
        max_participants: Nat;
    };

    // Storage
    private stable var rsvpEntries : [(Text, RSVP)] = [];
    private stable var eventEntries : [(Text, Event)] = [];
    private stable var nextId : Nat = 1;
    
    private transient var rsvps = Map.HashMap<Text, RSVP>(10, Text.equal, Text.hash);
    private transient var events = Map.HashMap<Text, Event>(10, Text.equal, Text.hash);
    
    // System functions for upgrades
    system func preupgrade() {
        rsvpEntries := Iter.toArray(rsvps.entries());
        eventEntries := Iter.toArray(events.entries());
    };

    system func postupgrade() {
        // Restore RSVPs from stable storage
        rsvps := Map.HashMap<Text, RSVP>(10, Text.equal, Text.hash);
        for ((id, rsvp) in rsvpEntries.vals()) {
            rsvps.put(id, rsvp);
        };
        
        // Restore events from stable storage
        events := Map.HashMap<Text, Event>(10, Text.equal, Text.hash);
        for ((id, event) in eventEntries.vals()) {
            events.put(id, event);
        };
        
        // Clear stable storage after restoration
        rsvpEntries := [];
        eventEntries := [];
    };

    // Helper function to generate ID
    private func generateId() : Text {
        let id = "rsvp_" # Nat.toText(nextId);
        nextId += 1;
        id
    };

    // Create a new event
    public func create_event(input: EventInput) : async Result.Result<Text, Text> {
        let eventId = "event_" # Nat.toText(nextId);
        nextId += 1;
        
        let newEvent : Event = {
            name = input.name;
            description = input.description;
            date = input.date;
            max_participants = input.max_participants;
            current_participants = 0;
            created_at = Time.now();
        };
        
        events.put(eventId, newEvent);
        return #Ok("Event created successfully with ID: " # eventId);
    };

    // Add RSVP
    public func add_rsvp(input: RSVPInput) : async Result.Result<Text, Text> {
        // Check if event exists
        let eventExists = switch (events.get(input.event_name)) {
            case (?event) { true };
            case null { 
                // If event doesn't exist by ID, check by name
                var found = false;
                for ((id, event) in events.entries()) {
                    if (event.name == input.event_name) {
                        found := true;
                    };
                };
                found
            };
        };

        if (not eventExists) {
            return #err("Event '" # input.event_name # "' does not exist");
        };

        // Check for duplicate RSVP
        for ((id, rsvp) in rsvps.entries()) {
            if (rsvp.event_name == input.event_name and 
                rsvp.participant_email == input.participant_email) {
                return #err("RSVP already exists for this email in this event");
            };
        };

        let rsvpId = generateId();
        let newRSVP : RSVP = {
            id = rsvpId;
            event_name = input.event_name;
            participant_name = input.participant_name;
            participant_email = input.participant_email;
            timestamp = Time.now();
            status = "confirmed";
        };

        rsvps.put(rsvpId, newRSVP);

        // Update event participant count
        for ((eventId, event) in events.entries()) {
            if (event.name == input.event_name) {
                let updatedEvent : Event = {
                    name = event.name;
                    description = event.description;
                    date = event.date;
                    max_participants = event.max_participants;
                    current_participants = event.current_participants + 1;
                    created_at = event.created_at;
                };
                events.put(eventId, updatedEvent);
            };
        };

        return #Ok("RSVP added successfully with ID: " # rsvpId);
    };

    // List all RSVPs
    public query func list_rsvps() : async [RSVP] {
        Iter.toArray(rsvps.vals())
    };

    // List RSVPs for specific event
    public query func list_rsvps_by_event(eventName: Text) : async [RSVP] {
        let filtered = Array.filter<RSVP>(
            Iter.toArray(rsvps.vals()),
            func(rsvp: RSVP) : Bool {
                rsvp.event_name == eventName
            }
        );
        filtered
    };

    // List all events
    public query func list_events() : async [Event] {
        Iter.toArray(events.vals())
    };

    // Get specific RSVP by ID
    public query func get_rsvp(id: Text) : async ?RSVP {
        rsvps.get(id)
    };

    // Cancel RSVP
    public func cancel_rsvp(rsvpId: Text) : async Result.Result<Text, Text> {
        switch (rsvps.get(rsvpId)) {
            case (?rsvp) {
                let updatedRSVP : RSVP = {
                    id = rsvp.id;
                    event_name = rsvp.event_name;
                    participant_name = rsvp.participant_name;
                    participant_email = rsvp.participant_email;
                    timestamp = rsvp.timestamp;
                    status = "cancelled";
                };
                rsvps.put(rsvpId, updatedRSVP);
                
                // Update event participant count
                for ((eventId, event) in events.entries()) {
                    if (event.name == rsvp.event_name and event.current_participants > 0) {
                        let updatedEvent : Event = {
                            name = event.name;
                            description = event.description;
                            date = event.date;
                            max_participants = event.max_participants;
                            current_participants = event.current_participants - 1;
                            created_at = event.created_at;
                        };
                        events.put(eventId, updatedEvent);
                    };
                };
                
                return #Ok("RSVP cancelled successfully");
            };
            case null {
                return #err("RSVP not found");
            };
        }
    };

    // Get event by name
    public query func get_event_by_name(name: Text) : async ?Event {
        for ((id, event) in events.entries()) {
            if (event.name == name) {
                return ?event;
            };
        };
        null
    };

    // Health check
    public query func health() : async Text {
        "RSVP Manager is running. Total RSVPs: " # 
        Nat.toText(rsvps.size()) # 
        ", Total Events: " # 
        Nat.toText(events.size())
    };
}