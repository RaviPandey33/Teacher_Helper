from extensions import db
from datetime import datetime
from datetime import date

class StudentComment(db.Model):
    __tablename__ = 'student_comments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    class_date = db.Column(db.Date, nullable=False, default=date.today)  # ✅ Add this
