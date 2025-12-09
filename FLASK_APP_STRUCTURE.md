# Flask Application Structure & Startup Information

## Flask App Initialization Files

### 1. `create_app()` Function
**File:** `sas_management/app.py`
- **Line 44:** `def create_app():`
- This is the main Flask application factory function that creates and configures the Flask app instance

### 2. `app = Flask(__name__)`
**File:** `sas_management/app.py`
- **Line 62:** `app = Flask(__name__, instance_path=instance_path, template_folder=templates_path, static_folder=static_path)`
- Created inside the `create_app()` function

### 3. `from flask import Flask`
**File:** `sas_management/app.py`
- **Line 3:** `from flask import Flask`
- Main import statement for Flask

### 4. `app.run()`
**File:** `sas_management/app.py`
- **Line 564:** `app.run(host="127.0.0.1", port=5000, debug=False)`
- Located in the `if __name__ == "__main__":` block

**Also found in:**
- `run_backend.py` (Line 7)
- `app_launcher.py` (Lines 13, 19)

---

## Correct Startup Files

### Primary Startup File
**File:** `sas_management/app.py`
- Contains the `create_app()` factory function
- Has `app = create_app()` at line 519
- Contains `if __name__ == "__main__":` block with `app.run()` at line 533-568
- **This is the correct file to run the Flask server directly:**
  ```bash
  python sas_management/app.py
  ```

### Alternative Startup Files

1. **`run_backend.py`** (Root directory)
   - Simple wrapper that imports app and runs it
   - Usage: `python run_backend.py`

2. **`app_launcher.py`** (Root directory)
   - More complex launcher with GUI support (webview)
   - Used for desktop application packaging
   - Usage: `python app_launcher.py`

---

## All Route Files (Blueprints)

All blueprint route files are located in `sas_management/blueprints/`:

### Core Routes
1. **`routes.py`** (Main routes file)
   - Blueprint: `core_bp` (no prefix)
   - Location: `sas_management/routes.py`

### Blueprint Route Files

2. **Accounting** - `blueprints/accounting/__init__.py`
   - Blueprint: `accounting_bp`
   - URL Prefix: `/accounting`

3. **Admin** - `blueprints/admin/__init__.py`
   - Blueprint: `admin_bp`
   - URL Prefix: `/admin`
   - Additional: `admin/admin_users_assign.py`, `admin/rbac.py`

4. **Analytics** - `blueprints/analytics/__init__.py`
   - Blueprint: `analytics_bp`
   - URL Prefix: `/analytics`

5. **AI Suite** - `blueprints/ai/routes.py`
   - Blueprint: `ai_bp`
   - URL Prefix: `/ai`

6. **Audit** - `blueprints/audit/__init__.py`
   - Blueprint: `audit_bp`
   - URL Prefix: `/admin`

7. **Auth** - `blueprints/auth/__init__.py`
   - Blueprint: `auth_bp`
   - URL Prefix: `/auth`

8. **Automation** - `blueprints/automation/routes.py`
   - Blueprint: `automation_bp`
   - URL Prefix: (check registration)

9. **Bakery** - `blueprints/bakery/__init__.py`
   - Blueprint: `bakery_bp`
   - URL Prefix: `/bakery`

10. **BI** - `blueprints/bi/__init__.py`
    - Blueprint: `bi_bp`
    - URL Prefix: (check registration)

11. **Branches** - `blueprints/branches/routes.py`
    - Blueprint: `branches_bp`
    - URL Prefix: (conditional, if ENABLE_BRANCHES)

12. **Cashbook** - `blueprints/cashbook/__init__.py`
    - Blueprint: `cashbook_bp`
    - URL Prefix: `/cashbook`

13. **Catering** - `blueprints/catering/__init__.py`
    - Blueprint: `catering_bp`
    - URL Prefix: `/catering`

14. **Chat** - `blueprints/chat/__init__.py`
    - Blueprint: `chat_bp`
    - URL Prefix: (check registration)

15. **Client Portal** - `blueprints/client_portal/routes.py`
    - Blueprint: `client_portal_bp`
    - URL Prefix: (check registration)

16. **Communication** - `blueprints/communication/__init__.py`
    - Blueprint: `comm_bp`
    - URL Prefix: `/communication`

17. **Contracts** - `blueprints/contracts/__init__.py`
    - Blueprint: `contracts_bp`
    - URL Prefix: (check registration)

18. **CRM** - `blueprints/crm/__init__.py`
    - Blueprint: `crm_bp`
    - URL Prefix: `/crm`

19. **Dispatch** - `blueprints/dispatch/routes.py`
    - Blueprint: `dispatch_bp`
    - URL Prefix: (check registration)

20. **Events** - `blueprints/events/__init__.py`
    - Blueprint: `events_bp`
    - URL Prefix: `/events`

21. **Floor Plans** - `blueprints/floor_plans/__init__.py`
    - Blueprint: `floor_plans_bp`
    - URL Prefix: `/floor-plans` ✅

22. **Floor Planner** - `blueprints/floorplanner/__init__.py`
    - Blueprint: `floorplanner_bp`
    - URL Prefix: `/floorplanner`

