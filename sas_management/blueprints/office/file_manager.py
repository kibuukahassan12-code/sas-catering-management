import os
from flask import Blueprint, request, redirect, url_for, flash, send_from_directory, render_template, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sas_management.models import UserRole
from sas_management.utils import role_required

office_bp = Blueprint("office", __name__, url_prefix="/office")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, "..", "..", "instance", "office_uploads")

os.makedirs(UPLOAD_ROOT, exist_ok=True)

# ================= LIST FILES =================
@office_bp.route("/", methods=["GET"])
@login_required
def file_manager():
    """List all files and folders in the file manager."""
    files = []
    folders = []
    
    try:
        if os.path.exists(UPLOAD_ROOT):
            for item in os.listdir(UPLOAD_ROOT):
                item_path = os.path.join(UPLOAD_ROOT, item)
                if os.path.isfile(item_path):
                    files.append({
                        "name": item,
                        "size": os.path.getsize(item_path),
                        "path": item_path
                    })
                elif os.path.isdir(item_path):
                    folders.append({
                        "name": item,
                        "path": item_path
                    })
    except Exception as e:
        flash(f"Error reading files: {str(e)}", "error")
    
    # Return JSON if requested, otherwise render template
    if request.args.get("format") == "json":
        return jsonify({"files": [f["name"] for f in files], "folders": [f["name"] for f in folders]})
    
    return render_template("office/file_manager.html", files=files, folders=folders)

# ================= UPLOAD FILE =================
@office_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    """Upload a file to the file manager."""
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("office.file_manager"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("office.file_manager"))

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_ROOT, filename)
    
    # Handle duplicate filenames
    counter = 1
    base_name, ext = os.path.splitext(filename)
    while os.path.exists(file_path):
        filename = f"{base_name}_{counter}{ext}"
        file_path = os.path.join(UPLOAD_ROOT, filename)
        counter += 1
    
    try:
        file.save(file_path)
        flash(f"File '{filename}' uploaded successfully", "success")
    except Exception as e:
        flash(f"Error uploading file: {str(e)}", "error")

    return redirect(url_for("office.file_manager"))

# ================= CREATE FOLDER =================
@office_bp.route("/folder", methods=["POST"])
@login_required
def create_folder():
    """Create a new folder in the file manager."""
    folder_name = request.form.get("folder", "").strip()
    if not folder_name:
        flash("Folder name required", "error")
        return redirect(url_for("office.file_manager"))

    # Validate folder name
    invalid_chars = '<>:"/\\|?*'
    if any(char in folder_name for char in invalid_chars):
        flash(f"Folder name contains invalid characters", "error")
        return redirect(url_for("office.file_manager"))

    folder_path = os.path.join(UPLOAD_ROOT, secure_filename(folder_name))
    
    try:
        os.makedirs(folder_path, exist_ok=True)
        flash(f"Folder '{folder_name}' created successfully", "success")
    except Exception as e:
        flash(f"Error creating folder: {str(e)}", "error")

    return redirect(url_for("office.file_manager"))

# ================= DELETE FILE (ADMIN ONLY) =================
@office_bp.route("/delete/<filename>", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def delete_file(filename):
    """Delete a file from the file manager. Admin only."""
    file_path = os.path.join(UPLOAD_ROOT, secure_filename(filename))
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            flash(f"File '{filename}' deleted successfully", "success")
        except Exception as e:
            flash(f"Error deleting file: {str(e)}", "error")
    else:
        flash("File not found", "error")

    return redirect(url_for("office.file_manager"))

# ================= DOWNLOAD FILE =================
@office_bp.route("/download/<filename>")
@login_required
def download_file(filename):
    """Download a file from the file manager."""
    file_path = os.path.join(UPLOAD_ROOT, secure_filename(filename))
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(UPLOAD_ROOT, secure_filename(filename), as_attachment=True)
    else:
        flash("File not found", "error")
        return redirect(url_for("office.file_manager"))
