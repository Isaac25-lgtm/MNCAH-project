"""
Abstract Base Class for Maternal, Neonatal, Child and Adolescent Health (MNCAH)
This module defines the base class that all MNCAH subclasses inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class PeriodType(Enum):
    """Enumeration for reporting period types"""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"

class ValidationStatus(Enum):
    """Enumeration for validation status colors"""
    GREEN = "green"    # Target met
    YELLOW = "yellow"  # Acceptable range
    RED = "red"        # Below target
    BLUE = "blue"      # Data validation issues

@dataclass
class PopulationData:
    """Data class to hold population information"""
    total_population: int
    period_type: PeriodType
    reporting_period: str
    
    @property
    def adjusted_population(self) -> int:
        """Adjust population based on reporting period"""
        if self.period_type == PeriodType.QUARTERLY:
            return self.total_population // 4
        elif self.period_type == PeriodType.MONTHLY:
            return self.total_population // 12
        return self.total_population
    
    @property
    def expected_pregnancies(self) -> float:
        """Calculate expected pregnancies (5% of adjusted population)"""
        return self.adjusted_population * 0.05
    
    @property
    def expected_deliveries(self) -> float:
        """Calculate expected deliveries (4.85% of adjusted population)"""
        return self.adjusted_population * 0.0485

class MaternalNeonatalChildAdolescentHealth(ABC):
    """
    Abstract Base Class for MNCAH indicators
    
    This class defines the common interface and shared functionality
    for all MNCAH subclasses (ANC, Intrapartum, PNC)
    """
    
    def __init__(self, population_data: PopulationData, raw_data: Dict[str, Any]):
        """
        Initialize MNCAH base class
        
        Args:
            population_data: PopulationData object containing population info
            raw_data: Dictionary containing raw indicator values from uploaded data
        """
        self.population_data = population_data
        self.raw_data = raw_data
        self.calculated_indicators = {}
        self.validation_results = {}
        
    @abstractmethod
    def calculate_indicators(self) -> Dict[str, float]:
        """
        Calculate all indicators for the specific MNCAH category
        
        Returns:
            Dict mapping indicator names to calculated values
        """
        pass
    
    @abstractmethod
    def validate_indicators(self) -> Dict[str, ValidationStatus]:
        """
        Validate all indicators against targets and rules
        
        Returns:
            Dict mapping indicator names to validation status
        """
        pass
    
    @abstractmethod
    def get_indicator_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        Get definitions for all indicators in this category
        
        Returns:
            Dict mapping indicator names to their definitions
        """
        pass
    
    def get_raw_value(self, indicator_code: str, default: float = 0.0) -> float:
        """
        Safely retrieve raw value from uploaded data
        
        Args:
            indicator_code: The code for the indicator (e.g., '105-AN01a')
            default: Default value if indicator not found
            
        Returns:
            The raw value or default
        """
        return float(self.raw_data.get(indicator_code, default))
    
    def calculate_percentage(self, numerator: float, denominator: float) -> float:
        """
        Calculate percentage with division by zero protection
        
        Args:
            numerator: The numerator value
            denominator: The denominator value
            
        Returns:
            Percentage value or 0.0 if denominator is zero
        """
        if denominator <= 0:
            return 0.0
        return (numerator / denominator) * 100
    
    def calculate_rate_per_thousand(self, numerator: float, denominator: float) -> float:
        """
        Calculate rate per 1000 with division by zero protection
        
        Args:
            numerator: The numerator value
            denominator: The denominator value
            
        Returns:
            Rate per 1000 or 0.0 if denominator is zero
        """
        if denominator <= 0:
            return 0.0
        return (numerator / denominator) * 1000
    
    def calculate_rate_per_hundred_thousand(self, numerator: float, denominator: float) -> float:
        """
        Calculate rate per 100,000 with division by zero protection
        
        Args:
            numerator: The numerator value
            denominator: The denominator value
            
        Returns:
            Rate per 100,000 or 0.0 if denominator is zero
        """
        if denominator <= 0:
            return 0.0
        return (numerator / denominator) * 100000
    
    def validate_value_range(self, value: float, min_val: float = 0.0, 
                           max_val: Optional[float] = None, 
                           allow_over_hundred: bool = False) -> bool:
        """
        Validate if value is within acceptable range
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value (None means no max)
            allow_over_hundred: Whether values over 100% are allowed
            
        Returns:
            True if value is valid, False otherwise
        """
        if value < min_val:
            return False
        
        if not allow_over_hundred and value > 100.0:
            return False
            
        if max_val is not None and value > max_val:
            return False
            
        return True
    
    def get_color_status(self, value: float, indicator_name: str) -> ValidationStatus:
        """
        Determine color status based on value and targets
        This method should be overridden by subclasses for specific rules
        
        Args:
            value: Calculated indicator value
            indicator_name: Name of the indicator
            
        Returns:
            ValidationStatus enum value
        """
        # Basic validation - check for negative values or NaN
        if value < 0 or not isinstance(value, (int, float)) or str(value).lower() == 'nan':
            return ValidationStatus.BLUE
        
        return ValidationStatus.GREEN  # Default - should be overridden
    
    def process_all(self) -> Dict[str, Any]:
        """
        Process all calculations and validations
        
        Returns:
            Complete results dictionary with calculations and validations
        """
        # Calculate all indicators
        self.calculated_indicators = self.calculate_indicators()
        
        # Validate all indicators
        self.validation_results = self.validate_indicators()
        
        # Return comprehensive results
        return {
            'indicators': self.calculated_indicators,
            'validations': {k: v.value for k, v in self.validation_results.items()},
            'population_info': {
                'total_population': self.population_data.total_population,
                'adjusted_population': self.population_data.adjusted_population,
                'expected_pregnancies': self.population_data.expected_pregnancies,
                'expected_deliveries': self.population_data.expected_deliveries,
                'period_type': self.population_data.period_type.value,
                'reporting_period': self.population_data.reporting_period
            },
            'definitions': self.get_indicator_definitions()
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the indicators
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.calculated_indicators:
            return {}
        
        values = list(self.calculated_indicators.values())
        validations = list(self.validation_results.values())
        
        return {
            'total_indicators': len(values),
            'average_value': sum(values) / len(values) if values else 0,
            'min_value': min(values) if values else 0,
            'max_value': max(values) if values else 0,
            'validation_counts': {
                'green': sum(1 for v in validations if v == ValidationStatus.GREEN),
                'yellow': sum(1 for v in validations if v == ValidationStatus.YELLOW),
                'red': sum(1 for v in validations if v == ValidationStatus.RED),
                'blue': sum(1 for v in validations if v == ValidationStatus.BLUE)
            }
        }
