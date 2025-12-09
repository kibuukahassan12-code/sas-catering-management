"""Google Maps API integration adapter."""
import os
from typing import Dict, List, Optional, Tuple
from flask import current_app

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class GoogleMapsAdapter:
    """Google Maps API adapter for geocoding, directions, and distance."""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        self.base_url = 'https://maps.googleapis.com/maps/api'
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.api_key) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Google Maps adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def geocode(self, address: str) -> Dict[str, any]:
        """
        Geocode an address to coordinates.
        
        Args:
            address: Address string
            
        Returns:
            Dict with 'success', 'lat', 'lng', 'formatted_address', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'lat': 0.3476,  # Kampala coordinates
                'lng': 32.5825,
                'formatted_address': address,
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/geocode/json'
            params = {
                'address': address,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                location = result['geometry']['location']
                return {
                    'success': True,
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': result.get('formatted_address', address),
                    'place_id': result.get('place_id', ''),
                    'mock': False
                }
            else:
                return {
                    'success': False,
                    'error': f"Geocoding failed: {data.get('status', 'UNKNOWN')}"
                }
        except requests.RequestException as e:
            if current_app:
                current_app.logger.error(f"Google Maps API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Google Maps adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = 'driving'
    ) -> Dict[str, any]:
        """
        Calculate distance and duration between origins and destinations.
        
        Args:
            origins: List of origin addresses/coordinates
            destinations: List of destination addresses/coordinates
            mode: travel mode (driving, walking, bicycling, transit)
            
        Returns:
            Dict with 'success', 'rows' (distance/duration matrix), 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'rows': [
                    {
                        'elements': [
                            {
                                'distance': {'value': 5000, 'text': '5.0 km'},
                                'duration': {'value': 600, 'text': '10 mins'}
                            }
                        ]
                    }
                ],
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/distancematrix/json'
            params = {
                'origins': '|'.join(origins),
                'destinations': '|'.join(destinations),
                'mode': mode,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                return {
                    'success': True,
                    'rows': data.get('rows', []),
                    'mock': False
                }
            else:
                return {
                    'success': False,
                    'error': f"Distance matrix failed: {data.get('status', 'UNKNOWN')}"
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def directions(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None,
        mode: str = 'driving'
    ) -> Dict[str, any]:
        """
        Get turn-by-turn directions.
        
        Args:
            origin: Starting address/coordinates
            destination: Ending address/coordinates
            waypoints: Optional list of intermediate waypoints
            mode: travel mode
            
        Returns:
            Dict with 'success', 'routes', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'routes': [{
                    'summary': 'Mock route',
                    'legs': [{
                        'distance': {'value': 5000, 'text': '5.0 km'},
                        'duration': {'value': 600, 'text': '10 mins'},
                        'steps': []
                    }]
                }],
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/directions/json'
            params = {
                'origin': origin,
                'destination': destination,
                'mode': mode,
                'key': self.api_key
            }
            
            if waypoints:
                params['waypoints'] = '|'.join(waypoints)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                return {
                    'success': True,
                    'routes': data.get('routes', []),
                    'mock': False
                }
            else:
                return {
                    'success': False,
                    'error': f"Directions failed: {data.get('status', 'UNKNOWN')}"
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

