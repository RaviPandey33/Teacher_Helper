class PaymentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    month = db.Column(db.String(20))
    amount = db.Column(db.Float)
    razorpay_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default="pending")
    link = db.Column(db.String(500))
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
