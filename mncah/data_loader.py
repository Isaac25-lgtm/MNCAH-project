"""
DataLoader class for loading raw MNCAH data from various sources.
"""

import pandas as pd
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

from .mncah_data import MNCAHData


class DataLoader:
    """
    Class to load raw MNCAH data from various file formats and sources.
    
    Supports CSV, JSON, Excel formats and provides data preprocessing capabilities.
    """
    
    def __init__(self, encoding: str = 'utf-8'):
        """
        Initialize DataLoader.
        
        Args:
            encoding: Default encoding for text files
        """
        self.encoding = encoding
        self.logger = logging.getLogger(__name__)
        
        # Column mapping for different data sources
        self.column_mappings = {
            'country_name': 'country',
            'Country': 'country',
            'Country Name': 'country',
            'Year': 'year',
            'year_value': 'year'
        }
    
    def load_from_csv(self, file_path: Union[str, Path], **kwargs) -> MNCAHData:
        """
        Load MNCAH data from CSV file.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments for pd.read_csv
            
        Returns:
            MNCAHData object
        """
        try:
            # Default CSV reading parameters
            csv_params = {
                'encoding': self.encoding,
                'na_values': ['', 'NA', 'N/A', 'null', 'NULL', '-']
            }
            csv_params.update(kwargs)
            
            data = pd.read_csv(file_path, **csv_params)
            self.logger.info(f"Loaded {len(data)} records from {file_path}")
            
            # Apply column mappings
            data = self._apply_column_mappings(data)
            
            # Create metadata
            metadata = {
                'source_file': str(file_path),
                'file_type': 'csv',
                'original_columns': list(data.columns),
                'records_loaded': len(data)
            }
            
            return MNCAHData(data, metadata)
            
        except Exception as e:
            self.logger.error(f"Error loading CSV file {file_path}: {str(e)}")
            raise
    
    def load_from_json(self, file_path: Union[str, Path]) -> MNCAHData:
        """
        Load MNCAH data from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            MNCAHData object
        """
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                json_data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(json_data, list):
                data = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                if 'data' in json_data:
                    data = pd.DataFrame(json_data['data'])
                else:
                    data = pd.DataFrame([json_data])
            else:
                raise ValueError("Unsupported JSON structure")
            
            self.logger.info(f"Loaded {len(data)} records from {file_path}")
            
            # Apply column mappings
            data = self._apply_column_mappings(data)
            
            # Create metadata
            metadata = {
                'source_file': str(file_path),
                'file_type': 'json',
                'original_columns': list(data.columns),
                'records_loaded': len(data)
            }
            
            return MNCAHData(data, metadata)
            
        except Exception as e:
            self.logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            raise
    
    def load_from_excel(self, file_path: Union[str, Path], sheet_name: Optional[str] = None, **kwargs) -> MNCAHData:
        """
        Load MNCAH data from Excel file.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to load (default: first sheet)
            **kwargs: Additional arguments for pd.read_excel
            
        Returns:
            MNCAHData object
        """
        try:
            # Default Excel reading parameters
            excel_params = {
                'na_values': ['', 'NA', 'N/A', 'null', 'NULL', '-']
            }
            excel_params.update(kwargs)
            
            if sheet_name:
                excel_params['sheet_name'] = sheet_name
            
            data = pd.read_excel(file_path, **excel_params)
            self.logger.info(f"Loaded {len(data)} records from {file_path}")
            
            # Apply column mappings
            data = self._apply_column_mappings(data)
            
            # Create metadata
            metadata = {
                'source_file': str(file_path),
                'file_type': 'excel',
                'sheet_name': sheet_name or 'default',
                'original_columns': list(data.columns),
                'records_loaded': len(data)
            }
            
            return MNCAHData(data, metadata)
            
        except Exception as e:
            self.logger.error(f"Error loading Excel file {file_path}: {str(e)}")
            raise
    
    def load_from_dict(self, data_dict: Dict) -> MNCAHData:
        """
        Load MNCAH data from dictionary.
        
        Args:
            data_dict: Dictionary containing data
            
        Returns:
            MNCAHData object
        """
        try:
            data = pd.DataFrame(data_dict)
            
            # Apply column mappings
            data = self._apply_column_mappings(data)
            
            # Create metadata
            metadata = {
                'source_type': 'dictionary',
                'original_columns': list(data.columns),
                'records_loaded': len(data)
            }
            
            return MNCAHData(data, metadata)
            
        except Exception as e:
            self.logger.error(f"Error loading data from dictionary: {str(e)}")
            raise
    
    def _apply_column_mappings(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply column name mappings to standardize column names."""
        data_copy = data.copy()
        
        # Apply mappings
        for old_name, new_name in self.column_mappings.items():
            if old_name in data_copy.columns:
                data_copy = data_copy.rename(columns={old_name: new_name})
        
        return data_copy
    
    def add_column_mapping(self, original_name: str, standard_name: str) -> None:
        """
        Add a new column mapping.
        
        Args:
            original_name: Original column name in source data
            standard_name: Standardized column name to map to
        """
        self.column_mappings[original_name] = standard_name
    
    def preprocess_data(self, data: pd.DataFrame, 
                       drop_duplicates: bool = True,
                       fill_missing: bool = False,
                       missing_strategy: str = 'mean') -> pd.DataFrame:
        """
        Preprocess the loaded data.
        
        Args:
            data: Raw data DataFrame
            drop_duplicates: Whether to drop duplicate rows
            fill_missing: Whether to fill missing values
            missing_strategy: Strategy for filling missing values ('mean', 'median', 'mode', 'zero')
            
        Returns:
            Preprocessed DataFrame
        """
        processed_data = data.copy()
        
        # Drop duplicates
        if drop_duplicates:
            initial_rows = len(processed_data)
            processed_data = processed_data.drop_duplicates()
            rows_dropped = initial_rows - len(processed_data)
            if rows_dropped > 0:
                self.logger.info(f"Dropped {rows_dropped} duplicate rows")
        
        # Handle missing values
        if fill_missing:
            numeric_cols = processed_data.select_dtypes(include=['number']).columns
            
            for col in numeric_cols:
                if processed_data[col].isna().any():
                    if missing_strategy == 'mean':
                        fill_value = processed_data[col].mean()
                    elif missing_strategy == 'median':
                        fill_value = processed_data[col].median()
                    elif missing_strategy == 'mode':
                        fill_value = processed_data[col].mode().iloc[0] if not processed_data[col].mode().empty else 0
                    elif missing_strategy == 'zero':
                        fill_value = 0
                    else:
                        fill_value = processed_data[col].mean()  # Default to mean
                    
                    processed_data[col] = processed_data[col].fillna(fill_value)
                    self.logger.info(f"Filled missing values in {col} with {missing_strategy}: {fill_value}")
        
        return processed_data
    
    def validate_file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists and is readable."""
        path = Path(file_path)
        return path.exists() and path.is_file()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return ['csv', 'json', 'xlsx', 'xls']