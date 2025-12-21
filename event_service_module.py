"""
Event Service Department Module Generator
Drop this script into your project root and run it (from your project's venv)

Usage (Windows PowerShell):
  python event_service_module.py

What it does:
- Creates a new Flask blueprint at sas_management/blueprints/service/
- Creates SQLAlchemy models at sas_management/service/models.py
- Creates Jinja2 templates under sas_management/templates/service/
- Adds a simple registration snippet you can paste into your app factory

IMPORTANT:
- This script assumes your project exposes `db` (SQLAlchemy instance) and `login` in sas_management.
  If `db` lives in a different module, adjust the import lines in the generated files.
- After creating files, run your existing migration workflow (flask db migrate/upgrade) OR
  allow your project's auto-fix system to sync the schema.

Files created (relative to repo root):
 - sas_management/service/models.py
 - sas_management/blueprints/service/__init__.py
 - sas_management/templates/service/dashboard.html
 - sas_management/templates/service/event_detail.html
 - sas_management/templates/service/_form_items.html
 - sas_management/templates/service/event_list.html
 - sas_management/templates/service/assign_team.html

This generator is opinionated but intentionally minimal so you can integrate with your app.
If your project structure differs, edit the TARGET_* paths below.
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent
TARGET_BASE = ROOT / "sas_management"
BLUEPRINT_DIR = TARGET_BASE / "blueprints" / "service"
MODELS_DIR = TARGET_BASE / "service"
TEMPLATES_DIR = TARGET_BASE / "templates" / "service"

for d in (BLUEPRINT_DIR, MODELS_DIR, TEMPLATES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 1) Models: sas_management/service/models.py
models_py = r"""
from datetime import datetime
from sqlalchemy.orm import relationship
from sas_management import db

class ServiceEvent(db.Model):
    __tablename__ = 'service_events'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, index=True, unique=True, nullable=False)  # FK to your main events table id
    event_name = db.Column(db.String(255), nullable=False)
    venue = db.Column(db.String(255))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='planned')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    teams = relationship('ServiceTeamAssignment', back_populates='service_event')
    item_issues = relationship('ServiceItemIssue', back_populates='service_event')
    stations = relationship('ServiceStation', back_populates='service_event')

    def __repr__(self):
        return f'<ServiceEvent {self.event_name} ({self.id})>'


class ServiceItem(db.Model):
    __tablename__ = 'service_items'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    qty_total = db.Column(db.Integer, default=0)
    qty_available = db.Column(db.Integer, default=0)
    trackable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ServiceItem {self.name} [{self.qty_available}/{self.qty_total}]>'


class ServiceItemIssue(db.Model):
    __tablename__ = 'service_item_issues'
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey('service_events.id'), nullable=False)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    issued_to = db.Column(db.String(255))
    issued_by = db.Column(db.String(255))
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    returned_qty = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='issued')  # issued, partial_returned, returned, lost, damaged

    # relations
    service_event = relationship('ServiceEvent', back_populates='item_issues')
    service_item = relationship('ServiceItem')

    def __repr__(self):
        return f'<Issue S{self.service_item_id} x{self.quantity} for event {self.service_event_id}>'


class ServiceTeamAssignment(db.Model):
    __tablename__ = 'service_team_assignments'
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey('service_events.id'), nullable=False)
    staff_id = db.Column(db.Integer, nullable=False)  # FK to your users/staff table
    role = db.Column(db.String(100))
    uniform_issued = db.Column(db.String(255))
    checked_in_at = db.Column(db.DateTime)
    checked_out_at = db.Column(db.DateTime)
    payment_due = db.Column(db.Numeric(10,2), default=0)

    service_event = relationship('ServiceEvent', back_populates='teams')

    def __repr__(self):
        return f'<Assignment staff={self.staff_id} event={self.service_event_id} role={self.role}>'


class ServiceStation(db.Model):
    __tablename__ = 'service_stations'
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey('service_events.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    supervisor_id = db.Column(db.Integer)
    opened_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)

    service_event = relationship('ServiceEvent', back_populates='stations')

    def __repr__(self):
        return f'<Station {self.name}>'


class ServiceIncident(db.Model):
    __tablename__ = 'service_incidents'
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey('service_events.id'), nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    reported_by = db.Column(db.String(255))
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='open')

    def __repr__(self):
        return f'<Incident {self.id} {self.category}>'
