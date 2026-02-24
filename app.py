import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Loading SAS Catering Management System...")

from sas_management.app import app

logger.info(f"Flask app loaded successfully. Debug mode: {app.debug}")
logger.info(f"Template folder: {app.template_folder}")
logger.info(f"Static folder: {app.static_folder}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
