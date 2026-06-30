import subprocess
import sys
import os
import time
import signal

# Ensure outputs are flushed immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("=== STARTING TASKFLOW SERVICES ===")

processes = []

def signal_handler(sig, frame):
    print("Received termination signal. Stopping all services...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
    # Wait briefly for graceful shutdown, then force kill if still running
    time.sleep(2)
    for p in processes:
        if p.poll() is None:
            p.kill()
    sys.exit(0)

# Register termination signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

print("1. Running database migrations...")
res = subprocess.run([sys.executable, "manage.py", "migrate"])
if res.returncode != 0:
    print(f"Migration failed with exit code {res.returncode}")
    sys.exit(res.returncode)

print("2. Starting Celery worker (concurrency=1)...")
worker_process = subprocess.Popen([
    sys.executable, "-u", "-m", "celery", "-A", "taskflow", "worker",
    "--loglevel=info", "--concurrency=1"
])
processes.append(worker_process)

print("3. Starting Celery beat...")
beat_process = subprocess.Popen([
    sys.executable, "-u", "-m", "celery", "-A", "taskflow", "beat",
    "--loglevel=info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"
])
processes.append(beat_process)

print("4. Starting web server...")
if os.name == 'posix':
    web_args = [
        "gunicorn",
        "taskflow.wsgi:application",
        "--bind",
        "0.0.0.0:8000",
        "--workers",
        "2",
        "--timeout",
        "120"
    ]
else:
    web_args = [
        sys.executable,
        "manage.py",
        "runserver",
        "0.0.0.0:8000"
    ]

web_process = subprocess.Popen(web_args)
processes.append(web_process)

# Monitor all processes. If any process exits, shut down the entire container.
while True:
    for p in processes:
        status = p.poll()
        if status is not None:
            print(f"Process {p.args} exited with code {status}. Shutting down container...")
            signal_handler(None, None)
    time.sleep(5)

