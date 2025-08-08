from extensions import db
from datetime import datetime

class FeeStatus(db.Model):
    __tablename__ = 'payment_statuses'
    __table_args__ = {'extend_existing': True}  # ✅ ADD THIS

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer,
                           db.ForeignKey('students.id', ondelete='CASCADE'),
                           nullable=False)
    month = db.Column(db.String(7), nullable=False)
    link_sent = db.Column(db.Boolean, default=False)
    payment_done = db.Column(db.Boolean, default=False)
    razorpay_payment_id = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship("Student", back_populates="payment_statuses")

