# Employee University Error Fix

## Issue
Internal Server Error when accessing the Employee University module.

## Root Causes

1. **Query Filter Issue**: The route was filtering courses by `Course.target_role == current_user.role`, but courses with `target_role=None` should be available to all roles. The query was excluding these courses.

2. **Template AttributeError**: The template was trying to access `course.target_role.value` when `target_role` could be `None`, causing an AttributeError.

3. **Missing Error Handling**: Routes didn't have try-except blocks to catch and handle errors gracefully.

## Fixes Applied

### 1. Fixed Query Filter (`blueprints/university/__init__.py`)

**Before:**
```python
courses = Course.query.filter(Course.target_role == current_user.role).order_by(
    Course.title.asc()
).all()
```

**After:**
```python
from sqlalchemy import or_
courses = Course.query.filter(
    Course.published == True
).filter(
    or_(
        Course.target_role == current_user.role,
        Course.target_role.is_(None)
    )
).order_by(Course.title.asc()).all()
```

This now:
- Only shows published courses
- Includes courses with `target_role=None` (available to all)
- Includes courses matching the user's role
- Has error handling with try-except

### 2. Fixed Template (`templates/university/index.html`)

**Before:**
```jinja2
<span class="badge">{{ course.target_role.value }}</span>
```

**After:**
```jinja2
{% if course.target_role %}
<span class="badge">{{ course.target_role.value }}</span>
{% else %}
<span class="badge">All Roles</span>
{% endif %}
```

Now handles `None` values safely.

### 3. Added Error Handling

Added try-except blocks to all routes:
- `index()` - University main page
- `view_course()` - Course details page
- `view_material()` - Material view page

All routes now:
- Log errors for debugging
- Show user-friendly flash messages
- Gracefully redirect on errors

### 4. Updated Course View Route

Fixed the access check to handle `target_role=None`:
```python
if course.target_role and course.target_role != current_user.role:
    flash("You do not have access to this course.", "warning")
    return redirect(url_for("university.index"))
```

## Files Modified

1. `blueprints/university/__init__.py`
   - Fixed `index()` route query
   - Added error handling to all routes
   - Improved access checks

2. `templates/university/index.html`
   - Added null checks for `target_role`
   - Improved display of course metadata
   - Better handling of missing descriptions

## Testing

✅ App loads successfully
✅ No linter errors
✅ Routes have proper error handling
✅ Template handles None values

## Status

**Employee University should now work without Internal Server Errors!**

The module will:
- Display all published courses
- Show courses available to all roles (target_role=None)
- Show courses specific to user's role
- Handle errors gracefully
- Display course information correctly

