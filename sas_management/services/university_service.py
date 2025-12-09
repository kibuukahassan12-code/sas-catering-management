"""Employee University Service Layer - Course creation, enrollment, progress tracking, quizzes, certificates."""
import os
import json
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from flask import current_app
from werkzeug.utils import secure_filename

from models import (
    db, Course, Lesson, LessonResource, Enrollment, Quiz, QuizQuestion,
    QuizAttempt, QuizAnswer, Certificate, CourseProgress, User
)


def generate_course_slug(title):
    """Generate a URL-friendly slug from course title."""
    slug = title.lower()
    slug = slug.replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    # Remove multiple consecutive dashes
    while '--' in slug:
        slug = slug.replace('--', '-')
    # Ensure uniqueness
    base_slug = slug
    counter = 1
    while Course.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def create_course(data):
    """Create a new course."""
    try:
        db.session.begin()
        
        title = data.get('title', '').strip()
        if not title:
            raise ValueError("Course title is required")
        
        slug = data.get('slug') or generate_course_slug(title)
        
        course = Course(
            title=title,
            slug=slug,
            description=data.get('description', '').strip(),
            category=data.get('category', '').strip(),
            difficulty=data.get('difficulty', 'Beginner'),
            duration_minutes=int(data.get('duration_minutes', 0) or 0),
            published=bool(data.get('published', False)),
            target_role=data.get('target_role')  # Optional
        )
        
        db.session.add(course)
        db.session.commit()
        
        return {"success": True, "course_id": course.id, "message": "Course created successfully"}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating course: {e}")
        return {"success": False, "error": str(e)}


