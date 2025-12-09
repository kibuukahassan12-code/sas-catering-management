"""Power BI integration adapter."""
import os
import json
from typing import Dict, List, Optional
from flask import current_app


class PowerBIAdapter:
    """Power BI export adapter."""
    
    def __init__(self):
        self.workspace_id = os.getenv('POWERBI_WORKSPACE_ID', '')
        self.dataset_id = os.getenv('POWERBI_DATASET_ID', '')
        self.client_id = os.getenv('POWERBI_CLIENT_ID', '')
        self.client_secret = os.getenv('POWERBI_CLIENT_SECRET', '')
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.workspace_id and self.dataset_id) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Power BI adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def export_data(self, data: List[Dict], table_name: str) -> Dict[str, any]:
        """
        Export data to Power BI dataset.
        
        Args:
            data: List of data records
            table_name: Target table name in Power BI
            
        Returns:
            Dict with 'success', 'rows_pushed', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'rows_pushed': len(data),
                'mock': True,
                'message': 'Mock Power BI export (not configured)'
            }
        
        try:
            # Power BI REST API push would go here
            # Requires OAuth2 authentication and Push Dataset API
            
            return {
                'success': False,
                'error': 'Power BI push requires OAuth2 setup. See Power BI REST API docs.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_csv_export(self, data: List[Dict], filename: str) -> Dict[str, any]:
        """
        Generate CSV file for Power BI import.
        
        Args:
            data: List of data records
            filename: Output filename
            
        Returns:
            Dict with 'success', 'file_path', 'error'
        """
        try:
            import csv
            import tempfile
            
            if not data:
                return {'success': False, 'error': 'No data to export'}
            
            # Get field names from first record
            fieldnames = list(data[0].keys())
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', prefix=filename)
            
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
            temp_file.close()
            
            return {
                'success': True,
                'file_path': temp_file.name,
                'rows': len(data),
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

