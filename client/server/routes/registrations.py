from flask import Blueprint, jsonify, request
from database import get_db, serialize_doc
from bson import ObjectId
from datetime import datetime

registrations_bp = Blueprint('registrations', __name__)

@registrations_bp.route('', methods=['GET'])
def get_all_registrations():
    db = get_db()
    if db is None:
        return jsonify([])
        
    from flask import session
    query = {}
    
    # Restrict registrations based on session user role
    if 'user' in session:
        user = session['user']
        role = user.get('role')
        if role == 'dept':
            dept_name = user.get('department')
            if dept_name:
                # Direct match, but case-insensitive to handle spacing/casing variations securely
                query["department"] = {"$regex": f"^{dept_name}$", "$options": "i"}
        elif role == 'event':
            # Event coordinator sees only registrations for their specific event (unless 'all' event scope is set)
            event_slug = user.get('event')
            if event_slug and event_slug.lower() != 'all':
                query["event"] = {"$regex": f"^{event_slug}$", "$options": "i"}
                
    registrations = list(db["registrations"].find(query))
    return jsonify(serialize_doc(registrations))

@registrations_bp.route('', methods=['POST'])
def create_registration():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    data = request.get_json() or {}
    
    # Resolve department (force department coordinator's department if logged in)
    from flask import session
    user_dept = session.get('user', {}).get('department') if 'user' in session else None
    user_role = session.get('user', {}).get('role') if 'user' in session else None
    
    if user_role == 'dept' and user_dept:
        dept = user_dept
    else:
        dept = data.get('department') or user_dept or 'General'
        
    # Extract fields
    reg_type = data.get('type')  # 'solo' or 'team'
    event_identifier = data.get('eventId') or data.get('event')
    
    if not reg_type or not event_identifier:
        return jsonify({"success": False, "message": "Missing registration type or event identifier"}), 400
        
    # Check if event exists (by id first, then by name)
    event = db["events"].find_one({"id": event_identifier})
    if not event:
        event = db["events"].find_one({"name": event_identifier})
        
    if not event:
        return jsonify({"success": False, "message": "Invalid event ID"}), 400
        
    event_id = event["id"]
        
    # Check if this department has already registered for this event (limit: 1 per dept)
    if dept and dept.lower() != 'general':
        existing_reg = db["registrations"].find_one({
            "department": {"$regex": f"^{dept}$", "$options": "i"},
            "event": event_id
        })
        if existing_reg:
            return jsonify({
                "success": False, 
                "message": f"Limit reached: Department '{dept}' has already registered for this event."
            }), 400
        
    # Build players list
    players = []
    from flask import session
    
    if reg_type == 'solo':
        # Retrieve player from players list or root properties
        players_input = data.get('players', [])
        if len(players_input) > 0 and isinstance(players_input[0], dict):
            p0 = players_input[0].copy()
            player_info = {
                "name": p0.get('name') or data.get('name'),
                "regno": p0.get('regno') or data.get('regno'),
                "email": p0.get('email') or data.get('email'),
                "phone": p0.get('phone') or data.get('phone'),
                "year": p0.get('year') or data.get('year'),
                "gender": p0.get('gender') or data.get('gender'),
                "isLeader": True
            }
            # Copy over any extra fields that might be inside the player dictionary
            for k, v in p0.items():
                if k not in player_info:
                    player_info[k] = v
        else:
            player_info = {
                "name": data.get('name'),
                "regno": data.get('regno'),
                "email": data.get('email'),
                "phone": data.get('phone'),
                "year": data.get('year'),
                "gender": data.get('gender'),
                "isLeader": True
            }
        
        # Validation
        if not player_info.get("name") or not player_info.get("regno") or not player_info.get("email"):
            return jsonify({"success": False, "message": "Missing required personal details (name, regno, email)"}), 400
            
        players.append(player_info)
        
        # Build document
        registration_doc = {
            "type": "solo",
            "event": event_id,
            "department": dept,
            "players": players,
            "medicalNotes": data.get('medicalNotes', 'None'),
            "extra": data.get('extra', {}),
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    elif reg_type == 'team':
        team_name = data.get('teamName')
        team_players_input = data.get('players', [])
        
        if not team_name:
            return jsonify({"success": False, "message": "Missing team name"}), 400
            
        if len(team_players_input) == 0:
            return jsonify({"success": False, "message": "At least one team member (leader) is required"}), 400
            
        for idx, p in enumerate(team_players_input):
            player_info = p.copy()
            player_info["isLeader"] = p.get('isLeader', idx == 0) # Defaults to first player as leader
            
            if not player_info.get("name") or not player_info.get("regno"):
                return jsonify({"success": False, "message": f"Player {idx+1} is missing required fields (name, regno)"}), 400
                
            players.append(player_info)
            
        # Build document
        registration_doc = {
            "type": "team",
            "event": event_id,
            "department": dept,
            "teamName": team_name,
            "players": players,
            "medicalNotes": data.get('medicalNotes', 'None'),
            "extra": data.get('extra', {}),
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        return jsonify({"success": False, "message": "Invalid registration type"}), 400
        
    try:
        result = db["registrations"].insert_one(registration_doc)
        inserted_id = str(result.inserted_id)
        
        # Also return the full created registration object
        registration_doc["_id"] = inserted_id
        return jsonify({
            "success": True, 
            "message": "Registration submitted successfully!",
            "registration": serialize_doc(registration_doc)
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to save registration: {str(e)}"}), 500

@registrations_bp.route('/<reg_id>', methods=['DELETE'])
def delete_registration(reg_id):
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    from flask import session
    query = {"_id": ObjectId(reg_id)}
    
    # Restrict deletion permission based on session user role
    if 'user' in session:
        user = session['user']
        role = user.get('role')
        if role == 'dept':
            dept_name = user.get('department')
            if dept_name:
                query["department"] = {"$regex": f"^{dept_name}$", "$options": "i"}
        elif role == 'event':
            event_slug = user.get('event')
            if event_slug and event_slug.lower() != 'all':
                query["event"] = {"$regex": f"^{event_slug}$", "$options": "i"}
                
    try:
        result = db["registrations"].delete_one(query)
        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Registration not found or unauthorized"}), 404
        return jsonify({"success": True, "message": "Registration deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error deleting registration: {str(e)}"}), 500
