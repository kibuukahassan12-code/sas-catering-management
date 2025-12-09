# SAS Management System - Complete Project Analysis

## === MODULES / BLUEPRINTS ===

### core
- **path**: `sas_management/routes.py`
- **prefix**: `/` (no prefix)
- **endpoints**:
  - `core.offline` → `/offline`
  - `core.pwa_test` → `/pwa-test`
  - `core.login` → `/`
  - `core.force_change_password` → `/force-change-password`
  - `core.dashboard` → `/dashboard`
  - `core.api_dashboard_upcoming_events` → `/api/dashboard/events/upcoming`
  - `core.api_dashboard_pipeline` → `/api/dashboard/pipeline`
  - `core.api_dashboard_pending_invoices` → `/api/dashboard/invoices/pending`
  - `core.api_dashboard_staff_availability` → `/api/dashboard/staff/availability`
  - `core.api_dashboard_low_stock` → `/api/dashboard/inventory/low-stock`
  - `core.api_dashboard_revenue_stats` → `/api/dashboard/revenue/stats`
  - `core.access_denied` → `/access_denied`
  - `core.logout` → `/logout`
  - `core.clients_list` → `/clients`
  - `core.clients_add` → `/clients/add`
  - `core.clients_edit` → `/clients/edit/<int:client_id>`
  - `core.clients_delete` → `/clients/delete/<int:client_id>`
  - `core.events_list` → `/events`
  - `core.events_add` → `/events/add`
  - `core.events_edit` → `/events/edit/<int:event_id>`
  - `core.events_delete` → `/events/delete/<int:event_id>`
  - `core.api_new_lead` → `/api/new_lead`
  - Multiple POS proxy routes (`/api/pos/*`)

### hire
- **path**: `sas_management/hire/__init__.py` + `sas_management/hire/routes.py`
- **prefix**: `/hire`
- **endpoints**:
  - `hire.index` → `/hire/`
  - `hire.orders_list` → `/hire/orders`

### maintenance (Equipment Maintenance)
- **path**: `sas_management/blueprints/hire/maintenance_routes.py`
- **prefix**: `/hire/maintenance`
- **endpoints**:
  - `maintenance.dashboard` → `/hire/maintenance/`
  - `maintenance.schedule` → `/hire/maintenance/schedule`
  - `maintenance.update_status` → `/hire/maintenance/update-status/<int:maintenance_id>`
  - `maintenance.maintenance_list` → `/hire/maintenance/list`
  - `maintenance.condition_report` → `/hire/maintenance/condition-report`
  - `maintenance.depreciation` → `/hire/maintenance/depreciation/<int:item_id>`
  - `maintenance.view_maintenance` → `/hire/maintenance/view/<int:maintenance_id>`

### catering
- **path**: `sas_management/blueprints/catering/__init__.py`
- **prefix**: `/catering`
- **endpoints**:
  - `catering.menu_list` → `/catering/`
  - Additional routes (check file for complete list)

### bakery
- **path**: `sas_management/blueprints/bakery/__init__.py`
- **prefix**: `/bakery`
- **endpoints**:
  - `bakery.dashboard` → `/bakery/dashboard`
  - `bakery.items_list` → `/bakery/items`
  - `bakery.orders_list` → `/bakery/orders`
  - `bakery.production_sheet` → `/bakery/production-sheet`
  - `bakery.reports` → `/bakery/reports`
  - Additional routes (check file for complete list)

### cashbook
- **path**: `sas_management/blueprints/cashbook/__init__.py`
- **prefix**: `/cashbook`
- **endpoints**:
  - `cashbook.index` → `/cashbook/`
  - Additional routes (check file for complete list)

### quotes
- **path**: `sas_management/blueprints/quotes/__init__.py`
- **prefix**: `/quotes`
- **endpoints**:
  - `quotes.dashboard` → `/quotes/` or `/quotes`
  - `quotes.new` → `/quotes/new`
  - `quotes.view` → `/quotes/view/<int:quotation_id>`
  - `quotes.convert` → `/quotes/convert/<int:quotation_id>`

