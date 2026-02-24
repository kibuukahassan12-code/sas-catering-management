# Starting the SAS Management System Server

## Quick Start

### Option 1: Set SECRET_KEY and Run (Recommended)
```powershell
# In PowerShell:
$env:SECRET_KEY = "your-secret-key-here"
python run_backend.py
```

### Option 2: Use Development Config (For Local Testing)
If you want to test without setting SECRET_KEY, temporarily modify `sas_management/app.py`:
```python
# Change line ~71 from:
app.config.from_object(ProductionConfig)
# To:
from config import DevelopmentConfig
app.config.from_object(DevelopmentConfig)
```

## Server URL
Once started, the server will be available at:
- **http://127.0.0.1:5000**
- **http://localhost:5000**

## Health Check
Test the server is running:
```powershell
curl http://127.0.0.1:5000/health
```

## Stopping the Server
Press `Ctrl+C` in the terminal where the server is running.

---

**Note**: The server is configured to require SECRET_KEY in production mode for security.
For local development, you can use DevelopmentConfig which has a default SECRET_KEY.
