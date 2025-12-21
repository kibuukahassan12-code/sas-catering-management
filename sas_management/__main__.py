"""Entry point for running the SAS Management System as a module.

Usage:
    python -m sas_management
    python -m sas_management.app
"""

import sys
import os

# Add the parent directory to the path so imports work correctly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

if __name__ == "__main__":
    # Canonical entry point: use create_app() to ensure proper initialization
    from sas_management.app import create_app
    
    app = create_app()
    
    import webbrowser
    import threading
    import time
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:5000')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=app.config.get('DEBUG', False)
    )

