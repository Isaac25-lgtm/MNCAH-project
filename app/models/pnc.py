"""
Postnatal Care (PNC) Model
This module implements all 4 PNC indicators and calculations.
"""

from typing import Dict
from .base import MaternalNeonatalChildAdolescentHealth, ValidationStatus, PopulationData


class PostnatalCare(MaternalNeonatalChildAdolescentHealth):
    """
    Postnatal Care subclass implementing all 4 PNC indicators:
    1. Breastfeeding at 1 hour
    2. PNC at 24 hours
    3. PNC at 6 days
    4. PNC at 6 weeks
    """
    
    def __init__(self, population_data: PopulationData, raw_data: Dict[str, any]):
        """
        Initialize PNC model
        
        Args:
            population_data: Population information for calculations
            raw_data: Raw data containing PNC indicator values
        """
        super().__init__(population_data, raw_data)
        
        # PNC-specific indicator codes from the requirements
        self.indicator_codes = {
            'live_births_total': '105-MA04b1',  # Denominator for all PNC indicators
            'breastfeeding_1hour': 'bf_1hour',  # Custom code for breastfeeding within 1 hour
            'pnc_24hours': 'pnc_24hrs',         # Custom code for PNC at 24 hours
            'pnc_6days': 'pnc_6days',           # Custom code for PNC at 6 days
            'pnc_6weeks': 'pnc_6weeks'          # Custom code for PNC at 6 weeks
        }
    
    def calculate_indicators(self) -> Dict[str, float]:
        """
        Calculate all PNC indicators according to MOH formulas
        
        Returns:
            Dictionary with calculated PNC indicator values
        """
        # Get raw values from uploaded data
        live_births_total = self.get_raw_value(self.indicator_codes['live_births_total'])
        breastfeeding_1hour = self.get_raw_value(self.indicator_codes['breastfeeding_1hour'])
        pnc_24hours = self.get_raw_value(self.indicator_codes['pnc_24hours'])
        pnc_6days = self.get_raw_value(self.indicator_codes['pnc_6days'])
        pnc_6weeks = self.get_raw_value(self.indicator_codes['pnc_6weeks'])
        
        # Calculate indicators using MOH formulas
        indicators = {
            # 1. Breastfeeding at 1 hour = (Mothers who initiated breastfeeding within 1st hour after delivery / Live births Total) × 100
            'breastfeeding_1hour': self.calculate_percentage(breastfeeding_1hour, live_births_total),
            
            # 2. PNC at 24 hours = (Post Natal Attendances 24Hrs / Live births Total) × 100
            'pnc_24hours': self.calculate_percentage(pnc_24hours, live_births_total),
            
            # 3. PNC at 6 days = (Post Natal Attendances 6Dys / Live births Total) × 100
            'pnc_6days': self.calculate_percentage(pnc_6days, live_births_total),
            
            # 4. PNC at 6 weeks = (Post Natal Attendances 6Wks / Live births Total) × 100
            'pnc_6weeks': self.calculate_percentage(pnc_6weeks, live_births_total)
        }
        
        return indicators
    
    def validate_indicators(self) -> Dict[str, ValidationStatus]:
        """
        Validate PNC indicators against MOH targets and rules
        
        Returns:
            Dictionary mapping indicator names to validation status
        """
        if not self.calculated_indicators:
            self.calculated_indicators = self.calculate_indicators()
        
        validations = {}
        
        for indicator_name, value in self.calculated_indicators.items():
            validations[indicator_name] = self._validate_pnc_indicator(indicator_name, value)
        
        return validations
    
    def _validate_pnc_indicator(self, indicator_name: str, value: float) -> ValidationStatus:
        """
        Validate individual PNC indicator based on MOH targets
        
        Args:
            indicator_name: Name of the indicator
            value: Calculated value
            
        Returns:
            ValidationStatus enum
        """
        # First check for data quality issues
        if value < 0 or not isinstance(value, (int, float)) or str(value).lower() == 'nan':
            return ValidationStatus.BLUE
        
        # PNC indicators cannot exceed 100% (cannot have more attendances than deliveries)
        if value > 100.0:
            return ValidationStatus.BLUE
        
        # Apply validation rules from requirements
        if indicator_name == 'breastfeeding_1hour':
            # Breastfeeding within 1 hour target is 100%
            # 100% = green, 90% to 99.9% = yellow, below 90% = red
            if value == 100.0:
                return ValidationStatus.GREEN
            elif 90.0 <= value <= 99.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'pnc_24hours':
            # PNC at 24 hours target is 100%
            # 100% = green, 90% to 99.9% = yellow, below 90% = red
            if value == 100.0:
                return ValidationStatus.GREEN
            elif 90.0 <= value <= 99.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'pnc_6days':
            # PNC at 6 days target is 75%
            # 75% to 100% = green, 60% to 74.9% = yellow, below 60% = red
            if 75.0 <= value <= 100.0:
                return ValidationStatus.GREEN
            elif 60.0 <= value <= 74.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'pnc_6weeks':
            # PNC at 6 weeks target is 75%
            # 75% to 100% = green, 60% to 74.9% = yellow, below 60% = red
            if 75.0 <= value <= 100.0:
                return ValidationStatus.GREEN
            elif 60.0 <= value <= 74.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        # Default case
        return ValidationStatus.BLUE
    
    def get_indicator_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        Get definitions for all PNC indicators
        
        Returns:
            Dictionary with indicator definitions, formulas, targets, and importance
        """
        return {
            'breastfeeding_1hour': {
                'name': 'Breastfeeding within 1 Hour',
                'definition': 'Proportion of mothers who started breastfeeding their newborns within one hour of birth',
                'formula': '(Mothers who initiated breastfeeding within 1st hour after delivery / Total live births) × 100',
                'target': '100% (Green), 90-99.9% (Yellow), <90% (Red)',
                'importance': 'Early initiation of breastfeeding improves newborn survival, bonding, and establishes successful breastfeeding',
                'data_element': 'bf_1hour - Mothers who initiated breastfeeding within the 1st hour after delivery',
                'who_recommendation': 'WHO recommends breastfeeding within one hour of birth for all newborns'
            },
            'pnc_24hours': {
                'name': 'PNC at 24 Hours',
                'definition': 'Proportion of mothers and newborns who received postnatal check-up within 24 hours after delivery',
                'formula': '(Post Natal Attendances 24Hrs / Total live births) × 100',
                'target': '100% (Green), 90-99.9% (Yellow), <90% (Red)',
                'importance': 'First 24 hours are critical for detecting and managing life-threatening complications in mothers and newborns',
                'data_element': 'pnc_24hrs - Post Natal Attendances 24Hrs',
                'who_recommendation': 'WHO recommends at least 3 PNC visits, with the first within 24 hours'
            },
            'pnc_6days': {
                'name': 'PNC at 6 Days',
                'definition': 'Proportion of mothers and newborns who received postnatal check-up within 6 days after delivery',
                'formula': '(Post Natal Attendances 6Dys / Total live births) × 100',
                'target': '75-100% (Green), 60-74.9% (Yellow), <60% (Red)',
                'importance': 'Early postnatal period is crucial for identifying delayed complications and ensuring proper feeding practices',
                'data_element': 'pnc_6days - Post Natal Attendances 6Dys',
                'who_recommendation': 'Second PNC contact recommended between day 3-7 for early problem detection'
            },
            'pnc_6weeks': {
                'name': 'PNC at 6 Weeks',
                'definition': 'Proportion of women who return to health facility for postnatal check-up around six weeks (42 days) after giving birth',
                'formula': '(Post Natal Attendances 6Wks / Total live births) × 100',
                'target': '75-100% (Green), 60-74.9% (Yellow), <60% (Red)',
                'importance': 'Six-week visit allows assessment of maternal recovery, family planning counseling, and newborn growth monitoring',
                'data_element': 'pnc_6weeks - Post Natal Attendances 6Wks',
                'who_recommendation': 'Final routine PNC contact at 6 weeks for maternal recovery assessment and family planning'
            }
        }
    
    def get_breastfeeding_analysis(self) -> Dict[str, any]:
        """
        Get detailed breastfeeding analysis
        
        Returns:
            Dictionary with breastfeeding-specific analysis
        """
        if not self.calculated_indicators:
            return {}
        
        bf_rate = self.calculated_indicators.get('breastfeeding_1hour', 0)
        
        analysis = {
            'current_rate': bf_rate,
            'target_rate': 100.0,
            'gap_to_target': max(0, 100.0 - bf_rate),
            'performance_level': 'Excellent' if bf_rate >= 95 else 'Good' if bf_rate >= 85 else 'Needs Improvement',
            'clinical_significance': self._get_breastfeeding_significance(bf_rate),
            'recommendations': self._get_breastfeeding_recommendations(bf_rate)
        }
        
        return analysis
    
    def get_pnc_continuum_analysis(self) -> Dict[str, any]:
        """
        Analyze the continuum of PNC care
        
        Returns:
            Dictionary with PNC continuum analysis
        """
        if not self.calculated_indicators:
            return {}
        
        pnc_24h = self.calculated_indicators.get('pnc_24hours', 0)
        pnc_6d = self.calculated_indicators.get('pnc_6days', 0)
        pnc_6w = self.calculated_indicators.get('pnc_6weeks', 0)
        
        # Calculate dropout rates
        dropout_24h_to_6d = max(0, pnc_24h - pnc_6d)
        dropout_6d_to_6w = max(0, pnc_6d - pnc_6w)
        total_dropout = max(0, pnc_24h - pnc_6w)
        
        analysis = {
            'pnc_cascade': {
                '24_hours': pnc_24h,
                '6_days': pnc_6d,
                '6_weeks': pnc_6w
            },
            'dropout_analysis': {
                '24h_to_6d_dropout': dropout_24h_to_6d,
                '6d_to_6w_dropout': dropout_6d_to_6w,
                'total_dropout': total_dropout
            },
            'retention_rate': (pnc_6w / pnc_24h * 100) if pnc_24h > 0 else 0,
            'critical_gaps': self._identify_pnc_gaps(pnc_24h, pnc_6d, pnc_6w),
            'recommendations': self._get_pnc_recommendations(pnc_24h, pnc_6d, pnc_6w)
        }
        
        return analysis
    
    def _get_breastfeeding_significance(self, rate: float) -> str:
        """Get clinical significance of breastfeeding rate"""
        if rate >= 90:
            return "Excellent early breastfeeding initiation supports optimal newborn health outcomes"
        elif rate >= 75:
            return "Good breastfeeding initiation but room for improvement to meet WHO recommendations"
        elif rate >= 50:
            return "Moderate breastfeeding initiation - significant opportunity to improve newborn outcomes"
        else:
            return "Low breastfeeding initiation poses risks to newborn survival and long-term health"
    
    def _get_breastfeeding_recommendations(self, rate: float) -> list:
        """Get recommendations based on breastfeeding rate"""
        recommendations = []
        
        if rate < 90:
            recommendations.extend([
                "Strengthen immediate postpartum support for breastfeeding initiation",
                "Train delivery staff on importance of skin-to-skin contact and early breastfeeding",
                "Implement Baby-Friendly Hospital Initiative practices"
            ])
        
        if rate < 75:
            recommendations.extend([
                "Review delivery practices that may delay breastfeeding initiation",
                "Provide targeted counseling during ANC on importance of early breastfeeding",
                "Address cultural or institutional barriers to immediate breastfeeding"
            ])
        
        if rate < 50:
            recommendations.extend([
                "Conduct comprehensive review of delivery and immediate postpartum protocols",
                "Implement intensive breastfeeding support program",
                "Consider community-based peer support interventions"
            ])
        
        return recommendations
    
    def _identify_pnc_gaps(self, pnc_24h: float, pnc_6d: float, pnc_6w: float) -> list:
        """Identify critical gaps in PNC continuum"""
        gaps = []
        
        if pnc_24h < 90:
            gaps.append("Critical gap in immediate postnatal care - high risk for maternal/neonatal complications")
        
        if pnc_6d < 60:
            gaps.append("Major gap in early postnatal follow-up - missed opportunities for problem detection")
        
        if pnc_6w < 60:
            gaps.append("Significant gap in routine postnatal care - limited family planning and recovery assessment")
        
        if pnc_6d < pnc_24h - 20:
            gaps.append("High dropout between 24-hour and 6-day visits - need retention strategies")
        
        if pnc_6w < pnc_6d - 20:
            gaps.append("High dropout between 6-day and 6-week visits - strengthen follow-up systems")
        
        return gaps
    
    def _get_pnc_recommendations(self, pnc_24h: float, pnc_6d: float, pnc_6w: float) -> list:
        """Get recommendations based on PNC performance"""
        recommendations = []
        
        # 24-hour PNC recommendations
        if pnc_24h < 95:
            recommendations.extend([
                "Strengthen immediate postpartum monitoring protocols",
                "Ensure all facility deliveries include 24-hour PNC check",
                "Improve discharge planning and early follow-up scheduling"
            ])
        
        # 6-day PNC recommendations
        if pnc_6d < 70:
            recommendations.extend([
                "Implement active follow-up systems for early postnatal period",
                "Strengthen community health worker engagement for PNC visits",
                "Address transportation and accessibility barriers"
            ])
        
        # 6-week PNC recommendations
        if pnc_6w < 70:
            recommendations.extend([
                "Integrate PNC with immunization services to improve attendance",
                "Strengthen family planning counseling as incentive for 6-week visit",
                "Implement reminder systems and community mobilization"
            ])
        
        # Continuum recommendations
        if (pnc_24h - pnc_6w) > 30:
            recommendations.extend([
                "Develop comprehensive PNC package to improve retention",
                "Implement client tracking and defaulter tracing systems",
                "Address service quality issues that may cause dropouts"
            ])
        
        return recommendations
