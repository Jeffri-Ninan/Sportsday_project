from flask import Blueprint, request, jsonify, session
import bcrypt
from database import get_db, serialize_doc

auth_bp = Blueprint('auth', __name__)

def seed_users():
    """Seeds default users for testing if database is empty."""
    db = get_db()
    if db is None:
        return
        
    users_col = db["users"]
    
    # Check if admin already exists
    if users_col.count_documents({}) == 0:
        default_users = [
            {
                "username": "admin",
                "role": "admin",
                "displayName": "System Admin",
                "password": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            },
            {
                "username": "cs_coord",
                "role": "dept",
                "displayName": "CS Coordinator",
                "department": "Computer Science",
                "password": bcrypt.hashpw("cs123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            },
            {
                "username": "it_coord",
                "role": "dept",
                "displayName": "IT Coordinator",
                "department": "Information Technology",
                "password": bcrypt.hashpw("it123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            },
            {
                "username": "bcom_coord",
                "role": "dept",
                "displayName": "BCom Coordinator",
                "department": "Bachelor of Commerce",
                "password": bcrypt.hashpw("bcom123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            },
            {
                "username": "electronics_science_coord",
                "role": "dept",
                "displayName": "Electronics Science Coordinator",
                "department": "Electronics & Science",
                "password": bcrypt.hashpw("elec123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            },
            {
                "username": "event_manager",
                "role": "event",
                "displayName": "Event Manager",
                "event": "all",
                "password": bcrypt.hashpw("event123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            }
        ]
        users_col.insert_many(default_users)
        print("Default users seeded successfully.")

    depts_col = db["departments"]
    if depts_col.count_documents({}) == 0:
        default_depts = [
            {
                "deptId": "25IT6UG",
                "name": "Information Technology",
                "coordinator": "Dr. John Kennady",
                "email": "kennady@it.sports.edu",
                "phone": "98787 98766",
                "totalStudents": 80,
                "shift": "Shift-I",
                "username": "it_coord",
                "password": "it123"
            },
            {
                "deptId": "25BC67T",
                "name": "Bachelor of Commerce",
                "coordinator": "S. Bharath",
                "email": "bharath@bcom.sports.edu",
                "phone": "94448 49752",
                "totalStudents": 120,
                "shift": "Shift-II",
                "username": "bcom_coord",
                "password": "bcom123"
            },
            {
                "deptId": "25CS768U",
                "name": "Computer Science",
                "coordinator": "Dr. Antony",
                "email": "antony@cs.sports.edu",
                "phone": "78845 24682",
                "totalStudents": 150,
                "shift": "Shift-I",
                "username": "cs_coord",
                "password": "cs123"
            },
            {
                "deptId": "25EL912S",
                "name": "Electronics & Science",
                "coordinator": "Dr. Meenakshi",
                "email": "meenakshi@elec.sports.edu",
                "phone": "97654 32109",
                "totalStudents": 90,
                "shift": "Shift-I",
                "username": "electronics_science_coord",
                "password": "elec123"
            }
        ]
        depts_col.insert_many(default_depts)
        print("Default departments seeded successfully.")

@auth_bp.route('/login', methods=['POST'])
def login():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Missing username or password"}), 400
        
    user = db["users"].find_one({"username": username})
    if not user:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401
        
    # Check password
    stored_password = user.get('password')
    try:
        # Verify hash
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            # Store in session
            user_session_info = {
                "username": user.get("username"),
                "role": user.get("role"),
                "displayName": user.get("displayName", user.get("username"))
            }
            if user.get("department"):
                user_session_info["department"] = user["department"]
            if user.get("event"):
                user_session_info["event"] = user["event"]
                
            session["user"] = user_session_info
            return jsonify({
                "success": True, 
                "message": "Logged in successfully",
                "user": user_session_info
            })
    except Exception as e:
        print(f"Error checking password: {e}")
        
    return jsonify({"success": False, "message": "Invalid username or password"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@auth_bp.route('/session', methods=['GET'])
def get_session():
    if 'user' in session:
        return jsonify({"authenticated": True, "user": session['user']})
    return jsonify({"authenticated": False}), 401

@auth_bp.route('/create-user', methods=['POST'])
def create_user():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    # Check if active session is admin
    if 'user' not in session or session['user'].get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized. Admin access required."}), 403
        
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    display_name = data.get('displayName')
    
    if not username or not password or not role or not display_name:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
        
    users_col = db["users"]
    if users_col.find_one({"username": username}):
        return jsonify({"success": False, "message": "Username already exists"}), 409
        
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = {
        "username": username,
        "password": hashed_password,
        "role": role,
        "displayName": display_name
    }
    
    if role == 'dept':
        new_user['department'] = data.get('department', 'General')
    elif role == 'event':
        new_user['event'] = data.get('event', 'general')
        
    users_col.insert_one(new_user)
    return jsonify({"success": True, "message": f"User {username} created successfully"})

@auth_bp.route('/seed', methods=['POST'])
def run_seed():
    try:
        seed_users()
        return jsonify({"success": True, "message": "Seeding script run successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

import random
import string
import re

@auth_bp.route('/register-dept', methods=['POST'])
def register_dept():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    # Check if active session is admin
    if 'user' not in session or session['user'].get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized. Admin access required."}), 403
        
    data = request.get_json() or {}
    department = data.get('department')
    coordinator_name = data.get('coordinatorName')
    email = data.get('email')
    phone = data.get('phone')
    total_students = data.get('totalStudents')
    shift = data.get('shift')
    
    if not department or not coordinator_name or not email or not phone:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
        
    # Generate Department ID / Username slug (e.g. "Electronics" -> "electronics_coord")
    dept_slug = re.sub(r'[^a-z0-9]', '_', department.lower())
    username = f"{dept_slug}_coord"
    
    # Check if user already exists
    users_col = db["users"]
    if users_col.find_one({"username": username}):
        return jsonify({"success": False, "message": f"Coordinator account '{username}' already exists"}), 409
        
    # Generate random password (8 alphanumeric characters)
    password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Insert User Document
    users_col.insert_one({
        "username": username,
        "password": hashed_password,
        "role": "dept",
        "displayName": f"{coordinator_name} ({department})",
        "department": department
    })
    
    # Insert Department Document for listing
    dept_id = f"26SD{random.randint(100, 999)}"
    dept_doc = {
        "deptId": dept_id,
        "name": department,
        "coordinator": coordinator_name,
        "email": email,
        "phone": phone,
        "totalStudents": total_students or 0,
        "shift": shift or 'Shift-I',
        "username": username,
        "password": password # Plain password for display in admin preview once
    }
    db["departments"].insert_one(dept_doc)
    
    return jsonify({
        "success": True,
        "message": "Department registered and coordinator login created successfully!",
        "username": username,
        "password": password,
        "deptId": dept_id
    }), 201

@auth_bp.route('/register-manager', methods=['POST'])
def register_manager():
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Database not available"}), 503
        
    # Check if active session is admin
    if 'user' not in session or session['user'].get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized. Admin access required."}), 403
        
    data = request.get_json() or {}
    department = data.get('department')
    coordinator_name = data.get('coordinatorName')
    staff_id = data.get('staffId')
    phone = data.get('phone')
    shift = data.get('shift')
    in_charge = data.get('inCharge')
    
    if not department or not coordinator_name or not staff_id or not phone:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
        
    # Generate event coordinator username (e.g. "it_football_coord")
    dept_slug = re.sub(r'[^a-z0-9]', '_', department.lower())
    incharge_slug = re.sub(r'[^a-z0-9]', '_', in_charge.lower()) if in_charge else 'general'
    username = f"{dept_slug}_{incharge_slug}_coord"
    
    # Check if user already exists
    users_col = db["users"]
    if users_col.find_one({"username": username}):
        return jsonify({"success": False, "message": f"Coordinator account '{username}' already exists"}), 409
        
    # Generate random password (8 alphanumeric characters)
    password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Insert User Document (event role)
    users_col.insert_one({
        "username": username,
        "password": hashed_password,
        "role": "event",
        "displayName": f"{coordinator_name} ({in_charge or 'Sports'})",
        "department": department,
        "event": incharge_slug
    })
    
    # Insert Department/Staff Document under departments collection
    dept_doc = {
        "deptId": staff_id,
        "name": department,
        "coordinator": coordinator_name,
        "phone": phone,
        "shift": shift or 'Shift-I',
        "inCharge": in_charge or 'General',
        "username": username,
        "password": password,
        "role": "event"
    }
    db["departments"].insert_one(dept_doc)
    
    return jsonify({
        "success": True,
        "message": "Event manager registered and login details created successfully!",
        "username": username,
        "password": password,
        "deptId": staff_id
    }), 201


@auth_bp.route('/departments', methods=['GET'])
def get_departments():
    db = get_db()
    if db is None:
        return jsonify([])
        
    depts = list(db["departments"].find({}))
    return jsonify(serialize_doc(depts))
