from extensions import db
from datetime import datetime, date


class Student(db.Model):
    __tablename__ = 'students'
    __table_args__ = {'extend_existing': True}  # ✅ Add this

    id = db.Column(db.Integer, primary_key=True)

    # 🔹 Basic Info
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    student_country_code = db.Column(db.String(10))   # ✅
    parent_country_code = db.Column(db.String(10))    # ✅
    parent_name = db.Column(db.String(150))
    parent_email = db.Column(db.String(150))
    parent_phone = db.Column(db.String(50))
    discord_id = db.Column(db.String(100))
    sibling_reference = db.Column(db.String(150))
    learning_subject = db.Column(db.String(100))
    notes = db.Column(db.Text)
    fee_per_month = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(20))                # ✅
    residing_country = db.Column(db.String(50))      # ✅
    
    reschedule_credits = db.Column(db.Integer, default=0)
    
    
    # 🔹 Timestamps and Status
    date_joined = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default="active")  # active or inactive

    # 🔹 Class Info
    classes_per_week = db.Column(db.String(20))
    timezone = db.Column(db.String(10))
    class_time_raw = db.Column(db.Text)  # Optional: to store multiple day+time combos (JSON or text)
    
    # ✅ Zoom Info
    zoom_link = db.Column(db.String(300))         # ✅ Zoom meeting URL
    zoom_password = db.Column(db.String(100))     # ✅ Optional password
    
    # 🔹 Profile Info
    date_of_birth = db.Column(db.Date)
    grade = db.Column(db.String(50))
    school_name = db.Column(db.String(100))
    hobbies = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    # 🔹 Future Tracking
    future_college = db.Column(db.String(100))
    future_stream = db.Column(db.String(100))
    career_interest = db.Column(db.Text)
    
    temporary_classes = db.relationship('TemporaryClass', cascade="all, delete-orphan", backref='student')
    skipped_classes = db.relationship('SkippedClass', cascade="all, delete-orphan", backref='student')
    # attendances = db.relationship('Attendance', cascade="all, delete-orphan")


    # ✅ Link to PaymentStatus with cascade delete
    payment_statuses = db.relationship(
    'FeeStatus',
    back_populates='student',
    cascade='all, delete-orphan',
    passive_deletes=True
    )

    

    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
