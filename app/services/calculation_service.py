"""
MNCAH Calculation Service
This service coordinates all MNCAH calculations and provides a unified interface 
for processing health indicator data.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from ..models.base import PopulationData, PeriodType, ValidationStatus
from ..models.anc import AntenatalCare
from ..models.intrapartum import IntrapartumCare
from ..models.pnc import PostnatalCare


class MNCHACalculationService:
    """
    Service class that orchestrates MNCAH calculations across all categories
    """
    
    def __init__(self):
        """Initialize the calculation service"""
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_indicators(self, 
                               population: int, 
                               period_type: str, 
                               reporting_period: str,
                               raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all MNCAH indicators for given data
        
        Args:
            population: Total annual population
            period_type: Type of reporting period (annual/quarterly/monthly)
            reporting_period: The reporting period identifier
            raw_data: Raw indicator data from uploaded file
            
        Returns:
            Dictionary with all calculated indicators and metadata
        """
        try:
            # Create population data object
            pop_data = PopulationData(
                total_population=population,
                period_type=PeriodType(period_type),
                reporting_period=reporting_period
            )
            
            self.logger.info(f"Starting MNCAH calculations for {reporting_period}")
            self.logger.info(f"Population: {population} ({period_type}), Adjusted: {pop_data.adjusted_population}")
            
            # Initialize models
            anc_model = AntenatalCare(pop_data, raw_data)
            intrapartum_model = IntrapartumCare(pop_data, raw_data)
            pnc_model = PostnatalCare(pop_data, raw_data)
            
            # Process each category
            anc_results = anc_model.process_all()
            intrapartum_results = intrapartum_model.process_all()
            pnc_results = pnc_model.process_all()
            
            # Compile comprehensive results
            results = {
                'calculation_metadata': {
                    'calculated_at': datetime.utcnow().isoformat(),
                    'population_data': {
                        'total_population': population,
                        'adjusted_population': pop_data.adjusted_population,
                        'expected_pregnancies': pop_data.expected_pregnancies,
                        'expected_deliveries': pop_data.expected_deliveries,
                        'period_type': period_type,
                        'reporting_period': reporting_period
                    }
                },
                'anc': anc_results,
                'intrapartum': intrapartum_results,
                'pnc': pnc_results,
                'summary': self._generate_summary(anc_results, intrapartum_results, pnc_results)
            }
            
            self.logger.info("MNCAH calculations completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in MNCAH calculations: {str(e)}")
            raise
    
    def _generate_summary(self, anc_results: Dict, intrapartum_results: Dict, 
                         pnc_results: Dict) -> Dict[str, Any]:
        """
        Generate summary statistics across all MNCAH categories
        
        Args:
            anc_results: ANC calculation results
            intrapartum_results: Intrapartum calculation results
            pnc_results: PNC calculation results
            
        Returns:
            Summary statistics dictionary
        """
        all_indicators = {}
        all_validations = {}
        
        # Collect all indicators and validations
        for category, results in [('anc', anc_results), 
                                 ('intrapartum', intrapartum_results), 
                                 ('pnc', pnc_results)]:
            if 'indicators' in results:
                for indicator, value in results['indicators'].items():
                    all_indicators[f"{category}_{indicator}"] = value
            
            if 'validations' in results:
                for indicator, status in results['validations'].items():
                    all_validations[f"{category}_{indicator}"] = status
        
        # Calculate summary statistics
        indicator_values = list(all_indicators.values())
        validation_counts = {
            'green': sum(1 for v in all_validations.values() if v == 'green'),
            'yellow': sum(1 for v in all_validations.values() if v == 'yellow'),
            'red': sum(1 for v in all_validations.values() if v == 'red'),
            'blue': sum(1 for v in all_validations.values() if v == 'blue')
        }
        
        total_indicators = len(all_indicators)
        
        summary = {
            'total_indicators': total_indicators,
            'indicator_statistics': {
                'mean': sum(indicator_values) / len(indicator_values) if indicator_values else 0,
                'min': min(indicator_values) if indicator_values else 0,
                'max': max(indicator_values) if indicator_values else 0,
                'count': len(indicator_values)
            },
            'validation_summary': {
                **validation_counts,
                'total': total_indicators,
                'validation_rate': (validation_counts['green'] / total_indicators * 100) if total_indicators > 0 else 0,
                'warning_rate': (validation_counts['yellow'] / total_indicators * 100) if total_indicators > 0 else 0,
                'error_rate': ((validation_counts['red'] + validation_counts['blue']) / total_indicators * 100) if total_indicators > 0 else 0
            },
            'category_summary': {
                'anc': self._get_category_summary(anc_results),
                'intrapartum': self._get_category_summary(intrapartum_results),
                'pnc': self._get_category_summary(pnc_results)
            },
            'overall_performance': self._assess_overall_performance(validation_counts, total_indicators)
        }
        
        return summary
    
    def _get_category_summary(self, category_results: Dict) -> Dict[str, Any]:
        """Generate summary for a specific MNCAH category"""
        if 'indicators' not in category_results or 'validations' not in category_results:
            return {}
        
        indicators = category_results['indicators']
        validations = category_results['validations']
        
        validation_counts = {
            'green': sum(1 for v in validations.values() if v == 'green'),
            'yellow': sum(1 for v in validations.values() if v == 'yellow'),
            'red': sum(1 for v in validations.values() if v == 'red'),
            'blue': sum(1 for v in validations.values() if v == 'blue')
        }
        
        total = len(indicators)
        
        return {
            'indicator_count': total,
            'validation_counts': validation_counts,
            'performance_score': (validation_counts['green'] / total * 100) if total > 0 else 0,
            'has_critical_issues': validation_counts['red'] + validation_counts['blue'] > 0
        }
    
    def _assess_overall_performance(self, validation_counts: Dict, total_indicators: int) -> str:
        """Assess overall performance level"""
        if total_indicators == 0:
            return "no_data"
        
        validation_rate = validation_counts['green'] / total_indicators * 100
        error_rate = (validation_counts['red'] + validation_counts['blue']) / total_indicators * 100
        
        if error_rate > 25:
            return "critical"
        elif error_rate > 10:
            return "needs_improvement"
        elif validation_rate >= 80:
            return "excellent"
        elif validation_rate >= 60:
            return "good"
        else:
            return "fair"
    
    def get_indicator_trends(self, facility_name: str, uploads: List[Dict]) -> Dict[str, Any]:
        """
        Analyze trends for indicators across multiple uploads
        
        Args:
            facility_name: Name of the facility
            uploads: List of upload data dictionaries
            
        Returns:
            Trend analysis results
        """
        try:
            trends = {}
            
            # Sort uploads by reporting period/date
            sorted_uploads = sorted(uploads, key=lambda x: x.get('uploaded_at', ''))
            
            if len(sorted_uploads) < 2:
                return {
                    'message': 'Insufficient data for trend analysis (minimum 2 data points required)',
                    'data_points': len(sorted_uploads)
                }
            
            # Extract indicators across time periods
            all_periods = []
            indicator_series = {}
            
            for upload in sorted_uploads:
                if 'processed_data' not in upload:
                    continue
                
                period = upload.get('reporting_period', 'Unknown')
                all_periods.append(period)
                
                # Extract indicators from all categories
                for category in ['anc', 'intrapartum', 'pnc']:
                    if category in upload['processed_data']:
                        indicators = upload['processed_data'][category].get('indicators', {})
                        for indicator, value in indicators.items():
                            full_name = f"{category}_{indicator}"
                            if full_name not in indicator_series:
                                indicator_series[full_name] = []
                            indicator_series[full_name].append({
                                'period': period,
                                'value': value,
                                'date': upload.get('uploaded_at')
                            })
            
            # Calculate trends for each indicator
            for indicator, series in indicator_series.items():
                if len(series) >= 2:
                    trends[indicator] = self._calculate_trend(series)
            
            return {
                'facility_name': facility_name,
                'analysis_date': datetime.utcnow().isoformat(),
                'periods_analyzed': all_periods,
                'total_periods': len(all_periods),
                'indicators_with_trends': len(trends),
                'trends': trends,
                'summary': self._summarize_trends(trends)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trends: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_trend(self, series: List[Dict]) -> Dict[str, Any]:
        """Calculate trend statistics for an indicator series"""
        values = [point['value'] for point in series]
        
        # Basic trend statistics
        latest_value = values[-1]
        earliest_value = values[0]
        change = latest_value - earliest_value
        percent_change = (change / earliest_value * 100) if earliest_value != 0 else 0
        
        # Simple trend direction
        if len(values) >= 2:
            recent_trend = "improving" if values[-1] > values[-2] else "declining" if values[-1] < values[-2] else "stable"
        else:
            recent_trend = "insufficient_data"
        
        # Calculate average change per period
        if len(values) > 1:
            total_periods = len(values) - 1
            avg_change_per_period = change / total_periods
        else:
            avg_change_per_period = 0
        
        return {
            'data_points': len(series),
            'earliest_value': earliest_value,
            'latest_value': latest_value,
            'absolute_change': change,
            'percent_change': percent_change,
            'average_change_per_period': avg_change_per_period,
            'recent_trend': recent_trend,
            'values_over_time': [{'period': p['period'], 'value': p['value']} for p in series]
        }
    
    def _summarize_trends(self, trends: Dict) -> Dict[str, Any]:
        """Summarize overall trend patterns"""
        if not trends:
            return {}
        
        improving_count = sum(1 for t in trends.values() if t['recent_trend'] == 'improving')
        declining_count = sum(1 for t in trends.values() if t['recent_trend'] == 'declining')
        stable_count = sum(1 for t in trends.values() if t['recent_trend'] == 'stable')
        
        total = len(trends)
        
        # Find indicators with largest improvements and declines
        sorted_by_change = sorted(trends.items(), key=lambda x: x[1]['percent_change'], reverse=True)
        
        return {
            'total_indicators': total,
            'trend_distribution': {
                'improving': improving_count,
                'declining': declining_count,
                'stable': stable_count
            },
            'trend_percentages': {
                'improving': (improving_count / total * 100) if total > 0 else 0,
                'declining': (declining_count / total * 100) if total > 0 else 0,
                'stable': (stable_count / total * 100) if total > 0 else 0
            },
            'best_performers': sorted_by_change[:3] if len(sorted_by_change) >= 3 else sorted_by_change,
            'areas_needing_attention': sorted_by_change[-3:] if len(sorted_by_change) >= 3 else [],
            'overall_trend': 'improving' if improving_count > declining_count else 'declining' if declining_count > improving_count else 'mixed'
        }
    
    def compare_facilities(self, facility_data: List[Dict]) -> Dict[str, Any]:
        """
        Compare performance across multiple facilities
        
        Args:
            facility_data: List of facility data with calculated indicators
            
        Returns:
            Comparative analysis results
        """
        try:
            if len(facility_data) < 2:
                return {'error': 'Need at least 2 facilities for comparison'}
            
            # Extract indicators for comparison
            facility_indicators = {}
            
            for facility in facility_data:
                facility_name = facility.get('facility_name', 'Unknown')
                facility_indicators[facility_name] = {}
                
                if 'processed_data' in facility:
                    for category in ['anc', 'intrapartum', 'pnc']:
                        if category in facility['processed_data']:
                            indicators = facility['processed_data'][category].get('indicators', {})
                            for indicator, value in indicators.items():
                                full_name = f"{category}_{indicator}"
                                facility_indicators[facility_name][full_name] = value
            
            # Calculate comparative statistics
            comparison_results = {}
            all_indicators = set()
            
            # Get all unique indicators
            for facility_data in facility_indicators.values():
                all_indicators.update(facility_data.keys())
            
            # Compare each indicator across facilities
            for indicator in all_indicators:
                values = []
                facility_values = {}
                
                for facility, indicators in facility_indicators.items():
                    if indicator in indicators:
                        value = indicators[indicator]
                        values.append(value)
                        facility_values[facility] = value
                
                if len(values) >= 2:
                    comparison_results[indicator] = {
                        'values_by_facility': facility_values,
                        'statistics': {
                            'mean': sum(values) / len(values),
                            'min': min(values),
                            'max': max(values),
                            'range': max(values) - min(values)
                        },
                        'rankings': self._rank_facilities(facility_values, indicator)
                    }
            
            return {
                'analysis_date': datetime.utcnow().isoformat(),
                'facilities_compared': list(facility_indicators.keys()),
                'indicators_compared': len(comparison_results),
                'comparisons': comparison_results,
                'summary': self._summarize_facility_comparison(comparison_results, facility_indicators)
            }
            
        except Exception as e:
            self.logger.error(f"Error in facility comparison: {str(e)}")
            return {'error': str(e)}
    
    def _rank_facilities(self, facility_values: Dict[str, float], indicator: str) -> List[Dict]:
        """Rank facilities for a specific indicator"""
        # Determine if higher is better (most indicators) or lower is better (mortality, stillbirths, etc.)
        lower_is_better_indicators = [
            'lbw_proportion', 'birth_asphyxia_proportion', 'fresh_stillbirths_rate',
            'neonatal_mortality_rate', 'perinatal_mortality_rate', 'maternal_mortality_ratio'
        ]
        
        reverse_sort = not any(term in indicator for term in lower_is_better_indicators)
        
        sorted_facilities = sorted(facility_values.items(), 
                                 key=lambda x: x[1], 
                                 reverse=reverse_sort)
        
        rankings = []
        for rank, (facility, value) in enumerate(sorted_facilities, 1):
            rankings.append({
                'rank': rank,
                'facility': facility,
                'value': value,
                'performance_level': 'high' if rank <= len(sorted_facilities) // 3 else 
                                   'medium' if rank <= 2 * len(sorted_facilities) // 3 else 'low'
            })
        
        return rankings
    
    def _summarize_facility_comparison(self, comparison_results: Dict, 
                                     facility_indicators: Dict) -> Dict[str, Any]:
        """Generate summary of facility comparison"""
        facilities = list(facility_indicators.keys())
        
        # Count top rankings per facility
        facility_rankings = {facility: {'top_rankings': 0, 'total_indicators': 0} 
                           for facility in facilities}
        
        for indicator, comparison in comparison_results.items():
            rankings = comparison['rankings']
            if rankings:
                top_facility = rankings[0]['facility']
                facility_rankings[top_facility]['top_rankings'] += 1
                
                for facility in facilities:
                    if any(r['facility'] == facility for r in rankings):
                        facility_rankings[facility]['total_indicators'] += 1
        
        # Calculate performance scores
        for facility, stats in facility_rankings.items():
            if stats['total_indicators'] > 0:
                stats['performance_score'] = (stats['top_rankings'] / stats['total_indicators']) * 100
            else:
                stats['performance_score'] = 0
        
        # Find best and worst performing facilities
        sorted_facilities = sorted(facility_rankings.items(), 
                                 key=lambda x: x[1]['performance_score'], 
                                 reverse=True)
        
        return {
            'facility_rankings': facility_rankings,
            'best_performing': sorted_facilities[0] if sorted_facilities else None,
            'needs_support': sorted_facilities[-1] if sorted_facilities else None,
            'performance_distribution': {
                'high_performers': len([f for f in sorted_facilities if f[1]['performance_score'] >= 70]),
                'medium_performers': len([f for f in sorted_facilities if 30 <= f[1]['performance_score'] < 70]),
                'low_performers': len([f for f in sorted_facilities if f[1]['performance_score'] < 30])
            }
        }
