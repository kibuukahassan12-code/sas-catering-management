"""SAS Office - File and Folder Management System."""
from datetime import datetime
import os
import uuid
import mimetypes
import zipfile
import shutil

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from sas_management.models import OfficeFile, OfficeFolder, User, UserRole, db
from sas_management.utils import role_required
from sas_management.utils.helpers import get_or_404

office_bp = Blueprint("office", __name__, url_prefix="/office")


def _office_uploads_dir():
    """Get or create the office uploads directory."""
    d = os.path.join(current_app.instance_path, "office_uploads")
    os.makedirs(d, exist_ok=True)
    return d


def _infer_file_type(filename):
    """Infer file type category from filename for organizational purposes.
    
    NOTE: This function only categorizes files for organization - it does NOT restrict
    which files can be uploaded. ALL file formats are accepted regardless of extension.
    Unknown or unrecognized file types are categorized as "document" by default.
    """
    if not filename or "." not in filename:
        return "document"
    ext = filename.rsplit(".", 1)[-1].lower()
    
    # Archive/Compressed files
    if ext in {"zip", "rar", "7z", "tar", "gz", "bz2"}:
        return "archive"
    # Images
    if ext in {"png", "jpg", "jpeg", "gif", "webp", "bmp", "svg", "ico", "tiff", "tif"}:
        return "image"
    # Videos
    if ext in {"mp4", "avi", "mov", "wmv", "flv", "webm", "mkv", "m4v", "3gp"}:
        return "video"
    # Audio
    if ext in {"mp3", "wav", "ogg", "m4a", "aac", "flac", "wma"}:
        return "audio"
    # Documents (default for all other file types - NO RESTRICTIONS)
    return "document"


def _get_mime_type(filename):
    """Get MIME type for file with comprehensive Office document support."""
    if not filename:
        return "application/octet-stream"
    
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    # Comprehensive MIME type mapping for Office documents and common file types
    mime_map = {
        # Microsoft Office Documents
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
        "xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
        "docm": "application/vnd.ms-word.document.macroEnabled.12",
        "dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
        "dotm": "application/vnd.ms-word.template.macroEnabled.12",
        "pptm": "application/vnd.ms-powerpoint.presentation.macroEnabled.12",
        "potx": "application/vnd.openxmlformats-officedocument.presentationml.template",
        "potm": "application/vnd.ms-powerpoint.template.macroEnabled.12",
        "ppsm": "application/vnd.ms-powerpoint.slideshow.macroEnabled.12",
        "sldx": "application/vnd.openxmlformats-officedocument.presentationml.slide",
        "sldm": "application/vnd.ms-powerpoint.slide.macroEnabled.12",
        
        # OpenOffice/LibreOffice
        "odt": "application/vnd.oasis.opendocument.text",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "odp": "application/vnd.oasis.opendocument.presentation",
        "odg": "application/vnd.oasis.opendocument.graphics",
        "odf": "application/vnd.oasis.opendocument.formula",
        
        # PDF
        "pdf": "application/pdf",
        
        # Text files
        "txt": "text/plain",
        "rtf": "application/rtf",
        "csv": "text/csv",
        
        # Images
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        
        # Videos
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "mov": "video/quicktime",
        "wmv": "video/x-ms-wmv",
        "flv": "video/x-flv",
        "webm": "video/webm",
        "mkv": "video/x-matroska",
        "m4v": "video/x-m4v",
        "3gp": "video/3gpp",
        
        # Audio
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wma": "audio/x-ms-wma",
        
        # Archives
        "zip": "application/zip",
        "rar": "application/x-rar-compressed",
        "7z": "application/x-7z-compressed",
        "tar": "application/x-tar",
        "gz": "application/gzip",
        "bz2": "application/x-bzip2",
        
        # Code files
        "html": "text/html",
        "htm": "text/html",
        "css": "text/css",
        "js": "application/javascript",
        "json": "application/json",
        "xml": "application/xml",
        "py": "text/x-python",
        "java": "text/x-java-source",
        "c": "text/x-c",
        "cpp": "text/x-c++",
        "cs": "text/x-csharp",
        
        # Data files
        "sql": "application/sql",
        "db": "application/x-sqlite3",
        "sqlite": "application/x-sqlite3",
    }
    
    # Check our custom map first
    if ext in mime_map:
        return mime_map[ext]
    
    # Fall back to Python's mimetypes module
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def _format_file_size(size_bytes):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


