"""Dispatch & Logistics routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import date

from models import db, Vehicle, DispatchRun, LoadSheetItem, User, UserRole
from utils import role_required

dispatch_bp = Blueprint("dispatch", __name__, url_prefix="/dispatch")

@dispatch_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """Dispatch dashboard."""
    vehicles = Vehicle.query.all()
    today_runs = DispatchRun.query.filter_by(run_date=date.today()).all()
    return render_template("dispatch/dispatch_dashboard.html", vehicles=vehicles, runs=today_runs)

@dispatch_bp.route("/optimize", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def optimize():
    """Optimize delivery route using advanced algorithm."""
    try:
        import json
        data = request.get_json()
        deliveries = data.get('deliveries', [])
        start_location = data.get('start_location')
        vehicles = data.get('vehicles', [])
        group_by_vehicle = data.get('group_by_vehicle', False)
        
        # Import optimization service
        from services.dispatch_service import optimize_route, group_deliveries_by_vehicle
        
        if not deliveries:
            return jsonify({
                'success': False,
                'error': 'No deliveries provided'
            }), 400
        
        # If grouping by vehicle, assign deliveries first
        if group_by_vehicle and vehicles:
            vehicle_assignments = group_deliveries_by_vehicle(deliveries, vehicles)
            
            optimized_routes = {}
            for vehicle_id, vehicle_deliveries in vehicle_assignments.items():
                if vehicle_deliveries:
                    result = optimize_route(vehicle_deliveries, start_location)
                    optimized_routes[vehicle_id] = result
            
            return jsonify({
                'success': True,
                'routes_by_vehicle': optimized_routes,
                'total_vehicles': len(optimized_routes),
                'optimization_method': 'grouped_by_vehicle'
            })
        else:
            # Single route optimization
            result = optimize_route(deliveries, start_location)
            return jsonify(result)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dispatch_bp.route("/loadsheet/<int:run_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def loadsheet(run_id):
    """Generate load sheet for dispatch run."""
    run = DispatchRun.query.get_or_404(run_id)
    items = LoadSheetItem.query.filter_by(dispatch_run_id=run_id).order_by(LoadSheetItem.id).all()
    return render_template("dispatch/loadsheet.html", run=run, items=items)

@dispatch_bp.route("/vehicles")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def vehicle_list():
    """List vehicles."""
    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    return render_template("dispatch/vehicle_list.html", vehicles=vehicles)

