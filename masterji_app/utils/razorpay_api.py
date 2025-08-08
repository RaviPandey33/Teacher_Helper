import razorpay
import os

client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_SECRET")))

def create_payment_link(name, email, amount_usd, description):
    amount_cents = int(amount_usd * 100)  # Razorpay takes amount in "paise"
    response = client.invoice.create({
        "type": "link",
        "amount": amount_cents,
        "currency": "USD",
        "description": description,
        "customer": {
            "email": email,
            "name": name
        },
        "notify": {"email": True},
        "reminder_enable": True
    })
    return response['short_url'], response['id']
