from flask import Flask
from flask_migrate import Migrate
from extensions import db, bcrypt, login_manager
from config import Config
from models.user import User
from flask_login import current_user
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# ✅ Init extensions
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# ✅ Setup login manager
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ Setup Flask-Migrate
migrate = Migrate(app, db)

# ✅ Register blueprints
from routes.auth import auth_bp
app.register_blueprint(auth_bp)

from routes.admin import admin_bp
app.register_blueprint(admin_bp)

# ✅ Inject user into templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ✅ Jinja filter for formatting month strings (e.g., '2025-05' -> 'May 2025')
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%B %Y'):
    try:
        return datetime.strptime(value, '%Y-%m').strftime(format)
    except Exception:
        return value

# ✅ Flask CLI entrypoint
if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5001)
