"""Test POS template path."""
from app import app

with app.app_context():
    try:
        # Test if template can be found
        from flask import render_template_string
        template_content = "{% extends 'base.html' %}{% block content %}Test{% endblock %}"
        rendered = render_template_string(template_content)
        print("✓ Template rendering works")
        
        # Test blueprint template path
        from blueprints.pos import pos_bp
        print(f"✓ POS blueprint loaded")
        print(f"  Template folder: {pos_bp.template_folder}")
        print(f"  Root path: {pos_bp.root_path}")
        
        # Try to get the template
        try:
            template = app.jinja_env.get_template('pos/pos_terminal.html')
            print("✓ Template 'pos/pos_terminal.html' found in main templates folder")
        except Exception as e:
            print(f"✗ Template 'pos/pos_terminal.html' not found: {e}")
            try:
                template = app.jinja_env.get_template('pos_terminal.html')
                print("✓ Template 'pos_terminal.html' found (blueprint template folder)")
            except Exception as e2:
                print(f"✗ Template 'pos_terminal.html' also not found: {e2}")
        
    except Exception as e:
        import traceback
        print(f"✗ ERROR: {e}")
        print(traceback.format_exc())

