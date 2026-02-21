import os


class BaseConfig:
    """Base configuration for SAS Best Foods Catering Management System."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    # Supabase PostgreSQL connection - set DATABASE_URL env var
    # Connection string format (pooler):
    # postgresql://postgres.[project-ref]:[password]@aws-[region].pooler.supabase.com:6543/postgres
    # Or direct:
    # postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///sas.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    DEBUG = False
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600 * 24 * 7
    
    # Application settings
    CURRENCY_PREFIX = "UGX "
    DEFAULT_PAGE_SIZE = 10
    
    # File upload settings
    UPLOAD_FOLDER = "files"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx", "ppt", "pptx"}
    
    # University video upload settings
    UNIVERSITY_UPLOAD_FOLDER = "sas_management/static/uploads/university"
    UNIVERSITY_MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max file size for videos
    
    # Enterprise Module Flags
    ENABLE_BRANCHES = os.environ.get("ENABLE_BRANCHES", "false").lower() == "true"
    ENABLE_SCHEDULER = os.environ.get("ENABLE_SCHEDULER", "true").lower() == "true"
    
    # AI Features
    AI_EVENT_PLANNER_ENABLED = os.environ.get("AI_EVENT_PLANNER_ENABLED", "true").lower() == "true"
    
    # SAS AI Module - Premium AI Features Hub
    AI_MODULE_ENABLED = os.environ.get("AI_MODULE_ENABLED", "true").lower() == "true"
    SAS_AI_ENABLED = AI_MODULE_ENABLED  # Alias for template compatibility
    
    # Employee University Module - Premium Training Hub
    EMPLOYEE_UNIVERSITY_ENABLED = os.environ.get("EMPLOYEE_UNIVERSITY_ENABLED", "true").lower() == "true"
    
    # Event Service Module
    EVENT_SERVICE_ENABLED = os.environ.get("EVENT_SERVICE_ENABLED", "true").lower() == "true"
    
    # Google Gemini AI Integration (optional)
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", None)
    
    # Individual AI Feature Flags - All enabled by default
    AI_FEATURES = {
        "event_planner": os.environ.get("AI_FEATURE_EVENT_PLANNER", "true").lower() == "true",
        "quotation_ai": os.environ.get("AI_FEATURE_QUOTATION_AI", "true").lower() == "true",
        "profit_analyzer": os.environ.get("AI_FEATURE_PROFIT_ANALYZER", "true").lower() == "true",
        "pricing_advisor": os.environ.get("AI_FEATURE_PRICING_ADVISOR", "true").lower() == "true",
        "staff_coach": os.environ.get("AI_FEATURE_STAFF_COACH", "true").lower() == "true",
        "inventory_predictor": os.environ.get("AI_FEATURE_INVENTORY_PREDICTOR", "true").lower() == "true",
        "client_analyzer": os.environ.get("AI_FEATURE_CLIENT_ANALYZER", "true").lower() == "true",
        "compliance_monitor": os.environ.get("AI_FEATURE_COMPLIANCE_MONITOR", "true").lower() == "true",
        "ops_chat": os.environ.get("AI_FEATURE_OPS_CHAT", "true").lower() == "true",
        "business_forecaster": os.environ.get("AI_FEATURE_BUSINESS_FORECASTER", "true").lower() == "true",
        "ai_chat": os.environ.get("AI_FEATURE_AI_CHAT", "true").lower() == "true",
    }


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"


class ProductionConfig(BaseConfig):
    DEBUG = False
