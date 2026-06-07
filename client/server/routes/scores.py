from flask import Blueprint, jsonify, request
from database import get_db, serialize_doc
from datetime import datetime

scores_bp = Blueprint('scores', __name__)

@scores_bp.route('', methods=['GET'])
def get_all_scores():
    db = get_db()
    if db is None:
        return jsonify([])
        
    scores = list(db["scores"].find({}))
    return jsonify(serialize_doc(scores))

@scores_bp.route('', methods=['POST'])
def save_score():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    data = request.get_json() or {}
    event_id = data.get('eventId')
    event_name = data.get('eventName')
    competitor = data.get('competitor')
    score = data.get('score')
    
    if not event_id or not event_name or not competitor or not score:
        return jsonify({"success": False, "message": "Missing required score fields"}), 400
        
    scores_col = db["scores"]
    
    # Store or update the live score for the competitor in this event
    score_doc = {
        "eventId": event_id,
        "eventName": event_name,
        "competitor": competitor,
        "score": score,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # Check if we should update or insert (keep a history or just show latest)
        # We can update the score if the competitor already has one for this event, or just insert new ones
        existing = scores_col.find_one({"eventId": event_id, "competitor": competitor})
        if existing:
            scores_col.update_one({"_id": existing["_id"]}, {"$set": score_doc})
            message = "Score updated successfully!"
        else:
            scores_col.insert_one(score_doc)
            message = "Score saved successfully!"
            
        return jsonify({"success": True, "message": message, "score": serialize_doc(score_doc)}), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to save score: {str(e)}"}), 500
