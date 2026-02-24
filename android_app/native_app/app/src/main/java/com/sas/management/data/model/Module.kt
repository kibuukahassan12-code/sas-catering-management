package com.sas.management.data.model

data class Module(
    val id: String,
    val name: String,
    val icon: String,
    val route: String,
    val description: String? = null
)

object Modules {
    val allModules = listOf(
        Module("dashboard", "Dashboard", "📊", "dashboard", "Main dashboard with KPIs"),
        Module("events", "Events", "📅", "events", "Event management and planning"),
        Module("pos", "POS", "💳", "pos", "Point of Sale terminal"),
        Module("hr", "HR", "👥", "hr", "Human Resources management"),
        Module("accounting", "Accounting", "💰", "accounting", "Financial management"),
        Module("catering", "Catering", "🍽️", "catering", "Menu and catering management"),
        Module("hire", "Hire", "📦", "hire", "Equipment hire orders"),
        Module("production", "Production", "🏭", "production", "Production management"),
        Module("communication", "Communication", "💬", "communication", "Messages and announcements"),
        Module("university", "University", "🎓", "university", "Employee training"),
        Module("admin", "Admin", "🛡️", "admin", "Administration panel"),
        Module("ai", "SAS AI", "🤖", "ai", "AI assistant"),
        Module("crm", "CRM", "📞", "crm", "Customer relationship management"),
        Module("inventory", "Inventory", "📋", "inventory", "Inventory management"),
        Module("dispatch", "Dispatch", "🚚", "dispatch", "Vehicle and dispatch"),
        Module("reports", "Reports", "📊", "reports", "Reports and analytics"),
        Module("bi", "Business Intelligence", "📈", "bi", "BI and analytics"),
        Module("automation", "Automation", "⚙️", "automation", "Workflow automation"),
        Module("vendors", "Vendors", "🏢", "vendors", "Vendor management"),
        Module("quotes", "Quotes", "📝", "quotes", "Quotations"),
        Module("invoices", "Invoices", "🧾", "invoices", "Invoice management"),
        Module("proposals", "Proposals", "📄", "proposals", "Proposal management"),
        Module("tasks", "Tasks", "✅", "tasks", "Task management"),
        Module("timeline", "Timeline", "⏰", "timeline", "Event timeline"),
        Module("floorplanner", "Floor Planner", "📐", "floorplanner", "Floor plan design"),
        Module("menu_builder", "Menu Builder", "🍴", "menu_builder", "Menu creation"),
        Module("contracts", "Contracts", "📜", "contracts", "Contract management"),
        Module("food_safety", "Food Safety", "🛡️", "food_safety", "Food safety compliance"),
        Module("incidents", "Incidents", "⚠️", "incidents", "Incident reporting"),
        Module("kds", "KDS", "📺", "kds", "Kitchen Display System"),
        Module("payroll", "Payroll", "💵", "payroll", "Payroll management"),
        Module("cashbook", "Cashbook", "💸", "cashbook", "Cashbook entries"),
        Module("analytics", "Analytics", "📊", "analytics", "Data analytics"),
        Module("audit", "Audit", "🔍", "audit", "Audit logs"),
        Module("integrations", "Integrations", "🔌", "integrations", "Third-party integrations"),
        Module("mobile_staff", "Mobile Staff", "📱", "mobile_staff", "Mobile staff app"),
        Module("client_portal", "Client Portal", "🌐", "client_portal", "Client access portal"),
        Module("chat", "Chat", "💬", "chat", "Internal chat"),
        Module("search", "Search", "🔍", "search", "Global search"),
        Module("leads", "Leads", "🎯", "leads", "Lead management"),
        Module("branches", "Branches", "🏢", "branches", "Branch management"),
        Module("bakery", "Bakery", "🥖", "bakery", "Bakery department"),
        Module("production_recipes", "Recipes", "📖", "production_recipes", "Recipe management"),
        Module("profitability", "Profitability", "📈", "profitability", "Profitability analysis"),
        Module("event_service", "Event Service", "🎪", "event_service", "Event service department")
    )
}