### university
- **path**: `sas_management/blueprints/university/__init__.py`
- **prefix**: `/university`
- **endpoints**:
  - `university.dashboard` → `/university/` or `/university/dashboard`
  - `university.course` → `/university/course/<int:course_id>`
  - `university.material` → `/university/material/<int:material_id>`
  - `university.material_download` → `/university/material/<int:material_id>/download`
  - `university.admin_courses` → `/university/admin/courses`
  - `university.admin_courses_add` → `/university/admin/courses/add`

### chat
- **path**: `sas_management/blueprints/chat/__init__.py`
- **prefix**: `/chat`
- **endpoints**: (check file for complete list)

### leads
- **path**: `sas_management/blueprints/leads/__init__.py`
- **prefix**: `/leads`
- **endpoints**: (check file for complete list)

### inventory
- **path**: `sas_management/blueprints/inventory/__init__.py`
- **prefix**: `/inventory`
- **endpoints**:
  - `inventory.ingredients_list` → `/inventory/ingredients`
  - `inventory.ingredients_add` → `/inventory/ingredients/add`
  - `inventory.ingredients_edit` → `/inventory/ingredients/edit/<int:ingredient_id>`
  - `inventory.ingredients_delete` → `/inventory/ingredients/delete/<int:ingredient_id>`

### invoices
- **path**: `sas_management/blueprints/invoices/__init__.py`
- **prefix**: `/invoices`
- **endpoints**:
  - `invoices.invoice_list` → `/invoices/`
  - Additional routes (check file for complete list)

### payroll
- **path**: `sas_management/blueprints/payroll/__init__.py`
- **prefix**: `/admin/payroll`
- **endpoints**:
  - `payroll.payroll_list` → `/admin/payroll/`
  - Additional routes (check file for complete list)

### reports
- **path**: `sas_management/blueprints/reports/__init__.py`
- **prefix**: `/reports`
- **endpoints**:
  - `reports.reports_index` → `/reports/`
  - Additional routes (check file for complete list)

### tasks
- **path**: `sas_management/blueprints/tasks/__init__.py`
- **prefix**: `/tasks`
- **endpoints**:
  - `tasks.task_list` → `/tasks/`
  - Additional routes (check file for complete list)

### audit
- **path**: `sas_management/blueprints/audit/__init__.py`
- **prefix**: `/admin`
- **endpoints**: (check file for complete list)

### crm
- **path**: `sas_management/blueprints/crm/__init__.py`
- **prefix**: `/crm`
- **endpoints**:
  - `crm.pipeline` → `/crm/pipeline`
  - `crm.pipeline_seed` → `/crm/pipeline/seed`
  - `crm.clients_view` → `/crm/clients/<int:client_id>`
  - `crm.clients_notes` → `/crm/clients/<int:client_id>/notes`
  - `crm.clients_documents` → `/crm/clients/<int:client_id>/documents`
  - `crm.clients_tags` → `/crm/clients/<int:client_id>/tags`
  - `crm.clients_communication` → `/crm/clients/<int:client_id>/communication`
  - `crm.clients_archive` → `/crm/clients/<int:client_id>/archive`
  - `crm.leads_convert` → `/crm/leads/<int:lead_id>/convert`
  - API routes for pipeline updates

### events
- **path**: `sas_management/blueprints/events/__init__.py`
- **prefix**: `/events`
- **endpoints**:
  - `events.events_list` → `/events/` or `/events/list`
  - `events.event_view` → `/events/<int:event_id>`
  - `events.event_create` → `/events/create`
  - `events.event_edit` → `/events/<int:event_id>/edit`
  - `events.event_delete` → `/events/<int:event_id>/delete`
  - `events.update_status` → `/events/<int:event_id>/update-status`
  - `events.timeline` → `/events/<int:event_id>/timeline`
  - `events.staffing` → `/events/<int:event_id>/staffing`
  - `events.costing` → `/events/<int:event_id>/costing`
  - `events.logistics` → `/events/<int:event_id>/logistics`
  - `events.checklist` → `/events/<int:event_id>/checklist`
  - `events.vendors` → `/events/<int:event_id>/vendors`
  - `events.approval` → `/events/<int:event_id>/approval`
  - `events.brief_pdf` → `/events/<int:event_id>/brief-pdf`
  - `events.venues_list` → `/events/venues`
  - `events.venues_create` → `/events/venues/create`
  - `events.menu_packages_list` → `/events/menu-packages`
  - `events.menu_packages_create` → `/events/menu-packages/create`
  - `events.vendors_manage` → `/events/vendors/manage`

