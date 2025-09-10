"""
MNCAHData class for representing and validating MNCAH data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime


class MNCAHData:
    """
    Class to represent and validate MNCAH (Maternal, Newborn, Child and Adolescent Health) data.
    
    This class handles data validation, storage, and basic operations on MNCAH indicators.
    """
    
    # Standard MNCAH indicators
    MATERNAL_INDICATORS = [
        'maternal_mortality_ratio',
        'antenatal_care_coverage',
        'skilled_birth_attendance',
        'institutional_delivery_rate'
    ]
    
    NEWBORN_INDICATORS = [
        'neonatal_mortality_rate',
        'low_birth_weight_prevalence',
        'early_breastfeeding_initiation'
    ]
    
    CHILD_INDICATORS = [
        'under5_mortality_rate',
        'infant_mortality_rate',
        'vaccination_coverage_dpt3',
        'vaccination_coverage_measles',
        'stunting_prevalence',
        'wasting_prevalence'
    ]
    
    ADOLESCENT_INDICATORS = [
        'adolescent_birth_rate',
        'adolescent_anemia_prevalence'
    ]
    
    ALL_INDICATORS = MATERNAL_INDICATORS + NEWBORN_INDICATORS + CHILD_INDICATORS + ADOLESCENT_INDICATORS
    
    def __init__(self, data: Union[pd.DataFrame, Dict] = None, metadata: Dict = None):
        """
        Initialize MNCAHData object.
        
        Args:
            data: Raw data as DataFrame or dictionary
            metadata: Additional metadata about the data source
        """
        self.data = pd.DataFrame() if data is None else self._process_data(data)
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self._validate_data()
    
    def _process_data(self, data: Union[pd.DataFrame, Dict]) -> pd.DataFrame:
        """Convert input data to standardized DataFrame format."""
        if isinstance(data, dict):
            return pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            return data.copy()
        else:
            raise ValueError("Data must be a pandas DataFrame or dictionary")
    
    def _validate_data(self) -> None:
        """Validate the MNCAH data structure and values."""
        if self.data.empty:
            return
        
        # Check for required columns
        required_cols = ['country', 'year']
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Validate year values
        if 'year' in self.data.columns:
            invalid_years = self.data['year'][(self.data['year'] < 1990) | (self.data['year'] > 2030)]
            if not invalid_years.empty:
                raise ValueError(f"Invalid years found: {invalid_years.tolist()}")
        
        # Validate indicator values (should be non-negative)
        indicator_cols = [col for col in self.data.columns if col in self.ALL_INDICATORS]
        for col in indicator_cols:
            negative_values = self.data[col][self.data[col] < 0]
            if not negative_values.empty:
                raise ValueError(f"Negative values found in {col}: {negative_values.tolist()}")
    
    def add_indicator(self, indicator_name: str, values: List[float]) -> None:
        """Add a new indicator to the dataset."""
        if indicator_name not in self.ALL_INDICATORS:
            raise ValueError(f"Unknown indicator: {indicator_name}")
        
        if len(values) != len(self.data):
            raise ValueError("Values length must match number of records")
        
        self.data[indicator_name] = values
        self._validate_data()
    
    def get_indicator_data(self, indicator: str) -> pd.Series:
        """Get data for a specific indicator."""
        if indicator not in self.data.columns:
            raise ValueError(f"Indicator {indicator} not found in data")
        return self.data[indicator]
    
    def get_countries(self) -> List[str]:
        """Get list of countries in the dataset."""
        if 'country' not in self.data.columns:
            return []
        return self.data['country'].unique().tolist()
    
    def get_years(self) -> List[int]:
        """Get list of years in the dataset."""
        if 'year' not in self.data.columns:
            return []
        return sorted(self.data['year'].unique().tolist())
    
    def filter_by_country(self, countries: Union[str, List[str]]) -> 'MNCAHData':
        """Filter data by country(ies)."""
        if isinstance(countries, str):
            countries = [countries]
        
        filtered_data = self.data[self.data['country'].isin(countries)]
        return MNCAHData(filtered_data, self.metadata)
    
    def filter_by_year(self, years: Union[int, List[int]]) -> 'MNCAHData':
        """Filter data by year(s)."""
        if isinstance(years, int):
            years = [years]
        
        filtered_data = self.data[self.data['year'].isin(years)]
        return MNCAHData(filtered_data, self.metadata)
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for all indicators."""
        indicator_cols = [col for col in self.data.columns if col in self.ALL_INDICATORS]
        
        if not indicator_cols:
            return {}
        
        summary = {}
        for indicator in indicator_cols:
            stats = self.data[indicator].describe()
            summary[indicator] = {
                'count': int(stats['count']),
                'mean': float(stats['mean']),
                'std': float(stats['std']),
                'min': float(stats['min']),
                'max': float(stats['max']),
                'median': float(stats['50%'])
            }
        
        return summary
    
    def __len__(self) -> int:
        """Return number of records."""
        return len(self.data)
    
    def __str__(self) -> str:
        """String representation of the data."""
        return f"MNCAHData: {len(self.data)} records, {len(self.get_countries())} countries, {len(self.get_years())} years"
    
    def __repr__(self) -> str:
        """Detailed representation of the data."""
        return f"MNCAHData(records={len(self.data)}, countries={self.get_countries()}, years={self.get_years()})"