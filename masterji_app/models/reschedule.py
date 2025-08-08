from extensions import db
from datetime import datetime
from models.payment_status import FeeStatus




    


from extensions import db
from datetime import datetime

from datetime import datetime, date


class TemporaryClass(db.Model):
    __tablename__ = 'temporary_classes'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    class_day = db.Column(db.String(20), nullable=False)
    class_time = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    zoom_link = db.Column(db.String(255), default='')  # ✅ GOOD
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_cancelled = db.Column(db.Boolean, default=False)  # ✅ Make sure this exists
    status = db.Column(db.String(20), default='active')


class SkippedClass(db.Model):
    __tablename__ = 'skipped_classes'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
