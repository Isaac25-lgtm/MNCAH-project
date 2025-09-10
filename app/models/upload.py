"""
Data Upload and Processing Model
This module handles file uploads, data processing, and storage for MNCAH indicators.
"""

import os
import json
import pandas as pd
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy import Enum as SQLEnum

from .base import PopulationData, PeriodType
from .anc import AntenatalCare
from .intrapartum import IntrapartumCare
from .pnc import PostnatalCare

Base = declarative_base()


class UploadStatus(Enum):
    """Status of data upload"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"


class ValidationLevel(Enum):
    """Level of validation issues"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DataUpload(Base):
    """
    Model to track data uploads and their processing status
    """
    __tablename__ = 'data_uploads'
    
    id = Column(Integer, primary_key=True)
    
    # Upload metadata
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=True)
    
    # Facility information
    facility_name = Column(String(200), nullable=False, index=True)
    district = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    facility_type = Column(String(100), nullable=True)
    
    # Population and period information
    total_population = Column(Integer, nullable=False)
    period_type = Column(SQLEnum(PeriodType), nullable=False)
    reporting_period = Column(String(50), nullable=False, index=True)
    
    # Upload tracking
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(UploadStatus), default=UploadStatus.PENDING, nullable=False)
    
    # Processing results
    raw_data = Column(JSON, nullable=True)  # Raw extracted data from file
    processed_data = Column(JSON, nullable=True)  # Calculated indicators
    validation_results = Column(JSON, nullable=True)  # Validation outcomes
    error_log = Column(Text, nullable=True)
    processing_notes = Column(Text, nullable=True)
    
    # Data quality metrics
    total_indicators = Column(Integer, default=0)
    valid_indicators = Column(Integer, default=0)
    warning_indicators = Column(Integer, default=0)
    error_indicators = Column(Integer, default=0)
    
    # Relationships
    uploaded_by_user = relationship("User", backref="uploads")
    
    def __init__(self, **kwargs):
        """Initialize data upload record"""
        super().__init__(**kwargs)
        self.uploaded_at = datetime.utcnow()
    
    @property
    def adjusted_population(self) -> int:
        """Get population adjusted for reporting period"""
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
    
    def process_upload(self) -> Tuple[bool, str]:
        """
        Process the uploaded data through MNCAH calculations
        
        Returns:
            Tuple of (success, message)
        """
        try:
            self.status = UploadStatus.PROCESSING
            
            if not self.raw_data:
                return False, "No raw data available to process"
            
            # Create population data object
            pop_data = PopulationData(
                total_population=self.total_population,
                period_type=self.period_type,
                reporting_period=self.reporting_period
            )
            
            # Initialize MNCAH models
            anc_model = AntenatalCare(pop_data, self.raw_data)
            intrapartum_model = IntrapartumCare(pop_data, self.raw_data)
            pnc_model = PostnatalCare(pop_data, self.raw_data)
            
            # Process each category
            anc_results = anc_model.process_all()
            intrapartum_results = intrapartum_model.process_all()
            pnc_results = pnc_model.process_all()
            
            # Combine results
            self.processed_data = {
                'anc': anc_results,
                'intrapartum': intrapartum_results,
                'pnc': pnc_results,
                'processing_metadata': {
                    'processed_at': datetime.utcnow().isoformat(),
                    'population_info': {
                        'total_population': self.total_population,
                        'adjusted_population': self.adjusted_population,
                        'expected_pregnancies': self.expected_pregnancies,
                        'expected_deliveries': self.expected_deliveries,
                        'period_type': self.period_type.value
                    }
                }
            }
            
            # Aggregate validation results
            self._aggregate_validation_results()
            
            # Update status
            self.processed_at = datetime.utcnow()
            self.status = UploadStatus.COMPLETED
            
            return True, "Data processed successfully"
            
        except Exception as e:
            self.status = UploadStatus.FAILED
            self.error_log = str(e)
            return False, f"Processing failed: {str(e)}"
    
    def _aggregate_validation_results(self):
        """Aggregate validation results from all MNCAH categories"""
        if not self.processed_data:
            return
        
        all_validations = {}
        total_count = 0
        valid_count = 0
        warning_count = 0
        error_count = 0
        
        # Collect validations from all categories
        for category in ['anc', 'intrapartum', 'pnc']:
            if category in self.processed_data:
                category_validations = self.processed_data[category].get('validations', {})
                for indicator, status in category_validations.items():
                    full_indicator_name = f"{category}_{indicator}"
                    all_validations[full_indicator_name] = status
                    total_count += 1
                    
                    if status == 'green':
                        valid_count += 1
                    elif status == 'yellow':
                        warning_count += 1
                    elif status in ['red', 'blue']:
                        error_count += 1
        
        # Store aggregated results
        self.validation_results = all_validations
        self.total_indicators = total_count
        self.valid_indicators = valid_count
        self.warning_indicators = warning_count
        self.error_indicators = error_count
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results"""
        return {
            'total_indicators': self.total_indicators,
            'valid_indicators': self.valid_indicators,
            'warning_indicators': self.warning_indicators,
            'error_indicators': self.error_indicators,
            'validation_rate': (self.valid_indicators / self.total_indicators * 100) if self.total_indicators > 0 else 0,
            'has_critical_issues': self.error_indicators > 0,
            'overall_status': self._get_overall_validation_status()
        }
    
    def _get_overall_validation_status(self) -> str:
        """Determine overall validation status"""
        if self.total_indicators == 0:
            return "no_data"
        elif self.error_indicators > 0:
            return "has_errors"
        elif self.warning_indicators > 0:
            return "has_warnings"
        else:
            return "all_valid"
    
    def get_indicator_value(self, category: str, indicator: str) -> Optional[float]:
        """Get calculated value for specific indicator"""
        if not self.processed_data or category not in self.processed_data:
            return None
        
        indicators = self.processed_data[category].get('indicators', {})
        return indicators.get(indicator)
    
    def get_indicator_validation(self, category: str, indicator: str) -> Optional[str]:
        """Get validation status for specific indicator"""
        if not self.processed_data or category not in self.processed_data:
            return None
        
        validations = self.processed_data[category].get('validations', {})
        return validations.get(indicator)
    
    def to_dict(self, include_data: bool = False) -> Dict[str, Any]:
        """
        Convert upload record to dictionary
        
        Args:
            include_data: Whether to include processed data (can be large)
        """
        result = {
            'id': self.id,
            'filename': self.original_filename,
            'facility_name': self.facility_name,
            'district': self.district,
            'region': self.region,
            'total_population': self.total_population,
            'adjusted_population': self.adjusted_population,
            'period_type': self.period_type.value,
            'reporting_period': self.reporting_period,
            'uploaded_at': self.uploaded_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'status': self.status.value,
            'validation_summary': self.get_validation_summary(),
            'file_size': self.file_size
        }
        
        if include_data:
            result.update({
                'raw_data': self.raw_data,
                'processed_data': self.processed_data,
                'validation_results': self.validation_results,
                'error_log': self.error_log
            })
        
        return result
    
    @validates('facility_name')
    def validate_facility_name(self, key, facility_name):
        """Validate facility name"""
        if not facility_name or not facility_name.strip():
            raise ValueError("Facility name is required")
        return facility_name.strip()
    
    @validates('total_population')
    def validate_population(self, key, population):
        """Validate population value"""
        if population <= 0:
            raise ValueError("Population must be greater than 0")
        if population > 10000000:  # 10 million max
            raise ValueError("Population value seems too large")
        return population
    
    def __repr__(self):
        return f'<DataUpload {self.facility_name} - {self.reporting_period}>'


class DataProcessor:
    """
    Helper class for processing uploaded data files
    """
    
    SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
    
    @classmethod
    def validate_file(cls, file_path: str, filename: str) -> Tuple[bool, str]:
        """
        Validate uploaded file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in cls.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type. Supported: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
        
        # Check file size
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > cls.MAX_FILE_SIZE:
                return False, f"File too large. Maximum size: {cls.MAX_FILE_SIZE // (1024*1024)}MB"
        
        return True, ""
    
    @classmethod
    def extract_data_from_file(cls, file_path: str, filename: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Extract data from uploaded file
        
        Returns:
            Tuple of (success, data_dict, error_message)
        """
        try:
            _, ext = os.path.splitext(filename.lower())
            
            if ext == '.csv':
                return cls._process_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                return cls._process_excel(file_path)
            else:
                return False, {}, "Unsupported file format"
                
        except Exception as e:
            return False, {}, f"Error processing file: {str(e)}"
    
    @classmethod
    def _process_csv(cls, file_path: str) -> Tuple[bool, Dict[str, Any], str]:
        """Process CSV file"""
        
        try:
            # Read CSV with multiple possible delimiters
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # If only one column, try different separators
            if len(df.columns) == 1:
                for sep in [';', '\t', '|']:
                    try:
                        df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                        if len(df.columns) > 1:
                            break
                    except:
                        continue
            
            return cls._extract_indicators_from_dataframe(df)
            
        except Exception as e:
            return False, {}, f"CSV processing error: {str(e)}"
    
    @classmethod
    def _process_excel(cls, file_path: str) -> Tuple[bool, Dict[str, Any], str]:
        """Process Excel file"""
        
        try:
            # Read Excel file (try first sheet)
            df = pd.read_excel(file_path, engine='openpyxl')
            return cls._extract_indicators_from_dataframe(df)
            
        except Exception as e:
            return False, {}, f"Excel processing error: {str(e)}"
    
    @classmethod
    def _extract_indicators_from_dataframe(cls, df) -> Tuple[bool, Dict[str, Any], str]:
        """
        Extract MNCAH indicators from DataFrame
        
        Expected format: columns like 'indicator_code' and 'value'
        or 'Indicator Code' and 'Value', etc.
        """
        try:
            # Normalize column names
            df.columns = df.columns.str.lower().str.strip()
            
            # Find indicator code and value columns
            code_col = None
            value_col = None
            
            for col in df.columns:
                if any(term in col for term in ['indicator', 'code', 'element']):
                    code_col = col
                elif any(term in col for term in ['value', 'count', 'number', 'total']):
                    value_col = col
            
            if not code_col or not value_col:
                return False, {}, "Could not find indicator code and value columns"
            
            # Extract data
            data = {}
            for _, row in df.iterrows():
                code = str(row[code_col]).strip()
                value = row[value_col]
                
                # Skip empty rows
                if pd.isna(code) or code == '' or pd.isna(value):
                    continue
                
                # Convert value to float
                try:
                    data[code] = float(value)
                except (ValueError, TypeError):
                    continue  # Skip invalid values
            
            if not data:
                return False, {}, "No valid indicator data found in file"
            
            return True, data, ""
            
        except Exception as e:
            return False, {}, f"Data extraction error: {str(e)}"
    
    @classmethod
    def create_upload_record(cls, file_path: str, original_filename: str, 
                           facility_name: str, population: int, period_type: str,
                           reporting_period: str, user_id: int, **kwargs) -> DataUpload:
        """
        Create upload record with extracted data
        
        Returns:
            DataUpload object
        """
        # Validate and extract data from file
        is_valid, error_msg = cls.validate_file(file_path, original_filename)
        if not is_valid:
            raise ValueError(error_msg)
        
        success, raw_data, error_msg = cls.extract_data_from_file(file_path, original_filename)
        if not success:
            raise ValueError(error_msg)
        
        # Create upload record
        upload = DataUpload(
            filename=os.path.basename(file_path),
            original_filename=original_filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            facility_name=facility_name,
            total_population=population,
            period_type=PeriodType(period_type),
            reporting_period=reporting_period,
            uploaded_by=user_id,
            raw_data=raw_data,
            **kwargs
        )
        
        return upload
