"""Expose the production Flask app when Gunicorn resolves the app package."""
import importlib.util
from pathlib import Path

_root_app = Path(__file__).resolve().parent.parent / "UltraKI.py"
spec = importlib.util.spec_from_file_location("ultraki_root_app", _root_app)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load {_root_app}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app
