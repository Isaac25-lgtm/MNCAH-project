"""
MNCAHAnalyzer class for performing analysis and calculating MNCAH indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime

from .mncah_data import MNCAHData


class MNCAHAnalyzer:
    """
    Class to perform comprehensive analysis of MNCAH data and calculate key indicators.
    
    Provides methods for trend analysis, comparative analysis, and target assessment.
    """
    
    # WHO/UNICEF targets for key indicators (for reference)
    GLOBAL_TARGETS = {
        'maternal_mortality_ratio': 70,  # per 100,000 live births by 2030
        'neonatal_mortality_rate': 12,   # per 1,000 live births by 2030
        'under5_mortality_rate': 25,     # per 1,000 live births by 2030
        'stunting_prevalence': 15,       # reduce by 40% by 2030
        'antenatal_care_coverage': 90,   # at least 4 visits
        'skilled_birth_attendance': 90,  # percentage
        'vaccination_coverage_dpt3': 90, # percentage
        'vaccination_coverage_measles': 95 # percentage
    }
    
    def __init__(self):
        """Initialize MNCAHAnalyzer."""
        self.logger = logging.getLogger(__name__)
        self.analysis_results = {}
        self.last_analysis_date = None
    
    def analyze_trends(self, data: MNCAHData, indicators: Optional[List[str]] = None) -> Dict:
        """
        Analyze trends for specified indicators over time.
        
        Args:
            data: MNCAHData object
            indicators: List of indicators to analyze (default: all available)
            
        Returns:
            Dictionary containing trend analysis results
        """
        if data.data.empty:
            return {}
        
        # Get available indicators
        available_indicators = [col for col in data.data.columns if col in data.ALL_INDICATORS]
        if not available_indicators:
            self.logger.warning("No MNCAH indicators found in data")
            return {}
        
        # Use specified indicators or all available
        if indicators is None:
            indicators = available_indicators
        else:
            indicators = [ind for ind in indicators if ind in available_indicators]
        
        trends = {}
        
        for indicator in indicators:
            indicator_trends = self._calculate_trend(data.data, indicator)
            if indicator_trends:
                trends[indicator] = indicator_trends
        
        self.analysis_results['trends'] = trends
        self.last_analysis_date = datetime.now()
        
        return trends
    
    def _calculate_trend(self, data: pd.DataFrame, indicator: str) -> Dict:
        """Calculate trend statistics for a single indicator."""
        if 'year' not in data.columns or indicator not in data.columns:
            return {}
        
        # Get clean data for the indicator
        clean_data = data[['year', indicator, 'country']].dropna()
        if len(clean_data) < 2:
            return {}
        
        # Calculate overall trend
        years = clean_data['year'].values
        values = clean_data[indicator].values
        
        # Linear regression for trend
        if len(years) > 1:
            trend_coef = np.polyfit(years, values, 1)[0]
        else:
            trend_coef = 0
        
        # Calculate summary statistics
        trend_info = {
            'overall_trend': 'improving' if trend_coef < 0 else 'worsening' if trend_coef > 0 else 'stable',
            'trend_coefficient': float(trend_coef),
            'data_points': len(clean_data),
            'year_range': [int(years.min()), int(years.max())],
            'value_range': [float(values.min()), float(values.max())],
            'latest_value': float(clean_data.loc[clean_data['year'].idxmax(), indicator]),
            'earliest_value': float(clean_data.loc[clean_data['year'].idxmin(), indicator])
        }
        
        # Country-specific trends
        country_trends = {}
        for country in clean_data['country'].unique():
            country_data = clean_data[clean_data['country'] == country]
            if len(country_data) >= 2:
                country_years = country_data['year'].values
                country_values = country_data[indicator].values
                country_coef = np.polyfit(country_years, country_values, 1)[0]
                
                country_trends[country] = {
                    'trend_coefficient': float(country_coef),
                    'trend_direction': 'improving' if country_coef < 0 else 'worsening' if country_coef > 0 else 'stable',
                    'data_points': len(country_data)
                }
        
        trend_info['country_trends'] = country_trends
        
        return trend_info
    
    def compare_countries(self, data: MNCAHData, indicators: Optional[List[str]] = None, 
                         year: Optional[int] = None) -> Dict:
        """
        Compare indicators across countries.
        
        Args:
            data: MNCAHData object
            indicators: List of indicators to compare
            year: Specific year for comparison (default: latest available)
            
        Returns:
            Dictionary containing country comparison results
        """
        if data.data.empty:
            return {}
        
        # Get available indicators
        available_indicators = [col for col in data.data.columns if col in data.ALL_INDICATORS]
        if not available_indicators:
            return {}
        
        if indicators is None:
            indicators = available_indicators
        else:
            indicators = [ind for ind in indicators if ind in available_indicators]
        
        # Determine year for comparison
        if year is None:
            year = data.data['year'].max()
        
        # Filter data for the specified year
        year_data = data.data[data.data['year'] == year]
        
        comparisons = {}
        
        for indicator in indicators:
            if indicator in year_data.columns:
                indicator_data = year_data[['country', indicator]].dropna()
                
                if len(indicator_data) > 0:
                    comparison_info = {
                        'year': year,
                        'countries_count': len(indicator_data),
                        'best_performing': {
                            'country': indicator_data.loc[indicator_data[indicator].idxmin(), 'country'],
                            'value': float(indicator_data[indicator].min())
                        },
                        'worst_performing': {
                            'country': indicator_data.loc[indicator_data[indicator].idxmax(), 'country'],
                            'value': float(indicator_data[indicator].max())
                        },
                        'average': float(indicator_data[indicator].mean()),
                        'median': float(indicator_data[indicator].median()),
                        'std_deviation': float(indicator_data[indicator].std()),
                        'country_values': indicator_data.set_index('country')[indicator].to_dict()
                    }
                    
                    comparisons[indicator] = comparison_info
        
        self.analysis_results['country_comparison'] = comparisons
        return comparisons
    
    def assess_targets(self, data: MNCAHData, custom_targets: Optional[Dict] = None) -> Dict:
        """
        Assess progress towards global targets.
        
        Args:
            data: MNCAHData object
            custom_targets: Custom target values (overrides global targets)
            
        Returns:
            Dictionary containing target assessment results
        """
        if data.data.empty:
            return {}
        
        # Use custom targets or global targets
        targets = custom_targets or self.GLOBAL_TARGETS
        
        latest_year = data.data['year'].max()
        latest_data = data.data[data.data['year'] == latest_year]
        
        target_assessment = {}
        
        for indicator, target_value in targets.items():
            if indicator in latest_data.columns:
                indicator_data = latest_data[['country', indicator]].dropna()
                
                if len(indicator_data) > 0:
                    # Calculate how many countries meet the target
                    meets_target = indicator_data[indicator] <= target_value
                    countries_meeting_target = meets_target.sum()
                    
                    assessment = {
                        'target_value': target_value,
                        'latest_year': latest_year,
                        'countries_assessed': len(indicator_data),
                        'countries_meeting_target': int(countries_meeting_target),
                        'percentage_meeting_target': float(countries_meeting_target / len(indicator_data) * 100),
                        'average_value': float(indicator_data[indicator].mean()),
                        'gap_to_target': float(indicator_data[indicator].mean() - target_value),
                        'countries_on_track': indicator_data[meets_target]['country'].tolist(),
                        'countries_off_track': indicator_data[~meets_target]['country'].tolist()
                    }
                    
                    target_assessment[indicator] = assessment
        
        self.analysis_results['target_assessment'] = target_assessment
        return target_assessment
    
    def calculate_composite_index(self, data: MNCAHData, indicators: List[str], 
                                weights: Optional[List[float]] = None) -> Dict:
        """
        Calculate a composite index from multiple indicators.
        
        Args:
            data: MNCAHData object
            indicators: List of indicators to include in composite
            weights: Weights for each indicator (default: equal weights)
            
        Returns:
            Dictionary containing composite index results
        """
        if data.data.empty:
            return {}
        
        # Validate indicators
        available_indicators = [ind for ind in indicators if ind in data.data.columns]
        if not available_indicators:
            return {}
        
        # Set equal weights if not provided
        if weights is None:
            weights = [1.0 / len(available_indicators)] * len(available_indicators)
        elif len(weights) != len(available_indicators):
            self.logger.warning("Weights length doesn't match indicators, using equal weights")
            weights = [1.0 / len(available_indicators)] * len(available_indicators)
        
        # Get latest year data
        latest_year = data.data['year'].max()
        latest_data = data.data[data.data['year'] == latest_year]
        
        # Calculate composite index for each country
        country_indices = {}
        
        for _, row in latest_data.iterrows():
            country = row['country']
            values = []
            
            for indicator in available_indicators:
                if pd.notna(row[indicator]):
                    # Normalize values (higher is better, so invert for mortality/morbidity indicators)
                    if 'mortality' in indicator or 'prevalence' in indicator:
                        normalized_value = 100 - min(100, row[indicator])  # Invert and cap at 100
                    else:
                        normalized_value = min(100, row[indicator])  # Cap at 100
                    values.append(normalized_value)
                else:
                    values.append(0)  # Handle missing values
            
            if values:
                composite_score = sum(w * v for w, v in zip(weights, values))
                country_indices[country] = float(composite_score)
        
        # Rank countries
        sorted_countries = sorted(country_indices.items(), key=lambda x: x[1], reverse=True)
        
        composite_results = {
            'indicators_used': available_indicators,
            'weights': weights,
            'year': latest_year,
            'country_scores': country_indices,
            'rankings': [{'rank': i+1, 'country': country, 'score': score} 
                        for i, (country, score) in enumerate(sorted_countries)],
            'top_performer': sorted_countries[0] if sorted_countries else None,
            'average_score': float(np.mean(list(country_indices.values()))) if country_indices else 0
        }
        
        self.analysis_results['composite_index'] = composite_results
        return composite_results
    
    def get_summary_report(self, data: MNCAHData) -> Dict:
        """
        Generate a comprehensive summary report.
        
        Args:
            data: MNCAHData object
            
        Returns:
            Dictionary containing summary report
        """
        summary = {
            'data_overview': {
                'total_records': len(data),
                'countries': data.get_countries(),
                'years': data.get_years(),
                'indicators_available': [col for col in data.data.columns if col in data.ALL_INDICATORS]
            },
            'data_quality': self._assess_data_quality(data),
            'basic_statistics': data.get_summary_stats()
        }
        
        # Add previous analysis results if available
        if self.analysis_results:
            summary['previous_analyses'] = {
                'available_analyses': list(self.analysis_results.keys()),
                'last_analysis_date': self.last_analysis_date.isoformat() if self.last_analysis_date else None
            }
        
        return summary
    
    def _assess_data_quality(self, data: MNCAHData) -> Dict:
        """Assess the quality of the data."""
        if data.data.empty:
            return {'status': 'no_data'}
        
        quality_assessment = {
            'completeness': {},
            'consistency': {},
            'outliers': {}
        }
        
        # Assess completeness
        for col in data.data.columns:
            if col in data.ALL_INDICATORS:
                missing_count = data.data[col].isna().sum()
                total_count = len(data.data)
                completeness_rate = (total_count - missing_count) / total_count * 100
                quality_assessment['completeness'][col] = {
                    'completeness_rate': float(completeness_rate),
                    'missing_values': int(missing_count)
                }
        
        # Check for duplicate records
        duplicates = data.data.duplicated().sum()
        quality_assessment['consistency']['duplicate_records'] = int(duplicates)
        
        # Basic outlier detection for numerical indicators
        for col in data.data.columns:
            if col in data.ALL_INDICATORS and data.data[col].dtype in ['int64', 'float64']:
                Q1 = data.data[col].quantile(0.25)
                Q3 = data.data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = data.data[(data.data[col] < lower_bound) | (data.data[col] > upper_bound)][col]
                quality_assessment['outliers'][col] = {
                    'outlier_count': len(outliers),
                    'outlier_percentage': float(len(outliers) / len(data.data) * 100)
                }
        
        return quality_assessment