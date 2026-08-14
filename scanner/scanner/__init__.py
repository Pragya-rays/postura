"""Postura scanner: standalone Collect + Judge package.

No web framework dependency. Runnable directly:

    python -m scanner example.com --tier public --json

The backend imports this package for collectors (Collect) and the rules
engine (Judge); it never imports FastAPI/SQLAlchemy back, keeping this
package framework-free and independently testable.
"""

__version__ = "0.1.0"