### production
- **path**: `sas_management/blueprints/production/__init__.py`
- **prefix**: `/production`
- **endpoints**:
  - `production.index` → `/production/`
  - `production.kitchen_checklist_list` → `/production/kitchen-checklist`
  - `production.delivery_qc_list` → `/production/delivery-qc`
  - `production.food_safety_list` → `/production/food-safety`
  - `production.hygiene_reports_list` → `/production/hygiene-reports`
  - Additional routes (check file for complete list)

### pos
- **path**: `sas_management/blueprints/pos/__init__.py`
- **prefix**: `/pos`
- **endpoints**:
  - `pos.index` → `/pos/`
  - `pos.dashboard` → `/pos/dashboard`
  - `pos.launcher` → `/pos/launcher`
  - `pos.terminal` → `/pos/terminal/<device_code>`
  - `pos.products` → `/pos/products`
  - Multiple API routes (`/api/devices`, `/api/shifts`, `/api/orders`, `/api/products`, etc.)

### accounting
- **path**: `sas_management/blueprints/accounting/__init__.py`
- **prefix**: `/accounting`
- **endpoints**:
  - `accounting.dashboard` → `/accounting/dashboard`
  - `accounting.journal` → `/accounting/journal`
  - `accounting.receipts_list` → `/accounting/receipts`
  - `accounting.receipt_view` → `/accounting/receipts/<int:receipt_id>/view`
  - `accounting.receipt_new` → `/accounting/receipts/new`
  - `accounting.receipt_print` → `/accounting/receipts/<int:receipt_id>/print`
  - Multiple API routes (`/api/accounts`, `/api/invoices`, `/api/payments`, `/api/receipts`, `/api/journal-entries`, `/api/trial-balance`)

### hr
- **path**: `sas_management/blueprints/hr/__init__.py`
- **prefix**: `/hr`
- **endpoints**:
  - `hr.dashboard` → `/hr/dashboard`
  - `hr.employee_list` → `/hr/employees`
  - `hr.roster_builder` → `/hr/roster`
  - `hr.leave_queue` → `/hr/leave`
  - `hr.attendance_review` → `/hr/attendance`
  - `hr.payroll_export` → `/hr/payroll`
  - Additional routes (check file for complete list)

### floorplanner
- **path**: `sas_management/blueprints/floorplanner/__init__.py`
- **prefix**: `/floorplanner`
- **endpoints**:
  - `floorplanner.dashboard` → `/floorplanner/dashboard`
  - `floorplanner.new` → `/floorplanner/new/<int:event_id>`
  - `floorplanner.create` → `/floorplanner/create/<int:event_id>`
  - `floorplanner.editor` → `/floorplanner/<int:id>/editor`
  - `floorplanner.save` → `/floorplanner/<int:id>/save`
  - `floorplanner.delete` → `/floorplanner/<int:id>/delete`
  - `floorplanner.export_png` → `/floorplanner/<int:id>/export/png`
  - `floorplanner.export_pdf` → `/floorplanner/<int:id>/export/pdf`

### floor_plans
- **path**: `sas_management/blueprints/floor_plans/__init__.py`
- **prefix**: `/` (root)
- **endpoints**:
  - `floor_plans_bp.floorplan_list` → `/floor-plans/` or `/floor-plans/list`
  - `floor_plans_bp.floorplan_new` → `/floor-plans/new`
  - `floor_plans_bp.floorplan_view` → `/floor-plans/<int:id>`
  - `floor_plans_bp.edit_floor_plan` → `/floor-plans/<int:id>/edit`
  - `floor_plans_bp.floorplan_open` → `/floor-plans/open/<int:id>`
  - Additional routes (check file for complete list)

### production_recipes
- **path**: `sas_management/blueprints/production_recipes/__init__.py`
- **prefix**: `/production/recipes`
- **endpoints**: (check file for complete list)

