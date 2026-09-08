import sys
from pathlib import Path

# Lets the suite run straight from a checkout without `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