"""

# 2) Blueprint: sas_management/blueprints/service/__init__.py
blueprint_py = r"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from sas_management import db
from sas_management.service.models import (
    ServiceEvent, ServiceItem, ServiceItemIssue,
    ServiceTeamAssignment, ServiceStation, ServiceIncident
)
from datetime import datetime

service_bp = Blueprint('service', __name__, template_folder='../../templates/service', url_prefix='/service')

@service_bp.route('/')
def dashboard():
    # basic dashboard: show events and counts
    events = ServiceEvent.query.order_by(ServiceEvent.start_date.desc()).limit(50).all()
    items_low = ServiceItem.query.filter(ServiceItem.qty_available <= 2).all()
    return render_template('dashboard.html', events=events, low_items=items_low)

@service_bp.route('/events')
def event_list():
    q = request.args.get('q')
    if q:
        events = ServiceEvent.query.filter(ServiceEvent.event_name.ilike(f'%{q}%')).all()
    else:
        events = ServiceEvent.query.order_by(ServiceEvent.start_date.desc()).all()
    return render_template('event_list.html', events=events)

@service_bp.route('/events/<int:id>')
def event_detail(id):
    ev = ServiceEvent.query.get_or_404(id)
    items = ServiceItemIssue.query.filter_by(service_event_id=ev.id).all()
    teams = ServiceTeamAssignment.query.filter_by(service_event_id=ev.id).all()
    stations = ServiceStation.query.filter_by(service_event_id=ev.id).all()
    incidents = ServiceIncident.query.filter_by(service_event_id=ev.id).all()
    return render_template('event_detail.html', event=ev, items=items, teams=teams, stations=stations, incidents=incidents)

@service_bp.route('/events/<int:id>/assign', methods=['GET','POST'])
def assign_team(id):
    ev = ServiceEvent.query.get_or_404(id)
    if request.method == 'POST':
        staff_id = int(request.form['staff_id'])
        role = request.form.get('role')
        assignment = ServiceTeamAssignment(service_event_id=ev.id, staff_id=staff_id, role=role)
        db.session.add(assignment)
        db.session.commit()
        flash('Staff assigned', 'success')
        return redirect(url_for('service.event_detail', id=ev.id))

    # You'll want to replace staff list with your actual staff lookup
    staff_list = current_app.config.get('SERVICE_STAFF_SAMPLE', [])
    return render_template('assign_team.html', event=ev, staff_list=staff_list)

@service_bp.route('/events/<int:id>/issue_item', methods=['POST'])
def issue_item(id):
    ev = ServiceEvent.query.get_or_404(id)
    item_id = int(request.form['item_id'])
    qty = int(request.form.get('quantity', 1))
    item = ServiceItem.query.get_or_404(item_id)
    if item.qty_available < qty:
        flash('Not enough items available', 'danger')
        return redirect(url_for('service.event_detail', id=ev.id))
    item.qty_available -= qty
    issue = ServiceItemIssue(service_event_id=ev.id, service_item_id=item.id, quantity=qty, issued_to=request.form.get('issued_to'), issued_by=current_app.config.get('CURRENT_USER_NAME','system'))
    db.session.add(issue)
    db.session.commit()
    flash('Item issued', 'success')
    return redirect(url_for('service.event_detail', id=ev.id))

@service_bp.route('/events/<int:id>/return_item/<int:issue_id>', methods=['POST'])
def return_item(id, issue_id):
    ev = ServiceEvent.query.get_or_404(id)
    issue = ServiceItemIssue.query.get_or_404(issue_id)
    returned = int(request.form.get('returned_qty', 0))
    issue.returned_qty = (issue.returned_qty or 0) + returned
    if issue.returned_qty >= issue.quantity:
        issue.status = 'returned'
    else:
        issue.status = 'partial_returned'
    item = ServiceItem.query.get(issue.service_item_id)
    item.qty_available = (item.qty_available or 0) + returned
    db.session.commit()
    flash('Return recorded', 'success')
    return redirect(url_for('service.event_detail', id=ev.id))

@service_bp.route('/events/<int:id>/incident', methods=['POST'])
def add_incident(id):
    ev = ServiceEvent.query.get_or_404(id)
    cat = request.form.get('category')
    desc = request.form.get('description')
    inc = ServiceIncident(service_event_id=ev.id, category=cat, description=desc, reported_by=current_app.config.get('CURRENT_USER_NAME','system'))
    db.session.add(inc)
    db.session.commit()
    flash('Incident logged', 'warning')
    return redirect(url_for('service.event_detail', id=ev.id))

"""

# 3) Templates

dashboard_html = r"""
{% extends 'base.html' %}
{% block content %}
<h1>Service Dashboard</h1>
<h3>Upcoming / Recent Events</h3>
<ul>
  {% for ev in events %}
    <li><a href="{{ url_for('service.event_detail', id=ev.id) }}">{{ ev.event_name }}</a> — {{ ev.start_date.strftime('%b %d, %Y') if ev.start_date else 'No Date' }} — {{ ev.status }}</li>
  {% else %}
    <li>No events</li>
  {% endfor %}
</ul>

<h3>Low stock items</h3>
<ul>
  {% for it in low_items %}
    <li>{{ it.name }} — available {{ it.qty_available }}</li>
  {% else %}
    <li>All good</li>
  {% endfor %}
</ul>
{% endblock %}
"""

