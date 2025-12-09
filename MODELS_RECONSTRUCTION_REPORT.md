# MODELS.PY RECONSTRUCTION REPORT
## Complete List of All SQLAlchemy Models Required

Based on comprehensive codebase search, here are ALL models that must be in `models.py`:

---

## 📍 **FILES CONTAINING MODEL DEFINITIONS:**

1. **models.py** (CURRENT - PARTIALLY OVERWRITTEN)
   - ✅ EventCostItem
   - ✅ EventRevenueItem
   - ❌ All other models missing

2. **models/ai_models.py** (SEPARATE FILE - AI MODELS)
   - AIPredictionRun
   - MenuRecommendation
   - ForecastResult
   - StaffingSuggestion
   - ShortageAlert
   - CostOptimization

---

## 📋 **REQUIRED MODELS (Based on Imports Across Codebase):**

### **CORE MODELS:**

1. **User** - User authentication and roles
   - Imported in: `app.py`, `routes.py`, `blueprints/crm/__init__.py`
   - Related: `UserRole` (Enum)

2. **Client** - Client management
   - Imported in: `routes.py`, `blueprints/bi/__init__.py`, `blueprints/accounting/__init__.py`, `blueprints/crm/__init__.py`
   - Related: `ClientNote`, `ClientDocument`, `ClientActivity`, `ClientCommunication`

3. **Event** - Event management
   - Imported in: `routes.py`, `blueprints/bi/__init__.py`, `blueprints/invoices/__init__.py`, `blueprints/crm/__init__.py`, `blueprints/profitability/routes.py`
   - Related: `EventStaffAssignment`, `EventMenuSelection`, `EventDocument`, `EventCommunication`

4. **Invoice** - Invoice management
   - Imported in: `routes.py`, `blueprints/invoices/__init__.py`, `blueprints/accounting/__init__.py`, `blueprints/crm/__init__.py`
   - Related: `InvoiceStatus` (Enum), `Receipt`

5. **Transaction** - Financial transactions
   - Imported in: `routes.py`, `blueprints/invoices/__init__.py`, `services/bi_service.py`
   - Related: `TransactionType` (Enum)

6. **Task** - Task management
   - Imported in: `routes.py`, `blueprints/crm/__init__.py`
   - Related: `TaskStatus` (Enum)

7. **Quotation** - Quotation management
   - Imported in: `routes.py`
   - Related: `QuotationLine`, `QuotationSource` (Enum)

8. **IncomingLead** - CRM leads
   - Imported in: `routes.py`, `blueprints/crm/__init__.py`, `blueprints/leads/__init__.py`

---

### **CATERING & MENU MODELS:**

9. **CateringItem** - Catering menu items
   - Imported in: `routes.py`

10. **BakeryItem** - Bakery items
    - Imported in: `blueprints/bi/__init__.py`

11. **Ingredient** - Ingredients inventory
    - Imported in: `routes.py`, `blueprints/bi/__init__.py`, `services/bi_service.py`

12. **RecipeItem** - Recipe components
    - Imported in: `routes.py`

---

### **INVENTORY & HIRE MODELS:**

13. **InventoryItem** - Inventory items
    - Imported in: `routes.py`

14. **HireOrder** - Equipment hire orders
    - Imported in: `routes.py`
    - Related: `HireOrderItem`

15. **HireOrderItem** - Hire order line items
    - Imported in: `routes.py`

---

### **ACCOUNTING MODELS:**

16. **Account** - Chart of accounts
    - Imported in: `blueprints/accounting/__init__.py`

17. **AccountingPayment** - Payment records
    - Imported in: `blueprints/accounting/__init__.py`, `blueprints/accounting/routes.py`

18. **AccountingReceipt** - Receipt records
    - Imported in: `blueprints/accounting/__init__.py`, `blueprints/accounting/routes.py`

19. **BankStatement** - Bank statements
    - Imported in: `blueprints/accounting/__init__.py`

20. **Journal** - Accounting journals
    - Imported in: `blueprints/accounting/__init__.py`
    - Related: `JournalEntry`, `JournalEntryLine`

21. **JournalEntry** - Journal entries
    - Imported in: `blueprints/accounting/__init__.py`

22. **JournalEntryLine** - Journal entry lines
    - Imported in: `blueprints/accounting/__init__.py`

---

### **BUSINESS INTELLIGENCE MODELS:**

23. **BIEventProfitability** - Event profitability analysis
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

24. **BIIngredientPriceTrend** - Ingredient price trends
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

25. **BISalesForecast** - Sales forecasts
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

26. **BIStaffPerformance** - Staff performance metrics
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

27. **BIBakeryDemand** - Bakery demand forecasts
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

28. **BICustomerBehavior** - Customer behavior analysis
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

29. **BIPOSHeatmap** - POS heatmap data
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

---

### **FLOOR PLANNER MODELS:**

30. **FloorPlan** - Floor plan designs
    - Imported in: `blueprints/floorplanner/__init__.py`

31. **SeatingAssignment** - Seating assignments
    - Imported in: `blueprints/floorplanner/__init__.py`

---