### search
- **path**: `sas_management/blueprints/search/__init__.py`
- **prefix**: `/search`
- **endpoints**:
  - `search.search` → `/search/`
  - Additional API routes (check file for complete list)

### analytics
- **path**: `sas_management/blueprints/analytics/__init__.py`
- **prefix**: `/analytics`
- **endpoints**: (check file for complete list)

### admin
- **path**: `sas_management/blueprints/admin/__init__.py`
- **prefix**: `/admin`
- **endpoints**:
  - `admin.dashboard` → `/admin/` or `/admin/dashboard`
  - `admin.roles_list` → `/admin/roles`
  - `admin.roles_create` → `/admin/roles/create`
  - `admin.permissions` → `/admin/permissions`
  - `admin.users_list` → `/admin/users`
  - `admin.users_add` → `/admin/users/add`
  - Additional routes (check file for complete list)

### admin_users
- **path**: `sas_management/blueprints/admin/admin_users_assign.py`
- **prefix**: `/admin`
- **endpoints**:
  - `admin_users.users_assign` → `/admin/users/assign-role` (or similar)

### rbac
- **path**: `sas_management/blueprints/admin/rbac.py`
- **prefix**: `/admin/rbac`
- **endpoints**:
  - `rbac.roles` → `/admin/rbac/roles`
  - `rbac.role_permissions` → `/admin/rbac/roles/<int:role_id>/permissions`
  - `rbac.permissions` → `/admin/rbac/permissions`
  - `rbac.users_roles` → `/admin/rbac/users/roles`
  - `rbac.logs` → `/admin/rbac/logs`

### auth
- **path**: `sas_management/blueprints/auth/__init__.py`
- **prefix**: `/auth`
- **endpoints**:
  - `auth.change_password` → `/auth/change-password`
  - Additional routes (check file for complete list)

### bi
- **path**: `sas_management/blueprints/bi/__init__.py`
- **prefix**: `/bi`
- **endpoints**: (check file for complete list)

### profitability
- **path**: `sas_management/blueprints/profitability/__init__.py`
- **prefix**: (check file)
- **endpoints**: (check file for complete list)

### communication
- **path**: `sas_management/blueprints/communication/__init__.py`
- **prefix**: `/communication`
- **endpoints**:
  - `communication.announcements_list` → `/communication/announcements`
  - `communication.announcement_view` → `/communication/announcements/<int:announcement_id>`
  - Additional routes (check file for complete list)

### menu_builder
- **path**: `sas_management/blueprints/menu_builder/__init__.py`
- **prefix**: `/menu-builder`
- **endpoints**:
  - `menu_builder.dashboard` → `/menu-builder/`
  - Additional routes (check file for complete list)

### contracts
- **path**: `sas_management/blueprints/contracts/__init__.py`
- **prefix**: `/contracts`
- **endpoints**: (check file for complete list)

### integrations
- **path**: `sas_management/blueprints/integrations/routes.py`
- **prefix**: `/integrations`
- **endpoints**: (check file for complete list)

### ai
- **path**: `sas_management/blueprints/ai/routes.py`
- **prefix**: `/ai`
- **endpoints**: (check file for complete list)

### client_portal
- **path**: `sas_management/blueprints/client_portal/routes.py`
- **prefix**: `/client`
- **endpoints**: (check file for complete list)

### proposals
- **path**: `sas_management/blueprints/proposals/routes.py`
- **prefix**: `/proposals`
- **endpoints**: (check file for complete list)

### dispatch
- **path**: `sas_management/blueprints/dispatch/routes.py`
- **prefix**: `/dispatch`
- **endpoints**: (check file for complete list)

### kds
- **path**: `sas_management/blueprints/kds/routes.py`
- **prefix**: `/kds`
- **endpoints**: (check file for complete list)

### mobile_staff
- **path**: `sas_management/blueprints/mobile_staff/routes.py`
- **prefix**: `/mobile`
- **endpoints**: (check file for complete list)

### timeline
- **path**: `sas_management/blueprints/timeline/routes.py`
- **prefix**: `/timeline`
- **endpoints**: (check file for complete list)

### incidents
- **path**: `sas_management/blueprints/incidents/routes.py`
- **prefix**: `/incidents`
- **endpoints**: (check file for complete list)

