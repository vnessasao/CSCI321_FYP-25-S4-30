"""
Main Flask application for Traffic Analysis system.
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.incidents import incidents_bp
from routes.bookmarks import bookmarks_bp

from routes.traffic_routes import traffic_bp
from routes.traffic import lta_bp
from routes.data_upload import data_upload_bp
from routes.bottlenecks import bottlenecks_bp
from routes.jam_prediction import jam_prediction_bp

# Phase 1 feature routes
from routes.trends import trends_bp
from routes.users import users_bp
from routes.algorithms import algorithms_bp

# Phase 2 feature routes
from routes.weather import weather_bp
from routes.transport import transport_bp

# Phase 3 feature routes
from routes.schedules import schedules_bp
from routes.anomalies import anomalies_bp

# Phase 4 feature routes
from routes.logs import logs_bp
from routes.permissions import permissions_bp
from routes.feedback import feedback_bp
from routes.backups import backups_bp

# Phase 5 feature routes (Government)
from routes.roadwork import roadwork_bp
from routes.emas import emas_bp

from database_config import db

# Load environment variables from .env file
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for frontend communication
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(incidents_bp, url_prefix='/api')
    app.register_blueprint(bookmarks_bp, url_prefix='/api')

    app.register_blueprint(traffic_bp, url_prefix='/api/traffic')
    app.register_blueprint(lta_bp, url_prefix='/api/lta')
    app.register_blueprint(data_upload_bp, url_prefix='/api/upload')
    app.register_blueprint(bottlenecks_bp, url_prefix='/api/bottlenecks')
    app.register_blueprint(jam_prediction_bp, url_prefix='/api/jam-prediction')

    # Phase 1 feature blueprints
    app.register_blueprint(trends_bp, url_prefix='/api/trends')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(algorithms_bp, url_prefix='/api/algorithms')

    # Phase 2 feature blueprints
    app.register_blueprint(weather_bp, url_prefix='/api/weather')
    app.register_blueprint(transport_bp, url_prefix='/api/transport')

    # Phase 3 feature blueprints
    app.register_blueprint(schedules_bp, url_prefix='/api/schedules')
    app.register_blueprint(anomalies_bp, url_prefix='/api/anomalies')

    # Phase 4 feature blueprints
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    app.register_blueprint(permissions_bp, url_prefix='/api/permissions')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(backups_bp, url_prefix='/api/backups')

    # Phase 5 feature blueprints (Government)
    app.register_blueprint(roadwork_bp, url_prefix='/api')
    app.register_blueprint(emas_bp, url_prefix='/api')


    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Traffic Analysis API is running'}, 200
    
    # Test database connection on startup
    try:
        db.init_db()
        print("✅ Database connection verified")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
