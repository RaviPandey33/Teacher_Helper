from flask import Flask, redirect, url_for
from flask_migrate import Migrate
from flask_login import current_user
from extensions import db, bcrypt, login_manager
from config import Config
from models.user import User
from datetime import datetime
from dotenv import load_dotenv
import json
from routes.admin import admin_bp

app = Flask(__name__)

# ✅ Load environment variables
load_dotenv()

# ✅ Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///masterji.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(Config)

# ✅ Register Jinja filter
@app.template_filter('fromjson')
def fromjson_filter(value):
    try:
        return json.loads(value)
    except Exception:
        return []

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%B %Y'):
    try:
        return datetime.strptime(value, '%Y-%m').strftime(format)
    except Exception:
        return value

# ✅ Init extensions
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# ✅ Setup login manager
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        return User.query.get(int(user_id))

# ✅ Setup Flask-Migrate
migrate = Migrate(app, db)

# ✅ Register blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.payments import payments
from routes.webhook import webhook_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payments)
app.register_blueprint(webhook_bp)

# ✅ Inject current_user into templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.route('/')
def home():
    return redirect(url_for('auth.login'))

@app.route('/ping')
def ping():
    return "Hello from Flask!" 

# ✅ Main
if __name__ == "__main__":
    # ✅ Auto-create all tables
    with app.app_context():
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5001)