### **EVENT-RELATED MODELS:**

32. **EventStaffAssignment** - Staff assignments for events
    - Imported in: `services/bi_service.py`

33. **EventMenuSelection** - Menu selections for events
    - Imported in: `services/bi_service.py`

34. **EventDocument** - Event documents
    - Referenced in event views

35. **EventCommunication** - Event communications
    - Referenced in event views

---

### **EMPLOYEE/HR MODELS:**

36. **Employee** - Employee records
    - Imported in: `blueprints/bi/__init__.py`, `services/bi_service.py`

---

### **ENUMS:**

- **UserRole** - User role enumeration
  - Imported in: `routes.py`, `blueprints/bi/__init__.py`, `blueprints/invoices/__init__.py`, `blueprints/accounting/__init__.py`, `blueprints/crm/__init__.py`, `blueprints/profitability/routes.py`

- **InvoiceStatus** - Invoice status enumeration
  - Imported in: `routes.py`, `blueprints/invoices/__init__.py`, `blueprints/accounting/__init__.py`

- **TransactionType** - Transaction type enumeration
  - Imported in: `routes.py`, `blueprints/invoices/__init__.py`, `services/bi_service.py`

- **TaskStatus** - Task status enumeration
  - Imported in: `routes.py`, `blueprints/crm/__init__.py`

- **QuotationSource** - Quotation source enumeration
  - Imported in: `routes.py`

---

## 🔍 **IMPORT LOCATIONS BY FILE:**

### **routes.py** imports:
```python
from models import (
    CateringItem, Client, ClientActivity, Event, HireOrder, HireOrderItem,
    IncomingLead, Ingredient, InventoryItem, Invoice, InvoiceStatus,
    Quotation, QuotationLine, QuotationSource, RecipeItem, Task, TaskStatus,
    Transaction, TransactionType, User, UserRole, db
)
```

### **blueprints/bi/__init__.py** imports:
```python
from models import (
    db, BIEventProfitability, BIIngredientPriceTrend, BISalesForecast,
    BIStaffPerformance, BIBakeryDemand, BICustomerBehavior, BIPOSHeatmap,
    Event, Ingredient, Employee, Client, BakeryItem, UserRole
)
```

### **blueprints/accounting/__init__.py** imports:
```python
from models import (
    Account, AccountingPayment, AccountingReceipt, BankStatement,
    Client, Invoice, InvoiceStatus, Journal, JournalEntry, JournalEntryLine,
    UserRole, db
)
```

### **blueprints/crm/__init__.py** imports:
```python
from models import (
    Client, ClientNote, ClientDocument, ClientActivity, ClientCommunication,
    Event, IncomingLead, Invoice, Task, User, UserRole, db
)
```

### **blueprints/invoices/__init__.py** imports:
```python
from models import (
    Event, Invoice, InvoiceStatus, Receipt, Transaction, TransactionType,
    UserRole, db
)
```

### **blueprints/profitability/routes.py** imports:
```python
from models import Event, EventCostItem, EventRevenueItem, UserRole, db
```

### **blueprints/floorplanner/__init__.py** imports:
```python
from models import db, FloorPlan, SeatingAssignment, Event, UserRole
```

---

## ⚠️ **CRITICAL FINDINGS:**

1. **models.py is MISSING all core models** - Only contains EventCostItem and EventRevenueItem
2. **models/ai_models.py exists separately** - Contains 6 AI-related models
3. **All imports will FAIL** until models.py is restored with all required models
4. **Database initialization requires `seed_initial_data()` function** - Referenced in `app.py`
5. **Required functions in models.py:**
   - `seed_initial_data(db)` - Seed initial database data
   - `configure_relationship_ordering()` - Configure SQLAlchemy relationship ordering
   - `setup_audit_logging()` - Set up audit logging functionality

---

## 📝 **RECOMMENDED ACTION:**

1. **Restore models.py from backup/git** - The file was accidentally overwritten
2. **Add EventCostItem and EventRevenueItem** to the restored file
3. **Ensure all models listed above are present**
4. **Verify `seed_initial_data()` function exists**
5. **Run database migration**: `db.create_all()` or `flask db upgrade`

---

## 📊 **SUMMARY:**

- **Total Models Required**: ~36+ model classes
- **Enums Required**: 5+ enumeration classes
- **Separate Model Files**: 1 (models/ai_models.py)
- **Current Status**: models.py is incomplete (only 2 models present)

---

---

## 🔧 **REQUIRED FUNCTIONS IN models.py:**

Based on `app.py` imports, the following functions must exist:

1. **`seed_initial_data(db)`**
   - Called in: `app.py` line 259
   - Purpose: Populate database with initial/seed data

2. **`configure_relationship_ordering()`**
   - Called in: `app.py` line 262-263
   - Purpose: Configure order_by for relationships that use forward references

3. **`setup_audit_logging()`**
   - Called in: `app.py` line 266-267
   - Purpose: Set up audit logging functionality

---

**Generated**: 2024
**Search Scope**: Entire codebase
**Patterns Searched**: db.Model, class definitions, relationship(), ForeignKey(), imports, function definitions

