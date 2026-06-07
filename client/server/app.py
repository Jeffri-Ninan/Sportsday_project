import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import database initialization
from database import get_db
# Import blueprints
from routes.auth import auth_bp, seed_users
from routes.events import events_bp, seed_events
from routes.registrations import registrations_bp
from routes.results import results_bp, seed_results
from routes.scores import scores_bp

# Load environment variables
load_dotenv(override=True)

app = Flask(__name__, 
            static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_sports_day_26")

from flask import redirect
@app.route('/')
def root_redirect():
    return redirect('/templates/dep_eve_login.html')

# Enable CORS for frontend integration with explicit origins to support credentials/cookies
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5000", "http://127.0.0.1:5000",
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:8000", "http://127.0.0.1:8000",
    "http://localhost:8080", "http://127.0.0.1:8080",
    "http://localhost:8888", "http://127.0.0.1:8888",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "null"
]}})

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(events_bp, url_prefix='/api/events')
app.register_blueprint(registrations_bp, url_prefix='/api/registrations')
app.register_blueprint(results_bp, url_prefix='/api/results')
app.register_blueprint(scores_bp, url_prefix='/api/scores')

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    db = get_db()
    db_status = "Connected" if db is not None else "Disconnected"
    return jsonify({
        "status": "healthy",
        "database": db_status
    }), 200

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# Perform seeding on startup
with app.app_context():
    try:
        print("Checking/seeding database...")
        seed_users()
        seed_events()
        seed_results()
        print("Seeding checks complete.")
    except Exception as e:
        print(f"Error during startup seeding: {e}")

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
