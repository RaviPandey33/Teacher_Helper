from flask import Blueprint, render_template, request, jsonify
from utils.razorpay_api import create_payment_link
from datetime import datetime
from models.student import Student
from models.payment_status import FeeStatus

from extensions import db  # ✅ Required for committing changes

payments = Blueprint('payments', __name__)


# ✅ Helper function to sanitize names for Razorpay
def clean_name(name):
    name = ''.join(c for c in name if c.isalpha() or c == ' ').strip()
    return name if len(name) >= 3 else "MasterJi Student"


@payments.route('/payments/send-links', methods=['GET', 'POST'])
def send_payment_links():
    students = Student.query.all()
    current_month = datetime.now().strftime('%B %Y')  # e.g., "June 2025"
    current_month_key = datetime.now().strftime('%Y-%m')  # e.g., "2025-06"

    if request.method == 'POST':
        data = request.get_json()
        selected_students = data.get('students', [])

        results = []
        for s in selected_students:
            link, razorpay_id = create_payment_link(
                name=clean_name(s['name']),  # ✅ Use sanitized name
                email=s['email'],
                amount_usd=s['amount'],
                description=f"Monthly Fee - {current_month}"
            )
            results.append({'name': s['name'], 'link': link})

            # ✅ Create or update PaymentStatus for current month
            status = FeeStatus.query.filter_by(student_id=s['id'], month=current_month_key).first()
            if not status:
                status = FeeStatus(student_id=s['id'], month=current_month_key)

            status.link_sent = True
            status.razorpay_payment_id = razorpay_id
            db.session.add(status)

        db.session.commit()
        return jsonify({'status': 'success', 'results': results})

    # ✅ GET: Pass statuses for UI display
    statuses = FeeStatus.query.filter_by(month=current_month_key).all()
    status_dict = {s.student_id: s for s in statuses}

    return render_template("payments.html", students=students, month=current_month, statuses=status_dict)


import hmac
import hashlib
import os
from flask import request, abort

@payments.route('/razorpay/webhook', methods=['POST'])
def razorpay_webhook():
    webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET')
    body = request.data
    signature = request.headers.get('X-Razorpay-Signature')

    # ✅ Verify webhook signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        abort(400, 'Invalid signature')

    payload = request.get_json()
    event = payload.get('event')

    if event == 'payment.link.paid':
        entity = payload['payload']['payment_link']['entity']
        razorpay_id = entity['id']

        # 🔄 Update PaymentStatus
        from models.payment_status import FeeStatus
        payment = FeeStatus.query.filter_by(razorpay_payment_id=razorpay_id).first()
        if payment:
            payment.payment_done = True
            from extensions import db
            db.session.commit()

    return '', 200
