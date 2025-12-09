"""Tableau integration adapter."""
import os
import json
from typing import Dict, List, Optional
from flask import current_app


class TableauAdapter:
    """Tableau export adapter."""
    
    def __init__(self):
        self.server_url = os.getenv('TABLEAU_SERVER_URL', '')
        self.site_id = os.getenv('TABLEAU_SITE_ID', '')
        self.username = os.getenv('TABLEAU_USERNAME', '')
        self.password = os.getenv('TABLEAU_PASSWORD', '')
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.server_url) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Tableau adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def export_data(self, data: List[Dict], datasource_name: str) -> Dict[str, any]:
        """
        Export data to Tableau datasource.
        
        Args:
            data: List of data records
            datasource_name: Target datasource name
            
        Returns:
            Dict with 'success', 'rows_pushed', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'rows_pushed': len(data),
                'mock': True,
                'message': 'Mock Tableau export (not configured)'
            }
        
        try:
            # Tableau REST API would go here
            # Requires authentication and Hyper API for data push
            
            return {
                'success': False,
                'error': 'Tableau push requires REST API setup. See Tableau REST API docs.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_json_export(self, data: List[Dict], filename: str) -> Dict[str, any]:
        """
        Generate JSON file for Tableau import.
        
        Args:
            data: List of data records
            filename: Output filename
            
        Returns:
            Dict with 'success', 'file_path', 'error'
        """
        try:
            import tempfile
            
            if not data:
                return {'success': False, 'error': 'No data to export'}
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', prefix=filename)
            json.dump(data, temp_file, indent=2, default=str)
            temp_file.close()
            
            return {
                'success': True,
                'file_path': temp_file.name,
                'rows': len(data),
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

