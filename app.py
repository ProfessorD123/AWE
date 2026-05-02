import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import requests   # ← NEW (required for Turnstile verification)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# SMTP config (loaded from .env)
# ──────────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "info@ampwave.events")

# ──────────────────────────────────────────────
# Cloudflare Turnstile
# ──────────────────────────────────────────────
TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET")   # ← NEW

def verify_turnstile(response_token, remote_ip):
    """Verify Cloudflare Turnstile token."""
    try:
        r = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": TURNSTILE_SECRET,
                "response": response_token,
                "remoteip": remote_ip
            },
            timeout=5
        )
        result = r.json()
        return result.get("success", False)
    except Exception as exc:
        logger.error("Turnstile verification failed: %s", exc)
        return False


def send_contact_email(name: str, email: str, phone: str, event_type: str,
                        event_date: str, message: str) -> bool:
    """Send a contact enquiry email to AmpWave and a confirmation to the sender."""
    try:
        # ── Internal notification ──────────────────────────────────────────
        internal = MIMEMultipart("alternative")
        internal["Subject"] = f"New Enquiry from {name} – AmpWave Events"
        internal["From"]    = SMTP_USER
        internal["To"]      = CONTACT_EMAIL
        internal["Reply-To"] = email

        internal_html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#222;background:#f9f9f9;padding:30px;">
          <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;
                      border-top:5px solid #FFD000;padding:30px;">
            <h2 style="color:#FFD000;margin-top:0;">New Hire Enquiry</h2>
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:8px 0;font-weight:bold;width:130px;">Name</td>
                  <td>{name}</td></tr>
              <tr><td style="padding:8px 0;font-weight:bold;">Email</td>
                  <td><a href="mailto:{email}">{email}</a></td></tr>
              <tr><td style="padding:8px 0;font-weight:bold;">Phone</td>
                  <td>{phone or '—'}</td></tr>
              <tr><td style="padding:8px 0;font-weight:bold;">Event Type</td>
                  <td>{event_type or '—'}</td></tr>
              <tr><td style="padding:8px 0;font-weight:bold;">Event Date</td>
                  <td>{event_date or '—'}</td></tr>
            </table>
            <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
            <h3 style="margin-bottom:8px;">Message</h3>
            <p style="white-space:pre-wrap;color:#444;">{message}</p>
            <p style="color:#999;font-size:0.85em;margin-top:30px;">
              Received {datetime.now().strftime("%d %b %Y at %H:%M")} AEST
            </p>
          </div>
        </body></html>
        """
        internal.attach(MIMEText(internal_html, "html"))

        # ── Auto-reply to sender ───────────────────────────────────────────
        reply = MIMEMultipart("alternative")
        reply["Subject"] = "Thanks for reaching out – AmpWave Events"
        reply["From"]    = CONTACT_EMAIL
        reply["To"]      = email

        reply_html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#222;background:#f9f9f9;padding:30px;">
          <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;
                      border-top:5px solid #FFD000;padding:30px;">
            <h2 style="color:#FFD000;margin-top:0;">Thanks, {name.split()[0]}!</h2>
            <p>We've received your enquiry and will be in touch within <strong>1–2 business days</strong>.</p>
            <p style="color:#555;">In the meantime, feel free to reply to this email or call us directly.</p>
            <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
            <p style="font-size:0.85em;color:#999;">
              AmpWave Events · Professional Event Audio Services · NSW &amp; ACT<br>
              <a href="mailto:info@ampwave.events" style="color:#FFD000;">info@ampwave.events</a>
            </p>
          </div>
        </body></html>
        """
        reply.attach(MIMEText(reply_html, "html"))

        # ── Send both ──────────────────────────────────────────────────────
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, CONTACT_EMAIL, internal.as_string())
            server.sendmail(CONTACT_EMAIL, email, reply.as_string())

        return True

    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return False


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":

        # ── NEW: Turnstile token check ───────────────────────────────
        token = request.form.get("cf-turnstile-response")
        if not token or not verify_turnstile(token, request.remote_addr):
            flash("Verification failed — please try again.", "error")
            return render_template("contact.html", form_data=request.form)
        # ─────────────────────────────────────────────────────────────

        name       = request.form.get("name", "").strip()
        email      = request.form.get("email", "").strip()
        phone      = request.form.get("phone", "").strip()
        event_type = request.form.get("event_type", "").strip()
        event_date = request.form.get("event_date", "").strip()
        message    = request.form.get("message", "").strip()

        errors = []
        if not name:    errors.append("Name is required.")
        if not email:   errors.append("Email is required.")
        if not message: errors.append("Message is required.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("contact.html",
                                   form_data=request.form)

        if send_contact_email(name, email, phone, event_type, event_date, message):
            flash("Thanks! We'll be in touch within 1–2 business days.", "success")
            return redirect(url_for("contact"))
        else:
            flash("Something went wrong sending your message. "
                  "Please email us directly at info@ampwave.events.", "error")
            return render_template("contact.html", form_data=request.form)

    return render_template("contact.html", form_data={})


@app.route("/tos")
def tos():
    return render_template("tos.html")


# ──────────────────────────────────────────────
# Dev runner
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)