### automation
- **path**: `sas_management/blueprints/automation/routes.py`
- **prefix**: `/automation`
- **endpoints**: (check file for complete list)

### vendors
- **path**: `sas_management/blueprints/vendors/routes.py`
- **prefix**: `/vendors`
- **endpoints**:
  - `vendors.dashboard` → `/vendors/`
  - `vendors.purchase_orders` → `/vendors/purchase-orders`
  - `vendors.create_po` → `/vendors/create-po`
  - Additional routes (check file for complete list)

### food_safety
- **path**: `sas_management/blueprints/food_safety/routes.py`
- **prefix**: `/food-safety`
- **endpoints**:
  - `food_safety.dashboard` → `/food-safety/dashboard`
  - `food_safety.temperature_log` → `/food-safety/temperature/log`
  - `food_safety.reports` → `/food-safety/reports`

### branches
- **path**: `sas_management/blueprints/branches/routes.py`
- **prefix**: `/branches`
- **endpoints**: (check file for complete list)
- **Note**: Only registered if `ENABLE_BRANCHES` config is True

---

## === DASHBOARD NAVIGATION ===

### Navigation Items from routes.py (dashboard view)

#### Main Modules:
- **Display Name**: Dashboard
  - **endpoint**: `core.dashboard`
  - **resolved route**: `/dashboard`
  - **status**: ✅ OK

- **Display Name**: Clients CRM
  - **endpoint**: `core.clients_list`
  - **resolved route**: `/clients`
  - **status**: ✅ OK

#### Events Module (with children):
- **Display Name**: Events
  - **endpoint**: `events.events_list`
  - **resolved route**: `/events/`
  - **status**: ✅ OK
  - **Children**:
    - **All Events**: `events.events_list` → `/events/` ✅ OK
    - **Create Event**: `events.event_create` → `/events/create` ✅ OK
    - **Venues**: `events.venues_list` → `/events/venues` ✅ OK
    - **Menu Packages**: `events.menu_packages_list` → `/events/menu-packages` ✅ OK
    - **Vendors**: `events.vendors_manage` → `/events/vendors/manage` ✅ OK
    - **Floor Planner**: `floorplanner.dashboard` → `/floorplanner/dashboard` ✅ OK
    - **Tasks**: `tasks.task_list` → `/tasks/` ✅ OK

#### Hire Department Module (with children):
- **Display Name**: Hire Department
  - **endpoint**: `hire.index`
  - **resolved route**: `/hire/`
  - **status**: ✅ OK (FIXED - now exists)
  - **Children**:
    - **Hire Overview**: `hire.index` → `/hire/` ✅ OK (FIXED)
    - **Hire Inventory**: `hire.inventory_list` → `/hire/inventory` ❌ **MISSING**
    - **Hire Orders**: `hire.orders_list` → `/hire/orders` ✅ OK (FIXED)
    - **Equipment Maintenance**: `maintenance.dashboard` → `/hire/maintenance/` ✅ OK

#### Production Department Module (with children):
- **Display Name**: Production Department
  - **endpoint**: `production.index`
  - **resolved route**: `/production/`
  - **status**: ✅ OK
  - **Children**:
    - **Production Overview**: `production.index` → `/production/` ✅ OK
    - **Menu Builder**: `menu_builder.dashboard` → `/menu-builder/` ✅ OK
    - **Catering Menu**: `catering.menu_list` → `/catering/` ✅ OK
    - **Ingredient Inventory**: `inventory.ingredients_list` → `/inventory/ingredients` ✅ OK
    - **Kitchen Checklist**: `production.kitchen_checklist_list` → `/production/kitchen-checklist` ✅ OK
    - **Delivery QC Checklist**: `production.delivery_qc_list` → `/production/delivery-qc` ✅ OK
    - **Food Safety Logs**: `production.food_safety_list` → `/production/food-safety` ✅ OK
    - **Hygiene Reports**: `production.hygiene_reports_list` → `/production/hygiene-reports` ✅ OK

