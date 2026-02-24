import os
os.environ['SECRET_KEY'] = 'sas-management-system-secret-key-2024-production'

# Start server and open browser
import webbrowser
import time
import subprocess

# Start Flask server
proc = subprocess.Popen(
    ['python', 'run_backend.py'],
    cwd=r'C:\Users\DELL\Desktop\sas management system',
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Wait for server to start
time.sleep(5)

# Open browser to login page
webbrowser.open('http://127.0.0.1:5000/')

print("Server running at http://127.0.0.1:5000")
print("Login with: admin@sas.com / password")
print("After login, go to /admin/dashboard")
