from sas_management.models import db
from datetime import datetime

class Service(db.Model):
    __tablename__ = "es_service"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10,2), nullable=False, default=0)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    items = db.relationship("ServiceItem", backref="service", cascade="all, delete-orphan", lazy="dynamic")
    tasks = db.relationship("ServiceTask", backref="service", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": float(self.price) if self.price else 0.0,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ServiceItem(db.Model):
    __tablename__ = "es_service_item"
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("es_service.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10,2), nullable=False, default=0)

    def total(self):
        return float(self.quantity) * float(self.unit_price)

class ServiceTask(db.Model):
    __tablename__ = "es_service_task"
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("es_service.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_to = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    due_date = db.Column(db.DateTime, nullable=True)

