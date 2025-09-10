"""
Data Validation Service
This service handles all data validation rules, quality checks, and outlier detection
for the MOH MNCAH Dashboard System.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..models.base import ValidationStatus


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Data class to represent a validation issue"""
    indicator: str
    category: str
    severity: ValidationSeverity
    message: str
    current_value: float
    expected_range: Optional[Tuple[float, float]] = None
    recommendation: Optional[str] = None


class DataValidationService:
    """
    Service for comprehensive data validation and quality assessment
    """
    
    def __init__(self):
        """Initialize validation service"""
        self.logger = logging.getLogger(__name__)
        
        # Define validation rules for each indicator
        self.validation_rules = self._initialize_validation_rules()
        
        # Define outlier detection thresholds
        self.outlier_thresholds = self._initialize_outlier_thresholds()
    
    def _initialize_validation_rules(self) -> Dict[str, Dict]:
        """Initialize comprehensive validation rules for all indicators"""
        return {
            # ANC Indicators
            'anc_1_coverage': {
                'min_value': 0,
                'max_value': None,  # Can exceed 100% (population-based)
                'allow_over_100': True,
                'target_green': (100, float('inf')),
                'target_yellow': (70, 99.9),
                'target_red': (0, 69.9),
                'typical_range': (60, 120),
                'critical_low': 30
            },
            'anc_1st_trimester': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (45, 100),
                'target_yellow': (30, 44.9),
                'target_red': (0, 29.9),
                'typical_range': (25, 80),
                'critical_low': 15
            },
            'anc_4_coverage': {
                'min_value': 0,
                'max_value': None,
                'allow_over_100': True,
                'target_green': (100, float('inf')),
                'target_yellow': (70, 99.9),
                'target_red': (0, 69.9),
                'typical_range': (50, 100),
                'critical_low': 25
            },
            'anc_8_coverage': {
                'min_value': 0,
                'max_value': None,
                'allow_over_100': True,
                'target_green': (100, float('inf')),
                'target_yellow': (70, 99.9),
                'target_red': (0, 69.9),
                'typical_range': (40, 90),
                'critical_low': 20
            },
            'ipt3_coverage': {
                'min_value': 0,
                'max_value': None,
                'allow_over_100': True,
                'target_green': (85, float('inf')),
                'target_yellow': (65, 84.9),
                'target_red': (0, 64.9),
                'typical_range': (60, 95),
                'critical_low': 40
            },
            'hb_testing_coverage': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (75, 100),
                'target_yellow': (60, 74.9),
                'target_red': (0, 59.9),
                'typical_range': (55, 90),
                'critical_low': 30
            },
            'iron_folic_anc1': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (75, 100),
                'target_yellow': (60, 74.9),
                'target_red': (0, 59.9),
                'typical_range': (55, 85),
                'critical_low': 35
            },
            'llin_coverage': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (85, 100),
                'target_yellow': (65, 84.9),
                'target_red': (0, 64.9),
                'typical_range': (60, 95),
                'critical_low': 40
            },
            'ultrasound_coverage': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (60, 100),
                'target_yellow': (40, 59.9),
                'target_red': (0, 39.9),
                'typical_range': (30, 80),
                'critical_low': 15
            },
            
            # Intrapartum Indicators
            'institutional_deliveries': {
                'min_value': 0,
                'max_value': None,
                'allow_over_100': True,
                'target_green': (68, float('inf')),
                'target_yellow': (55, 67.9),
                'target_red': (0, 54.9),
                'typical_range': (50, 85),
                'critical_low': 30
            },
            'lbw_proportion': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (0, 5),
                'target_yellow': (5.1, 10),
                'target_red': (10.1, 100),
                'typical_range': (3, 15),
                'critical_high': 20
            },
            'lbw_kmc_proportion': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (100, 100),
                'target_yellow': (90, 99.9),
                'target_red': (0, 89.9),
                'typical_range': (75, 100),
                'critical_low': 50
            },
            'birth_asphyxia_proportion': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (0, 1),
                'target_yellow': (1.1, 3),
                'target_red': (3.1, 100),
                'typical_range': (0.5, 5),
                'critical_high': 8
            },
            'successful_resuscitation_proportion': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (100, 100),
                'target_yellow': (80, 99.9),
                'target_red': (0, 79.9),
                'typical_range': (70, 100),
                'critical_low': 60
            },
            'fresh_stillbirths_rate': {
                'min_value': 0,
                'max_value': 1000,
                'allow_over_100': True,
                'target_green': (0, 5),
                'target_yellow': (5.1, 10),
                'target_red': (10.1, 1000),
                'typical_range': (2, 15),
                'critical_high': 25
            },
            'neonatal_mortality_rate': {
                'min_value': 0,
                'max_value': 1000,
                'allow_over_100': True,
                'target_green': (0, 5),
                'target_yellow': (5.1, 10),
                'target_red': (10.1, 1000),
                'typical_range': (3, 20),
                'critical_high': 30
            },
            'perinatal_mortality_rate': {
                'min_value': 0,
                'max_value': 1000,
                'allow_over_100': True,
                'target_green': (0, 12),
                'target_yellow': (12.1, 20),
                'target_red': (20.1, 1000),
                'typical_range': (8, 30),
                'critical_high': 50
            },
            'maternal_mortality_ratio': {
                'min_value': 0,
                'max_value': 100000,
                'allow_over_100': True,
                'target_green': (0, 200),
                'target_yellow': (201, 400),
                'target_red': (401, 100000),
                'typical_range': (100, 800),
                'critical_high': 1000
            },
            
            # PNC Indicators
            'breastfeeding_1hour': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (100, 100),
                'target_yellow': (90, 99.9),
                'target_red': (0, 89.9),
                'typical_range': (80, 100),
                'critical_low': 60
            },
            'pnc_24hours': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (100, 100),
                'target_yellow': (90, 99.9),
                'target_red': (0, 89.9),
                'typical_range': (75, 100),
                'critical_low': 50
            },
            'pnc_6days': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (75, 100),
                'target_yellow': (60, 74.9),
                'target_red': (0, 59.9),
                'typical_range': (50, 85),
                'critical_low': 30
            },
            'pnc_6weeks': {
                'min_value': 0,
                'max_value': 100,
                'allow_over_100': False,
                'target_green': (75, 100),
                'target_yellow': (60, 74.9),
                'target_red': (0, 59.9),
                'typical_range': (45, 80),
                'critical_low': 25
            }
        }
    
    def _initialize_outlier_thresholds(self) -> Dict[str, float]:
        """Initialize outlier detection thresholds (Z-score based)"""
        return {
            'mild_outlier': 2.0,    # 2 standard deviations
            'severe_outlier': 3.0,  # 3 standard deviations
            'extreme_outlier': 4.0  # 4 standard deviations
        }
    
    def validate_upload_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of uploaded and processed data
        
        Args:
            processed_data: Dictionary containing calculated indicators
            
        Returns:
            Validation report with issues and recommendations
        """
        validation_report = {
            'validation_date': datetime.utcnow().isoformat(),
            'overall_status': 'valid',
            'issues': [],
            'summary': {
                'total_indicators': 0,
                'valid_indicators': 0,
                'issues_found': 0,
                'critical_issues': 0,
                'warnings': 0
            },
            'recommendations': []
        }
        
        try:
            # Validate each category
            for category in ['anc', 'intrapartum', 'pnc']:
                if category in processed_data:
                    category_issues = self._validate_category(
                        category, 
                        processed_data[category]
                    )
                    validation_report['issues'].extend(category_issues)
            
            # Update summary
            self._update_validation_summary(validation_report)
            
            # Generate recommendations
            validation_report['recommendations'] = self._generate_recommendations(
                validation_report['issues']
            )
            
            return validation_report
            
        except Exception as e:
            self.logger.error(f"Error in data validation: {str(e)}")
            validation_report['overall_status'] = 'error'
            validation_report['error'] = str(e)
            return validation_report
    
    def _validate_category(self, category: str, category_data: Dict) -> List[ValidationIssue]:
        """Validate indicators within a specific category"""
        issues = []
        
        indicators = category_data.get('indicators', {})
        validations = category_data.get('validations', {})
        
        for indicator, value in indicators.items():
            indicator_issues = self._validate_indicator(
                category, indicator, value, validations.get(indicator)
            )
            issues.extend(indicator_issues)
        
        return issues
    
    def _validate_indicator(self, category: str, indicator: str, value: float, 
                          validation_status: str) -> List[ValidationIssue]:
        """Validate individual indicator"""
        issues = []
        
        if indicator not in self.validation_rules:
            # Unknown indicator
            issues.append(ValidationIssue(
                indicator=indicator,
                category=category,
                severity=ValidationSeverity.WARNING,
                message=f"No validation rules defined for indicator {indicator}",
                current_value=value
            ))
            return issues
        
        rules = self.validation_rules[indicator]
        
        # Check for basic data quality issues
        if value < 0:
            issues.append(ValidationIssue(
                indicator=indicator,
                category=category,
                severity=ValidationSeverity.CRITICAL,
                message="Negative values are not allowed for health indicators",
                current_value=value,
                recommendation="Review data entry and calculation methods"
            ))
        
        # Check maximum value constraints
        if rules['max_value'] is not None and value > rules['max_value']:
            issues.append(ValidationIssue(
                indicator=indicator,
                category=category,
                severity=ValidationSeverity.CRITICAL,
                message=f"Value exceeds maximum allowed ({rules['max_value']})",
                current_value=value,
                recommendation="Verify data accuracy and calculation formulas"
            ))
        
        # Check for values over 100% where not allowed
        if not rules['allow_over_100'] and value > 100:
            issues.append(ValidationIssue(
                indicator=indicator,
                category=category,
                severity=ValidationSeverity.ERROR,
                message="Value cannot exceed 100% for this indicator",
                current_value=value,
                recommendation="Check numerator and denominator values for calculation errors"
            ))
        
        # Check for critical thresholds
        if 'critical_low' in rules and value < rules['critical_low']:
            issues.append(ValidationIssue(
                indicator=indicator,
                category=category,
                severity=ValidationSeverity.CRITICAL,
                message=f"Value is critically low (below {rules['critical_low']})",
                current_value=value,
                recommendation="Immediate intervention required to improve service delivery"
            ))
        
        if 'critical_high' in rules and value > rules['critical_high']:
            issues.append(ValidationIssue(
                indicator=indicator,
                category=category,
                severity=ValidationSeverity.CRITICAL,
                message=f"Value is critically high (above {rules['critical_high']})",
                current_value=value,
                recommendation="Investigate causes and implement corrective measures"
            ))
        
        # Check for outliers compared to typical ranges
        typical_range = rules.get('typical_range')
        if typical_range and (value < typical_range[0] or value > typical_range[1]):
            severity = ValidationSeverity.WARNING
            if value < typical_range[0] - (typical_range[1] - typical_range[0]) * 0.5:
                severity = ValidationSeverity.ERROR
            elif value > typical_range[1] + (typical_range[1] - typical_range[0]) * 0.5:
                severity = ValidationSeverity.ERROR
            
            issues.append(ValidationIssue(
                indicator=indicator,
                category=category,
                severity=severity,
                message=f"Value outside typical range ({typical_range[0]}-{typical_range[1]})",
                current_value=value,
                expected_range=typical_range,
                recommendation="Review data for potential errors or investigate unusual circumstances"
            ))
        
        return issues
    
    def _update_validation_summary(self, validation_report: Dict) -> None:
        """Update validation summary statistics"""
        issues = validation_report['issues']
        
        # Count by severity
        critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        
        validation_report['summary'].update({
            'issues_found': len(issues),
            'critical_issues': critical_count,
            'errors': error_count,
            'warnings': warning_count
        })
        
        # Determine overall status
        if critical_count > 0:
            validation_report['overall_status'] = 'critical'
        elif error_count > 0:
            validation_report['overall_status'] = 'error'
        elif warning_count > 0:
            validation_report['overall_status'] = 'warning'
        else:
            validation_report['overall_status'] = 'valid'
    
    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate actionable recommendations based on validation issues"""
        recommendations = []
        
        # Count issues by type
        critical_indicators = set()
        data_quality_issues = 0
        over_100_issues = 0
        negative_value_issues = 0
        
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                critical_indicators.add(issue.indicator)
            
            if "negative" in issue.message.lower():
                negative_value_issues += 1
            elif "exceed 100%" in issue.message:
                over_100_issues += 1
            elif "data" in issue.message.lower():
                data_quality_issues += 1
        
        # Generate specific recommendations
        if critical_indicators:
            recommendations.append(
                f"URGENT: {len(critical_indicators)} indicators have critical issues requiring "
                "immediate attention and intervention."
            )
        
        if negative_value_issues > 0:
            recommendations.append(
                "Review data entry processes to prevent negative values. Implement validation "
                "at data entry level."
            )
        
        if over_100_issues > 0:
            recommendations.append(
                "Verify calculation formulas and check numerator/denominator relationships "
                "for indicators exceeding 100%."
            )
        
        if data_quality_issues > 3:
            recommendations.append(
                "Consider comprehensive data quality training and implement automated "
                "validation checks in data collection systems."
            )
        
        # General recommendations
        if len(issues) > 10:
            recommendations.append(
                "High number of validation issues detected. Recommend systematic review "
                "of data collection and processing procedures."
            )
        
        return recommendations
    
    def detect_historical_anomalies(self, historical_data: List[Dict], 
                                  current_data: Dict) -> Dict[str, Any]:
        """
        Detect anomalies by comparing current data with historical trends
        
        Args:
            historical_data: List of previous data uploads
            current_data: Current upload data
            
        Returns:
            Anomaly detection report
        """
        anomaly_report = {
            'analysis_date': datetime.utcnow().isoformat(),
            'anomalies_detected': [],
            'statistical_summary': {},
            'recommendations': []
        }
        
        try:
            if len(historical_data) < 3:
                anomaly_report['note'] = 'Insufficient historical data for anomaly detection (minimum 3 data points required)'
                return anomaly_report
            
            # Extract indicator time series
            indicator_series = self._extract_time_series(historical_data)
            
            # Check current values against historical patterns
            current_indicators = self._extract_current_indicators(current_data)
            
            for indicator, current_value in current_indicators.items():
                if indicator in indicator_series and len(indicator_series[indicator]) >= 3:
                    anomaly = self._detect_indicator_anomaly(
                        indicator, current_value, indicator_series[indicator]
                    )
                    if anomaly:
                        anomaly_report['anomalies_detected'].append(anomaly)
            
            # Generate statistical summary
            anomaly_report['statistical_summary'] = self._generate_anomaly_summary(
                anomaly_report['anomalies_detected']
            )
            
            return anomaly_report
            
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {str(e)}")
            anomaly_report['error'] = str(e)
            return anomaly_report
    
    def _extract_time_series(self, historical_data: List[Dict]) -> Dict[str, List[float]]:
        """Extract time series data for each indicator"""
        indicator_series = {}
        
        for data_point in historical_data:
            if 'processed_data' not in data_point:
                continue
            
            for category in ['anc', 'intrapartum', 'pnc']:
                if category in data_point['processed_data']:
                    indicators = data_point['processed_data'][category].get('indicators', {})
                    for indicator, value in indicators.items():
                        full_name = f"{category}_{indicator}"
                        if full_name not in indicator_series:
                            indicator_series[full_name] = []
                        indicator_series[full_name].append(value)
        
        return indicator_series
    
    def _extract_current_indicators(self, current_data: Dict) -> Dict[str, float]:
        """Extract current indicator values"""
        current_indicators = {}
        
        if 'processed_data' in current_data:
            for category in ['anc', 'intrapartum', 'pnc']:
                if category in current_data['processed_data']:
                    indicators = current_data['processed_data'][category].get('indicators', {})
                    for indicator, value in indicators.items():
                        full_name = f"{category}_{indicator}"
                        current_indicators[full_name] = value
        
        return current_indicators
    
    def _detect_indicator_anomaly(self, indicator: str, current_value: float, 
                                historical_values: List[float]) -> Optional[Dict]:
        """Detect anomaly for specific indicator using statistical methods"""
        if len(historical_values) < 3:
            return None
        
        # Calculate statistical measures
        mean = sum(historical_values) / len(historical_values)
        variance = sum((x - mean) ** 2 for x in historical_values) / len(historical_values)
        std_dev = variance ** 0.5
        
        if std_dev == 0:  # No variation in historical data
            if current_value != mean:
                return {
                    'indicator': indicator,
                    'current_value': current_value,
                    'historical_mean': mean,
                    'anomaly_type': 'deviation_from_constant',
                    'severity': 'moderate',
                    'message': f'Value differs from constant historical value of {mean:.2f}'
                }
            return None
        
        # Calculate Z-score
        z_score = abs(current_value - mean) / std_dev
        
        # Determine anomaly severity
        if z_score >= self.outlier_thresholds['extreme_outlier']:
            severity = 'extreme'
        elif z_score >= self.outlier_thresholds['severe_outlier']:
            severity = 'severe'
        elif z_score >= self.outlier_thresholds['mild_outlier']:
            severity = 'mild'
        else:
            return None  # Not an anomaly
        
        return {
            'indicator': indicator,
            'current_value': current_value,
            'historical_mean': mean,
            'historical_std': std_dev,
            'z_score': z_score,
            'anomaly_type': 'statistical_outlier',
            'severity': severity,
            'message': f'Value is {z_score:.2f} standard deviations from historical mean',
            'direction': 'above' if current_value > mean else 'below'
        }
    
    def _generate_anomaly_summary(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """Generate summary of detected anomalies"""
        if not anomalies:
            return {'total_anomalies': 0, 'message': 'No anomalies detected'}
        
        severity_counts = {}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_anomalies': len(anomalies),
            'severity_distribution': severity_counts,
            'most_severe': max(anomalies, key=lambda x: {'extreme': 4, 'severe': 3, 'mild': 2}.get(x.get('severity'), 1)),
            'categories_affected': len(set(a['indicator'].split('_')[0] for a in anomalies))
        }
    
    def generate_data_quality_report(self, upload_data: Dict) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report
        
        Args:
            upload_data: Complete upload data with validation results
            
        Returns:
            Comprehensive data quality report
        """
        report = {
            'report_date': datetime.utcnow().isoformat(),
            'facility_name': upload_data.get('facility_name', 'Unknown'),
            'reporting_period': upload_data.get('reporting_period', 'Unknown'),
            'data_quality_score': 0,
            'quality_dimensions': {},
            'recommendations': [],
            'executive_summary': ''
        }
        
        try:
            # Calculate quality dimensions
            completeness_score = self._assess_completeness(upload_data)
            accuracy_score = self._assess_accuracy(upload_data)
            consistency_score = self._assess_consistency(upload_data)
            validity_score = self._assess_validity(upload_data)
            
            report['quality_dimensions'] = {
                'completeness': completeness_score,
                'accuracy': accuracy_score,
                'consistency': consistency_score,
                'validity': validity_score
            }
            
            # Calculate overall score (weighted average)
            weights = {'completeness': 0.25, 'accuracy': 0.30, 'consistency': 0.25, 'validity': 0.20}
            report['data_quality_score'] = sum(
                score * weights[dimension] 
                for dimension, score in report['quality_dimensions'].items()
            )
            
            # Generate recommendations
            report['recommendations'] = self._generate_quality_recommendations(
                report['quality_dimensions']
            )
            
            # Create executive summary
            report['executive_summary'] = self._create_executive_summary(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating data quality report: {str(e)}")
            report['error'] = str(e)
            return report
    
    def _assess_completeness(self, upload_data: Dict) -> float:
        """Assess data completeness (0-100 score)"""
        required_indicators = len(self.validation_rules)
        
        if 'processed_data' not in upload_data:
            return 0.0
        
        found_indicators = 0
        for category in ['anc', 'intrapartum', 'pnc']:
            if category in upload_data['processed_data']:
                indicators = upload_data['processed_data'][category].get('indicators', {})
                found_indicators += len(indicators)
        
        return min(100, (found_indicators / required_indicators) * 100)
    
    def _assess_accuracy(self, upload_data: Dict) -> float:
        """Assess data accuracy based on validation results (0-100 score)"""
        if 'validation_results' not in upload_data:
            return 50.0  # Default score if no validation available
        
        validation_results = upload_data['validation_results']
        if not validation_results:
            return 50.0
        
        green_count = sum(1 for status in validation_results.values() if status == 'green')
        total_count = len(validation_results)
        
        return (green_count / total_count * 100) if total_count > 0 else 0.0
    
    def _assess_consistency(self, upload_data: Dict) -> float:
        """Assess internal data consistency (0-100 score)"""
        # Check for logical consistency between related indicators
        consistency_checks = []
        
        if 'processed_data' in upload_data:
            # ANC consistency checks
            if 'anc' in upload_data['processed_data']:
                anc_indicators = upload_data['processed_data']['anc'].get('indicators', {})
                
                # ANC 4 should be <= ANC 1
                if 'anc_1_coverage' in anc_indicators and 'anc_4_coverage' in anc_indicators:
                    consistency_checks.append(
                        anc_indicators['anc_4_coverage'] <= anc_indicators['anc_1_coverage'] * 1.1  # Allow 10% margin
                    )
                
                # ANC 8 should be <= ANC 4
                if 'anc_4_coverage' in anc_indicators and 'anc_8_coverage' in anc_indicators:
                    consistency_checks.append(
                        anc_indicators['anc_8_coverage'] <= anc_indicators['anc_4_coverage'] * 1.1
                    )
        
        if not consistency_checks:
            return 80.0  # Default if no checks possible
        
        passed_checks = sum(consistency_checks)
        return (passed_checks / len(consistency_checks) * 100)
    
    def _assess_validity(self, upload_data: Dict) -> float:
        """Assess data validity against business rules (0-100 score)"""
        validity_score = 100.0
        
        if 'processed_data' not in upload_data:
            return 0.0
        
        # Check for values outside reasonable ranges
        penalty_count = 0
        total_indicators = 0
        
        for category in ['anc', 'intrapartum', 'pnc']:
            if category in upload_data['processed_data']:
                indicators = upload_data['processed_data'][category].get('indicators', {})
                for indicator, value in indicators.items():
                    total_indicators += 1
                    
                    if indicator in self.validation_rules:
                        rules = self.validation_rules[indicator]
                        typical_range = rules.get('typical_range')
                        
                        if typical_range:
                            # Penalize values significantly outside typical range
                            if value < typical_range[0] * 0.5 or value > typical_range[1] * 2:
                                penalty_count += 1
        
        if total_indicators > 0:
            validity_score -= (penalty_count / total_indicators * 50)  # Up to 50 point penalty
        
        return max(0, validity_score)
    
    def _generate_quality_recommendations(self, quality_dimensions: Dict[str, float]) -> List[str]:
        """Generate recommendations based on quality assessment"""
        recommendations = []
        
        for dimension, score in quality_dimensions.items():
            if score < 60:
                if dimension == 'completeness':
                    recommendations.append(
                        "Data completeness is low. Ensure all required indicators are included in uploads."
                    )
                elif dimension == 'accuracy':
                    recommendations.append(
                        "Data accuracy issues detected. Review calculation methods and data entry procedures."
                    )
                elif dimension == 'consistency':
                    recommendations.append(
                        "Data consistency problems found. Check for logical relationships between indicators."
                    )
                elif dimension == 'validity':
                    recommendations.append(
                        "Data validity concerns identified. Verify values are within expected ranges."
                    )
            elif score < 80:
                recommendations.append(f"Moderate {dimension} issues - consider process improvements.")
        
        # Overall recommendations
        overall_score = sum(quality_dimensions.values()) / len(quality_dimensions)
        if overall_score < 70:
            recommendations.append(
                "Overall data quality is below acceptable standards. Recommend comprehensive review "
                "of data collection and processing systems."
            )
        
        return recommendations
    
    def _create_executive_summary(self, report: Dict[str, Any]) -> str:
        """Create executive summary of data quality assessment"""
        score = report['data_quality_score']
        facility = report['facility_name']
        period = report['reporting_period']
        
        if score >= 90:
            quality_level = "Excellent"
            summary = f"Data quality for {facility} ({period}) is excellent with minimal issues detected."
        elif score >= 80:
            quality_level = "Good"
            summary = f"Data quality for {facility} ({period}) is good with minor improvements needed."
        elif score >= 70:
            quality_level = "Acceptable"
            summary = f"Data quality for {facility} ({period}) is acceptable but requires attention."
        elif score >= 60:
            quality_level = "Poor"
            summary = f"Data quality for {facility} ({period}) is poor and needs significant improvement."
        else:
            quality_level = "Critical"
            summary = f"Data quality for {facility} ({period}) is critically low and requires immediate action."
        
        # Add dimension-specific insights
        dimensions = report['quality_dimensions']
        weak_areas = [dim for dim, score in dimensions.items() if score < 70]
        
        if weak_areas:
            summary += f" Key areas needing improvement: {', '.join(weak_areas)}."
        
        return summary
    
    def check_data_freshness(self, upload_date: datetime, 
                           reporting_period: str, 
                           period_type: str) -> Dict[str, Any]:
        """
        Check if data is submitted within acceptable timeframes
        
        Args:
            upload_date: When data was uploaded
            reporting_period: The reporting period
            period_type: Type of period (monthly/quarterly/annual)
            
        Returns:
            Freshness assessment
        """
        freshness_report = {
            'upload_date': upload_date.isoformat(),
            'reporting_period': reporting_period,
            'period_type': period_type,
            'is_timely': True,
            'days_delay': 0,
            'status': 'on_time',
            'message': ''
        }
        
        try:
            # Define acceptable delays by period type
            max_delays = {
                'monthly': 15,    # 15 days after month end
                'quarterly': 30,  # 30 days after quarter end
                'annual': 60      # 60 days after year end
            }
            
            max_delay = max_delays.get(period_type, 30)
            
            # For demonstration, assume data should be submitted within max_delay days
            # In real implementation, you'd parse the reporting_period to get exact dates
            current_date = datetime.utcnow()
            days_since_upload = (current_date - upload_date).days
            
            # Simple freshness check (can be enhanced with actual period parsing)
            if days_since_upload > max_delay:
                freshness_report.update({
                    'is_timely': False,
                    'days_delay': days_since_upload - max_delay,
                    'status': 'delayed',
                    'message': f'Data submitted {days_since_upload - max_delay} days beyond acceptable timeframe'
                })
            elif days_since_upload > max_delay * 0.8:  # Warning threshold
                freshness_report.update({
                    'status': 'near_deadline',
                    'message': 'Data submitted close to deadline'
                })
            else:
                freshness_report['message'] = 'Data submitted in timely manner'
            
            return freshness_report
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness: {str(e)}")
            freshness_report['error'] = str(e)
            return freshness_report
    
    def generate_validation_dashboard_data(self, 
                                         validation_results: List[Dict]) -> Dict[str, Any]:
        """
        Generate aggregated data for validation dashboard
        
        Args:
            validation_results: List of validation results from multiple uploads
            
        Returns:
            Dashboard data for validation monitoring
        """
        dashboard_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'total_uploads': len(validation_results),
            'validation_overview': {
                'valid_uploads': 0,
                'uploads_with_warnings': 0,
                'uploads_with_errors': 0,
                'uploads_with_critical_issues': 0
            },
            'indicator_quality_trends': {},
            'facility_performance': {},
            'common_issues': [],
            'recommendations': []
        }
        
        try:
            # Process each validation result
            all_issues = []
            facility_scores = {}
            
            for result in validation_results:
                facility = result.get('facility_name', 'Unknown')
                
                # Count upload status
                if result.get('overall_status') == 'valid':
                    dashboard_data['validation_overview']['valid_uploads'] += 1
                elif result.get('overall_status') == 'warning':
                    dashboard_data['validation_overview']['uploads_with_warnings'] += 1
                elif result.get('overall_status') == 'error':
                    dashboard_data['validation_overview']['uploads_with_errors'] += 1
                elif result.get('overall_status') == 'critical':
                    dashboard_data['validation_overview']['uploads_with_critical_issues'] += 1
                
                # Collect issues for analysis
                if 'issues' in result:
                    all_issues.extend(result['issues'])
                
                # Track facility performance
                quality_score = result.get('data_quality_score', 0)
                if facility not in facility_scores:
                    facility_scores[facility] = []
                facility_scores[facility].append(quality_score)
            
            # Analyze common issues
            dashboard_data['common_issues'] = self._analyze_common_issues(all_issues)
            
            # Calculate facility performance averages
            for facility, scores in facility_scores.items():
                avg_score = sum(scores) / len(scores)
                dashboard_data['facility_performance'][facility] = {
                    'average_quality_score': avg_score,
                    'total_uploads': len(scores),
                    'performance_trend': 'stable'  # Could be enhanced with trend analysis
                }
            
            # Generate system-wide recommendations
            dashboard_data['recommendations'] = self._generate_system_recommendations(
                dashboard_data['validation_overview'],
                dashboard_data['common_issues']
            )
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating validation dashboard data: {str(e)}")
            dashboard_data['error'] = str(e)
            return dashboard_data
    
    def _analyze_common_issues(self, all_issues: List[ValidationIssue]) -> List[Dict]:
        """Analyze and rank common validation issues"""
        issue_counts = {}
        
        for issue in all_issues:
            issue_type = issue.message
            if issue_type not in issue_counts:
                issue_counts[issue_type] = {
                    'count': 0,
                    'severity': issue.severity.value,
                    'indicators_affected': set(),
                    'categories_affected': set()
                }
            
            issue_counts[issue_type]['count'] += 1
            issue_counts[issue_type]['indicators_affected'].add(issue.indicator)
            issue_counts[issue_type]['categories_affected'].add(issue.category)
        
        # Convert to list and sort by frequency
        common_issues = []
        for issue_type, data in issue_counts.items():
            common_issues.append({
                'issue_type': issue_type,
                'frequency': data['count'],
                'severity': data['severity'],
                'indicators_affected': len(data['indicators_affected']),
                'categories_affected': list(data['categories_affected']),
                'percentage': 0  # Will be calculated after sorting
            })
        
        # Sort by frequency and calculate percentages
        common_issues.sort(key=lambda x: x['frequency'], reverse=True)
        total_issues = len(all_issues)
        
        for issue in common_issues:
            issue['percentage'] = (issue['frequency'] / total_issues * 100) if total_issues > 0 else 0
        
        return common_issues[:10]  # Return top 10 common issues
    
    def _generate_system_recommendations(self, 
                                       validation_overview: Dict, 
                                       common_issues: List[Dict]) -> List[str]:
        """Generate system-wide recommendations"""
        recommendations = []
        
        total_uploads = sum(validation_overview.values())
        if total_uploads == 0:
            return recommendations
        
        # Calculate percentages
        error_rate = (validation_overview['uploads_with_errors'] + 
                     validation_overview['uploads_with_critical_issues']) / total_uploads * 100
        
        if error_rate > 25:
            recommendations.append(
                "HIGH PRIORITY: Over 25% of uploads have critical data quality issues. "
                "Implement comprehensive data quality training program."
            )
        elif error_rate > 10:
            recommendations.append(
                "MEDIUM PRIORITY: Significant data quality issues detected. "
                "Review data collection processes and provide targeted training."
            )
        
        # Recommendations based on common issues
        if common_issues:
            top_issue = common_issues[0]
            if top_issue['frequency'] > total_uploads * 0.5:
                recommendations.append(
                    f"Address most common issue: '{top_issue['issue_type']}' affects "
                    f"{top_issue['percentage']:.1f}% of uploads."
                )
        
        # General recommendations
        valid_rate = validation_overview['valid_uploads'] / total_uploads * 100
        if valid_rate < 60:
            recommendations.extend([
                "Implement automated data validation at point of entry",
                "Establish data quality monitoring dashboard",
                "Create standardized data quality training materials",
                "Set up regular data quality review meetings"
            ])
        
        return recommendations
