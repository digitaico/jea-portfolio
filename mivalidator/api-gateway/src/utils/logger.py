import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from shared.utils.logger import setup_logger

# Re-export the setup_logger function
__all__ = ['setup_logger'] 