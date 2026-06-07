from flask import Blueprint, jsonify, request
from database import get_db, serialize_doc
from bson import ObjectId

results_bp = Blueprint('results', __name__)

DEFAULT_RESULTS = [
    # Solo Event Leaderboard (100m Sprint)
    {
        "type": "solo",
        "eventId": "sprint",
        "eventName": "100m Sprint Championship",
        "standings": [
            {"rank": 1, "participantName": "Aditya Sharma", "regno": "UG23CS01", "record": "10.82s", "department": "Computer Science"},
            {"rank": 2, "participantName": "Harish Kumar", "regno": "UG23ME12", "record": "11.10s", "department": "Mechanical Eng."},
            {"rank": 3, "participantName": "Rahul Varma", "regno": "UG23EC09", "record": "11.25s", "department": "Electronics & Comm."}
        ]
    },
    # Solo Event Leaderboard (High Jump)
    {
        "type": "solo",
        "eventId": "highjump",
        "eventName": "High Jump",
        "standings": [
            {"rank": 1, "participantName": "Vikram Singh", "regno": "UG24CS45", "record": "1.95m", "department": "Computer Science"},
            {"rank": 2, "participantName": "Siddharth Roy", "regno": "UG23CE04", "record": "1.90m", "department": "Civil Eng."},
            {"rank": 3, "participantName": "Arjun Das", "regno": "UG25EE11", "record": "1.85m", "department": "Electrical Eng."}
        ]
    },
    # Team Event Leaderboard (Football)
    {
        "type": "team",
        "eventId": "football",
        "eventName": "Football Knockout Cup",
        "standings": [
            {"rank": 1, "teamName": "FC computer Science", "department": "Computer Science", "record": "Winner (3-1)"},
            {"rank": 2, "teamName": "Mechanical Warriors", "department": "Mechanical Eng.", "record": "Runner-Up"},
            {"rank": 3, "teamName": "ECE strikers", "department": "Electronics & Comm.", "record": "Third Place"}
        ]
    },
    # Team Event Leaderboard (Basketball)
    {
        "type": "team",
        "eventId": "basketball",
        "eventName": "Basketball Cup",
        "standings": [
            {"rank": 1, "teamName": "CS Ballers", "department": "Computer Science", "record": "Winner (62-58)"},
            {"rank": 2, "teamName": "EEE Thunder", "department": "Electrical Eng.", "record": "Runner-Up"},
            {"rank": 3, "teamName": "Civil Giants", "department": "Civil Eng.", "record": "Third Place"}
        ]
    }
]

def seed_results():
    """Seeds default results/standings list if empty."""
    db = get_db()
    if db is None:
        return
    
    results_col = db["results"]
    if results_col.count_documents({}) == 0:
        results_col.insert_many(DEFAULT_RESULTS)
        print("Default results seeded successfully.")

@results_bp.route('', methods=['GET'])
def get_all_results():
    db = get_db()
    if db is None:
        return jsonify([])
        
    results = list(db["results"].find({}))
    return jsonify(serialize_doc(results))

@results_bp.route('', methods=['POST'])
def create_result():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    data = request.get_json() or {}
    event_id = data.get('eventId')
    event_name = data.get('eventName')
    reg_type = data.get('type') # 'solo' or 'team'
    standings = data.get('standings', [])
    
    if not event_id or not event_name or not reg_type or len(standings) == 0:
        return jsonify({"success": False, "message": "Missing required result fields"}), 400
        
    results_col = db["results"]
    
    # Check if a result already exists for this event; if so, update it, otherwise insert
    existing = results_col.find_one({"eventId": event_id})
    
    result_doc = {
        "type": reg_type,
        "eventId": event_id,
        "eventName": event_name,
        "standings": standings
    }
    
    try:
        if existing:
            results_col.update_one({"_id": existing["_id"]}, {"$set": result_doc})
            message = "Leaderboard updated successfully!"
        else:
            results_col.insert_one(result_doc)
            message = "Leaderboard created successfully!"
            
        return jsonify({"success": True, "message": message, "result": serialize_doc(result_doc)})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to save result: {str(e)}"}), 500
