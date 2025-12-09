"""Global Search Blueprint."""
from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from services.search_service import global_search, quick_search

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("")
@login_required
def search():
    """Global search results page."""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return render_template("search_results.html",
            query="",
            results={},
            total=0,
            counts={}
        )
    
    search_result = global_search(query, limit_per_type=20)
    
    if not search_result['success']:
        current_app.logger.warning(f"Search failed: {search_result.get('error')}")
        return render_template("search_results.html",
            query=query,
            results={},
            total=0,
            counts={},
            error=search_result.get('error')
        )
    
    return render_template("search_results.html",
        query=search_result['query'],
        results=search_result['results'],
        total=search_result['total'],
        counts=search_result['counts']
    )


@search_bp.route("/api/quick")
@login_required
def api_quick_search():
    """API endpoint for quick search (autocomplete suggestions)."""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({"success": False, "results": []}), 200
    
    result = quick_search(query, limit=5)
    
    return jsonify(result), 200

