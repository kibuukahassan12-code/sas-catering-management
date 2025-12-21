import os
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for, jsonify, send_file, abort
from flask_login import current_user, login_required

from sas_management.models import (
    Course, Material, UserRole, db, Lesson, LessonResource, Enrollment,
    Quiz, QuizQuestion, QuizAttempt, QuizAnswer, Certificate, CourseProgress, User
)
from sas_management.utils import role_required, paginate_query

def require_university_enabled(f):
    """Decorator to require Employee University module to be enabled."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get("EMPLOYEE_UNIVERSITY_ENABLED", True):
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({"error": "Employee University is disabled"}), 403
            return render_template("university/premium_locked.html"), 403
        return f(*args, **kwargs)
    return decorated_function

from sas_management.services.university_service import (
    create_course,
    add_lesson,
    upload_resource,
    enroll_user,
    record_progress,
    submit_quiz,
    generate_certificate,
    get_user_courses
)

university_bp = Blueprint("university", __name__, url_prefix="/university")

def get_upload_folder():
    """Get the upload folder path, creating it if it doesn't exist."""
    upload_folder = os.path.join(current_app.instance_path, "..", current_app.config.get("UPLOAD_FOLDER", "files"))
    upload_folder = os.path.abspath(upload_folder)
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

@university_bp.route("/", endpoint="index")
@university_bp.route("/dashboard", endpoint="dashboard")
@login_required
@require_university_enabled
def university_dashboard():
    """Main employee view - shows courses available to the current user's role."""
    try:
        # Safe query - only use existing fields
        courses = Course.query.filter(Course.published == True).order_by(Course.title.asc()).limit(6).all()
        return render_template("university/university_dashboard.html", courses=courses)
    except Exception as e:
        current_app.logger.exception(f"Error loading university dashboard: {e}")
        return render_template("university/university_dashboard.html", courses=[])

# Alias for compatibility
dashboard = university_dashboard

@university_bp.route("/upload", methods=["GET", "POST"])
@login_required
@require_university_enabled
def upload():
    """Upload university material."""
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("No file selected", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        save_path = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "university",
            filename
        )
        file.save(save_path)
        flash("File uploaded successfully", "success")
        return redirect(url_for("university.dashboard"))

    return render_template("university/upload.html")