event_list_html = r"""
{% extends 'base.html' %}
{% block content %}
<h1>Service Events</h1>
<form method="get">
  <input type="text" name="q" placeholder="search" value="{{ request.args.get('q','') }}">
  <button type="submit">Search</button>
</form>
<ul>
  {% for ev in events %}
    <li><a href="{{ url_for('service.event_detail', id=ev.id) }}">{{ ev.event_name }}</a> — {{ ev.start_date.strftime('%b %d, %Y') if ev.start_date else 'No Date' }}</li>
  {% else %}
    <li>No events</li>
  {% endfor %}
</ul>
{% endblock %}
"""

event_detail_html = r"""
{% extends 'base.html' %}
{% block content %}
<h1>{{ event.event_name }}</h1>
<p>Venue: {{ event.venue }}</p>
<p>Dates: {{ event.start_date.strftime('%b %d, %Y') if event.start_date else 'No Date' }} — {{ event.end_date.strftime('%b %d, %Y') if event.end_date else 'No Date' }}</p>

<h3>Teams</h3>
<ul>
  {% for t in teams %}
    <li>Staff ID: {{ t.staff_id }} — Role: {{ t.role }} — Checked in: {{ t.checked_in_at if t.checked_in_at else '—' }}</li>
  {% else %}
    <li>No team assigned</li>
  {% endfor %}
</ul>

<h3>Items issued</h3>
<form method="post" action="{{ url_for('service.issue_item', id=event.id) }}">
  {% include '_form_items.html' %}
</form>
<ul>
  {% for it in items %}
    <li>{{ it.service_item.name }} x{{ it.quantity }} — returned: {{ it.returned_qty }} — status: {{ it.status }}
      <form method="post" action="{{ url_for('service.return_item', id=event.id, issue_id=it.id) }}" style="display:inline">
        <input type="number" name="returned_qty" min="0" max="{{ it.quantity }}" value="0">
        <button type="submit">Return</button>
      </form>
    </li>
  {% else %}
    <li>No items issued</li>
  {% endfor %}
</ul>

<h3>Stations</h3>
<ul>
  {% for s in stations %}
    <li>{{ s.name }} — Supervisor: {{ s.supervisor_id if s.supervisor_id else '—' }}</li>
  {% else %}
    <li>No stations configured</li>
  {% endfor %}
</ul>

<h3>Incidents</h3>
<ul>
  {% for inc in incidents %}
    <li>[{{ inc.status }}] {{ inc.category }} — {{ inc.description }} — by {{ inc.reported_by }} at {{ inc.reported_at }}</li>
  {% else %}
    <li>No incidents</li>
  {% endfor %}
</ul>

<p><a href="{{ url_for('service.assign_team', id=event.id) }}">Assign staff</a></p>

<h3>Log an incident</h3>
<form method="post" action="{{ url_for('service.add_incident', id=event.id) }}">
  <input name="category" placeholder="Category">
  <textarea name="description" placeholder="Describe the incident"></textarea>
  <button type="submit">Log</button>
</form>

{% endblock %}
"""

form_items_html = r"""
<label for="item_id">Item</label>
<select name="item_id" id="item_id">
  {% for it in current_app.extensions['db'].session.query(ServiceItem).order_by(ServiceItem.name).all() %}
    <option value="{{ it.id }}">{{ it.name }} (available: {{ it.qty_available }})</option>
  {% endfor %}
</select>
<label for="quantity">Quantity</label>
<input name="quantity" type="number" min="1" value="1">
<label for="issued_to">Issued to (staff/station)</label>
<input name="issued_to" type="text">
<button type="submit">Issue</button>
"""

assign_team_html = r"""
{% extends 'base.html' %}
{% block content %}
<h1>Assign Staff to {{ event.event_name }}</h1>
<form method="post">
  <label for="staff_id">Staff</label>
  <select name="staff_id">
    {% for s in staff_list %}
      <option value="{{ s.id }}">{{ s.name }}</option>
    {% endfor %}
  </select>
  <label for="role">Role</label>
  <input name="role" placeholder="e.g., Waiter">
  <button type="submit">Assign</button>
</form>
{% endblock %}
"""

# Write files
(MODELS_DIR / 'models.py').write_text(models_py)
(BLUEPRINT_DIR / '__init__.py').write_text(blueprint_py)
(TEMPLATES_DIR / 'dashboard.html').write_text(dashboard_html)
(TEMPLATES_DIR / 'event_list.html').write_text(event_list_html)
(TEMPLATES_DIR / 'event_detail.html').write_text(event_detail_html)
(TEMPLATES_DIR / '_form_items.html').write_text(form_items_html)
(TEMPLATES_DIR / 'assign_team.html').write_text(assign_team_html)

print('Event Service module files created successfully.')
print('Files created under sas_management/service, sas_management/blueprints/service, sas_management/templates/service')
print('\nNext steps:')
print('1) Import and register the blueprint in your app factory:')
print("   from sas_management.blueprints.service import service_bp\n   app.register_blueprint(service_bp)")
print('2) Run migrations (flask db migrate, flask db upgrade) or rely on your auto-fix schema.')
print('3) Add at least one ServiceItem and ServiceEvent via the shell or admin to test the views.')

