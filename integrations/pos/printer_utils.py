"""POS printer utility functions."""
import os
from typing import Dict, List


class PrinterUtils:
    """Utility functions for POS printing."""
    
    @staticmethod
    def format_receipt_data(
        order_items: List[Dict],
        total: float,
        paid: float,
        change: float = 0,
        header: str = "SAS BEST FOODS",
        address: str = "",
        phone: str = ""
    ) -> Dict[str, any]:
        """Format order data for receipt printing."""
        return {
            'header': header,
            'address': address,
            'phone': phone,
            'items': order_items,
            'total': total,
            'paid': paid,
            'change': change
        }
    
    @staticmethod
    def format_kitchen_ticket(
        order_id: str,
        items: List[Dict],
        special_instructions: str = ""
    ) -> Dict[str, any]:
        """Format kitchen ticket data."""
        return {
            'order_id': order_id,
            'items': items,
            'special_instructions': special_instructions
        }

