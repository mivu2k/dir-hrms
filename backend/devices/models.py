from django.db import models

class Device(models.Model):
    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('UNKNOWN', 'Unknown'),
    ]

    name = models.CharField(max_length=150)
    ip_address = models.CharField(max_length=50)
    port = models.IntegerField(default=4370)
    password = models.IntegerField(default=0, help_text="Biometric device communication password (Comkey), default is 0.")
    location = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_simulated = models.BooleanField(default=True, help_text="If enabled, connection and downloads will be simulated.")
    
    connection_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNKNOWN')
    last_sync_time = models.DateTimeField(null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    firmware_version = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port}) {'[SIMULATED]' if self.is_simulated else ''}"


class DeviceLog(models.Model):
    EVENT_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CONN_SUCCESS', 'Connection Successful'),
        ('CONN_FAILED', 'Connection Failed'),
        ('SYNC_SUCCESS', 'Sync Successful'),
        ('SYNC_FAILED', 'Sync Failed'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES, default='INFO')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.event_type}] {self.device.name} at {self.timestamp}"
