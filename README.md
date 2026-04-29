# AmpWave Events – Flask Application

## Project Structure

```
ampwave/
├── app.py               # Flask application & SMTP logic
├── wsgi.py              # Gunicorn entry point
├── gunicorn.conf.py     # Gunicorn configuration
├── requirements.txt     # Python dependencies
├── .env.template        # Environment variable template
├── .env                 # Your local secrets (never commit this)
└── templates/
    ├── base.html        # Shared layout
    ├── index.html
    ├── about.html
    ├── services.html
    ├── contact.html     # SMTP contact form
    └── tos.html         # Terms & Conditions of Hire
└── static/
    ├── images/          # Drop your existing images here
    │   ├── pa-system.jpg
    │   ├── mixer.jpg
    │   ├── corporate-event.jpg
    │   └── SM58-1.jpg
```

---

## Quick Start (local development)

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.template .env
# Edit .env with your SMTP credentials and secret key

# 4. Run the development server
python app.py
# Visit http://localhost:5000
```

---

## Production Deployment (Gunicorn)

```bash
# Run with the provided config (binds to 0.0.0.0:8000)
gunicorn -c gunicorn.conf.py wsgi:app

# Or quickly with inline options
gunicorn --workers=3 --bind=0.0.0.0:8000 wsgi:app
```

### Systemd service (recommended for VPS/Linux servers)

Create `/etc/systemd/system/ampwave.service`:

```ini
[Unit]
Description=AmpWave Events – Gunicorn
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/ampwave
EnvironmentFile=/var/www/ampwave/.env
ExecStart=/var/www/ampwave/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ampwave
sudo systemctl start ampwave
```

### Nginx reverse proxy (recommended)

```nginx
server {
    listen 80;
    server_name ampwave.events www.ampwave.events;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /var/www/ampwave/static/;
        expires 30d;
    }
}
```

Secure with Certbot: `sudo certbot --nginx -d ampwave.events -d www.ampwave.events`

---

## SMTP / Email Setup

The contact form sends:
1. **An internal notification** to `info@ampwave.events` with all enquiry details.
2. **An auto-reply** to the client confirming receipt.

### Gmail App Password (recommended)
1. Enable 2-Step Verification on your Google account.
2. Go to **myaccount.google.com → Security → App Passwords**.
3. Create a password for "Mail" → copy it into `SMTP_PASSWORD` in your `.env`.

### Other SMTP providers
Update `SMTP_HOST` and `SMTP_PORT` in `.env` (e.g. Mailgun, SendGrid, Zoho).

---

## Important Notes

- **Never commit `.env`** — add it to `.gitignore`.
- Update `[INSERT ABN]` in `templates/tos.html` with your actual ABN.
- Drop static images into `static/images/` (same filenames as the original HTML files).