@university_bp.route("/course/<int:course_id>")
@university_bp.route("/courses/<int:course_id>")
@login_required
def employee_course_detail(course_id):
    """View course details and materials for employees."""
    try:
        course = Course.query.get_or_404(course_id)
        
        # Check access: course must be published
        if not course.published:
            flash("This course is not available.", "warning")
            return redirect(url_for("university.employee_course_list"))
        
        # Get materials for this course
        materials = Material.query.filter_by(course_id=course_id).order_by(Material.order_index.asc()).all()
        
        # Check if user is enrolled
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        # Create enrollment if viewing for first time
        if not enrollment:
            enrollment = Enrollment(
                user_id=current_user.id,
                course_id=course_id
            )
            db.session.add(enrollment)
            db.session.commit()
        
        # Check completion status
        is_completed = enrollment.completed_at is not None
        
        return render_template(
            "university/employee_course_detail.html",
            course=course,
            materials=materials,
            enrollment=enrollment,
            is_completed=is_completed
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading course: {e}")
        flash("Error loading course.", "danger")
        return redirect(url_for("university.employee_course_list"))

@university_bp.route("/course/<int:course_id>/complete", methods=["POST"])
@login_required
def mark_course_complete(course_id):
    """Mark a course as complete for the current user."""
    try:
        course = Course.query.get_or_404(course_id)
        if not course.published:
            flash("Course not available.", "warning")
            return redirect(url_for("university.employee_course_list"))
        
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        if not enrollment:
            flash("You are not enrolled in this course.", "warning")
            return redirect(url_for("university.employee_course_detail", course_id=course_id))
        
        if enrollment.completed_at is None:
            enrollment.completed_at = datetime.utcnow()
            db.session.commit()
            flash("Course marked as complete!", "success")
        else:
            flash("Course already completed.", "info")
        
        return redirect(url_for("university.employee_course_detail", course_id=course_id))
    except Exception as e:
        current_app.logger.exception(f"Error marking course complete: {e}")
        flash("Error updating course status.", "danger")
        return redirect(url_for("university.employee_course_list"))

@university_bp.route("/course/<int:course_id>/certificate")
@login_required
def view_certificate_employee(course_id):
    """View certificate for completed course (HTML only, no PDF)."""
    try:
        course = Course.query.get_or_404(course_id)
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        if not enrollment or not enrollment.completed_at:
            flash("Course must be completed to view certificate.", "warning")
            return redirect(url_for("university.employee_course_detail", course_id=course_id))
        
        return render_template(
            "university/certificate.html",
            course=course,
            enrollment=enrollment,
            user=current_user
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading certificate: {e}")
        flash("Error loading certificate.", "danger")
        return redirect(url_for("university.employee_course_list"))

@university_bp.route("/material/<int:material_id>")
@login_required
def view_material(material_id):
    """View material details."""
    try:
        material = Material.query.get_or_404(material_id)
        
        # Check course is published
        if not material.course.published:
            flash("This material is not available.", "warning")
            return redirect(url_for("university.employee_course_list"))
        
        return render_template("university/material_view.html", material=material)
    except Exception as e:
        current_app.logger.exception(f"Error loading material: {e}")
        return redirect(url_for("university.employee_course_list"))

@university_bp.route("/material/<int:material_id>/download")
@login_required
def download_material(material_id):
    """Download a material file (protected route)."""
    try:
        material = Material.query.get_or_404(material_id)
        
        # Check course is published
        if not material.course.published:
            flash("This material is not available.", "warning")
            return redirect(url_for("university.employee_course_list"))
        
        # Get file path
        if material.file_path:
            # Try static folder first
            static_path = os.path.join(current_app.root_path, "static", material.file_path)
            if os.path.exists(static_path):
                return send_from_directory(
                    os.path.dirname(static_path),
                    os.path.basename(static_path),
                    as_attachment=True
                )
            
            # Try upload folder
            upload_folder = get_upload_folder()
            file_path = os.path.join(upload_folder, os.path.basename(material.file_path))
            if os.path.exists(file_path):
                return send_from_directory(
                    upload_folder,
                    os.path.basename(material.file_path),
                    as_attachment=True
                )
        
        flash("File not found.", "warning")
        return redirect(url_for("university.view_material", material_id=material_id))
    except Exception as e:
        current_app.logger.exception(f"Error downloading material: {e}")
        flash("Error downloading file.", "danger")
        return redirect(url_for("university.employee_course_list"))

# Admin routes
@university_bp.route("/admin/courses")
@login_required
@role_required(UserRole.Admin)
def admin_course_list():
    """Admin: List all courses."""
    pagination = paginate_query(Course.query.order_by(Course.title.asc()))
    return render_template(
        "university/admin/courses.html",
        courses=pagination.items,
        pagination=pagination,
    )

# Route alias for compatibility
admin_courses_list = admin_course_list

@university_bp.route("/admin/courses/add", methods=["GET", "POST"])
@university_bp.route("/admin/course/new", methods=["GET", "POST"], endpoint="admin_course_create")
@login_required
@role_required(UserRole.Admin)
def admin_courses_add():
    """Admin: Add a new course."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        published = request.form.get("published") == "on" or request.form.get("published") == "true"

        if not title:
            flash("Title is required.", "danger")
            return render_template(
                "university/admin/course_form.html",
                action="Add",
                course=None,
            )

        course = Course(
            title=title,
            description=description,
            published=published
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created successfully.", "success")
        return redirect(url_for("university.admin_course_list"))

    return render_template(
        "university/admin/course_form.html",
        action="Add",
        course=None,
    )

# Route alias for requested endpoint name
admin_course_create = admin_courses_add

@university_bp.route("/admin/courses/edit/<int:course_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin)
def admin_courses_edit(course_id):
    """Admin: Edit an existing course."""
    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        course.title = request.form.get("title", course.title).strip()
        course.description = request.form.get("description", course.description).strip()
        course.published = request.form.get("published") == "on" or request.form.get("published") == "true"

        try:
            db.session.commit()
            flash("Course updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating course: {e}")
            flash("Error updating course.", "danger")
        
        return redirect(url_for("university.admin_course_list"))

    return render_template(
        "university/admin/course_form.html",
        action="Edit",
        course=course,
    )

@university_bp.route("/admin/course/<int:id>/materials", endpoint="admin_course_materials")
@login_required
@role_required(UserRole.Admin)
def admin_course_materials(id):
    """Admin: View and manage materials for a course."""
    course = Course.query.get_or_404(id)
    materials = Material.query.filter_by(course_id=id).order_by(Material.order_index.asc()).all()
    return render_template(
        "university/admin/course_materials.html",
        course=course,
        materials=materials
    )

@university_bp.route("/admin/courses/delete/<int:course_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def admin_courses_delete(course_id):
    """Admin: Delete a course."""
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("university.admin_course_list"))

# Admin progress view
@university_bp.route("/admin/progress")
@login_required
@role_required(UserRole.Admin)
def admin_progress():
    """Admin: View employee course progress."""
    try:
        # Get all employees (users, excluding admins)
        employees = User.query.filter(User.role != UserRole.Admin).all()
        
        progress_data = []
        for employee in employees:
            # Get enrollments for this employee
            enrollments = Enrollment.query.filter_by(user_id=employee.id).all()
            
            enrolled_count = len(enrollments)
            # Check completion: completed_at is not None means completed
            completed_count = len([e for e in enrollments if e.completed_at is not None])
            
            # Calculate progress percentage
            if enrolled_count > 0:
                progress_percent = (completed_count / enrolled_count) * 100
            else:
                progress_percent = 0
            
            progress_data.append({
                'employee': employee,
                'enrolled_count': enrolled_count,
                'completed_count': completed_count,
                'progress_percent': round(progress_percent, 1)
            })
        
        # Sort by progress percentage (descending)
        progress_data.sort(key=lambda x: x['progress_percent'], reverse=True)
        
        return render_template(
            "university/admin/progress.html",
            progress_data=progress_data
        )
    except Exception as e:
        current_app.logger.error(f"Error loading admin progress: {e}")
        flash("Error loading progress data.", "danger")
        return render_template(
            "university/admin/progress.html",
            progress_data=[]
        )

@university_bp.route("/admin/materials")
@login_required
@role_required(UserRole.Admin)
def admin_materials_list():
    """Admin: List all materials."""
    pagination = paginate_query(
        Material.query.order_by(Material.course_id.asc(), Material.title.asc())
    )
    return render_template(
        "university/admin/materials_list.html",
        materials=pagination.items,
        pagination=pagination,
    )

@university_bp.route("/admin/materials/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin)
def admin_materials_add():
    """Admin: Add a new material."""
    courses = Course.query.order_by(Course.title.asc()).all()

    if not courses:
        flash("Create a course before adding materials.", "warning")
        return redirect(url_for("university.admin_courses_add"))

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        title = request.form.get("title", "").strip()
        
        # Handle file upload
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename and '.' in file.filename:
                filename = secure_filename(file.filename)
                # Add timestamp to avoid collisions
                import time
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                
                upload_folder = get_upload_folder()
                file_path_full = os.path.join(upload_folder, filename)
                file.save(file_path_full)
                file_path = filename  # Store relative path
            else:
                # Fall back to text path if file upload fails or not provided
                file_path = request.form.get("file_path", "").strip()
                if not file_path:
                    flash("Please upload a file or provide a file path.", "danger")
                    return render_template(
                        "university/admin/material_form.html",
                        action="Add",
                        material=None,
                        courses=courses,
                    )
        else:
            file_path = request.form.get("file_path", "").strip()

        if not course_id or not title or not file_path:
            flash("All fields are required.", "danger")
            return render_template(
                "university/admin/material_form.html",
                action="Add",
                material=None,
                courses=courses,
            )

        material = Material(course_id=course_id, title=title, file_path=file_path)
        db.session.add(material)
        db.session.commit()
        flash("Material added successfully.", "success")
        return redirect(url_for("university.admin_materials_list"))

    return render_template(
        "university/admin/material_form.html",
        action="Add",
        material=None,
        courses=courses,
    )

@university_bp.route("/admin/materials/edit/<int:material_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin)
def admin_materials_edit(material_id):
    """Admin: Edit an existing material."""
    material = Material.query.get_or_404(material_id)
    courses = Course.query.order_by(Course.title.asc()).all()

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        material.title = request.form.get("title", material.title).strip()
        
        # Handle file upload (optional - only update if new file is uploaded)
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename and '.' in file.filename:
                filename = secure_filename(file.filename)
                # Add timestamp to avoid collisions
                import time
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                
                upload_folder = get_upload_folder()
                
                # Delete old file if it exists
                old_file_path = os.path.join(upload_folder, material.file_path)
                if os.path.exists(old_file_path) and os.path.isfile(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except Exception:
                        pass  # Silently fail if file deletion fails
                
                file_path_full = os.path.join(upload_folder, filename)
                file.save(file_path_full)
                material.file_path = filename
            else:
                # If no new file uploaded, keep existing path or use text input
                file_path = request.form.get("file_path", material.file_path).strip()
                if file_path:
                    material.file_path = file_path
        else:
            # Fall back to text path if no file upload
            file_path = request.form.get("file_path", material.file_path).strip()
            if file_path:
                material.file_path = file_path

        if course_id:
            material.course_id = course_id

        db.session.commit()
        flash("Material updated successfully.", "success")
        return redirect(url_for("university.admin_materials_list"))

    return render_template(
        "university/admin/material_form.html",
        action="Edit",
        material=material,
        courses=courses,
    )

@university_bp.route("/admin/materials/delete/<int:material_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def admin_materials_delete(material_id):
    """Admin: Delete a material."""
    material = Material.query.get_or_404(material_id)
    db.session.delete(material)
    db.session.commit()
    flash("Material deleted.", "info")
    return redirect(url_for("university.admin_materials_list"))

@university_bp.route("/admin/course/upload", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin)
def admin_course_upload():
    """Admin: Upload course video."""
    if request.method == "GET":
        # Get all courses for dropdown
        courses = Course.query.order_by(Course.title.asc()).all()
        return render_template(
            "university/admin/upload.html",
            courses=courses
        )
    
    # POST: Handle file upload
    course_id = request.form.get("course_id", type=int)
    title = request.form.get("title", "").strip()
    upload_file = request.files.get("upload_file")
    
    if not course_id:
        flash("Course selection is required.", "danger")
        courses = Course.query.order_by(Course.title.asc()).all()
        return render_template("university/admin/upload.html", courses=courses)
    
    if not title:
        flash("Title is required.", "danger")
        courses = Course.query.order_by(Course.title.asc()).all()
        return render_template("university/admin/upload.html", courses=courses)
    
    if not upload_file or not upload_file.filename:
        flash("File is required.", "danger")
        courses = Course.query.order_by(Course.title.asc()).all()
        return render_template("university/admin/upload.html", courses=courses)
    
    # Verify course exists
    course = Course.query.get_or_404(course_id)
    
    # Accept all file formats - no restriction
    mime_type = upload_file.content_type or "application/octet-stream"
    
    # Get upload folder from config
    upload_folder = current_app.config.get("UNIVERSITY_UPLOAD_FOLDER", "sas_management/static/uploads/university")
    # Handle both relative and absolute paths
    if os.path.isabs(upload_folder):
        upload_path = upload_folder
    else:
        upload_path = os.path.join(current_app.root_path, "..", upload_folder)
        upload_path = os.path.abspath(upload_path)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save file with secure filename
    original_filename = upload_file.filename
    filename = secure_filename(original_filename)
    # Add timestamp to avoid collisions
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"
    file_path = os.path.join(upload_path, filename)
    
    upload_file.save(file_path)
    
    # Store relative path for Material record (relative to static folder for URL generation)
    # Use path relative to static folder
    static_relative = os.path.join("uploads", "university", filename).replace("\\", "/")
    relative_path = static_relative
    
    # Create Material record
    material = Material(
        course_id=course_id,
        title=title,
        file_path=relative_path,
        material_type=mime_type,
        content=f"File upload: {original_filename}"
    )
    db.session.add(material)
    db.session.commit()
    
    flash(f"File uploaded successfully: {original_filename}", "success")
    return redirect(url_for("university.admin_materials_list"))

# Alias for requested endpoint name
@university_bp.route("/admin/upload", methods=["GET", "POST"], endpoint="admin_material_upload")
@login_required
@role_required(UserRole.Admin)
def admin_material_upload():
    """Admin: Upload material - alias for admin_course_upload."""
    return admin_course_upload()

# ============================
# COMPREHENSIVE ROUTES
# ============================

@university_bp.route("/courses")
@login_required
def employee_course_list():
    """Course catalog - shows only published courses."""
    try:
        from sqlalchemy import or_
        
        search = request.args.get('search', '').strip()
        
        # Only show published courses - no role filtering
        query = Course.query.filter(Course.published == True)
        
        if search:
            query = query.filter(
                or_(
                    Course.title.ilike(f'%{search}%'),
                    Course.description.ilike(f'%{search}%')
                )
            )
        
        if category:
            query = query.filter(Course.category == category)
        
        if difficulty:
            query = query.filter(Course.difficulty == difficulty)
        
        pagination = paginate_query(query.order_by(Course.title.asc()))
        
        # Get user enrollments to show enrollment status
        enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(user_id=current_user.id).all()]
        
        return render_template("university/employee_courses.html",
            courses=pagination.items,
            pagination=pagination,
            search=search,
            enrolled_course_ids=enrolled_course_ids
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading courses list: {e}")
        return render_template("university/employee_courses.html", courses=[], pagination=None, search="", enrolled_course_ids=[])
        return render_template("university/course_list.html",
            courses=[], pagination=None, search="", category="", difficulty="",
            enrolled_course_ids=[], categories=[]
        )

@university_bp.route("/courses/<int:course_id>")
@university_bp.route("/courses/<slug>")
@login_required
def course_view_enhanced(course_id=None, slug=None):
    """Enhanced course view with lessons and enrollment."""
    try:
        # Support both ID and slug
        if course_id:
            course = Course.query.get_or_404(course_id)
        elif slug:
            course = Course.query.filter_by(slug=slug).first_or_404()
        else:
            flash("Invalid course identifier.", "danger")
            return redirect(url_for("university.courses_list"))
        
        # Check access
        if not course.published:
            flash("This course is not available.", "warning")
            return redirect(url_for("university.courses_list"))
        
        if course.target_role and course.target_role != current_user.role:
            flash("You do not have access to this course.", "warning")
            return redirect(url_for("university.courses_list"))
        
        # Get enrollment
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()
        
        # Get lessons with progress
        lessons_with_progress = []
        if enrollment:
            for lesson in course.lessons:
                progress = CourseProgress.query.filter_by(
                    enrollment_id=enrollment.id,
                    lesson_id=lesson.id
                ).first()
                lessons_with_progress.append({
                    'lesson': lesson,
                    'completed': progress.completed if progress else False,
                    'progress': progress
                })
        else:
            lessons_with_progress = [{'lesson': l, 'completed': False, 'progress': None} for l in course.lessons]
        
        return render_template("university/course_view_enhanced.html",
            course=course,
            enrollment=enrollment,
            lessons_with_progress=lessons_with_progress
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading course: {e}")
        return redirect(url_for("university.courses_list"))

@university_bp.route("/lesson/<int:lesson_id>")
@university_bp.route("/lessons/<int:lesson_id>")
@login_required
def view_lesson(lesson_id):
    """View lesson content and resources."""
    try:
        lesson = Lesson.query.get_or_404(lesson_id)
        course = lesson.course
        
        # Check access
        if not course.published:
            flash("This course is not available.", "warning")
            return redirect(url_for("university.courses_list"))
        
        if course.target_role and course.target_role != current_user.role:
            flash("You do not have access to this lesson.", "warning")
            return redirect(url_for("university.courses_list"))
        
        # Get enrollment
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()
        
        if not enrollment:
            flash("You must enroll in this course first.", "warning")
            return redirect(url_for("university.course_view_enhanced", course_id=course.id))
        
        # Get lesson progress
        lesson_progress = CourseProgress.query.filter_by(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id
        ).first()
        
        # Get resources - use relationship safely
        resources = []
        try:
            if hasattr(lesson, 'resources'):
                resources = list(lesson.resources) if lesson.resources else []
            else:
                # Try querying directly if relationship doesn't work
                resources = LessonResource.query.filter_by(lesson_id=lesson_id).order_by(LessonResource.id.asc()).all()
        except Exception as e:
            current_app.logger.warning(f"Error getting resources: {e}")
            resources = []
        
        # Get quiz if available - use relationship safely
        quiz = None
        try:
            if hasattr(lesson, 'quiz') and lesson.quiz:
                quiz = lesson.quiz
            else:
                # Try querying directly if relationship doesn't work
                quiz = Quiz.query.filter_by(lesson_id=lesson_id).first()
        except Exception as e:
            current_app.logger.warning(f"Error getting quiz: {e}")
            quiz = None
        
        # Get previous/next lessons
        all_lessons = course.lessons
        current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson_id), -1)
        prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
        next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None
        
        return render_template("university/lesson_view.html",
            lesson=lesson,
            course=course,
            enrollment=enrollment,
            lesson_progress=lesson_progress,
            resources=resources,
            quiz=quiz,
            prev_lesson=prev_lesson,
            next_lesson=next_lesson
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading lesson: {e}")
        return redirect(url_for("university.courses_list"))

@university_bp.route("/quiz/<int:quiz_id>")
@login_required
def view_quiz(quiz_id):
    """Take a quiz."""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        lesson = quiz.lesson if quiz.lesson_id else None
        course = lesson.course if lesson else (quiz.course if quiz.course_id else None)
        
        if not course:
            flash("Quiz not associated with a course.", "warning")
            return redirect(url_for("university.index"))
        
        # Check access
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()
        
        if not enrollment:
            flash("You must enroll in this course first.", "warning")
            return redirect(url_for("university.course_view_enhanced", course_id=course.id))
        
        # Get questions
        questions = quiz.questions.order_by(QuizQuestion.order.asc()).all()
        
        # Parse question metadata
        questions_with_choices = []
        for q in questions:
            try:
                metadata = json.loads(q.question_metadata) if q.question_metadata else {}
                questions_with_choices.append({
                    'question': q,
                    'choices': metadata.get('choices', []),
                    'correct': metadata.get('correct', ''),
                    'explanation': metadata.get('explanation', '')
                })
            except:
                questions_with_choices.append({
                    'question': q,
                    'choices': [],
                    'correct': '',
                    'explanation': ''
                })
        
        # Get user's latest attempt
        latest_attempt = QuizAttempt.query.filter_by(
            quiz_id=quiz_id,
            user_id=current_user.id
        ).order_by(QuizAttempt.started_at.desc()).first()
        
        return render_template("university/quiz_view.html",
            quiz=quiz,
            questions=questions_with_choices,
            lesson=lesson,
            course=course,
            latest_attempt=latest_attempt
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading quiz: {e}")
        return redirect(url_for("university.index"))

@university_bp.route("/certificate/<int:certificate_id>")
@university_bp.route("/certificates/<int:certificate_id>/view")
@login_required
def view_certificate(certificate_id):
    """View certificate."""
    try:
        certificate = Certificate.query.get_or_404(certificate_id)
        enrollment = certificate.enrollment
        
        # Check ownership - Admin bypass
        if enrollment.user_id != current_user.id:
            if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
                if current_user.role != UserRole.Admin:
                    flash("You do not have access to this certificate.", "warning")
                    return redirect(url_for("university.index"))
        
        course = enrollment.course
        user = enrollment.user
        
        return render_template("university/certificate_view.html",
            certificate=certificate,
            enrollment=enrollment,
            course=course,
            user=user
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading certificate: {e}")
        return redirect(url_for("university.index"))

@university_bp.route("/enroll/<int:course_id>", methods=["POST"])
@login_required
def enroll_in_course(course_id):
    """Enroll in a course."""
    try:
        result = enroll_user(current_user.id, course_id)
        if result['success']:
            flash("Successfully enrolled in course!", "success")
        else:
            flash(result.get('error', 'Failed to enroll.'), "danger")
    except Exception as e:
        current_app.logger.exception(f"Error enrolling: {e}")
    
    return redirect(url_for("university.course_view_enhanced", course_id=course_id))

@university_bp.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
@login_required
def mark_lesson_complete(lesson_id):
    """Mark a lesson as complete."""
    try:
        lesson = Lesson.query.get_or_404(lesson_id)
        course = lesson.course
        
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first_or_404()
        
        result = record_progress(current_user.id, course.id, lesson_id=lesson_id, mark_complete=True)
        
        if result['success']:
            flash("Lesson marked as complete!", "success")
        else:
            flash("Failed to update progress.", "danger")
    except Exception as e:
        current_app.logger.exception(f"Error marking lesson complete: {e}")
    
    return redirect(url_for("university.view_lesson", lesson_id=lesson_id))

# REST API endpoints
@university_bp.route("/api/quiz/<int:quiz_id>/submit", methods=["POST"])
@login_required
def api_submit_quiz(quiz_id):
    """API: Submit quiz answers."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        answers = data.get('answers', [])
        
        result = submit_quiz_service(quiz_id, current_user.id, answers)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error submitting quiz: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@university_bp.route("/api/user-courses/<int:user_id>")
@login_required
def api_user_courses(user_id):
    """API: Get user's courses."""
    # Admin bypass
    if user_id != current_user.id:
        if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
            if current_user.role != UserRole.Admin:
                return jsonify({"error": "Unauthorized"}), 403
    
    try:
        result = get_user_courses(user_id)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error getting user courses: {e}")
        return jsonify({"error": str(e)}), 500

@university_bp.route("/api/certificates/<int:certificate_id>/download")
@login_required
def api_certificate_download(certificate_id):
    """Download certificate PDF."""
    try:
        certificate = Certificate.query.get_or_404(certificate_id)
        enrollment = certificate.enrollment
        
        # Check ownership - Admin bypass
        if enrollment.user_id != current_user.id:
            if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
                if current_user.role != UserRole.Admin:
                    flash("You do not have access to this certificate.", "warning")
                    return redirect(url_for("university.index"))
        
        # Check if PDF exists
        if certificate.pdf_path:
            pdf_path = os.path.join(current_app.instance_path, certificate.pdf_path)
            if os.path.exists(pdf_path):
                return send_file(pdf_path, mimetype='application/pdf', as_attachment=True,
                               download_name=f"certificate_{certificate.certificate_ref}.pdf")
        
        flash("Certificate PDF not found. Please contact administrator.", "warning")
        return redirect(url_for("university.view_certificate", certificate_id=certificate_id))
    except Exception as e:
        current_app.logger.exception(f"Error downloading certificate: {e}")
        return redirect(url_for("university.index"))

@university_bp.route("/export_static")
@login_required
def export_static():
    """Export university index page as static HTML."""
    try:
        # Replace with actual sample data if you're not logged in
        sample_courses = [
            {
                'id': 1,
                'title': 'Team Onboarding',
                'target_role': type('obj', (object,), {'value': 'Staff'}),
                'difficulty': 'Easy',
                'description': 'Introduction to company operations.',
                'lessons': [1, 2],
                'materials': [1],
                'duration_minutes': 30
            }
        ]
        
        # Ensure static_site directory exists
        static_site_dir = os.path.join(current_app.instance_path, "..", "static_site")
        static_site_dir = os.path.abspath(static_site_dir)
        os.makedirs(static_site_dir, exist_ok=True)
        
        # Render template with sample data
        html = render_template("university/index.html", courses=sample_courses, current_user=current_user)
        
        # Write to static file
        output_path = os.path.join(static_site_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        flash(f"HTML exported to {output_path}", "success")
        return redirect(url_for("university.index"))
    except Exception as e:
        current_app.logger.exception(f"Error exporting static HTML: {e}")
        flash(f"Error exporting static HTML: {str(e)}", "danger")
        return redirect(url_for("university.index"))

# Route alias for requested endpoint name (admin_course_edit)
@university_bp.route("/admin/course/<int:id>/edit", methods=["GET", "POST"], endpoint="admin_course_edit")
@login_required
@role_required(UserRole.Admin)
def admin_course_edit(id):
    """Admin: Edit an existing course (alias route)."""
    return admin_courses_edit(id)

# Backward compatibility aliases for existing template references
@university_bp.route("/lessons/<int:lesson_id>")
@login_required
def lesson_view(lesson_id):
    """Backward compatibility alias for view_lesson."""
    return view_lesson(lesson_id)

@university_bp.route("/certificates/<int:certificate_id>/view")
@login_required
def certificate_view(certificate_id):
    """Backward compatibility alias for view_certificate."""
    return view_certificate(certificate_id)

# Backward compatibility: quiz_view endpoint
# The route /quiz/<id> is handled by view_quiz, but templates may reference quiz_view
# Flask will use the function name as endpoint, so we need an alias
def quiz_view(quiz_id):
    """Backward compatibility alias for view_quiz."""
    return view_quiz(quiz_id)
# Register the alias route
university_bp.add_url_rule("/quiz/<int:quiz_id>", "quiz_view", quiz_view, methods=["GET"])

