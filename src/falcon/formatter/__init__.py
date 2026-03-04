"""
Falcon Code Formatter

Passive AST-based formatter that automatically normalizes Falcon code
during execution without requiring manual CLI commands.
"""

from .formatter import FalconFormatter
from .printer import Printer
from .rules import FormattingRules

__all__ = ["FalconFormatter", "Printer", "FormattingRules"]
