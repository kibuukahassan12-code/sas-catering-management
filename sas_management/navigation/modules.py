# Fresh, clean navigation module for SAS

def get_modules():
    return [
        {
            'name': 'Dashboard',
            'url': '/dashboard',
            'icon': 'dashboard'
        },
        {
            'name': 'SAS Office',
            'url': '/office/',
            'icon': 'folder',
            'children': [
                {'name': 'File Manager', 'url': '/office/'},
            ]
        },
        {
            'name': 'Event Service Department',
            'url': '/service/',
            'icon': 'event',
            'children': [
                {'name': 'Services Overview', 'url': '/service/'},
                {'name': 'All Events', 'url': '/service/events'},
                {'name': 'Create Event', 'url': '/service/event/add'},
                {'name': 'Service Orders', 'url': '/service/orders'},
                {'name': 'Costing & Quotations', 'url': '/service/costing'},
                {'name': 'Staff Assignments', 'url': '/service/staff'},
                {'name': 'Vendors', 'url': '/service/vendors'},
                {'name': 'Timeline', 'url': '/service/timeline'},
                {'name': 'Documents', 'url': '/service/documents'},
                {'name': 'Checklists', 'url': '/service/checklists'},
                {'name': 'Messages', 'url': '/service/messages'},
                {'name': 'Reports', 'url': '/service/reports'},
                {'name': 'Analytics', 'url': '/service/analytics'}
            ]
        },
        {
            'name': 'Production',
            'url': '/production/',
            'icon': 'factory',
            'children': [
                {'name': 'Production Dashboard', 'url': '/production/'},
                {'name': 'Production Orders', 'url': '/production/order/new'},
                {'name': 'Budgets', 'url': '/production/budgets'},
                {'name': 'Create Budget', 'url': '/production/budget/new'},
                {'name': 'Daily Inventory', 'url': '/production/inventory'},
                {'name': 'Inventory Report', 'url': '/production/inventory/report'},
                {'name': 'Kitchen Checklist', 'url': '/production/kitchen-checklist'},
                {'name': 'Food Safety', 'url': '/production/food-safety'},
                {'name': 'Hygiene Reports', 'url': '/production/hygiene-reports'},
                {'name': 'Delivery QC', 'url': '/production/delivery-qc'},
            ]
        },
        {
            'name': 'Catering Menu',
            'url': '/catering/',
            'icon': 'food',
            'children': [
                {'name': 'Menu Items', 'url': '/catering/menu'},
                {'name': 'Categories', 'url': '/catering/categories'},
            ]
        },
        {
            'name': 'Bakery',
            'url': '/bakery/',
            'icon': 'bread',
            'children': [
                {'name': 'Bakery Dashboard', 'url': '/bakery/'},
                {'name': 'Menu Items', 'url': '/bakery/items'},
                {'name': 'Orders', 'url': '/bakery/orders'},
            ]
        },
        {
            'name': 'POS System',
            'url': '/pos/',
            'icon': 'cash',
            'children': [
                {'name': 'POS Dashboard', 'url': '/pos/'},
                {'name': 'Products', 'url': '/pos/products'},
                {'name': 'Devices', 'url': '/pos/devices'},
                {'name': 'Shifts', 'url': '/pos/shifts'},
            ]
        },
        {
            'name': 'Hire Orders',
            'url': '/hire/',
            'icon': 'package',
            'children': [
                {'name': 'All Orders', 'url': '/hire/orders'},
                {'name': 'Create Order', 'url': '/hire/order/new'},
                {'name': 'Equipment', 'url': '/hire/equipment'},
            ]
        },
        {
            'name': 'Accounting',
            'url': '/accounting/',
            'icon': 'calculator',
            'children': [
                {'name': 'Dashboard', 'url': '/accounting/'},
                {'name': 'Transactions', 'url': '/accounting/transactions'},
                {'name': 'Invoices', 'url': '/accounting/invoices'},
                {'name': 'Receipts', 'url': '/accounting/receipts'},
                {'name': 'Chart of Accounts', 'url': '/accounting/accounts'},
            ]
        },
        {
            'name': 'HR & Employees',
            'url': '/hr/dashboard',
            'icon': 'users',
            'children': [
                {'name': 'HR Dashboard', 'url': '/hr/dashboard'},
                {'name': 'Employees', 'url': '/hr/employees'},
                {'name': 'Attendance', 'url': '/hr/attendance'},
                {'name': 'Leave Requests', 'url': '/hr/leave'},
                {'name': 'Shifts', 'url': '/hr/shifts'},
            ]
        },
        {
            'name': 'Inventory',
            'url': '/production/inventory',
            'icon': 'box',
            'children': [
                {'name': 'Daily Inventory', 'url': '/production/inventory'},
                {'name': 'Inventory Report', 'url': '/production/inventory/report'},
            ]
        },
        {
            'name': 'CRM & Leads',
            'url': '/crm/pipeline',
            'icon': 'user-check',
            'children': [
                {'name': 'CRM Dashboard', 'url': '/crm/pipeline'},
                {'name': 'Clients', 'url': '/crm/clients'},
                {'name': 'Leads', 'url': '/leads/'},
            ]
        },
        {
            'name': 'Quotes & Proposals',
            'url': '/quotes/',
            'icon': 'file-text',
            'children': [
                {'name': 'Quotations', 'url': '/quotes/'},
                {'name': 'Proposals', 'url': '/proposals/'},
            ]
        },
        {
            'name': 'Recipes',
            'url': '/production/recipes',
            'icon': 'book-open',
            'children': [
                {'name': 'Recipe Dashboard', 'url': '/production/recipes/dashboard'},
                {'name': 'All Recipes', 'url': '/production/recipes'},
            ]
        },
        {
            'name': 'University',
            'url': '/university/',
            'icon': 'graduation-cap',
            'children': [
                {'name': 'Employee University', 'url': '/university/'},
                {'name': 'Courses', 'url': '/university/courses'},
                {'name': 'My Courses', 'url': '/university/my-courses'},
            ]
        },
        {
            'name': 'Reports & Analytics',
            'url': '/bi/dashboard',
            'icon': 'chart-bar',
            'children': [
                {'name': 'BI Dashboard', 'url': '/bi/dashboard'},
                {'name': 'Event Profitability', 'url': '/bi/event-profitability'},
                {'name': 'Sales Forecast', 'url': '/bi/sales-forecast'},
                {'name': 'Staff Performance', 'url': '/bi/staff-performance'},
                {'name': 'Ingredient Trends', 'url': '/bi/ingredient-trends'},
            ]
        },
        {
            'name': 'Settings & Admin',
            'url': '/admin/',
            'icon': 'settings',
            'children': [
                {'name': 'Admin Dashboard', 'url': '/admin/'},
                {'name': 'Users', 'url': '/admin/users'},
                {'name': 'Roles & Permissions', 'url': '/admin/rbac/'},
                {'name': 'Chat Bot', 'url': '/ai/chat'},
            ]
        },
    ]
