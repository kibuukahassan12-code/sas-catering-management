"""Route optimization for delivery."""
import math
from typing import List, Dict, Tuple
from flask import current_app


class RouteOptimizer:
    """Simple route optimizer using nearest-neighbor algorithm."""
    
    def __init__(self):
        self.mock_mode = False
    
    def optimize_route(
        self,
        start_location: Tuple[float, float],
        delivery_locations: List[Dict[str, any]],
        return_to_start: bool = True
    ) -> Dict[str, any]:
        """
        Optimize delivery route using nearest-neighbor algorithm.
        
        Args:
            start_location: (lat, lng) tuple of starting point
            delivery_locations: List of dicts with 'lat', 'lng', 'address', 'order_id'
            return_to_start: Whether to return to start location
            
        Returns:
            Dict with 'success', 'route' (ordered list), 'total_distance', 'error'
        """
        try:
            if not delivery_locations:
                return {
                    'success': True,
                    'route': [],
                    'total_distance': 0,
                    'mock': False
                }
            
            # Convert to list of tuples with metadata
            points = [
                {
                    'coords': (loc['lat'], loc['lng']),
                    'data': loc
                }
                for loc in delivery_locations
            ]
            
            # Nearest-neighbor algorithm
            route = []
            current = start_location
            remaining = points.copy()
            total_distance = 0
            
            while remaining:
                # Find nearest point
                nearest = None
                nearest_dist = float('inf')
                nearest_idx = -1
                
                for idx, point in enumerate(remaining):
                    dist = self._haversine_distance(
                        current,
                        point['coords']
                    )
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest = point
                        nearest_idx = idx
                
                if nearest:
                    route.append(nearest['data'])
                    total_distance += nearest_dist
                    current = nearest['coords']
                    remaining.pop(nearest_idx)
            
            # Return to start if requested
            if return_to_start and route:
                final_dist = self._haversine_distance(current, start_location)
                total_distance += final_dist
            
            return {
                'success': True,
                'route': route,
                'total_distance': total_distance,  # in kilometers
                'total_distance_km': round(total_distance, 2),
                'mock': False
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Route optimization error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _haversine_distance(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance between two lat/lng points using Haversine formula.
        
        Returns distance in kilometers.
        """
        R = 6371  # Earth radius in km
        
        lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
        lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def batch_optimize(
        self,
        start_location: Tuple[float, float],
        delivery_batches: List[List[Dict[str, any]]],
        max_route_distance: float = 50.0  # km
    ) -> Dict[str, any]:
        """
        Optimize multiple delivery batches.
        
        Args:
            start_location: Starting point
            delivery_batches: List of delivery location lists
            max_route_distance: Maximum distance per route
            
        Returns:
            Dict with 'success', 'routes' (list of optimized routes), 'error'
        """
        try:
            optimized_routes = []
            
            for batch in delivery_batches:
                result = self.optimize_route(start_location, batch, return_to_start=True)
                if result['success']:
                    if result['total_distance'] <= max_route_distance:
                        optimized_routes.append(result['route'])
                    else:
                        # Split batch if too long
                        mid = len(batch) // 2
                        batch1 = batch[:mid]
                        batch2 = batch[mid:]
                        
                        route1 = self.optimize_route(start_location, batch1, return_to_start=True)
                        route2 = self.optimize_route(start_location, batch2, return_to_start=True)
                        
                        if route1['success']:
                            optimized_routes.append(route1['route'])
                        if route2['success']:
                            optimized_routes.append(route2['route'])
            
            return {
                'success': True,
                'routes': optimized_routes,
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

