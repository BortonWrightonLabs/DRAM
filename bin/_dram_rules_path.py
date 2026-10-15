import sys
from pathlib import Path

source = Path(__file__).resolve().parent / "rules" / "src"
sys.path.insert(0, str(source))
