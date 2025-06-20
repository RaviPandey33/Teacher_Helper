from extensions import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: 'YYYY-MM' (e.g., '2025-06')
    status = db.Column(db.String(10), nullable=False, default='Unpaid')  # 'Paid' or 'Unpaid'

    student = db.relationship('Student', backref='payments')