@office_bp.route("")
@office_bp.route("/")
@login_required
def index():
    """Main file manager view."""
    folder_id = request.args.get("folder", type=int)
    current_folder = None
    if folder_id:
        current_folder = get_or_404(OfficeFolder, folder_id)
    
    # Get folders in current directory
    folders = OfficeFolder.query.filter_by(parent_id=folder_id).order_by(OfficeFolder.name).all()
    
    # Get files in current directory
    files = OfficeFile.query.filter_by(folder_id=folder_id).order_by(OfficeFile.name).all()
    
    # Build breadcrumb path
    breadcrumbs = []
    if current_folder:
        f = current_folder
        while f:
            breadcrumbs.insert(0, {"id": f.id, "name": f.name})
            f = f.parent
    
    return render_template(
        "office/index.html",
        folders=folders,
        files=files,
        current_folder=current_folder,
        breadcrumbs=breadcrumbs,
        format_file_size=_format_file_size,
    )


@office_bp.route("/folder/new", methods=["POST"])
@login_required
def create_folder():
    """Create a new folder."""
    name = request.form.get("name", "").strip()
    parent_id_str = request.form.get("parent_id", "").strip()
    
    # Handle empty string or None for parent_id
    parent_id = None
    if parent_id_str:
        try:
            parent_id = int(parent_id_str)
        except (ValueError, TypeError):
            parent_id = None
    
    if not name:
        flash("Folder name is required.", "error")
        if parent_id:
            return redirect(url_for("office.index", folder=parent_id))
        return redirect(url_for("office.index"))
    
    # Check if folder with same name exists in parent
    existing = OfficeFolder.query.filter_by(name=name, parent_id=parent_id).first()
    if existing:
        flash("A folder with this name already exists.", "error")
        if parent_id:
            return redirect(url_for("office.index", folder=parent_id))
        return redirect(url_for("office.index"))
    
    try:
        folder = OfficeFolder(
            name=name,
            parent_id=parent_id,
            created_by=current_user.id,
        )
        db.session.add(folder)
        db.session.commit()
        
        flash(f"Folder '{name}' created successfully.", "success")
        current_app.logger.info(f"Folder '{name}' created by user {current_user.id} in parent {parent_id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating folder: {e}")
        flash(f"Error creating folder: {str(e)}", "error")
    
    if parent_id:
        return redirect(url_for("office.index", folder=parent_id))
    return redirect(url_for("office.index"))


