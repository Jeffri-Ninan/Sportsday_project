from flask import Blueprint, jsonify, request
from database import get_db, serialize_doc

events_bp = Blueprint('events', __name__)

DEFAULT_EVENTS = [
    # Solo Events
    {
        "id": "sprint",
        "displayName": "100m Sprint Championship",
        "type": "solo",
        "image": "100m_Sprint.jpg.jpeg",
        "description": "Showcase your raw speed in the classic track event.",
        "date": "2026-10-10",
        "time": "09:00 AM",
        "venue": "Main Athletic Track"
    },
    {
        "id": "sprint200m",
        "displayName": "200m Sprint",
        "type": "solo",
        "image": "200m_Sprint.jpg.jpeg",
        "description": "Test your endurance and speed in the half-lap dash.",
        "date": "2026-10-10",
        "time": "11:00 AM",
        "venue": "Main Athletic Track"
    },
    {
        "id": "highjump",
        "displayName": "High Jump",
        "type": "solo",
        "image": "High_Jump.jpg.jpeg",
        "description": "Leap over the bar and set new heights.",
        "date": "2026-10-11",
        "time": "09:30 AM",
        "venue": "Jumping Pit A"
    },
    {
        "id": "longjump",
        "displayName": "Long Jump",
        "type": "solo",
        "image": "Long_Jump.jpg.jpeg",
        "description": "Sprint down the runway and leap into the sand pit.",
        "date": "2026-10-11",
        "time": "02:00 PM",
        "venue": "Jumping Pit B"
    },
    {
        "id": "badminton",
        "displayName": "Badminton Singles",
        "type": "solo",
        "image": "Badminton_Singles.jpg.jpeg",
        "description": "Fast-paced racket action on the indoor courts.",
        "date": "2026-10-12",
        "time": "10:00 AM",
        "venue": "Indoor Sports Complex"
    },
    # Team Events
    {
        "id": "basketball",
        "displayName": "Basketball",
        "type": "team",
        "image": "BasketBall.jpg.jpeg",
        "description": "5v5 tournament on the concrete courts.",
        "date": "2026-10-13",
        "time": "08:30 AM",
        "venue": "Outdoor Basketball Court"
    },
    {
        "id": "football",
        "displayName": "Football",
        "type": "team",
        "image": "Football.jpg.jpeg",
        "description": "11v11 knockout cup on the grass turf.",
        "date": "2026-10-14",
        "time": "08:00 AM",
        "venue": "Main Football Ground"
    },
    {
        "id": "cricket",
        "displayName": "Cricket",
        "type": "team",
        "image": "Cricket.jpg.jpeg",
        "description": "T10 format tournament with tennis ball.",
        "date": "2026-10-15",
        "time": "07:30 AM",
        "venue": "College Cricket Ground"
    },
    {
        "id": "volleyball",
        "displayName": "Volleyball",
        "type": "team",
        "image": "VolleyBall.jpg.jpeg",
        "description": "6v6 clash of spikes and blocks.",
        "date": "2026-10-12",
        "time": "03:00 PM",
        "venue": "Outdoor Volleyball Court"
    }
]

def seed_events():
    """Seeds default events list if empty."""
    db = get_db()
    if db is None:
        return
    
    events_col = db["events"]
    if events_col.count_documents({}) == 0:
        events_col.insert_many(DEFAULT_EVENTS)
        print("Default events seeded successfully.")

@events_bp.route('', methods=['GET'])
def get_all_events():
    db = get_db()
    if db is None:
        return jsonify([])
    
    events = list(db["events"].find({}))
    return jsonify(serialize_doc(events))

@events_bp.route('', methods=['POST'])
def create_event():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    # Check if active session is admin
    from flask import session
    if 'user' not in session or session['user'].get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized. Admin access required."}), 403
        
    data = request.get_json() or {}
    name = data.get('name')
    event_id = data.get('id')
    date = data.get('date')
    venue = data.get('venue')
    status = data.get('status', 'Active')
    
    if not name or not event_id or not date or not venue:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
        
    events_col = db["events"]
    if events_col.find_one({"id": event_id}):
        return jsonify({"success": False, "message": f"Event ID '{event_id}' already exists"}), 409
        
    new_event = {
        "id": event_id,
        "displayName": name,
        "type": "team" if name.lower() in ["football", "basketball", "volleyball", "cricket"] else "solo",
        "image": f"{event_id}.jpg.jpeg",
        "description": f"{name} tournament.",
        "date": date,
        "time": "09:00 AM",
        "venue": venue,
        "status": status
    }
    
    events_col.insert_one(new_event)
    return jsonify({
        "success": True, 
        "message": f"Event '{name}' created successfully",
        "event": serialize_doc(new_event)
    }), 201

@events_bp.route('/<event_id>', methods=['GET'])
def get_event(event_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not available"}), 503
        
    event = db["events"].find_one({"id": event_id})
    if not event:
        return jsonify({"error": "Event not found"}), 404
        
    return jsonify(serialize_doc(event))

