from extensions import db
from datetime import date

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'Present' or 'Absent'

    student = db.relationship('Student', backref='attendances')
