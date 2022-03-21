from glob import glob
from importlib import import_module
from os.path import basename, dirname, isfile, join

_files = glob(join(dirname(__file__), "types", "*.py"))
_modules = [
    basename(f[:-3]) for f in _files if isfile(f) and not basename(f).startswith("_")
]

drivers = {}

for module_name in _modules:
    module = import_module(f".{module_name}", "enhydris.telemetry.types")
    Telemetry = getattr(module, "Telemetry")
    drivers[module_name] = Telemetry
