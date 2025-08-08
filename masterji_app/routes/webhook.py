from flask import Blueprint, request, jsonify
import hmac
import hashlib
import os
from models.payment_status import FeeStatus
from extensions import db
from datetime import datetime

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET')
    payload = request.data
    received_sig = request.headers.get('X-Razorpay-Signature')

    # 🔒 Verify webhook authenticity
    generated_sig = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(generated_sig, received_sig):
        return jsonify({'status': 'unauthenticated'}), 403

    event = request.get_json()
    if event['event'] == 'payment_link.paid':
        link_id = event['payload']['payment_link']['entity']['id']
        email = event['payload']['payment_link']['entity']['customer']['email']

        # 💾 Find and update the payment status
        from models.student import Student
        student = Student.query.filter_by(parent_email=email).first()
        if student:
            month_key = datetime.now().strftime('%Y-%m')
            status = FeeStatus.query.filter_by(student_id=student.id, month=month_key).first()
            if status:
                status.paid = True
            else:
                status = FeeStatus(student_id=student.id, month=month_key, link_sent=True, paid=True)
                db.session.add(status)

            db.session.commit()

    return jsonify({'status': 'success'}), 200
