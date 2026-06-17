import datetime
import random
import time
import logging
from django.utils import timezone
from devices.models import Device, DeviceLog
from employees.models import Employee

logger = logging.getLogger(__name__)

# Try importing pyzk components, fallback gracefully in simulator mode if not available
try:
    from zk import ZK, const
    PYZK_AVAILABLE = True
except ImportError:
    PYZK_AVAILABLE = False
    logger.warning("pyzk package is not installed or import failed. ZKTeco physical connections will not function.")


class ZKService:
    """
    Service to handle communications with ZKTeco biometric devices.
    Supports both real physical connection via pyzk and simulated mock connection.
    """
    def __init__(self, device: Device):
        self.device = device
        self.conn = None
        self.zk = None
        self.is_connected = False

    def connect(self) -> bool:
        """Connects to the ZKTeco device (physical or simulated)"""
        if self.device.is_simulated:
            logger.info(f"Simulating connection to device: {self.device.name}")
            time.sleep(0.5)  # Simulate network latency
            self.is_connected = True
            self._log_event('CONN_SUCCESS', "Successfully connected to simulated device.")
            self.device.connection_status = 'ONLINE'
            self.device.save()
            return True

        if not PYZK_AVAILABLE:
            error_msg = "Cannot connect: pyzk package is not installed."
            logger.error(error_msg)
            self._log_event('CONN_FAILED', error_msg)
            self.device.connection_status = 'OFFLINE'
            self.device.save()
            return False

        try:
            logger.info(f"Connecting to ZKTeco device {self.device.ip_address}:{self.device.port}")
            self.zk = ZK(self.device.ip_address, port=self.device.port, timeout=8, password=self.device.password, force_udp=True)
            self.conn = self.zk.connect()
            self.is_connected = True
            self.device.connection_status = 'ONLINE'
            self.device.save()
            self._log_event('CONN_SUCCESS', "Connection established successfully.")
            return True
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.exception(error_msg)
            self.is_connected = False
            self.device.connection_status = 'OFFLINE'
            self.device.save()
            self._log_event('CONN_FAILED', error_msg)
            return False

    def disconnect(self):
        """Gracefully disconnects from the device"""
        if self.device.is_simulated:
            self.is_connected = False
            logger.info(f"Disconnected from simulated device: {self.device.name}")
            return

        if self.conn:
            try:
                self.conn.enable_device()
                self.conn.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")
            finally:
                self.conn = None
                self.is_connected = False

    def _log_event(self, event_type: str, message: str):
        """Helper to create a DeviceLog entry"""
        DeviceLog.objects.create(
            device=self.device,
            event_type=event_type,
            message=message
        )

    def get_health(self) -> dict:
        """Retrieves hardware info and stats from the device"""
        if not self.is_connected:
            raise Exception("Device is not connected.")

        if self.device.is_simulated:
            return {
                'serial_number': self.device.serial_number or "SIM-ZK-800X-987",
                'firmware_version': self.device.firmware_version or "ZK-uFace800-v3.0.1",
                'platform': "uFace800",
                'device_name': self.device.name,
                'user_count': Employee.objects.filter(bio_device_user_id__isnull=False).count() or 5,
                'log_count': random.randint(120, 450)
            }

        try:
            self.conn.disable_device()
            sn = self.conn.get_serialnumber()
            firmware = self.conn.get_firmware_version()
            platform = self.conn.get_platform()
            
            # Update device model fields
            self.device.serial_number = sn
            self.device.firmware_version = firmware
            self.device.save()

            # Retrieve counts
            users = self.conn.get_users()
            logs = self.conn.get_attendance()

            self.conn.enable_device()
            return {
                'serial_number': sn,
                'firmware_version': firmware,
                'platform': platform,
                'device_name': self.device.name,
                'user_count': len(users),
                'log_count': len(logs)
            }
        except Exception as e:
            self.conn.enable_device()
            raise Exception(f"Failed to get device info: {str(e)}")

    def get_attendance(self) -> list:
        """
        Retrieves all attendance logs from the device.
        Returns a list of dicts: [{'bio_device_user_id': str, 'timestamp': datetime, 'punch_type': str, 'verification_mode': str}]
        """
        if not self.is_connected:
            raise Exception("Device is not connected.")

        if self.device.is_simulated:
            # Generate simulated logs for all employees who have a bio_device_user_id
            simulated_logs = []
            employees = Employee.objects.filter(bio_device_user_id__isnull=False, status='ACTIVE')
            
            # Generate logs for today and yesterday to have good dashboard data
            today = timezone.localdate()
            yesterday = today - datetime.timedelta(days=1)
            
            for date in [yesterday, today]:
                for emp in employees:
                    # Decide if the employee comes today (85% probability)
                    if random.random() < 0.85:
                        # Late check-in chance (20%)
                        late_chance = random.random() < 0.20
                        if late_chance:
                            # Late: 09:15 AM to 10:30 AM
                            check_in_time = datetime.datetime.combine(
                                date, 
                                datetime.time(hour=9, minute=random.randint(16, 59), second=random.randint(0, 59))
                            )
                        else:
                            # On-time: 08:30 AM to 08:59 AM
                            check_in_time = datetime.datetime.combine(
                                date, 
                                datetime.time(hour=8, minute=random.randint(30, 59), second=random.randint(0, 59))
                            )
                        
                        # Set to timezone-aware
                        check_in_dt = timezone.make_aware(check_in_time)
                        simulated_logs.append({
                            'bio_device_user_id': emp.bio_device_user_id,
                            'timestamp': check_in_dt,
                            'punch_type': 'CHECK_IN',
                            'verification_mode': random.choice(['FACE', 'FINGER'])
                        })
                        
                        # Decide check-out (95% chance of checking out if checked in)
                        if random.random() < 0.95:
                            # Check-out time: 17:00 PM to 18:30 PM
                            check_out_time = datetime.datetime.combine(
                                date, 
                                datetime.time(hour=17, minute=random.randint(0, 59), second=random.randint(0, 59))
                            )
                            check_out_dt = timezone.make_aware(check_out_time)
                            simulated_logs.append({
                                'bio_device_user_id': emp.bio_device_user_id,
                                'timestamp': check_out_dt,
                                'punch_type': 'CHECK_OUT',
                                'verification_mode': random.choice(['FACE', 'FINGER'])
                            })
            
            # Sort by timestamp ascending
            simulated_logs.sort(key=lambda x: x['timestamp'])
            return simulated_logs

        try:
            self.conn.disable_device()
            raw_logs = self.conn.get_attendance()
            self.conn.enable_device()

            formatted_logs = []
            for log in raw_logs:
                # pyzk log punch states: 0 = CHECK_IN, 1 = CHECK_OUT (can vary based on device configuration)
                # Usually: 0/4/20 = Check-in, 1/5/21 = Check-out.
                # We can do a basic mapping
                punch = 'UNKNOWN'
                if log.status in [0, 4, 20]:
                    punch = 'CHECK_IN'
                elif log.status in [1, 5, 21]:
                    punch = 'CHECK_OUT'
                elif log.status == 2:
                    punch = 'BREAK_OUT'
                elif log.status == 3:
                    punch = 'BREAK_IN'
                
                # Verification modes: 1 = Fingerprint, 15 = Face, 4 = Card, etc.
                mode = 'FINGER'
                if log.user_id:  # Mode mappings can be added based on device spec
                    if log.punch == 1:
                        mode = 'FINGER'
                    elif log.punch == 15:
                        mode = 'FACE'
                    elif log.punch == 4:
                        mode = 'RFID'
                
                # Check timezone
                log_dt = timezone.make_aware(log.timestamp) if timezone.is_naive(log.timestamp) else log.timestamp
                
                formatted_logs.append({
                    'bio_device_user_id': str(log.user_id),
                    'timestamp': log_dt,
                    'punch_type': punch,
                    'verification_mode': mode
                })
            
            return formatted_logs
        except Exception as e:
            try:
                self.conn.enable_device()
            except Exception:
                pass
            raise Exception(f"Failed to fetch attendance logs: {str(e)}")

    def get_users(self) -> list:
        """
        Downloads all biometric users registered on the device.
        Supports physical device connections and returns mock users in simulated mode.
        """
        if not self.is_connected:
            raise Exception("Device is not connected.")

        if self.device.is_simulated:
            # Create a simple mock user container class
            class MockZKUser:
                def __init__(self, user_id, name):
                    self.user_id = user_id
                    self.name = name
                    self.privilege = 0
                    self.card_id = ''

            # Return Ten, Eleven, Twelve as sample unmapped users to test imports
            return [
                MockZKUser('10', 'Device User Ten'),
                MockZKUser('11', 'Device User Eleven'),
                MockZKUser('12', 'Device User Twelve')
            ]

        try:
            self.conn.disable_device()
            users = self.conn.get_users()
            self.conn.enable_device()
            return users
        except Exception as e:
            try:
                self.conn.enable_device()
            except Exception:
                pass
            raise Exception(f"Failed to get users from physical device: {str(e)}")

    def sync_user_information(self) -> bool:
        """
        Uploads all database employees who have a biometric device user ID to the device.
        Updates user names and cards on the device.
        """
        if not self.is_connected:
            raise Exception("Device is not connected.")

        employees = Employee.objects.filter(bio_device_user_id__isnull=False, status='ACTIVE')
        
        if self.device.is_simulated:
            logger.info(f"Simulating user sync for {employees.count()} employees.")
            time.sleep(0.3)
            self._log_event('SYNC_SUCCESS', f"Simulated user sync completed. Uploaded {employees.count()} users.")
            return True

        try:
            self.conn.disable_device()
            for emp in employees:
                # name in zk uFace800 has a limit, typically 24 chars
                fullname = f"{emp.first_name} {emp.last_name}"[:24]
                user_id = int(emp.bio_device_user_id)
                # privilege: 0 = User, 14 = Admin (Super Admin)
                privilege = 14 if emp.role == 'SUPER_ADMIN' else 0
                
                # Write to device
                self.conn.set_user(
                    uid=user_id,
                    name=fullname,
                    privilege=privilege,
                    password='',
                    card_id=emp.passport or '',
                    user_id=str(user_id)
                )
            
            self.conn.enable_device()
            self._log_event('SYNC_SUCCESS', f"User sync completed. Uploaded {employees.count()} users to device.")
            return True
        except Exception as e:
            self.conn.enable_device()
            error_msg = f"User sync failed: {str(e)}"
            logger.error(error_msg)
            self._log_event('SYNC_FAILED', error_msg)
            return False