#### Accounting Department Module (with children):
- **Display Name**: Accounting Department
  - **endpoint**: `accounting.dashboard`
  - **resolved route**: `/accounting/dashboard`
  - **status**: ✅ OK
  - **Children**:
    - **Accounting Overview**: `accounting.dashboard` → `/accounting/dashboard` ✅ OK
    - **Receipting System**: `accounting.receipts_list` → `/accounting/receipts` ✅ OK
    - **Quotations**: `quotes.dashboard` → `/quotes/` ✅ OK
    - **Invoices**: `invoices.invoice_list` → `/invoices/` ✅ OK
    - **Cashbook**: `cashbook.index` → `/cashbook/` ✅ OK
    - **Financial Reports**: `reports.reports_index` → `/reports/` ✅ OK
    - **Payroll Management**: `payroll.payroll_list` → `/admin/payroll/` ✅ OK

#### Bakery Department Module (with children):
- **Display Name**: Bakery Department
  - **endpoint**: `bakery.dashboard`
  - **resolved route**: `/bakery/dashboard`
  - **status**: ✅ OK
  - **Children**:
    - **Bakery Overview**: `bakery.dashboard` → `/bakery/dashboard` ✅ OK
    - **Bakery Menu**: `bakery.items_list` → `/bakery/items` ✅ OK
    - **Bakery Orders**: `bakery.orders_list` → `/bakery/orders` ✅ OK
    - **Production Sheet**: `bakery.production_sheet` → `/bakery/production-sheet` ✅ OK
    - **Reports**: `bakery.reports` → `/bakery/reports` ✅ OK

#### POS System:
- **Display Name**: POS System
  - **endpoint**: `pos.index`
  - **resolved route**: `/pos/`
  - **status**: ✅ OK

#### HR Department Module (with children):
- **Display Name**: HR Department
  - **endpoint**: `hr.dashboard`
  - **resolved route**: `/hr/dashboard`
  - **status**: ✅ OK
  - **Children**:
    - **HR Overview**: `hr.dashboard` → `/hr/dashboard` ✅ OK
    - **Employee Management**: `hr.employee_list` → `/hr/employees` ✅ OK
    - **Roster Builder**: `hr.roster_builder` → `/hr/roster` ✅ OK
    - **Leave Requests**: `hr.leave_queue` → `/hr/leave` ✅ OK
    - **Attendance Review**: `hr.attendance_review` → `/hr/attendance` ✅ OK
    - **Payroll Export**: `hr.payroll_export` → `/hr/payroll` ✅ OK

#### Admin Module (with children):
- **Display Name**: Admin
  - **endpoint**: `admin.roles_list`
  - **resolved route**: `/admin/roles`
  - **status**: ✅ OK
  - **Children**:
    - **Roles & Permissions**: `admin.roles_list` → `/admin/roles` ✅ OK
    - **User Role Assignment**: `admin_users.users_assign` → `/admin/users/assign` ✅ OK

### Navigation Items from base.html (Bottom Navigation Bar)

- **Display Name**: Dashboard
  - **endpoint**: `core.dashboard`
  - **resolved route**: `/dashboard`
  - **status**: ✅ OK

- **Display Name**: Events
  - **endpoint**: `events.events_list`
  - **resolved route**: `/events/`
  - **status**: ✅ OK

- **Display Name**: Catering
  - **endpoint**: `catering.menu_list`
  - **resolved route**: `/catering/`
  - **status**: ✅ OK

- **Display Name**: Hire
  - **endpoint**: `hire.orders_list`
  - **resolved route**: `/hire/orders`
  - **status**: ✅ OK (FIXED)

- **Display Name**: Profile
  - **endpoint**: `admin.users_list` (if super admin) or `auth.change_password`
  - **resolved route**: `/admin/users` or `/auth/change-password`
  - **status**: ✅ OK

### Navigation Items from dashboard.html

- **Display Name**: View All Events
  - **endpoint**: `core.events_list`
  - **resolved route**: `/events`
  - **status**: ✅ OK

- **Display Name**: View Event
  - **endpoint**: `core.events_edit`
  - **resolved route**: `/events/edit/<int:event_id>`
  - **status**: ✅ OK

- **Display Name**: Open Full Pipeline
  - **endpoint**: `crm.pipeline`
  - **resolved route**: `/crm/pipeline`
  - **status**: ✅ OK

