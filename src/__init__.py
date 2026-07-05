# This file marks the `src` directory as a Python "package".
# 
# WHY IS THIS NEEDED?
#   When you run `python -m src.pipeline`, Python needs to know that `src/`
#   is a package (a collection of Python modules that belong together).
#   An __init__.py file in the directory signals that to Python.
#   It can be completely empty — its mere existence is what matters.
#
# This enables imports like:
#   from src.config import GAMES
#   from src.db import get_connection
