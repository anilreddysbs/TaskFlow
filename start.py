import subprocess
import sys
import os

# Ensure outputs are flushed immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("=== STARTING TASKFLOW SERVICES ===")

print("1. Running database migrations...")
res = subprocess.run([sys.executable, "manage.py", "migrate"])
if res.returncode != 0:
    print(f"Migration failed with exit code {res.returncode}")
    sys.exit(res.returncode)

print("2. Starting Celery worker (concurrency=1)...")
worker_process = subprocess.Popen([
    sys.executable, "-m", "celery", "-A", "taskflow", "worker",
    "--loglevel=info", "--concurrency=1"
])

print("3. Starting Celery beat...")
beat_process = subprocess.Popen([
    sys.executable, "-m", "celery", "-A", "taskflow", "beat",
    "--loglevel=info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"
])

print("4. Starting Gunicorn web server...")
gunicorn_args = [
    "gunicorn",
    "taskflow.wsgi:application",
    "--bind",
    "0.0.0.0:8000",
    "--workers",
    "2",
    "--timeout",
    "120"
]

if os.name == 'posix':
    # Replace the current python script process with Gunicorn on Linux (PID 1)
    os.execvp("gunicorn", gunicorn_args)
else:
    # Windows fallback
    res = subprocess.run(gunicorn_args)
    sys.exit(res.returncode)