@office_bp.route("/file/upload", methods=["POST"])
@login_required
def upload_file():
    """Upload file(s) to SAS Office. Supports multiple files and ZIP extraction.
    
    ACCEPTS ALL FILE FORMATS - No restrictions on file types or extensions.
    Files are organized by type (document, image, video, audio, archive) for better organization,
    but any file format can be uploaded regardless of extension.
    """
    folder_id_str = request.form.get("folder_id", "").strip()
    
    # Handle empty string or None for folder_id
    folder_id = None
    if folder_id_str:
        try:
            folder_id = int(folder_id_str)
        except (ValueError, TypeError):
            folder_id = None
    
    description = request.form.get("description", "").strip()
    extract_zip = request.form.get("extract_zip", "false").lower() == "true"
    
    # Handle multiple files (from 'file' field, can be multiple)
    files = request.files.getlist("file")
    
    if not files or not any(f.filename for f in files):
        flash("No file selected.", "error")
        if folder_id:
            return redirect(url_for("office.index", folder=folder_id))
        return redirect(url_for("office.index"))
    
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    base_dir = _office_uploads_dir()
    uploaded_count = 0
    extracted_count = 0
    errors = []
    
    for file in files:
        if not file.filename:
            continue
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            errors.append(f"{file.filename} is too large (max {MAX_FILE_SIZE / (1024*1024):.0f}MB)")
            continue
        
        try:
            # Save file - ACCEPTS ALL FILE FORMATS (no restrictions)
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
            # Generate unique filename preserving extension (or no extension if file has none)
            unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
            
            # Organize by type (for organization only - does NOT restrict file types)
            file_type = _infer_file_type(original_filename)
            type_folder = os.path.join(base_dir, file_type)
            os.makedirs(type_folder, exist_ok=True)
            
            file_path = os.path.join(type_folder, unique_filename)
            
            # Ensure directory exists before saving
            os.makedirs(type_folder, exist_ok=True)
            
            # Save the file
            file.save(file_path)
            
            # Verify file was saved
            if not os.path.exists(file_path):
                raise Exception(f"File was not saved to {file_path}")
            
            # Handle ZIP file extraction if requested
            if file_type == "archive" and ext == "zip" and extract_zip:
                try:
                    extracted = _extract_zip_file(file_path, folder_id, current_user.id, base_dir)
                    extracted_count += extracted
                    # Also keep the ZIP file itself
                    relative_path = os.path.join("office_uploads", file_type, unique_filename)
                    office_file = OfficeFile(
                        name=original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename,
                        original_filename=original_filename,
                        file_path=relative_path,
                        file_size=file_size,
                        file_type=file_type,
                        folder_id=folder_id,
                        uploaded_by=current_user.id,
                        description=description,
                    )
                    db.session.add(office_file)
                    uploaded_count += 1
                except Exception as e:
                    current_app.logger.exception(f"Error extracting ZIP file {file.filename}: {e}")
                    errors.append(f"Failed to extract {file.filename}: {str(e)}")
                    # Still save the ZIP file even if extraction fails
                    relative_path = os.path.join("office_uploads", file_type, unique_filename)
                    office_file = OfficeFile(
                        name=original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename,
                        original_filename=original_filename,
                        file_path=relative_path,
                        file_size=file_size,
                        file_type=file_type,
                        folder_id=folder_id,
                        uploaded_by=current_user.id,
                        description=description,
                    )
                    db.session.add(office_file)
                    uploaded_count += 1
            else:
                # Store relative path
                relative_path = os.path.join("office_uploads", file_type, unique_filename)
                
                # Create database record
                office_file = OfficeFile(
                    name=original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename,
                    original_filename=original_filename,
                    file_path=relative_path,
                    file_size=file_size,
                    file_type=file_type,
                    folder_id=folder_id,
                    uploaded_by=current_user.id,
                    description=description,
                )
                db.session.add(office_file)
                uploaded_count += 1
                current_app.logger.info(f"File uploaded to SAS Office: {original_filename} (saved as {unique_filename}) by user {current_user.id} to {file_path}")
                
                # Verify file exists on disk
                if not os.path.exists(file_path):
                    raise Exception(f"File was not saved correctly to {file_path}")
        except Exception as e:
            current_app.logger.exception(f"Error uploading file {file.filename}: {e}")
            errors.append(f"Failed to upload {file.filename}: {str(e)}")
    
    # Commit all database changes
    try:
        if uploaded_count > 0:
            db.session.commit()
            current_app.logger.info(f"Committed {uploaded_count} file(s) to database successfully")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error committing files to database: {e}")
        errors.append(f"Database error: {str(e)}")
    
    # Show success/error messages
    if uploaded_count > 0:
        if extracted_count > 0:
            flash(f"{uploaded_count} file(s) uploaded and stored successfully. {extracted_count} file(s) extracted from ZIP.", "success")
        else:
            flash(f"{uploaded_count} file(s) uploaded and stored successfully.", "success")
    if errors:
        for err in errors:
            flash(err, "error")
    
    if folder_id:
        return redirect(url_for("office.index", folder=folder_id))
    return redirect(url_for("office.index"))


