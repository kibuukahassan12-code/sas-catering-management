"""AI Suite database models."""
from datetime import datetime, date
from models import db


class AIPredictionRun(db.Model):
    """Track AI prediction runs for audit and debugging."""
    __tablename__ = "ai_prediction_run"
    
    id = db.Column(db.Integer, primary_key=True)
    run_type = db.Column(db.String(80))  # menu, forecast, staffing, shortages, cost_opt
    model_name = db.Column(db.String(120))
    parameters = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIPredictionRun {self.run_type} at {self.created_at}>'


class MenuRecommendation(db.Model):
    """AI-generated menu recommendations."""
    __tablename__ = "menu_recommendation"
    
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, nullable=True)  # FK to menu_item
    recommendation = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float)  # Confidence score 0-1
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MenuRecommendation {self.id} score={self.score}>'


class ForecastResult(db.Model):
    """Sales/demand forecast results."""
    __tablename__ = "forecast_result"
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50))  # POS, Catering, Bakery
    date = db.Column(db.Date, nullable=False)
    predicted = db.Column(db.Numeric(14, 2), nullable=False)
    actual = db.Column(db.Numeric(14, 2), nullable=True)
    model_name = db.Column(db.String(120))
    run_id = db.Column(db.Integer, db.ForeignKey('ai_prediction_run.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    run = db.relationship('AIPredictionRun', foreign_keys=[run_id])
    
    def __repr__(self):
        return f'<ForecastResult {self.source} {self.date} pred={self.predicted}>'


class StaffingSuggestion(db.Model):
    """AI-generated staffing recommendations."""
    __tablename__ = "staffing_suggestion"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=True)  # FK to event
    date = db.Column(db.Date, nullable=False)
    suggested_staff_count = db.Column(db.Integer, nullable=False)
    roles_breakdown = db.Column(db.Text)  # JSON string: {"chef": 2, "waiter": 5, ...}
    confidence = db.Column(db.Float)  # 0-1
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StaffingSuggestion event={self.event_id} staff={self.suggested_staff_count}>'


class ShortageAlert(db.Model):
    """AI-predicted inventory shortage alerts."""
    __tablename__ = "shortage_alert"
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_item_id = db.Column(db.Integer, nullable=False)  # FK to inventory_item
    predicted_shortage_date = db.Column(db.Date, nullable=False)
    recommended_order_qty = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high
    status = db.Column(db.String(20), default='active')  # active, resolved, dismissed
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<ShortageAlert item={self.inventory_item_id} severity={self.severity}>'


class CostOptimization(db.Model):
    """AI cost optimization suggestions."""
    __tablename__ = "cost_optimization"
    
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, nullable=True)
    event_id = db.Column(db.Integer, nullable=True)
    suggestion_type = db.Column(db.String(50))  # supplier_swap, portion_tweak, substitute
    current_cost = db.Column(db.Numeric(14, 2))
    suggested_cost = db.Column(db.Numeric(14, 2))
    savings = db.Column(db.Numeric(14, 2))
    details = db.Column(db.Text)  # JSON or description
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CostOptimization {self.suggestion_type} savings={self.savings}>'

