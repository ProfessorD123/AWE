# gunicorn.conf.py
# Run with: gunicorn -c gunicorn.conf.py wsgi:app

import multiprocessing

# ── Binding ────────────────────────────────────────
bind            = "0.0.0.0:8000"

# ── Workers ────────────────────────────────────────
# 2-4 x CPU cores is a common starting point
workers         = multiprocessing.cpu_count() * 2 + 1
worker_class    = "sync"
timeout         = 120
keepalive       = 5

# ── Logging ────────────────────────────────────────
accesslog       = "-"        # stdout
errorlog        = "-"        # stderr
loglevel        = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# ── Process naming ─────────────────────────────────
proc_name       = "ampwave_events"

# ── Security ───────────────────────────────────────
limit_request_line   = 4094
limit_request_fields = 100