def add_lesson(course_id, data):
    """Add a lesson to a course."""
    try:
        db.session.begin()
        
        course = Course.query.get(course_id)
        if not course:
            raise ValueError("Course not found")
        
        title = data.get('title', '').strip()
        if not title:
            raise ValueError("Lesson title is required")
        
        # Get max order for this course
        max_order = db.session.query(func.max(Lesson.order)).filter_by(course_id=course_id).scalar() or 0
        
        lesson = Lesson(
            course_id=course_id,
            title=title,
            content=data.get('content', '').strip(),
            order=int(data.get('order', max_order + 1)),
            lesson_type=data.get('lesson_type', 'video'),
            duration_minutes=int(data.get('duration_minutes', 0) or 0)
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        return {"success": True, "lesson_id": lesson.id, "message": "Lesson added successfully"}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error adding lesson: {e}")
        return {"success": False, "error": str(e)}


def upload_resource(lesson_id, file, resource_type='document', display_name=None, uploaded_by=None):
    """Upload a resource file for a lesson."""
    try:
        db.session.begin()
        
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            raise ValueError("Lesson not found")
        
        if not file or not file.filename:
            raise ValueError("No file provided")
        
        # Ensure upload folder exists
        upload_folder = os.path.join(current_app.instance_path, "university_uploads")
        os.makedirs(upload_folder, exist_ok=True)
        
        # Secure filename
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        
        # Determine subfolder based on resource type
        if resource_type in ['image', 'video']:
            subfolder = resource_type + 's'
        else:
            subfolder = 'documents'
        
        resource_folder = os.path.join(upload_folder, subfolder)
        os.makedirs(resource_folder, exist_ok=True)
        
        filepath = os.path.join(resource_folder, filename)
        file.save(filepath)
        
        # Store relative path
        relative_path = f"university_uploads/{subfolder}/{filename}"
        
        resource = LessonResource(
            lesson_id=lesson_id,
            resource_type=resource_type,
            url=relative_path,
            filename=filename,
            display_name=display_name or filename,
            uploaded_by=uploaded_by
        )
        
        db.session.add(resource)
        db.session.commit()
        
        return {
            "success": True,
            "resource_id": resource.id,
            "url": relative_path,
            "message": "Resource uploaded successfully"
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error uploading resource: {e}")
        return {"success": False, "error": str(e)}


def enroll_user(user_id, course_id):
    """Enroll a user in a course."""
    try:
        db.session.begin()
        
        # Check if already enrolled
        existing = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if existing:
            return {"success": False, "error": "User already enrolled in this course"}
        
        course = Course.query.get(course_id)
        if not course:
            raise ValueError("Course not found")
        
        enrollment = Enrollment(
            user_id=user_id,
            course_id=course_id,
            enrolled_at=datetime.utcnow()
        )
        
        db.session.add(enrollment)
        
        # Create progress tracking for each lesson
        for lesson in course.lessons:
            progress = CourseProgress(
                enrollment_id=None,  # Will be set after flush
                lesson_id=lesson.id,
                completed=False
            )
            db.session.add(progress)
        
        db.session.flush()  # Get enrollment ID
        
        # Update progress entries with enrollment_id
        for progress in CourseProgress.query.filter_by(enrollment_id=None, lesson_id__in=[l.id for l in course.lessons]).all():
            progress.enrollment_id = enrollment.id
        
        db.session.commit()
        
        return {"success": True, "enrollment_id": enrollment.id, "message": "Enrolled successfully"}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error enrolling user: {e}")
        return {"success": False, "error": str(e)}


def record_progress(user_id, course_id, lesson_id=None, percent=None, mark_complete=False):
    """Record progress for a user in a course."""
    try:
        db.session.begin()
        
        enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if not enrollment:
            raise ValueError("User not enrolled in this course")
        
        if lesson_id and mark_complete:
            # Mark lesson as complete
            progress = CourseProgress.query.filter_by(
                enrollment_id=enrollment.id,
                lesson_id=lesson_id
            ).first()
            
            if progress and not progress.completed:
                progress.completed = True
                progress.completed_at = datetime.utcnow()
                enrollment.last_accessed_at = datetime.utcnow()
        
        # Calculate overall course progress
        total_lessons = len(enrollment.course.lessons)
        if total_lessons > 0:
            completed_lessons = CourseProgress.query.filter_by(
                enrollment_id=enrollment.id,
                completed=True
            ).count()
            enrollment.progress = int((completed_lessons / total_lessons) * 100)
        elif percent is not None:
            enrollment.progress = int(percent)
        
        # Check if course is completed
        if enrollment.progress >= 100 and not enrollment.completed:
            enrollment.completed = True
            enrollment.completed_at = datetime.utcnow()
            
            # Generate certificate
            generate_certificate(enrollment.id)
        
        enrollment.last_accessed_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "progress": enrollment.progress, "completed": enrollment.completed}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error recording progress: {e}")
        return {"success": False, "error": str(e)}


def submit_quiz(quiz_id, user_id, answers):
    """Submit quiz answers and grade them."""
    try:
        db.session.begin()
        
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")
        
        # Create quiz attempt
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            started_at=datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.flush()
        
        total_points = 0
        earned_points = 0
        
        # Grade each answer
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            user_answer = answer_data.get('answer', '')
            
            question = QuizQuestion.query.get(question_id)
            if not question or question.quiz_id != quiz_id:
                continue
            
            total_points += question.points
            
            # Parse metadata to get correct answer
            is_correct = False
            try:
                metadata = json.loads(question.question_metadata) if question.question_metadata else {}
                correct_answer = metadata.get('correct', '')
                
                if question.question_type == 'mcq':
                    is_correct = str(user_answer).lower() == str(correct_answer).lower()
                elif question.question_type == 'tf':
                    is_correct = str(user_answer).lower() in ['true', 't', '1'] if correct_answer else str(user_answer).lower() in ['false', 'f', '0']
                else:
                    # For short answer, check similarity (simple comparison)
                    is_correct = str(user_answer).lower().strip() == str(correct_answer).lower().strip()
            except:
                pass
            
            points_earned = question.points if is_correct else 0
            earned_points += points_earned
            
            quiz_answer = QuizAnswer(
                attempt_id=attempt.id,
                question_id=question_id,
                answer=user_answer,
                is_correct=is_correct,
                points_earned=points_earned
            )
            db.session.add(quiz_answer)
        
        # Calculate score
        score = int((earned_points / total_points * 100)) if total_points > 0 else 0
        passed = score >= quiz.passing_score
        
        attempt.score = score
        attempt.passed = passed
        attempt.submitted_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            "success": True,
            "attempt_id": attempt.id,
            "score": score,
            "passed": passed,
            "total_points": total_points,
            "earned_points": earned_points,
            "passing_score": quiz.passing_score
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error submitting quiz: {e}")
        return {"success": False, "error": str(e)}


def generate_certificate(enrollment_id):
    """Generate a PDF certificate for course completion."""
    try:
        db.session.begin()
        
        enrollment = Enrollment.query.get(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        if not enrollment.completed:
            raise ValueError("Course must be completed before generating certificate")
        
        # Check if certificate already exists
        existing = Certificate.query.filter_by(enrollment_id=enrollment_id).first()
        if existing:
            return {"success": True, "certificate_id": existing.id, "certificate_ref": existing.certificate_ref}
        
        # Generate certificate reference
        certificate_ref = f"CERT-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        
        # Generate verification code
        verification_code = secrets.token_urlsafe(16)
        
        certificate = Certificate(
            enrollment_id=enrollment_id,
            certificate_ref=certificate_ref,
            issued_at=datetime.utcnow(),
            verification_code=verification_code
        )
        
        db.session.add(certificate)
        db.session.flush()
        
        # Generate PDF (will be done by route handler using ReportLab)
        # Store path after PDF generation
        
        db.session.commit()
        
        return {
            "success": True,
            "certificate_id": certificate.id,
            "certificate_ref": certificate_ref,
            "verification_code": verification_code
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error generating certificate: {e}")
        return {"success": False, "error": str(e)}


def get_user_courses(user_id):
    """Get all courses for a user (enrolled and available)."""
    enrolled_courses = db.session.query(Course).join(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()
    
    # Get available courses (published, matching role if specified)
    user = User.query.get(user_id)
    available_query = Course.query.filter_by(published=True)
    
    if user and user.role:
        # Show courses without target_role restriction or matching role
        available_query = available_query.filter(
            (Course.target_role.is_(None)) | (Course.target_role == user.role)
        )
    
    available_courses = available_query.all()
    
    return {
        "enrolled": [{"id": c.id, "title": c.title, "slug": c.slug, "progress": None} for c in enrolled_courses],
        "available": [{"id": c.id, "title": c.title, "slug": c.slug} for c in available_courses if c.id not in [ec.id for ec in enrolled_courses]]
    }

