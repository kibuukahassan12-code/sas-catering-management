@echo off
echo Building SAS EXE...

set PYTHON="C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"

%PYTHON% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --noconsole ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "blueprints;blueprints" ^
    --add-data ".env;." ^
    --add-data "sas.db;instance" ^
    --hidden-import flask_login ^
    --hidden-import flask_sqlalchemy ^
    --hidden-import flask_limiter ^
    --hidden-import flask_bcrypt ^
    --hidden-import flask_wtf ^
    --hidden-import wtforms ^
    --hidden-import email_validator ^
    --hidden-import python_dotenv ^
    --hidden-import PIL ^
    --onefile app.py

echo Done. Check the dist folder.
