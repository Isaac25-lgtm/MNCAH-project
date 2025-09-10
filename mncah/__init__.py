"""
MNCAH Data Analysis System
A Object-Oriented Programming system for auto-analyzing MNCAH (Maternal, Newborn, Child and Adolescent Health) data.
"""

__version__ = "1.0.0"
__author__ = "MNCAH Analysis Team"

from .data_loader import DataLoader
from .mncah_data import MNCAHData
from .analyzer import MNCAHAnalyzer
from .report_generator import ReportGenerator
from .system import MNCAHSystem

__all__ = [
    'DataLoader',
    'MNCAHData', 
    'MNCAHAnalyzer',
    'ReportGenerator',
    'MNCAHSystem'
]