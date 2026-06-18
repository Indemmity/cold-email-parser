"""Entry point for Streamlit Cloud deployment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.streamlit_app import *
