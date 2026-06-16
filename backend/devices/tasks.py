from celery import shared_task
from django.utils import timezone
import logging
from devices.models import Device, DeviceLog
from devices.services.zk_service import ZKService
from employees.models import Employee
from attendance.models import AttendanceLog
from attendance.services import calculate_daily_summary

logger = logging.getLogger(__name__)

@shared_task
def sync_device_attendance(device_id: int) -> dict:
    """
    Downloads biometric logs from a specific device, inserts them,
    and updates daily attendance summaries for affected employees.
    """
    try:
        device = Device.objects.get(id=device_id, is_active=True)
    except Device.DoesNotExist:
        logger.error(f"Sync task: Device with ID {device_id} not found or inactive.")
        return {'status': 'error', 'message': f'Device {device_id} not found/inactive'}

    zk = ZKService(device)
    if not zk.connect():
        return {'status': 'error', 'message': f'Failed to connect to device {device.name}'}

    try:
        # 1. Fetch attendance logs
        logs = zk.get_attendance()
        logger.info(f"Retrieved {len(logs)} logs from device: {device.name}")

        new_logs_count = 0
        affected_pairs = set()  # set of (employee, date) to recalculate daily summary
        mismatched_ids = set()

        # 2. Save logs to database
        from attendance.models import AttendanceSummary
        for raw_log in logs:
            bio_id = raw_log['bio_device_user_id']
            try:
                # Find matching employee by biometric user ID
                employee = Employee.objects.get(bio_device_user_id=bio_id, status='ACTIVE')
            except Employee.DoesNotExist:
                mismatched_ids.add(str(bio_id))
                continue

            # Create or get raw log
            # Since we have unique_together (employee, timestamp), we use get_or_create
            log_obj, created = AttendanceLog.objects.get_or_create(
                employee=employee,
                timestamp=raw_log['timestamp'],
                defaults={
                    'device': device,
                    'punch_type': raw_log['punch_type'],
                    'verification_mode': raw_log['verification_mode']
                }
            )

            if created:
                new_logs_count += 1
            
            # Recalculate daily summary if log is new OR if summary doesn't exist yet for this date
            local_date = timezone.localtime(raw_log['timestamp']).date()
            if created or not AttendanceSummary.objects.filter(employee=employee, date=local_date).exists():
                affected_pairs.add((employee, local_date))

        # Log mismatched IDs as a warning in DeviceLog for admin visibility
        if mismatched_ids:
            warn_msg = f"Found device logs with biometric IDs {sorted(list(mismatched_ids))} that have no matching active Employee in the database."
            logger.warning(warn_msg)
            zk._log_event('WARNING', warn_msg)

        # 3. Recalculate daily summaries for affected employee/dates
        for emp, date in affected_pairs:
            calculate_daily_summary(emp, date)

        # 4. Update device state
        device.last_sync_time = timezone.now()
        device.save()
        
        success_msg = f"Biometric sync successful. Downloaded {len(logs)} logs. Inserted {new_logs_count} new punches. Updated {len(affected_pairs)} employee day records."
        zk._log_event('SYNC_SUCCESS', success_msg)
        logger.info(success_msg)
        
        return {
            'status': 'success',
            'total_logs': len(logs),
            'new_logs': new_logs_count,
            'recalculated_days': len(affected_pairs)
        }

    except Exception as e:
        error_msg = f"Error during attendance logs sync: {str(e)}"
        logger.exception(error_msg)
        zk._log_event('SYNC_FAILED', error_msg)
        return {'status': 'error', 'message': error_msg}
        
    finally:
        zk.disconnect()


@shared_task
def sync_all_active_devices() -> str:
    """
    Periodic cron task to sync all active ZKTeco devices.
    """
    devices = Device.objects.filter(is_active=True)
    results = []
    
    for dev in devices:
        # We can delay the task execution to run concurrently using celery workers
        # sync_device_attendance.delay(dev.id)
        # For simplicity and synchronous logging inside standard scheduler context, we call it directly here
        res = sync_device_attendance(dev.id)
        results.append(f"Device {dev.name}: {res['status']}")
        
    return f"Periodic device sync run finished. Results: {', '.join(results)}"


@shared_task
def check_devices_health() -> str:
    """
    Periodic task to check connections and update health parameters.
    """
    devices = Device.objects.filter(is_active=True)
    online_count = 0
    
    for dev in devices:
        zk = ZKService(dev)
        if zk.connect():
            try:
                info = zk.get_health()
                dev.serial_number = info['serial_number']
                dev.firmware_version = info['firmware_version']
                dev.connection_status = 'ONLINE'
                dev.save()
                online_count += 1
            except Exception as e:
                dev.connection_status = 'OFFLINE'
                dev.save()
                logger.error(f"Health check failed for device {dev.name}: {str(e)}")
            finally:
                zk.disconnect()
        else:
            dev.connection_status = 'OFFLINE'
            dev.save()
            
    return f"Device health checks complete. {online_count}/{devices.count()} devices ONLINE."
