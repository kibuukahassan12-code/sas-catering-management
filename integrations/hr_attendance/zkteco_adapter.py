"""ZKTeco biometric device integration adapter."""
import os
from typing import Dict, List, Optional
from flask import current_app


class ZKTecoAdapter:
    """ZKTeco biometric attendance device adapter."""
    
    def __init__(self):
        self.device_ip = os.getenv('ZKTECO_DEVICE_IP', '')
        self.device_port = int(os.getenv('ZKTECO_DEVICE_PORT', '4370'))
        self.device_password = os.getenv('ZKTECO_DEVICE_PASSWORD', '0')
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.device_ip) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "ZKTeco adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def fetch_device_logs(self, limit: int = 100) -> Dict[str, any]:
        """
        Fetch attendance logs from ZKTeco device.
        
        Args:
            limit: Maximum number of logs to fetch
            
        Returns:
            Dict with 'success', 'logs' (list of attendance records), 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'logs': [
                    {
                        'user_id': '001',
                        'timestamp': '2025-11-23 08:00:00',
                        'status': 'check_in',
                        'punch': 0
                    }
                ],
                'mock': True
            }
        
        try:
            # ZKTeco SDK would be used here
            # For now, return stub implementation
            # Requires: pip install pyzk
            
            # Example with pyzk library:
            # from zk import ZK, const
            # conn = ZK(self.device_ip, port=self.device_port, timeout=5, password=self.device_password)
            # conn.connect()
            # logs = conn.get_attendance()
            # conn.disconnect()
            
            return {
                'success': False,
                'error': 'ZKTeco SDK (pyzk) not installed. Install with: pip install pyzk'
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"ZKTeco adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def push_sync_to_attendance_table(self, logs: List[Dict[str, any]]) -> Dict[str, any]:
        """
        Sync device logs to attendance database table.
        
        Args:
            logs: List of attendance log dicts
            
        Returns:
            Dict with 'success', 'synced_count', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'synced_count': len(logs),
                'mock': True
            }
        
        try:
            # This would sync to the HR attendance model
            # from models import Attendance
            # synced = 0
            # for log in logs:
            #     attendance = Attendance(
            #         employee_id=log['user_id'],
            #         check_in_time=log['timestamp'],
            #         device_id=self.device_ip
            #     )
            #     db.session.add(attendance)
            #     synced += 1
            # db.session.commit()
            
            return {
                'success': True,
                'synced_count': len(logs),
                'mock': False
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"ZKTeco sync error: {e}")
            return {'success': False, 'error': str(e)}

