"""Dispatch and logistics service functions."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    # Radius of the Earth in kilometers
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def optimize_route(deliveries: List[Dict[str, Any]], start_location: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Optimize delivery route using nearest neighbor algorithm with priority consideration.
    
    Args:
        deliveries: List of delivery dictionaries with:
            - id: Delivery ID
            - address: Delivery address
            - latitude: Latitude coordinate
            - longitude: Longitude coordinate
            - priority: Priority level (higher = more important)
            - estimated_time: Estimated delivery time in minutes
            - weight: Weight/capacity required
        start_location: Starting location dict with 'latitude' and 'longitude'
    
    Returns:
        Dictionary with optimized route and statistics
    """
    if not deliveries:
        return {
            'success': True,
            'route': [],
            'total_distance': 0,
            'total_time': 0,
            'optimization_method': 'none'
        }
    
    # Default start location (Kampala, Uganda - approximate SAS location)
    if not start_location:
        start_location = {'latitude': 0.3476, 'longitude': 32.5825}
    
    # Filter deliveries with valid coordinates
    valid_deliveries = [
        d for d in deliveries
        if d.get('latitude') is not None and d.get('longitude') is not None
    ]
    
    if not valid_deliveries:
        # If no coordinates, sort by priority and return
        sorted_deliveries = sorted(deliveries, key=lambda x: x.get('priority', 0), reverse=True)
        return {
            'success': True,
            'route': sorted_deliveries,
            'total_distance': 0,
            'total_time': sum(d.get('estimated_time', 0) for d in sorted_deliveries),
            'optimization_method': 'priority_only',
            'message': 'No coordinates provided, sorted by priority only'
        }
    
    # Nearest Neighbor Algorithm with Priority Weighting
    optimized_route = []
    remaining_deliveries = valid_deliveries.copy()
    current_location = start_location
    total_distance = 0.0
    total_time = 0
    
    while remaining_deliveries:
        best_delivery = None
        best_score = float('inf')
        
        for delivery in remaining_deliveries:
            # Calculate distance
            distance = calculate_distance(
                current_location['latitude'],
                current_location['longitude'],
                delivery['latitude'],
                delivery['longitude']
            )
            
            # Calculate priority-adjusted score
            # Lower score = better (closer + higher priority)
            priority = delivery.get('priority', 0)
            priority_multiplier = max(0.1, 1.0 - (priority / 10.0))  # Higher priority = lower multiplier
            
            # Score combines distance and priority
            score = distance * priority_multiplier
            
            if score < best_score:
                best_score = score
                best_delivery = delivery
        
        if best_delivery:
            # Add to route
            distance = calculate_distance(
                current_location['latitude'],
                current_location['longitude'],
                best_delivery['latitude'],
                best_delivery['longitude']
            )
            
            optimized_route.append({
                **best_delivery,
                'distance_from_previous': round(distance, 2),
                'cumulative_distance': round(total_distance + distance, 2)
            })
            
            total_distance += distance
            total_time += best_delivery.get('estimated_time', 15)  # Default 15 minutes per stop
            
            # Update current location
            current_location = {
                'latitude': best_delivery['latitude'],
                'longitude': best_delivery['longitude']
            }
            
            # Remove from remaining
            remaining_deliveries.remove(best_delivery)
    
    # Calculate return distance to start
    if optimized_route:
        last_delivery = optimized_route[-1]
        return_distance = calculate_distance(
            last_delivery['latitude'],
            last_delivery['longitude'],
            start_location['latitude'],
            start_location['longitude']
        )
        total_distance += return_distance
    
    return {
        'success': True,
        'route': optimized_route,
        'total_distance': round(total_distance, 2),
        'total_time': total_time,
        'total_stops': len(optimized_route),
        'return_distance': round(return_distance, 2) if optimized_route else 0,
        'optimization_method': 'nearest_neighbor_with_priority',
        'start_location': start_location
    }


def group_deliveries_by_vehicle(deliveries: List[Dict[str, Any]], vehicles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group deliveries by vehicle based on capacity and location.
    
    Args:
        deliveries: List of delivery dictionaries
        vehicles: List of vehicle dictionaries with 'capacity' and 'id'
    
    Returns:
        Dictionary mapping vehicle_id to list of deliveries
    """
    vehicle_assignments = {v['id']: [] for v in vehicles}
    vehicle_capacity_used = {v['id']: 0 for v in vehicles}
    
    # Sort deliveries by priority (highest first)
    sorted_deliveries = sorted(deliveries, key=lambda x: x.get('priority', 0), reverse=True)
    
    for delivery in sorted_deliveries:
        delivery_weight = delivery.get('weight', 0)
        
        # Find best vehicle (has capacity and is closest)
        best_vehicle_id = None
        best_score = float('inf')
        
        for vehicle in vehicles:
            vehicle_id = vehicle['id']
            capacity = vehicle.get('capacity', 0)
            current_used = vehicle_capacity_used[vehicle_id]
            
            # Check if vehicle has capacity
            if current_used + delivery_weight <= capacity:
                # Score based on current load (prefer less loaded vehicles)
                load_factor = current_used / capacity if capacity > 0 else 0
                score = load_factor
                
                if score < best_score:
                    best_score = score
                    best_vehicle_id = vehicle_id
        
        if best_vehicle_id:
            vehicle_assignments[best_vehicle_id].append(delivery)
            vehicle_capacity_used[best_vehicle_id] += delivery_weight
    
    return vehicle_assignments


def estimate_delivery_time(distance_km: float, traffic_factor: float = 1.2) -> int:
    """
    Estimate delivery time in minutes based on distance.
    
    Args:
        distance_km: Distance in kilometers
        traffic_factor: Traffic multiplier (default 1.2 for 20% traffic delay)
    
    Returns:
        Estimated time in minutes
    """
    # Average speed: 40 km/h in urban areas
    base_speed_kmh = 40
    base_time_hours = distance_km / base_speed_kmh
    adjusted_time_hours = base_time_hours * traffic_factor
    
    # Add 10 minutes per stop for loading/unloading
    stop_time_minutes = 10
    
    total_minutes = int((adjusted_time_hours * 60) + stop_time_minutes)
    return max(5, total_minutes)  # Minimum 5 minutes
