# Fresh, clean navigation module for SAS

def get_modules():
    return [
        {
            'name': 'Dashboard',
            'url': '/dashboard',
            'icon': 'dashboard'
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
        }
    ]
