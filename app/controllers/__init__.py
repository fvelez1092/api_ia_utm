"""Controladores de la aplicación."""
from flask import Blueprint
from os.path import dirname, basename, isfile, join
import os
import glob
import importlib.util

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]


# Obtener la lista de archivos en el módulo 'controllers'
controllers_dir = os.path.dirname(__file__)
module_files = [f for f in os.listdir(controllers_dir) if f.endswith('.py') and f != '__init__.py']

# Crear una lista para almacenar las instancias de Blueprints
__blueprints__ = []

# Importar y buscar instancias de Blueprints en cada archivo
for module_file in module_files:
    module_name = os.path.splitext(module_file)[0]
    module_path = os.path.join(controllers_dir, module_file)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name in dir(module):
        item = getattr(module, name)
        if isinstance(item, Blueprint) and name.endswith("_blueprint"):
            __blueprints__.append(item)