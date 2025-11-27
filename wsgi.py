import importlib.util
import sys
import os

spec = importlib.util.spec_from_file_location(
	"app", os.path.join(os.path.dirname(__file__), "flask-spectacles", "app.py")
)
module = importlib.util.module_from_spec(spec)
sys.modules["app"] = module
spec.loader.exec_module(module)

app = module.create_app()
