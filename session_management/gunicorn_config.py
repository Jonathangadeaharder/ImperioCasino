"""
Gunicorn configuration for ImperioCasino production deployment.

This configuration is optimized for production use with multiple worker processes,
appropriate timeouts, and comprehensive logging.
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'  # Use 'gevent' or 'eventlet' for async if needed
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests to prevent memory leaks
max_requests_jitter = 50  # Add randomness to max_requests to prevent all workers restarting at once
timeout = 30  # Workers silent for more than this many seconds are killed and restarted
graceful_timeout = 30  # Give workers this many seconds to finish requests before force kill
keepalive = 2  # Keep-alive connections

# Process naming
proc_name = 'imperiocasino'

# Logging
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', 'logs/gunicorn_access.log')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', 'logs/gunicorn_error.log')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
daemon = False  # Set to True to run as daemon, but use systemd instead
pidfile = None  # Let systemd manage the PID
umask = 0o007
user = None  # Set by systemd
group = None  # Set by systemd
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn instead of NGINX)
# Usually SSL is handled by NGINX, but these options are available
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting ImperioCasino Gunicorn server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading ImperioCasino Gunicorn server...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"ImperioCasino server is ready. Listening on: {bind}")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Forking new master process...")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"Worker received ABORT signal (pid: {worker.pid})")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited, in the master process."""
    print(f"Worker exited (pid: {worker.pid})")

def worker_exit(server, worker):
    """Called just after a worker has been exited, in the worker process."""
    pass

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    print(f"Number of workers changed from {old_value} to {new_value}")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Shutting down ImperioCasino Gunicorn server...")

# Environment variables (optional - can also use .env)
raw_env = []
if os.environ.get('FLASK_ENV'):
    raw_env.append(f"FLASK_ENV={os.environ.get('FLASK_ENV')}")