- **Display Name**: View All Tasks
  - **endpoint**: `tasks.task_list`
  - **resolved route**: `/tasks/`
  - **status**: ✅ OK

- **Display Name**: View Inventory
  - **endpoint**: `hire.inventory_list`
  - **resolved route**: `/hire/inventory`
  - **status**: ❌ **MISSING**

- **Display Name**: View Invoices
  - **endpoint**: `invoices.invoice_list`
  - **resolved route**: `/invoices/`
  - **status**: ✅ OK

- **Display Name**: View Events
  - **endpoint**: `core.events_list`
  - **resolved route**: `/events`
  - **status**: ✅ OK

- **Display Name**: View All (Announcements)
  - **endpoint**: `communication.announcements_list`
  - **resolved route**: `/communication/announcements`
  - **status**: ✅ OK

- **Display Name**: Read More (Announcement)
  - **endpoint**: `communication.announcement_view`
  - **resolved route**: `/communication/announcements/<int:announcement_id>`
  - **status**: ✅ OK

- **Display Name**: + New Client
  - **endpoint**: `core.clients_add`
  - **resolved route**: `/clients/add`
  - **status**: ✅ OK

- **Display Name**: + New Event
  - **endpoint**: `events.event_create`
  - **resolved route**: `/events/create`
  - **status**: ✅ OK

- **Display Name**: Sales Pipeline
  - **endpoint**: `crm.pipeline`
  - **resolved route**: `/crm/pipeline`
  - **status**: ✅ OK

---

## === MISSING / BROKEN ENDPOINTS ===

### ❌ CRITICAL MISSING ENDPOINTS:

1. **`hire.inventory_list`**
   - **Expected route**: `/hire/inventory`
   - **Used in**: 
     - Dashboard navigation (Hire Department → Hire Inventory)
     - Dashboard alerts (View Inventory link)
   - **Status**: ❌ **MISSING** - Route does not exist in `sas_management/hire/routes.py`
   - **Action Required**: Add route to `sas_management/hire/routes.py`

### ✅ VERIFIED ENDPOINTS (All OK):

1. **`accounting.receipts_list`**
   - **Route**: `/accounting/receipts`
   - **Used in**: Dashboard navigation (Accounting Department → Receipting System)
   - **Status**: ✅ **OK** - Verified in `sas_management/blueprints/accounting/routes.py`

2. **`admin_users.users_assign`**
   - **Route**: `/admin/users/assign`
   - **Used in**: Dashboard navigation (Admin → User Role Assignment)
   - **Status**: ✅ **OK** - Verified in `sas_management/blueprints/admin/admin_users_assign.py`

3. **`communication.announcements_list`**
   - **Route**: `/communication/announcements`
   - **Used in**: Dashboard template
   - **Status**: ✅ **OK** - Verified in `sas_management/blueprints/communication/__init__.py`

4. **`communication.announcement_view`**
   - **Route**: `/communication/announcements/<int:announcement_id>`
   - **Used in**: Dashboard template
   - **Status**: ✅ **OK** - Verified in `sas_management/blueprints/communication/__init__.py`

### ✅ RECENTLY FIXED ENDPOINTS:

1. **`hire.index`**
   - **Route**: `/hire/`
   - **Status**: ✅ **FIXED** - Now exists in `sas_management/hire/routes.py`

2. **`hire.orders_list`**
   - **Route**: `/hire/orders`
   - **Status**: ✅ **FIXED** - Now exists in `sas_management/hire/routes.py`

---

## === SUMMARY ===

### Total Blueprints Registered: 50+
### Total Navigation Items: 40+
### Missing Endpoints: 1 critical
### Verified Endpoints: 4 (all OK)

### Priority Actions:
1. **HIGH PRIORITY**: Add `hire.inventory_list` route to `sas_management/hire/routes.py`
   - This endpoint is referenced in:
     - Dashboard navigation (Hire Department → Hire Inventory)
     - Dashboard alerts (View Inventory link)
2. **LOW PRIORITY**: Complete route documentation for blueprints with incomplete endpoint lists

---

**Report Generated**: Analysis of complete sas_management project structure
**Last Updated**: After hire module repair

