from extensions import db
from datetime import datetime

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))

    student_country_code = db.Column(db.String(10))   # ✅ New field
    parent_country_code = db.Column(db.String(10))    # ✅ New field

    parent_name = db.Column(db.String(150))
    parent_email = db.Column(db.String(150))
    parent_phone = db.Column(db.String(50))
    discord_id = db.Column(db.String(100))
    sibling_reference = db.Column(db.String(150))
    learning_subject = db.Column(db.String(100))
    notes = db.Column(db.Text)

    fee_per_month = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(20))                # ✅ New field
    residing_country = db.Column(db.String(50))      # ✅ New field

    date_joined = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default="active")  # active or inactive