def _extract_zip_file(zip_path, target_folder_id, user_id, base_dir):
    """Extract ZIP file contents to the file manager.
    
    Returns:
        int: Number of files extracted
    """
    extracted_count = 0
    max_extract_size = 100 * 1024 * 1024  # 100MB total extraction limit
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check total extraction size
            total_size = sum(info.file_size for info in zip_ref.infolist())
            if total_size > max_extract_size:
                raise ValueError(f"ZIP file too large to extract (max {max_extract_size / (1024*1024):.0f}MB)")
            
            # Extract all files
            for member in zip_ref.infolist():
                # Skip directories
                if member.filename.endswith('/'):
                    continue
                
                # Security: Skip files with absolute paths or dangerous paths
                if os.path.isabs(member.filename) or '..' in member.filename:
                    current_app.logger.warning(f"Skipping potentially dangerous file in ZIP: {member.filename}")
                    continue
                
                try:
                    # Extract file to temporary location first
                    safe_name = secure_filename(os.path.basename(member.filename))
                    if not safe_name:
                        safe_name = f"extracted_{uuid.uuid4().hex}"
                    
                    # Determine file type
                    file_type = _infer_file_type(safe_name)
                    type_folder = os.path.join(base_dir, file_type)
                    os.makedirs(type_folder, exist_ok=True)
                    
                    # Generate unique filename
                    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
                    unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
                    extract_path = os.path.join(type_folder, unique_filename)
                    
                    # Extract file
                    with zip_ref.open(member) as source:
                        with open(extract_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    
                    # Get file size
                    file_size = os.path.getsize(extract_path)
                    
                    # Create database record
                    relative_path = os.path.join("office_uploads", file_type, unique_filename)
                    office_file = OfficeFile(
                        name=safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name,
                        original_filename=safe_name,
                        file_path=relative_path,
                        file_size=file_size,
                        file_type=file_type,
                        folder_id=target_folder_id,
                        uploaded_by=user_id,
                        description=f"Extracted from ZIP: {os.path.basename(zip_path)}",
                    )
                    db.session.add(office_file)
                    extracted_count += 1
                    
                except Exception as e:
                    current_app.logger.warning(f"Error extracting file {member.filename} from ZIP: {e}")
                    continue
            
            db.session.flush()  # Flush to get IDs but don't commit yet
            
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file format")
    except Exception as e:
        raise ValueError(f"Error extracting ZIP: {str(e)}")
    
    return extracted_count


@office_bp.route("/file/<int:file_id>/download")
@login_required
def download_file(file_id):
    """Download a file - FORCES download for ALL file types.
    
    CRITICAL: This route ALWAYS downloads files. It is the ONLY way to download files.
    The View button route (view_file) NEVER downloads files.
    """
    office_file = get_or_404(OfficeFile, file_id)
    base_dir = _office_uploads_dir()
    
    # Handle both relative paths (office_uploads/...) and absolute paths
    if office_file.file_path.startswith("office_uploads/"):
        full_path = os.path.join(base_dir, office_file.file_path.replace("office_uploads/", ""))
    else:
        # If it's already a relative path without prefix, join directly
        full_path = os.path.join(base_dir, office_file.file_path)
    
    if not os.path.exists(full_path):
        flash("File not found on server.", "error")
        return redirect(url_for("office.index"))
    
    mime_type = _get_mime_type(office_file.original_filename)
    
    # CRITICAL: FORCE download for ALL file types - this is the download route
    # as_attachment MUST be True to force download
    as_attachment = True
    
    # Create response with forced download
    response = send_file(
        full_path,
        as_attachment=as_attachment,  # ALWAYS True for download route
        download_name=office_file.original_filename,  # Always set download name
        mimetype=mime_type,
    )
    
    # CRITICAL: Explicitly set Content-Disposition: attachment to FORCE download
    # This ensures the file is ALWAYS downloaded, never displayed
    from urllib.parse import quote
    safe_filename = quote(office_file.original_filename, safe='')
    response.headers['Content-Disposition'] = f'attachment; filename="{office_file.original_filename}"; filename*=UTF-8\'\'{safe_filename}'
    
    # Ensure Content-Type is set correctly
    response.headers['Content-Type'] = mime_type
    
    current_app.logger.info(f"FORCING DOWNLOAD of file: {office_file.original_filename}")
    
    return response


@office_bp.route("/file/<int:file_id>/view")
@login_required
def view_file(file_id):
    """View a file - displays in browser (not downloaded).
    
    CRITICAL: This route serves files with Content-Disposition: inline to ensure
    files are DISPLAYED in the browser, not downloaded.
    
    Behavior:
    - PDFs, images, text files, HTML: Display directly in browser
    - Office documents (Excel, Word, PowerPoint): Open in native applications (not downloaded)
    - Other files: Open in associated applications (not downloaded)
    
    Files are served with:
    - Content-Disposition: inline (prevents downloads)
    - Proper MIME types for correct browser/OS handling
    - X-Content-Type-Options: nosniff (prevents MIME sniffing)
    """
    office_file = get_or_404(OfficeFile, file_id)
    base_dir = _office_uploads_dir()
    
    # Resolve file path - handle multiple path formats
    file_path = office_file.file_path
    
    # CRITICAL: Normalize path separators - handle both / and \ (Windows vs Unix)
    # Files might be stored with either forward slashes or backslashes
    # On Windows, paths might be stored with backslashes, so normalize to forward slashes
    file_path_normalized = file_path.replace(os.sep, "/")  # Convert OS-specific separators to forward slashes
    if "\\" in file_path_normalized:  # Also handle literal backslashes
        file_path_normalized = file_path_normalized.replace("\\", "/")
    
    # CRITICAL: Files are stored with path like "office_uploads/document/unique_filename.xlsx"
    # We need to resolve this to the actual file location
    # The base_dir is: {instance_path}/office_uploads
    # So "office_uploads/document/file.xlsx" should resolve to: {instance_path}/office_uploads/document/file.xlsx
    
    # Try multiple path resolution strategies
    possible_paths = []
    
    # Strategy 1: Remove "office_uploads/" or "office_uploads\" prefix and join with base_dir
    # This is the most common case - files stored as "office_uploads/{type}/{filename}"
    clean_path = None
    if file_path_normalized.startswith("office_uploads/"):
        clean_path = file_path_normalized.replace("office_uploads/", "", 1)
        possible_paths.append(os.path.normpath(os.path.join(base_dir, clean_path)))
    
    # Strategy 2: If path doesn't start with "office_uploads/", try joining directly
    # Some files might be stored as just "{type}/{filename}"
    if clean_path:
        possible_paths.append(os.path.normpath(os.path.join(base_dir, clean_path)))
    else:
        possible_paths.append(os.path.normpath(os.path.join(base_dir, file_path_normalized)))
    
    # Strategy 3: Try with instance_path directly (in case base_dir calculation is wrong)
    instance_base = current_app.instance_path
    if clean_path:
        possible_paths.append(os.path.normpath(os.path.join(instance_base, "office_uploads", clean_path)))
    else:
        possible_paths.append(os.path.normpath(os.path.join(instance_base, "office_uploads", file_path_normalized)))
    
    # Strategy 4: If path is absolute and within base_dir, use it directly
    if os.path.isabs(file_path):
        if base_dir in file_path or instance_base in file_path:
            possible_paths.append(os.path.normpath(file_path))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_paths = []
    for path in possible_paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    possible_paths = unique_paths
    
    # Find the first path that exists and is a file
    full_path = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            full_path = path
            current_app.logger.info(f"Found file at: {full_path}")
            break
    
    # FALLBACK: If file not found by path, try searching by filename
    # This handles cases where the stored path might be incorrect but the file exists
    if not full_path and base_dir and os.path.exists(base_dir):
        try:
            # Extract the unique filename from the stored path (UUID-based)
            # Files are stored as "office_uploads/{type}/{uuid}.{ext}"
            # Use the already normalized path from above
            if "/" in file_path_normalized:
                unique_filename = file_path_normalized.split("/")[-1]  # Get the UUID filename
            else:
                unique_filename = file_path_normalized
            
            # Also try matching by original filename (case-insensitive)
            original_filename_lower = office_file.original_filename.lower()
            
            current_app.logger.info(
                f"Searching for file: unique_filename={unique_filename}, "
                f"original_filename={office_file.original_filename}"
            )
            
            # Search in all subdirectories
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    file_lower = file.lower()
                    # Match by unique filename (UUID) - this is the most reliable
                    if file == unique_filename:
                        candidate_path = os.path.join(root, file)
                        if os.path.isfile(candidate_path):
                            full_path = candidate_path
                            current_app.logger.warning(
                                f"File found by UUID search: "
                                f"Stored path={office_file.file_path}, "
                                f"Found at={full_path}"
                            )
                            break
                    # Also try matching by original filename (case-insensitive)
                    elif file_lower == original_filename_lower:
                        candidate_path = os.path.join(root, file)
                        if os.path.isfile(candidate_path):
                            full_path = candidate_path
                            current_app.logger.warning(
                                f"File found by original filename search: "
                                f"Original={office_file.original_filename}, "
                                f"Found at={full_path}"
                            )
                            break
                if full_path:
                    break
        except Exception as e:
            current_app.logger.exception(f"Error during file search fallback: {e}")
    
    # Log path resolution for debugging
    current_app.logger.info(
        f"Opening file: ID={file_id}, "
        f"Original filename={office_file.original_filename}, "
        f"Stored path={office_file.file_path}, "
        f"Base dir={base_dir}, "
        f"Tried paths={possible_paths}, "
        f"Found path={full_path}"
    )
    
    # Verify file exists - log detailed error if not found
    if not full_path or not os.path.exists(full_path):
        # Last resort: Try to find ANY file with matching extension in the upload directory
        if base_dir and os.path.exists(base_dir):
            try:
                ext = office_file.original_filename.rsplit(".", 1)[-1].lower() if "." in office_file.original_filename else ""
                if ext:
                    # Search for any file with the same extension that might be the one
                    for root, dirs, files in os.walk(base_dir):
                        for file in files:
                            if file.lower().endswith(f".{ext.lower()}"):
                                # Check file size as additional verification
                                candidate_path = os.path.join(root, file)
                                try:
                                    candidate_size = os.path.getsize(candidate_path)
                                    # If file size matches (within 1KB tolerance), it might be the file
                                    if abs(candidate_size - office_file.file_size) < 1024:
                                        full_path = candidate_path
                                        current_app.logger.warning(
                                            f"File found by extension and size match: "
                                            f"Original={office_file.original_filename}, "
                                            f"Found={file}, Size match: {candidate_size} vs {office_file.file_size}, "
                                            f"Path={full_path}"
                                        )
                                        break
                                except:
                                    pass
                        if full_path:
                            break
            except Exception as e:
                current_app.logger.warning(f"Error during extension-based search: {e}")
        
        # If still not found, log detailed error
        if not full_path or not os.path.exists(full_path):
            # List files in base_dir for debugging
            debug_info = f"Base dir exists: {os.path.exists(base_dir)}, Base dir: {base_dir}"
            if os.path.exists(base_dir):
                try:
                    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
                    debug_info += f", Subdirectories: {subdirs}"
                    # Try to find the file in subdirectories
                    for subdir in subdirs:
                        subdir_path = os.path.join(base_dir, subdir)
                        if os.path.isdir(subdir_path):
                            files_in_subdir = [f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))]
                            if files_in_subdir:
                                debug_info += f", Files in {subdir}: {files_in_subdir[:5]}"  # Show first 5 files
                except Exception as e:
                    debug_info += f", Error listing dir: {str(e)}"
            
            current_app.logger.error(
                f"File not found for OfficeFile ID {file_id}: "
                f"Original filename={office_file.original_filename}, "
                f"Stored path={office_file.file_path}, "
                f"File size={office_file.file_size}, "
                f"Base dir={base_dir}, "
                f"Instance path={current_app.instance_path}, "
                f"Tried paths={possible_paths}, "
                f"{debug_info}"
            )
            # Don't return JSON - always redirect to avoid JSON error display
            flash(f"File not found: {office_file.original_filename}. Please check server logs for details.", "error")
            return redirect(url_for("office.index"))
    
    # Verify it's actually a file (not a directory)
    if not os.path.isfile(full_path):
        current_app.logger.error(f"Path is not a file: {full_path}")
        flash(f"Path is not a file: {office_file.original_filename}", "error")
        return redirect(url_for("office.index"))
    
    mime_type = _get_mime_type(office_file.original_filename)
    ext = office_file.original_filename.rsplit(".", 1)[-1].lower() if "." in office_file.original_filename else ""
    
    # Files that should open in native applications (for viewing/editing)
    # Use inline disposition so browser/OS opens them in the appropriate app
    # Excel files (.xlsx, .xls, .xlsm, .xlsb) are included and will open in Microsoft Excel
    native_app_extensions = {
        # Office documents (Excel, Word, PowerPoint)
        # Excel formats: xlsx, xls, xlsm, xlsb - all open in Microsoft Excel
        "doc", "docx", "xls", "xlsx", "ppt", "pptx", "xlsm", "xlsb", "docm",
        "dotx", "dotm", "pptm", "potx", "potm", "ppsm", "sldx", "sldm",
        # OpenOffice
        "odt", "ods", "odp", "odg", "odf",
        # PDF
        "pdf",
        # Text files
        "txt", "rtf", "csv",
        # Images
        "png", "jpg", "jpeg", "gif", "webp", "bmp", "svg", "ico", "tiff", "tif",
        # Videos
        "mp4", "avi", "mov", "wmv", "flv", "webm", "mkv", "m4v", "3gp",
        # Audio
        "mp3", "wav", "ogg", "m4a", "aac", "flac", "wma",
        # Code files
        "html", "htm", "css", "js", "json", "xml", "py", "java", "c", "cpp", "cs",
    }
    
    # Always use inline for view route - let browser/OS handle opening in native app
    # This allows Excel files to open in Excel, Word files in Word, PDFs in PDF viewer, etc.
    # IMPORTANT: All files should display inline (not download) when using the View button
    # CRITICAL: as_attachment MUST be False to prevent downloads
    as_attachment = False
    
    # Use send_file with proper parameters for native app opening
    # CRITICAL: as_attachment=False means Content-Disposition: inline
    # This tells the browser to open the file in the associated application
    try:
        # For Excel and PDF files, NEVER set download_name to prevent forced downloads
        # Setting download_name=None ensures Flask doesn't add attachment headers
        download_name_param = None  # Always None for view route to prevent downloads
        
        response = send_file(
            full_path,
            as_attachment=False,  # ALWAYS False for view route - never download
            download_name=None,  # None = don't force download name, prevents download prompts
            mimetype=mime_type,
        )
        current_app.logger.info(
            f"Successfully serving file for viewing: {office_file.original_filename} "
            f"(MIME: {mime_type}, Path: {full_path}, Size: {os.path.getsize(full_path)} bytes)"
        )
    except FileNotFoundError:
        current_app.logger.error(f"File not found: {full_path}")
        flash(f"File not found: {office_file.original_filename}", "error")
        return redirect(url_for("office.index"))
    except Exception as e:
        current_app.logger.exception(f"Error serving file {office_file.original_filename}: {e}")
        flash(f"Error opening file: {str(e)}", "error")
        return redirect(url_for("office.index"))
    
    # ========================================================================
    # CRITICAL: FORCE DISPLAY ONLY - NO DOWNLOADS ALLOWED
    # ========================================================================
    # This route is for VIEWING files only. It MUST NEVER download files.
    # The download_file route is the ONLY route that downloads files.
    # ========================================================================
    
    from urllib.parse import quote
    safe_filename = quote(office_file.original_filename, safe='')
    
    # FORCE Content-Disposition: inline - this PREVENTS downloads
    # This is the PRIMARY safeguard against downloads
    # For Excel and PDF, use simple 'inline' without filename to prevent download prompts
    if ext in ['xlsx', 'xls', 'xlsm', 'xlsb', 'pdf']:
        response.headers['Content-Disposition'] = 'inline'
    else:
        response.headers['Content-Disposition'] = f'inline; filename="{office_file.original_filename}"; filename*=UTF-8\'\'{safe_filename}'
    
    # Prevent MIME type sniffing to ensure browser respects our Content-Type
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Ensure MIME type is correct - this is critical for browser to display files correctly
    response.headers['Content-Type'] = mime_type
    
    # Files that can be displayed directly in browser
    browser_displayable = {
        'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'ico', 'tiff', 'tif',
        'txt', 'html', 'htm', 'css', 'js', 'json', 'xml', 'csv',
        'mp4', 'webm', 'ogg', 'mp3', 'wav'
    }
    
    # Special handling for different file types - ALL set to inline (no download)
    if ext in ['xlsx', 'xls', 'xlsm', 'xlsb']:
        # Excel files - set proper MIME type, browser will open in Excel (NOT download)
        if ext == 'xlsx':
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif ext == 'xls':
            response.headers['Content-Type'] = 'application/vnd.ms-excel'
        elif ext == 'xlsm':
            response.headers['Content-Type'] = 'application/vnd.ms-excel.sheet.macroEnabled.12'
        elif ext == 'xlsb':
            response.headers['Content-Type'] = 'application/vnd.ms-excel.sheet.binary.macroEnabled.12'
        # CRITICAL: Force inline for Excel files - prevents download, opens in Excel
        # Remove filename from Content-Disposition to prevent download prompts
        response.headers['Content-Disposition'] = 'inline'
        # Additional headers to prevent download
        response.headers['X-Download-Options'] = 'noopen'
        response.headers['X-Content-Disposition'] = 'inline'
        # Remove any download-related headers
        if 'Content-Disposition' in response.headers and 'attachment' in response.headers['Content-Disposition']:
            response.headers['Content-Disposition'] = 'inline'
        current_app.logger.info(f"VIEW ONLY - Excel file will open in Excel application (NO DOWNLOAD): {office_file.original_filename}")
    elif ext == 'pdf':
        # PDF files - ensure they open in browser PDF viewer (inline display)
        response.headers['Content-Type'] = 'application/pdf'
        # CRITICAL: Force inline for PDF files - ensures browser displays them, not downloads
        # Use inline without filename to prevent download prompts
        response.headers['Content-Disposition'] = 'inline'
        # Additional headers to prevent download
        response.headers['X-Download-Options'] = 'noopen'
        response.headers['X-Content-Disposition'] = 'inline'
        # Ensure PDF is displayed, not downloaded
        if 'Content-Disposition' in response.headers and 'attachment' in response.headers['Content-Disposition']:
            response.headers['Content-Disposition'] = 'inline'
        current_app.logger.info(f"VIEW ONLY - PDF file will display in browser viewer (NO DOWNLOAD): {office_file.original_filename}")
    elif ext in ['docx', 'doc']:
        # Word files - set proper MIME type, browser will open in Word (NOT download)
        if ext == 'docx':
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif ext == 'doc':
            response.headers['Content-Type'] = 'application/msword'
        current_app.logger.info(f"VIEW ONLY - Word file will open in Word (NO DOWNLOAD): {office_file.original_filename}")
    elif ext in ['pptx', 'ppt']:
        # PowerPoint files - set proper MIME type, browser will open in PowerPoint (NOT download)
        if ext == 'pptx':
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        elif ext == 'ppt':
            response.headers['Content-Type'] = 'application/vnd.ms-powerpoint'
        current_app.logger.info(f"VIEW ONLY - PowerPoint file will open in PowerPoint (NO DOWNLOAD): {office_file.original_filename}")
    elif ext in browser_displayable:
        # Files that can display directly in browser (PDF, images, text, etc.)
        current_app.logger.info(f"VIEW ONLY - File will display in browser (NO DOWNLOAD): {office_file.original_filename} (MIME: {mime_type})")
    else:
        # Other file types - will open in associated application (NOT download)
        current_app.logger.info(f"VIEW ONLY - File will open in associated app (NO DOWNLOAD): {office_file.original_filename} (MIME: {mime_type})")
    
    # ========================================================================
    # MULTIPLE SAFEGUARDS TO PREVENT DOWNLOADS
    # ========================================================================
    
    # Safeguard 1: Verify Content-Disposition is inline (not attachment)
    if 'Content-Disposition' in response.headers:
        if 'attachment' in response.headers['Content-Disposition']:
            # FORCE it back to inline - this should never happen, but we're being extra safe
            current_app.logger.error(f"SECURITY: view_file route had attachment header! Forcing to inline for {office_file.original_filename}")
            response.headers['Content-Disposition'] = response.headers['Content-Disposition'].replace('attachment', 'inline')
    
    # Safeguard 2: Remove any download-related query parameters or headers
    # Ensure no download triggers exist
    
    # Safeguard 3: Explicitly verify as_attachment was False
    # (This is already set above, but we log it for verification)
    current_app.logger.info(f"VIEW ROUTE VERIFICATION: File {office_file.original_filename} - as_attachment={as_attachment}, Content-Disposition={response.headers.get('Content-Disposition', 'NOT SET')}")
    
    # Final verification: Content-Disposition MUST be inline
    final_disposition = response.headers.get('Content-Disposition', '')
    if 'attachment' in final_disposition.lower():
        # This should NEVER happen - log error and force fix
        current_app.logger.critical(f"CRITICAL ERROR: view_file route attempting to download {office_file.original_filename}! Forcing inline.")
        # For Excel and PDF, use simple 'inline' without filename
        if ext in ['xlsx', 'xls', 'xlsm', 'xlsb', 'pdf']:
            response.headers['Content-Disposition'] = 'inline'
        else:
            response.headers['Content-Disposition'] = f'inline; filename="{office_file.original_filename}"; filename*=UTF-8\'\'{safe_filename}'
    
    return response


