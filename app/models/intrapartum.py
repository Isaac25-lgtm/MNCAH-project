"""
Intrapartum/Maternal and Perinatal Death and Surveillance Report (MPDSR) Model
This module implements all 9 intrapartum indicators and calculations.
"""

from typing import Dict
from .base import MaternalNeonatalChildAdolescentHealth, ValidationStatus, PopulationData


class IntrapartumCare(MaternalNeonatalChildAdolescentHealth):
    """
    Intrapartum Care subclass implementing all 9 intrapartum indicators:
    1. Deliveries (Institutional Deliveries)
    2. LBW (Low Birth Weight proportion)
    3. LBW initiated on KMC (Kangaroo Mother Care)
    4. Babies with Birth asphyxia
    5. Babies with Birth asphyxia successfully resuscitated
    6. Fresh still births per 1000 Deliveries
    7. Neonatal mortality rate
    8. Perinatal mortality rate
    9. Institutional Maternal mortality ratio
    """
    
    def __init__(self, population_data: PopulationData, raw_data: Dict[str, any]):
        """
        Initialize Intrapartum model
        
        Args:
            population_data: Population information for calculations
            raw_data: Raw data containing intrapartum indicator values
        """
        super().__init__(population_data, raw_data)
        
        # Intrapartum-specific indicator codes from the requirements
        self.indicator_codes = {
            'total_deliveries': '105-MA04a',
            'live_births_total': '105-MA04b1',
            'live_births_lbw': '105-MA04b2',
            'fresh_stillbirths': '105-MA04c1',
            'macerated_stillbirths': '105-MA04d1',
            'lbw_kmc': '105-MA07',
            'newborn_deaths_0_7': '105-MA11',
            'neonatal_deaths_8_28': '105-MA12',
            'maternal_deaths': '105-MA13',
            'birth_asphyxia': '105-MA24',
            'successful_resuscitation': '105-MA25'
        }
    
    def calculate_indicators(self) -> Dict[str, float]:
        """
        Calculate all intrapartum indicators according to MOH formulas
        
        Returns:
            Dictionary with calculated intrapartum indicator values
        """
        expected_deliveries = self.population_data.expected_deliveries
        
        # Get raw values from uploaded data
        total_deliveries = self.get_raw_value(self.indicator_codes['total_deliveries'])
        live_births_total = self.get_raw_value(self.indicator_codes['live_births_total'])
        live_births_lbw = self.get_raw_value(self.indicator_codes['live_births_lbw'])
        fresh_stillbirths = self.get_raw_value(self.indicator_codes['fresh_stillbirths'])
        macerated_stillbirths = self.get_raw_value(self.indicator_codes['macerated_stillbirths'])
        lbw_kmc = self.get_raw_value(self.indicator_codes['lbw_kmc'])
        newborn_deaths_0_7 = self.get_raw_value(self.indicator_codes['newborn_deaths_0_7'])
        neonatal_deaths_8_28 = self.get_raw_value(self.indicator_codes['neonatal_deaths_8_28'])
        maternal_deaths = self.get_raw_value(self.indicator_codes['maternal_deaths'])
        birth_asphyxia = self.get_raw_value(self.indicator_codes['birth_asphyxia'])
        successful_resuscitation = self.get_raw_value(self.indicator_codes['successful_resuscitation'])
        
        # Calculate indicators using MOH formulas
        indicators = {
            # 1. Institutional Deliveries = (Deliveries in unit - Live births - Total / Expected deliveries) × 100
            'institutional_deliveries': self.calculate_percentage(live_births_total, expected_deliveries),
            
            # 2. Proportion of LBW babies = (Deliveries in unit - Live births - less than 2.5kg / Deliveries in unit - Live births - Total) × 100
            'lbw_proportion': self.calculate_percentage(live_births_lbw, live_births_total),
            
            # 3. Proportion of LBW babies initiated on KMC = (Low birth weight babies initiated on KMC / Deliveries in unit - Live births - less than 2.5kg) × 100
            'lbw_kmc_proportion': self.calculate_percentage(lbw_kmc, live_births_lbw),
            
            # 4. Proportion of babies with Birth asphyxia = (No.of babies with Birth asphyxia / Deliveries in unit - Live births – Total) × 100
            'birth_asphyxia_proportion': self.calculate_percentage(birth_asphyxia, live_births_total),
            
            # 5. Proportion of babies with Birth asphyxia successfully resuscitated = (No. of Live babies Successfully Resuscitated / No.of babies with Birth asphyxia) × 100
            'successful_resuscitation_proportion': self.calculate_percentage(successful_resuscitation, birth_asphyxia),
            
            # 6. Fresh still births per 1000 Deliveries = (Deliveries in unit - Fresh still birth – Total / Deliveries in unit – Total) × 1000
            'fresh_stillbirths_rate': self.calculate_rate_per_thousand(fresh_stillbirths, total_deliveries),
            
            # 7. Neonatal mortality rate = ((Newborn deaths (0-7 days) + Neonatal Death 8-28 days) / Deliveries in unit - Live births – Total) × 1000
            'neonatal_mortality_rate': self.calculate_rate_per_thousand(
                (newborn_deaths_0_7 + neonatal_deaths_8_28), 
                live_births_total
            ),
            
            # 8. Perinatal Mortality rate = [(Newborn deaths (0-7 days) + Macerated still births + Fresh still births) / Deliveries in unit – Total] × 1000
            'perinatal_mortality_rate': self.calculate_rate_per_thousand(
                (newborn_deaths_0_7 + macerated_stillbirths + fresh_stillbirths), 
                total_deliveries
            ),
            
            # 9. Institutional Maternal mortality ratio = (Maternal deaths / Deliveries in unit - Live births – Total) × 100,000
            'maternal_mortality_ratio': self.calculate_rate_per_hundred_thousand(maternal_deaths, live_births_total)
        }
        
        return indicators
    
    def validate_indicators(self) -> Dict[str, ValidationStatus]:
        """
        Validate intrapartum indicators against MOH targets and rules
        
        Returns:
            Dictionary mapping indicator names to validation status
        """
        if not self.calculated_indicators:
            self.calculated_indicators = self.calculate_indicators()
        
        validations = {}
        
        for indicator_name, value in self.calculated_indicators.items():
            validations[indicator_name] = self._validate_intrapartum_indicator(indicator_name, value)
        
        return validations
    
    def _validate_intrapartum_indicator(self, indicator_name: str, value: float) -> ValidationStatus:
        """
        Validate individual intrapartum indicator based on MOH targets
        
        Args:
            indicator_name: Name of the indicator
            value: Calculated value
            
        Returns:
            ValidationStatus enum
        """
        # First check for data quality issues
        if value < 0 or not isinstance(value, (int, float)) or str(value).lower() == 'nan':
            return ValidationStatus.BLUE
        
        # Apply validation rules from requirements
        if indicator_name == 'institutional_deliveries':
            # Deliveries target is 68%. Can be above 100%
            # 68% and above = green, 55% to 67.9% = yellow, below 55% = red
            if value >= 68.0:
                return ValidationStatus.GREEN
            elif 55.0 <= value <= 67.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'lbw_proportion':
            # LBW target is 5% or less. Cannot be above 100%
            # 5% or less = green, 5.1% to 10% = yellow, above 10% to 100% = red
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value <= 5.0:
                return ValidationStatus.GREEN
            elif 5.1 <= value <= 10.0:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'lbw_kmc_proportion':
            # LBW initiated on KMC target is 100%. Cannot be above 100%
            # 100% = green, 90% to 99.9% = yellow, below 90% = red
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value == 100.0:
                return ValidationStatus.GREEN
            elif 90.0 <= value <= 99.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'birth_asphyxia_proportion':
            # Birth asphyxia target is 1% or less. Cannot be above 100%
            # 1% or less = green, 1.1% to 3% = yellow, above 3% to 100% = red
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value <= 1.0:
                return ValidationStatus.GREEN
            elif 1.1 <= value <= 3.0:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'successful_resuscitation_proportion':
            # Successful resuscitation target is 100%. Cannot be above 100%
            # 100% = green, 80% to 99.9% = yellow, below 80% = red
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value == 100.0:
                return ValidationStatus.GREEN
            elif 80.0 <= value <= 99.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'fresh_stillbirths_rate':
            # Fresh still births per 1000 deliveries target is ≤5. Cannot be above 1000
            # 5 or less = green, 5.1 to 10 = yellow, above 10 = red
            if value > 1000.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value <= 5.0:
                return ValidationStatus.GREEN
            elif 5.1 <= value <= 10.0:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'neonatal_mortality_rate':
            # Neonatal mortality rate (per 1000 live births) target is ≤5. Cannot be above 1000
            # 5 or less = green, 5.1 to 10 = yellow, above 10 = red
            if value > 1000.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value <= 5.0:
                return ValidationStatus.GREEN
            elif 5.1 <= value <= 10.0:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'perinatal_mortality_rate':
            # Perinatal mortality rate (per 1000 births) target is ≤12. Cannot be above 1000
            # 12 or less = green, 12.1 to 20 = yellow, above 20 = red
            if value > 1000.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value <= 12.0:
                return ValidationStatus.GREEN
            elif 12.1 <= value <= 20.0:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'maternal_mortality_ratio':
            # Maternal mortality ratio - using Uganda's target of reducing MMR
            # Using 300 per 100,000 as target threshold based on Uganda's context
            # ≤200 = green, 201-400 = yellow, >400 = red
            if value <= 200.0:
                return ValidationStatus.GREEN
            elif 201.0 <= value <= 400.0:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        # Default case
        return ValidationStatus.BLUE
    
    def get_indicator_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        Get definitions for all intrapartum indicators
        
        Returns:
            Dictionary with indicator definitions, formulas, targets, and importance
        """
        return {
            'institutional_deliveries': {
                'name': 'Institutional Deliveries',
                'definition': 'Proportion of deliveries that occur in health facilities',
                'formula': '(Live births in unit / Expected deliveries) × 100',
                'target': '68% and above (Green), 55-67.9% (Yellow), <55% (Red)',
                'importance': 'Facility deliveries ensure skilled attendance and emergency care access',
                'data_element': '105-MA04b1. Deliveries in unit - Live births - Total'
            },
            'lbw_proportion': {
                'name': 'Low Birth Weight Proportion',
                'definition': 'Percentage of live-born infants who weigh less than 2,500 grams (2.5 kg) at birth',
                'formula': '(LBW babies / Total live births) × 100',
                'target': '≤5% (Green), 5.1-10% (Yellow), >10% (Red)',
                'importance': 'LBW is associated with increased neonatal mortality and long-term health issues',
                'data_element': '105-MA04b2. Deliveries in unit - Live births - less than 2.5kg'
            },
            'lbw_kmc_proportion': {
                'name': 'LBW Babies Initiated on KMC',
                'definition': 'Proportion of Low Birth Weight (LBW) babies who are initiated on Kangaroo Mother Care (KMC)',
                'formula': '(LBW babies initiated on KMC / LBW babies) × 100',
                'target': '100% (Green), 90-99.9% (Yellow), <90% (Red)',
                'importance': 'KMC improves survival rates and development outcomes for LBW babies',
                'data_element': '105-MA07. Low birth weight babies initiated on kangaroo (KMC)'
            },
            'birth_asphyxia_proportion': {
                'name': 'Babies with Birth Asphyxia',
                'definition': 'Proportion of newborns diagnosed with birth asphyxia (insufficient oxygen before, during, or just after birth)',
                'formula': '(Babies with Birth asphyxia / Total live births) × 100',
                'target': '≤1% (Green), 1.1-3% (Yellow), >3% (Red)',
                'importance': 'Birth asphyxia is a leading cause of neonatal mortality and disability',
                'data_element': '105-MA24. No.of babies with Birth asphyxia'
            },
            'successful_resuscitation_proportion': {
                'name': 'Successfully Resuscitated Birth Asphyxia',
                'definition': 'Proportion of babies with birth asphyxia who were successfully resuscitated (APGAR ≥7 after 5 minutes)',
                'formula': '(Successfully resuscitated babies / Babies with birth asphyxia) × 100',
                'target': '100% (Green), 80-99.9% (Yellow), <80% (Red)',
                'importance': 'Successful resuscitation prevents death and long-term complications from birth asphyxia',
                'data_element': '105-MA25. No. of Live babies Successfully Resuscitated'
            },
            'fresh_stillbirths_rate': {
                'name': 'Fresh Stillbirths Rate',
                'definition': 'Babies born without signs of life after 28 weeks gestation who died during labor/delivery per 1000 deliveries',
                'formula': '(Fresh stillbirths / Total deliveries) × 1000',
                'target': '≤5 per 1000 (Green), 5.1-10 per 1000 (Yellow), >10 per 1000 (Red)',
                'importance': 'Fresh stillbirths indicate quality of intrapartum care and emergency response',
                'data_element': '105-MA04c1. Deliveries in unit - Fresh still birth – Total'
            },
            'neonatal_mortality_rate': {
                'name': 'Neonatal Mortality Rate',
                'definition': 'Number of neonatal deaths (deaths of live-born babies within first 28 days) per 1,000 live births',
                'formula': '((Newborn deaths 0-7 days + Neonatal deaths 8-28 days) / Total live births) × 1000',
                'target': '≤5 per 1000 (Green), 5.1-10 per 1000 (Yellow), >10 per 1000 (Red)',
                'importance': 'Neonatal mortality reflects quality of newborn care and maternal health services',
                'data_element': '105-MA11 + 105-MA12. Newborn deaths (0-7 days) + Neonatal Death 8-28 days'
            },
            'perinatal_mortality_rate': {
                'name': 'Perinatal Mortality Rate',
                'definition': 'Number of stillbirths plus early neonatal deaths (within first 7 days) per 1,000 total births',
                'formula': '((Early neonatal deaths + Fresh stillbirths + Macerated stillbirths) / Total deliveries) × 1000',
                'target': '≤12 per 1000 (Green), 12.1-20 per 1000 (Yellow), >20 per 1000 (Red)',
                'importance': 'PMR reflects quality of both antenatal and intrapartum care services',
                'data_element': '105-MA11 + 105-MA04c1 + 105-MA04d1'
            },
            'maternal_mortality_ratio': {
                'name': 'Institutional Maternal Mortality Ratio',
                'definition': 'Number of maternal deaths per 100,000 deliveries in health facilities',
                'formula': '(Maternal deaths / Total live births) × 100,000',
                'target': '≤200 per 100,000 (Green), 201-400 per 100,000 (Yellow), >400 per 100,000 (Red)',
                'importance': 'IMMR indicates quality of maternal health services and emergency obstetric care',
                'data_element': '105-MA13. Maternal deaths'
            }
        }
