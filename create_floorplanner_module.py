# create_floorplanner_module.py  
# Installer that builds a complete working floor planner module  
# including models, blueprint, templates, JS, and DB migration.

import os, textwrap

ROOT = os.path.abspath(os.path.dirname(__file__))

def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)

# Directories
bp_dir = os.path.join(ROOT, "blueprints", "floorplanner")
service_dir = os.path.join(ROOT, "services")
tpl_dir = os.path.join(ROOT, "templates", "floorplanner")
static_js_dir = os.path.join(ROOT, "static", "js", "floorplanner")
models_path = os.path.join(ROOT, "models.py")
fix_all_path = os.path.join(ROOT, "fix_all_tables.py")

ensure_dir(bp_dir)
ensure_dir(service_dir)
ensure_dir(tpl_dir)
ensure_dir(static_js_dir)

# Blueprint
with open(os.path.join(bp_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(textwrap.dedent("""
    from flask import Blueprint, render_template, request, jsonify, current_app
    from flask_login import login_required, current_user
    from services.floorplanner_service import create_floorplan, get_floorplan_by_event, save_floorplan_layout
    from models import Event

    bp = Blueprint("floorplanner", __name__, url_prefix="/floorplanner")

    @bp.route("/dashboard")
    @login_required
    def dashboard():
        events = Event.query.order_by(Event.event_date.desc()).all()
        return render_template("floorplanner/dashboard.html", events=events)

    @bp.route("/<int:event_id>/editor")
    @login_required
    def editor(event_id):
        event = Event.query.get_or_404(event_id)
        floorplan = get_floorplan_by_event(event_id)
        return render_template("floorplanner/editor.html", event=event, floorplan=floorplan)

    @bp.route("/<int:event_id>/create", methods=["POST"])
    @login_required
    def create(event_id):
        data = request.get_json() or {}
        fp = create_floorplan(event_id, data.get("name", f"Floor Plan - {event_id}"), current_user.id)
        return jsonify({"ok": True, "id": fp.id})

    @bp.route("/<int:floorplan_id>/save", methods=["POST"])
    @login_required
    def save(floorplan_id):
        payload = request.get_json() or {}
        save_floorplan_layout(floorplan_id, payload.get("layout", {}), current_user.id)
        return jsonify({"ok": True})
    """).strip())

# Service
with open(os.path.join(service_dir, "floorplanner_service.py"), "w", encoding="utf-8") as f:
    f.write(textwrap.dedent("""
    import json
    from datetime import datetime
    from models import db, FloorPlan

    def create_floorplan(event_id, name, created_by):
        fp = FloorPlan(event_id=event_id, name=name, json_layout="{}", created_by=created_by)
        db.session.add(fp)
        db.session.commit()
        return fp

    def get_floorplan_by_event(event_id):
        return FloorPlan.query.filter_by(event_id=event_id).first()

    def save_floorplan_layout(floorplan_id, layout_json, user_id):
        fp = FloorPlan.query.get(floorplan_id)
        fp.json_layout = json.dumps(layout_json)
        fp.updated_at = datetime.utcnow()
        db.session.commit()
        return fp
    """).strip())

# Dashboard template
with open(os.path.join(tpl_dir, "dashboard.html"), "w", encoding="utf-8") as f:
    f.write(textwrap.dedent("""
    {% extends "base.html" %}
    {% block title %}Floor Planner Dashboard{% endblock %}
    {% block content %}
    <h2>Floor Planner — Events</h2>
    <table class="table">
        <thead>
            <tr><th>Event</th><th>Date</th><th>Venue</th><th>Guests</th><th></th></tr>
        </thead>
        <tbody>
            {% for e in events %}
            <tr>
                <td>{{ e.name }}</td>
                <td>{{ e.event_date }}</td>
                <td>{{ e.venue_name or '' }}</td>
                <td>{{ e.guest_count or 0 }}</td>
                <td>
                    <a href="{{ url_for('floorplanner.editor', event_id=e.id) }}" class="btn btn-warning btn-sm">
                        Open Floor Planner
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endblock %}
    """).strip())

# Editor template
with open(os.path.join(tpl_dir, "editor.html"), "w", encoding="utf-8") as f:
    f.write(textwrap.dedent("""
    {% extends "base.html" %}
    {% block head_extras %}
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/4.6.0/fabric.min.js"></script>
    {% endblock %}
    {% block content %}
    <h2>Floor Planner: {{ event.name }}</h2>
    <div style="display:flex;gap:20px;">
        <div>
            <button id="add-table" class="btn">Add Round Table</button>
            <button id="add-rect" class="btn">Add Rect Table</button>
            <button id="add-chair" class="btn">Add Chair</button>
            <hr/>
            <button id="save-plan" class="btn btn-success">Save Plan</button>
        </div>
        <canvas id="floorcanvas" width="1200" height="700" style="border:1px solid #ccc"></canvas>
    </div>
    <script src="{{ url_for('static', filename='js/floorplanner/floorplanner.js') }}"></script>
    <script>
    initFloorPlanner({{ floorplan.json_layout|safe if floorplan else '{}' }},
                     {{ floorplan.id if floorplan else 'null' }},
                     {{ event.id }});
    </script>
    {% endblock %}
    """).strip())

# JS
with open(os.path.join(static_js_dir, "floorplanner.js"), "w", encoding="utf-8") as f:
    f.write(textwrap.dedent("""
    function initFloorPlanner(initialLayout, floorplanId, eventId) {
      const canvas = new fabric.Canvas("floorcanvas");

      if (initialLayout && Object.keys(initialLayout).length) {
        try { canvas.loadFromJSON(initialLayout, canvas.renderAll.bind(canvas)); }
        catch (e) { console.log("Could not load layout", e); }
      }

      document.getElementById("add-table").onclick = () => {
        canvas.add(new fabric.Circle({ radius:40, fill:"#f5c", left:100, top:100 }));
      };
      document.getElementById("add-rect").onclick = () => {
        canvas.add(new fabric.Rect({ width:120, height:60, fill:"#f5c", left:150, top:150 }));
      };
      document.getElementById("add-chair").onclick = () => {
        canvas.add(new fabric.Rect({ width:30, height:30, fill:"#ddd", left:200, top:200 }));
      };

      document.getElementById("save-plan").onclick = () => {
        const layout = canvas.toJSON(["type"]);
        const saveId = floorplanId;

        if (!saveId) {
          fetch(`/floorplanner/${eventId}/create`, {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({ name:`Floor Plan - ${eventId}` })
          })
          .then(r=>r.json())
          .then(res=>{
            fetch(`/floorplanner/${res.id}/save`, {
              method:"POST",
              headers:{"Content-Type":"application/json"},
              body: JSON.stringify({ layout })
            }).then(()=>location.reload());
          });
        } else {
          fetch(`/floorplanner/${saveId}/save`, {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({ layout })
          }).then(()=>location.reload());
        }
      };
    }
    """).strip())

# Append models
model_snip = """

# --- FLOOR PLANNER MODELS ---

from datetime import datetime

class FloorPlan(db.Model):
    __tablename__ = "floor_plan"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    json_layout = db.Column(db.Text, nullable=False, default="{}")
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class SeatingAssignment(db.Model):
    __tablename__ = "seating_assignment"
    id = db.Column(db.Integer, primary_key=True)
    floorplan_id = db.Column(db.Integer, db.ForeignKey("floor_plan.id"), nullable=False)
    guest_name = db.Column(db.String(120))
    table_id = db.Column(db.String(80))
    seat_number = db.Column(db.String(50))
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
"""

if "FLOOR PLANNER MODELS" not in open(models_path, encoding="utf-8").read():
    with open(models_path, "a", encoding="utf-8") as f:
        f.write("\n" + model_snip)

# DB migration
fix_snip = """

def fix_floor_plan_table(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(floor_plan)")
    cols = [x[1] for x in cur.fetchall()]
    if "json_layout" not in cols:
        cur.execute("ALTER TABLE floor_plan ADD COLUMN json_layout TEXT DEFAULT '{}'")

    cur.execute("PRAGMA table_info(seating_assignment)")
    s = [x[1] for x in cur.fetchall()]
    if "seat_number" not in s:
        cur.execute("ALTER TABLE seating_assignment ADD COLUMN seat_number TEXT")
    if "special_requests" not in s:
        cur.execute("ALTER TABLE seating_assignment ADD COLUMN special_requests TEXT")
    conn.commit()
"""

if "fix_floor_plan_table" not in open(fix_all_path, encoding="utf-8").read():
    with open(fix_all_path, "a", encoding="utf-8") as f:
        f.write("\n" + fix_snip)

print("Floor planner module created. Now run:")
print("python fix_all_tables.py")
print("python app.py")