@office_bp.route("/file/<int:file_id>/delete", methods=["POST", "DELETE"])
@login_required
@role_required(UserRole.Admin)
def delete_file(file_id):
    """Delete a file. Admin only."""
    office_file = get_or_404(OfficeFile, file_id)
    folder_id = office_file.folder_id
    
    # Delete physical file
    base_dir = _office_uploads_dir()
    # Handle both relative paths (office_uploads/...) and absolute paths
    if office_file.file_path.startswith("office_uploads/"):
        full_path = os.path.join(base_dir, office_file.file_path.replace("office_uploads/", ""))
    else:
        full_path = os.path.join(base_dir, office_file.file_path)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        current_app.logger.warning(f"Could not delete file: {e}")
    
    db.session.delete(office_file)
    db.session.commit()
    
    flash("File deleted successfully.", "success")
    if folder_id:
        return redirect(url_for("office.index", folder=folder_id))
    return redirect(url_for("office.index"))


@office_bp.route("/folder/<int:folder_id>/delete", methods=["POST", "DELETE"])
@login_required
@role_required(UserRole.Admin)
def delete_folder(folder_id):
    """Delete a folder. Admin only. Must be empty."""
    folder = get_or_404(OfficeFolder, folder_id)
    parent_id = folder.parent_id
    
    # Check if folder is empty
    if folder.subfolders or folder.files:
        flash("Cannot delete folder. It must be empty.", "error")
        if parent_id:
            return redirect(url_for("office.index", folder=parent_id))
        return redirect(url_for("office.index"))
    
    db.session.delete(folder)
    db.session.commit()
    
    flash("Folder deleted successfully.", "success")
    if parent_id:
        return redirect(url_for("office.index", folder=parent_id))
    return redirect(url_for("office.index"))


@office_bp.route("/api/search")
@login_required
def api_search():
    """Search for files and folders."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"files": [], "folders": []})
    
    # Search files
    files = OfficeFile.query.filter(
        OfficeFile.name.ilike(f"%{query}%") | OfficeFile.original_filename.ilike(f"%{query}%")
    ).limit(50).all()
    
    # Search folders
    folders = OfficeFolder.query.filter(OfficeFolder.name.ilike(f"%{query}%")).limit(20).all()
    
    return jsonify({
        "files": [
            {
                "id": f.id,
                "name": f.name,
                "original_filename": f.original_filename,
                "file_type": f.file_type,
                "folder_id": f.folder_id,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in files
        ],
        "folders": [
            {
                "id": f.id,
                "name": f.name,
                "parent_id": f.parent_id,
            }
            for f in folders
        ],
    })
