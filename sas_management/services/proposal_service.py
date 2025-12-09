"""Proposal service."""
from flask import current_app

def calculate_proposal_total(blocks_json, markup_percent=0):
    """Calculate proposal total from blocks."""
    try:
        import json
        blocks = json.loads(blocks_json) if isinstance(blocks_json, str) else blocks_json
        subtotal = sum(float(block.get('price', 0)) for block in blocks)
        total = subtotal * (1 + markup_percent / 100)
        return {'success': True, 'subtotal': subtotal, 'total': total}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error calculating proposal total: {e}")
        return {'success': False, 'error': str(e)}

def generate_proposal_pdf(proposal_id):
    """Generate PDF for proposal."""
    try:
        from models import Proposal
        proposal = Proposal.query.get(proposal_id)
        if not proposal:
            return {'success': False, 'error': 'Proposal not found'}
        
        # TODO: Implement PDF generation with ReportLab
        return {'success': False, 'error': 'PDF generation not implemented'}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error generating PDF: {e}")
        return {'success': False, 'error': str(e)}

