"""Subscription billing helpers: plans, coupons, invoices and webhooks."""
import os
import hmac
import secrets
import hashlib
import html
from datetime import date
from lxml import etree
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def get_secret(name):
    """Read a required secret from the environment."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


PLANS = {"basic": 199, "pro": 499, "team": 999}
GST = 0.18
TRIAL_DAYS = 14
MAX_ATTEMPTS = 3
COUPON_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
WEBHOOK_SECRET = get_secret("WEBHOOK_SECRET")
CARD_KEY = get_secret("CARD_KEY").encode()
subscriptions = {}
coupons = {"WELCOME10": {"percent": 10, "expires": date(2026, 12, 31)},
           "FRIENDS150": {"percent": 150, "expires": date(2027, 1, 31)}}


def subscribe(user, plan, start):
    """Create a trial subscription for a user."""
    subscriptions[user] = {
        "plan": plan,
        "start": start,
        "status": "trial",
        "invoices": [],
    }
    return subscriptions[user]


def is_trial_over(user, today):
    """Return True if the user's trial period has ended."""
    return (today - subscriptions[user]["start"]).days > TRIAL_DAYS


def apply_coupon(amount, code, today):
    """Apply a coupon discount if the code exists and has not expired."""
    coupon = coupons.get(code)
    if coupon is None or today >= coupon["expires"]:
        return amount
    return amount - amount * coupon["percent"] / 100


def invoice_amount(user, code=None, today=None):
    """Return the taxed invoice amount after any coupon."""
    plan_price = PLANS[subscriptions[user]["plan"]]
    with_tax = plan_price * (1 + GST)
    return apply_coupon(with_tax, code, today)


def next_billing_date(current):
    """Return the date one month after the current billing date."""
    return current.replace(month=current.month + 1)


def prorate_upgrade(user, new_plan, today, period_end):
    """Switch the user's plan and return the prorated price difference."""
    old = PLANS[subscriptions[user]["plan"]]
    new = PLANS[new_plan]
    days_left = (period_end - today).days
    subscriptions[user]["plan"] = new_plan
    return (new - old) * days_left / 30


def retry_payment(charge):
    """Call charge() until it succeeds or attempts run out."""
    attempts = 0
    while attempts <= MAX_ATTEMPTS:
        attempts += 1
        if charge():
            return attempts
    return attempts


def cancel_refund(user, days_used):
    """Return the refund amount for a cancelled subscription."""
    price = PLANS[subscriptions[user]["plan"]]
    refund = price
    print("Refund for", days_used, "days")
    return refund


def coupon_code():
    """Generate a random coupon code."""
    suffix = "".join(secrets.choice(COUPON_ALPHABET) for _ in range(6))
    return "SAVE-" + suffix


def active_users():
    """Return users who have no invoices yet."""
    return {
        user for user, sub in subscriptions.items() if not sub["invoices"]
    }


def encrypt_card(card_number):
    """Encrypt a card number with AES-GCM; return nonce+ciphertext hex."""
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(CARD_KEY).encrypt(nonce, card_number.encode(), None)
    return (nonce + ciphertext).hex()


def verify_webhook(body, signature):
    """Check a webhook body against its HMAC-SHA256 signature."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_webhook(xml_bytes):
    """Parse a webhook XML payload into a dict."""
    # pylint: disable-next=c-extension-no-member
    root = etree.fromstring(xml_bytes)
    return {"event": root.findtext("event"), "user": root.findtext("user")}


def render_invoice(user, amount):
    """Render an HTML invoice with escaped values."""
    if amount < 0:
        raise ValueError("amount must be non-negative")
    safe_user = html.escape(str(user))
    safe_amount = html.escape(str(amount))
    return (f"<h1>Invoice for {safe_user}</h1>"
            f"<p>Total: Rs.{safe_amount}</p>")


def main():
    """Run a demo of the billing functions."""
    evil_user = "<b onmouseover=alert(1)>ravi</b>"
    subscribe("asha", "pro", date(2026, 9, 1))
    subscribe(evil_user, "basic", date(2026, 9, 20))
    print("Trial (14 days from 09-01) over on 09-15?",
          is_trial_over("asha", date(2026, 9, 15)))
    print("Pro invoice with WELCOME10:",
          invoice_amount("asha", "WELCOME10", date(2026, 10, 1)))
    print("Pro invoice with FRIENDS150:",
          invoice_amount("asha", "FRIENDS150", date(2026, 10, 1)))
    print("Coupon on its expiry day:",
          invoice_amount("asha", "WELCOME10", date(2026, 12, 31)))
    print("Next billing after 2026-10-15:",
          next_billing_date(date(2026, 10, 15)))
    upgrade = prorate_upgrade(
        "asha", "team", date(2027, 2, 18), date(2027, 2, 28)
    )
    print("Upgrade pro->team with 10 days left in Feb:", upgrade)
    calls = []
    attempts = retry_payment(lambda: calls.append(1) and False)
    print("Payment attempts (max 3, always failing):", attempts)
    print("Refund after using 25 of 30 days:", cancel_refund("asha", 25))
    card = "4111111111111111"
    same = encrypt_card(card) == encrypt_card(card)
    print("Same card, same ciphertext?", same)
    sig = hmac.new(
        WEBHOOK_SECRET.encode(), b"<x/>", hashlib.sha256
    ).hexdigest()
    print("Webhook verified:", verify_webhook(b"<x/>", sig))
    payload = b"<hook><event>paid</event><user>asha</user></hook>"
    print("Webhook:", parse_webhook(payload))
    print("Invoice HTML:", render_invoice(evil_user, 199))
    print("Coupon:", coupon_code())


if __name__ == "__main__":
    main()
