"""Configuration package for Kiro backend."""

# Import settings from the parent config module
import sys
import os

# Add parent directory to path to import config.py
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from the main config.py file in parent directory
import importlib.util
config_path = os.path.join(parent_dir, 'config.py')
spec = importlib.util.spec_from_file_location("main_config", config_path)
main_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_config)

# Export the settings
settings = main_config.settings
DATABASE_CONFIG = main_config.DATABASE_CONFIG
REDIS_CONFIG = main_config.REDIS_CONFIG
LOGGING_CONFIG = main_config.LOGGING_CONFIG

from .alerts import *