23. **Food Safety** - `blueprints/food_safety/routes.py`
    - Blueprint: `food_safety_bp`
    - URL Prefix: `/food-safety`

24. **Hire** - `blueprints/hire/__init__.py`
    - Blueprint: `hire_bp`
    - URL Prefix: `/hire`
    - Additional: `hire/maintenance_routes.py`

25. **HR** - `blueprints/hr/__init__.py`
    - Blueprint: `hr_bp`
    - URL Prefix: `/hr`

26. **Incidents** - `blueprints/incidents/routes.py`
    - Blueprint: `incidents_bp`
    - URL Prefix: (check registration)

27. **Integrations** - `blueprints/integrations/routes.py`
    - Blueprint: `integrations_bp`
    - URL Prefix: `/integrations`

28. **Inventory** - `blueprints/inventory/__init__.py`
    - Blueprint: `inventory_bp`
    - URL Prefix: `/inventory`

29. **Invoices** - `blueprints/invoices/__init__.py`
    - Blueprint: `invoices_bp`
    - URL Prefix: `/invoices`

30. **KDS** - `blueprints/kds/routes.py`
    - Blueprint: `kds_bp`
    - URL Prefix: (check registration)

31. **Leads** - `blueprints/leads/__init__.py`
    - Blueprint: `leads_bp`
    - URL Prefix: `/leads`

32. **Menu Builder** - `blueprints/menu_builder/__init__.py`
    - Blueprint: `menu_builder_bp`
    - URL Prefix: `/menu-builder`

33. **Mobile Staff** - `blueprints/mobile_staff/routes.py`
    - Blueprint: `mobile_staff_bp`
    - URL Prefix: (check registration)

34. **Payroll** - `blueprints/payroll/__init__.py`
    - Blueprint: `payroll_bp`
    - URL Prefix: `/admin/payroll`

35. **POS** - `blueprints/pos/__init__.py`
    - Blueprint: `pos_bp`
    - URL Prefix: `/pos`

36. **Production** - `blueprints/production/__init__.py`
    - Blueprint: `production_bp`
    - URL Prefix: `/production`
    - Additional: `production/quality_control.py`

37. **Production Recipes** - `blueprints/production_recipes/__init__.py`
    - Blueprint: `recipes_bp`
    - URL Prefix: `/production/recipes`

38. **Profitability** - `blueprints/profitability/routes.py`
    - Blueprint: `profitability_bp`
    - URL Prefix: (check registration)

39. **Proposals** - `blueprints/proposals/routes.py`
    - Blueprint: `proposals_bp`
    - URL Prefix: (check registration)

40. **Quotes** - `blueprints/quotes/__init__.py`
    - Blueprint: `quotes_bp`
    - URL Prefix: `/quotes`

41. **Reports** - `blueprints/reports/__init__.py`
    - Blueprint: `reports_bp`
    - URL Prefix: `/reports`

42. **Search** - `blueprints/search/__init__.py`
    - Blueprint: `search_bp`
    - URL Prefix: (check registration)

43. **Tasks** - `blueprints/tasks/__init__.py`
    - Blueprint: `tasks_bp`
    - URL Prefix: `/tasks`

44. **Timeline** - `blueprints/timeline/routes.py`
    - Blueprint: `timeline_bp`
    - URL Prefix: `/timeline`

45. **University** - `blueprints/university/__init__.py`
    - Blueprint: `university_bp`
    - URL Prefix: `/university`

46. **Vendors** - `blueprints/vendors/routes.py`
    - Blueprint: `vendors_bp`
    - URL Prefix: `/vendors`

---

## Floor Plans Blueprint Confirmation

**File:** `sas_management/blueprints/floor_plans/__init__.py`

**Blueprint Definition:**
```python
floor_plans_bp = Blueprint("floor_plans", __name__, url_prefix="/floor-plans")
```

**Registration in app.py:**
```python
from blueprints.floor_plans import floor_plans_bp
app.register_blueprint(floor_plans_bp)
```
(Line 162-163)

**Correct URL Paths:**
- List: `/floor-plans/` or `/floor-plans/list`
- New: `/floor-plans/new`
- Edit: `/floor-plans/<id>/edit`
- Open: `/floor-plans/open/<id>`
- View: `/floor-plans/<id>`
- Save: `/floor-plans/save` (POST)
- Export PNG: `/floor-plans/export/<id>/png`
- Assign: `/floor-plans/assign/<id>` (POST)

**URL For Helper:**
```python
url_for("floor_plans.edit_floor_plan", id=floor_plan_id)
url_for("floor_plans.floorplan_open", id=floor_plan_id)
url_for("floor_plans.list")
url_for("floor_plans.new")
```

---

## Quick Start Guide

### To run the Flask server:

**Option 1: Direct (Recommended)**
```bash
cd "sas_management"
python app.py
```

**Option 2: Using run_backend.py**
```bash
python run_backend.py
```

**Option 3: Using app_launcher.py (Desktop GUI)**
```bash
python app_launcher.py
```

The server will start on: `http://127.0.0.1:5000`

