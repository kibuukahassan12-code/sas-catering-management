"""ESC/POS printer integration adapter."""
import os
from typing import Dict, Optional
from flask import current_app

try:
    from escpos.printer import Usb, Network, Serial, File
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False
    Usb = Network = Serial = File = None


class ESCPOSAdapter:
    """ESC/POS printer adapter for receipt printing."""
    
    def __init__(self):
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = ESCPOS_AVAILABLE and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "ESC/POS adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def print_receipt(
        self,
        printer_config: Dict[str, any],
        receipt_data: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Print receipt using ESC/POS commands.
        
        Args:
            printer_config: Dict with 'type' (usb/network/serial/file), connection params
            receipt_data: Dict with 'header', 'items', 'footer', 'total', etc.
            
        Returns:
            Dict with 'success', 'error'
        """
        if self.mock_mode or not self.enabled:
            if current_app:
                current_app.logger.info(f"Mock print receipt: {receipt_data.get('total', 0)}")
            return {
                'success': True,
                'mock': True,
                'message': 'Mock receipt printed (ESC/POS not configured)'
            }
        
        try:
            printer = self._get_printer(printer_config)
            if not printer:
                return {'success': False, 'error': 'Could not initialize printer'}
            
            # Print header
            printer.set(align='center', font='a', bold=True, double_height=True)
            printer.text(f"\n{receipt_data.get('header', 'SAS BEST FOODS')}\n")
            printer.text(f"{receipt_data.get('address', '')}\n")
            printer.text(f"{receipt_data.get('phone', '')}\n")
            printer.text("-" * 32 + "\n")
            
            # Print items
            printer.set(align='left', font='a', bold=False)
            for item in receipt_data.get('items', []):
                name = item.get('name', '')[:20]
                qty = item.get('quantity', 0)
                price = item.get('price', 0)
                total = qty * price
                printer.text(f"{name:<20} {qty:>3} x {price:>8.2f}\n")
                printer.text(f"{'':<20} {total:>12.2f}\n")
            
            # Print footer
            printer.text("-" * 32 + "\n")
            printer.set(bold=True)
            printer.text(f"TOTAL: {receipt_data.get('total', 0):>20.2f}\n")
            printer.text(f"PAID: {receipt_data.get('paid', 0):>20.2f}\n")
            if receipt_data.get('change', 0) > 0:
                printer.text(f"CHANGE: {receipt_data.get('change', 0):>18.2f}\n")
            
            printer.text("\n" * 2)
            printer.cut()
            printer.close()
            
            return {'success': True, 'mock': False}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"ESC/POS print error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_printer(self, config: Dict[str, any]):
        """Initialize printer based on config."""
        printer_type = config.get('type', 'file').lower()
        
        try:
            if printer_type == 'usb':
                return Usb(
                    idVendor=config.get('vendor_id', 0x04f9),
                    idProduct=config.get('product_id', 0x2016)
                )
            elif printer_type == 'network':
                return Network(config.get('host', '192.168.1.100'), port=config.get('port', 9100))
            elif printer_type == 'serial':
                return Serial(config.get('port', '/dev/ttyUSB0'), baudrate=config.get('baudrate', 9600))
            elif printer_type == 'file':
                return File(config.get('file_path', '/dev/usb/lp0'))
            else:
                return None
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Printer initialization error: {e}")
            return None

