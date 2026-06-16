import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')

app = Celery('hrms')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Periodic Tasks (Celery Beat Schedule)
app.conf.beat_schedule = {
    'sync-all-biometric-devices-every-minute': {
        'task': 'devices.tasks.sync_all_active_devices',
        'schedule': 60.0,  # runs every 60 seconds
    },
    'check-devices-health-every-5-minutes': {
        'task': 'devices.tasks.check_devices_health',
        'schedule': 300.0,  # runs every 5 minutes
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
