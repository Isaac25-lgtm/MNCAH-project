"""
Antenatal Care (ANC) Model
This module implements all ANC indicators and calculations as specified in the requirements.
"""

from typing import Dict
from .base import MaternalNeonatalChildAdolescentHealth, ValidationStatus, PopulationData


class AntenatalCare(MaternalNeonatalChildAdolescentHealth):
    """
    Antenatal Care subclass implementing all 9 ANC indicators:
    1. ANC 1 Coverage
    2. ANC 1st Trimester 
    3. ANC 4 Coverage
    4. ANC 8 Coverage
    5. IPT 3 Coverage
    6. Proportion of ANC 1 clients who had an Hb test
    7. LLIN Coverage
    8. Iron/Folic Acid at ANC1
    9. Obstetric Ultrasound scan
    """
    
    def __init__(self, population_data: PopulationData, raw_data: Dict[str, any]):
        """
        Initialize ANC model
        
        Args:
            population_data: Population information for calculations
            raw_data: Raw data containing ANC indicator values
        """
        super().__init__(population_data, raw_data)
        
        # ANC-specific indicator codes from the requirements
        self.indicator_codes = {
            'anc_1st_visit': '105-AN01a',
            'anc_1st_trimester': '105-AN01b', 
            'anc_4th_visit': '105-AN02',
            'anc_8_visits': '105-AN04',
            'ipt3_dose': '105-AN010',
            'hb_test_anc1': '105-AN17',
            'iron_folic_anc1': '105-AN21',
            'llin_anc1': '105-AN23',
            'ultrasound_scan': '105-AN24a'
        }
    
    def calculate_indicators(self) -> Dict[str, float]:
        """
        Calculate all ANC indicators according to MOH formulas
        
        Returns:
            Dictionary with calculated ANC indicator values
        """
        expected_pregnancies = self.population_data.expected_pregnancies
        
        # Get raw values from uploaded data
        anc_1st_visit = self.get_raw_value(self.indicator_codes['anc_1st_visit'])
        anc_1st_trimester = self.get_raw_value(self.indicator_codes['anc_1st_trimester'])
        anc_4th_visit = self.get_raw_value(self.indicator_codes['anc_4th_visit'])
        anc_8_visits = self.get_raw_value(self.indicator_codes['anc_8_visits'])
        ipt3_dose = self.get_raw_value(self.indicator_codes['ipt3_dose'])
        hb_test_anc1 = self.get_raw_value(self.indicator_codes['hb_test_anc1'])
        iron_folic_anc1 = self.get_raw_value(self.indicator_codes['iron_folic_anc1'])
        llin_anc1 = self.get_raw_value(self.indicator_codes['llin_anc1'])
        ultrasound_scan = self.get_raw_value(self.indicator_codes['ultrasound_scan'])
        
        # Calculate indicators using MOH formulas
        indicators = {
            # 1. ANC 1 Coverage = (ANC 1st Visit for women / Expected pregnancies) × 100
            'anc_1_coverage': self.calculate_percentage(anc_1st_visit, expected_pregnancies),
            
            # 2. ANC 1st Trimester Coverage = (ANC 1st Visit 1st Trimester / Expected pregnancies) × 100
            'anc_1st_trimester': self.calculate_percentage(anc_1st_trimester, expected_pregnancies),
            
            # 3. ANC 4 Coverage = (ANC 4th Visit for women / Expected pregnancies) × 100
            'anc_4_coverage': self.calculate_percentage(anc_4th_visit, expected_pregnancies),
            
            # 4. ANC 8 Coverage = (ANC 8 contacts/visits for women / Expected pregnancies) × 100
            'anc_8_coverage': self.calculate_percentage(anc_8_visits, expected_pregnancies),
            
            # 5. IPT 3 Coverage = (Third dose IPT (IPT3) / Expected pregnancies) × 100
            'ipt3_coverage': self.calculate_percentage(ipt3_dose, expected_pregnancies),
            
            # 6. Proportion of ANC 1 clients who had an Hb test = (Hb Test at ANC 1st contact / Expected pregnancies) × 100
            'hb_testing_coverage': self.calculate_percentage(hb_test_anc1, expected_pregnancies),
            
            # 7. LLIN Coverage = (Pregnant Women receiving LLINs at ANC 1st visit / Expected pregnancies) × 100
            'llin_coverage': self.calculate_percentage(llin_anc1, expected_pregnancies),
            
            # 8. Iron/Folic Acid at ANC1 = (Pregnant Women receiving atleast 30 tablets of Iron/Folic Acid at ANC 1st contact / Expected pregnancies) × 100
            'iron_folic_anc1': self.calculate_percentage(iron_folic_anc1, expected_pregnancies),
            
            # 9. Obstetric Ultrasound scan = (Pregnant women who received obstetric ultra sound scan during any ANC visits / ANC 1st Visit for women) × 100
            'ultrasound_coverage': self.calculate_percentage(ultrasound_scan, anc_1st_visit)
        }
        
        return indicators
    
    def validate_indicators(self) -> Dict[str, ValidationStatus]:
        """
        Validate ANC indicators against MOH targets and rules
        
        Returns:
            Dictionary mapping indicator names to validation status
        """
        if not self.calculated_indicators:
            self.calculated_indicators = self.calculate_indicators()
        
        validations = {}
        
        for indicator_name, value in self.calculated_indicators.items():
            validations[indicator_name] = self._validate_anc_indicator(indicator_name, value)
        
        return validations
    
    def _validate_anc_indicator(self, indicator_name: str, value: float) -> ValidationStatus:
        """
        Validate individual ANC indicator based on MOH targets
        
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
        if indicator_name == 'anc_1_coverage':
            # ANC 1 target is 100%. Can be above 100% as it's population based
            # 100% and above = green, 70% to 99.9% = yellow, below 70% = red
            if value >= 100.0:
                return ValidationStatus.GREEN
            elif 70.0 <= value <= 99.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'anc_1st_trimester':
            # ANC 1st Trimester target is 45%. Cannot be above 100%
            # 45% to 100% = green, 30% to 44.9% = yellow, below 30% = red
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif 45.0 <= value <= 100.0:
                return ValidationStatus.GREEN
            elif 30.0 <= value <= 44.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name in ['anc_4_coverage', 'anc_8_coverage']:
            # ANC 4 and ANC 8 can be above 100% (population based estimation)
            # Using same targets as ANC 1: 100% and above = green, 70% to 99.9% = yellow, below 70% = red
            if value >= 100.0:
                return ValidationStatus.GREEN
            elif 70.0 <= value <= 99.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'ipt3_coverage':
            # IPT3 target is 85%. Can be above 100%
            # 85% and above = green, 65% to 84.9% = yellow, below 65% = red
            if value >= 85.0:
                return ValidationStatus.GREEN
            elif 65.0 <= value <= 84.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'hb_testing_coverage':
            # Hb testing target is 75%. Cannot be above 100%
            # 75% to 100% = green, 60% to 74.9% = yellow, below 60% = red
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif 75.0 <= value <= 100.0:
                return ValidationStatus.GREEN
            elif 60.0 <= value <= 74.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'iron_folic_anc1':
            # Iron/Folic at ANC 1 target is 75%. Cannot be above 100%
            # 75% to 100% = green, 60% to 74.9% = yellow, below 60% = red
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif 75.0 <= value <= 100.0:
                return ValidationStatus.GREEN
            elif 60.0 <= value <= 74.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'llin_coverage':
            # LLIN coverage - using similar targets as other ANC interventions
            # Assuming 85% target like IPT3
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value >= 85.0:
                return ValidationStatus.GREEN
            elif 65.0 <= value <= 84.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        elif indicator_name == 'ultrasound_coverage':
            # Ultrasound coverage - cannot be above 100% as denominator is ANC 1 visits
            # Using 60% as target (reasonable for resource-limited settings)
            if value > 100.0:
                return ValidationStatus.BLUE  # Data quality issue
            elif value >= 60.0:
                return ValidationStatus.GREEN
            elif 40.0 <= value <= 59.9:
                return ValidationStatus.YELLOW
            else:
                return ValidationStatus.RED
        
        # Default case
        return ValidationStatus.BLUE
    
    def get_indicator_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        Get definitions for all ANC indicators
        
        Returns:
            Dictionary with indicator definitions, formulas, targets, and importance
        """
        return {
            'anc_1_coverage': {
                'name': 'ANC 1 Coverage',
                'definition': 'Proportion of pregnant women who attend their first antenatal care (ANC) visit during pregnancy',
                'formula': '(ANC 1st Visit for women / Expected pregnancies) × 100',
                'target': '100% and above (Green), 70-99.9% (Yellow), <70% (Red)',
                'importance': 'Early ANC contact is crucial for identifying and managing pregnancy complications',
                'data_element': '105-AN01a. ANC 1st Visit for women'
            },
            'anc_1st_trimester': {
                'name': 'ANC 1st Trimester',
                'definition': 'First antenatal care (ANC) visit within the first 12 weeks (3 months) of pregnancy',
                'formula': '(ANC 1st Visit 1st Trimester / Expected pregnancies) × 100',
                'target': '45-100% (Green), 30-44.9% (Yellow), <30% (Red)',
                'importance': 'Early booking allows for timely interventions and better pregnancy outcomes',
                'data_element': '105-AN01b. ANC 1st Visit for women (1st Trimester)'
            },
            'anc_4_coverage': {
                'name': 'ANC 4 Coverage',
                'definition': 'Proportion of pregnant women who attended at least four antenatal care (ANC) visits during pregnancy',
                'formula': '(ANC 4th Visit for women / Expected pregnancies) × 100',
                'target': '100% and above (Green), 70-99.9% (Yellow), <70% (Red)',
                'importance': 'Four ANC visits allow adequate monitoring and intervention according to WHO guidelines',
                'data_element': '105-AN02. ANC 4th Visit for women'
            },
            'anc_8_coverage': {
                'name': 'ANC 8 Coverage',
                'definition': 'Proportion of pregnant women who complete at least 8 antenatal care contacts during pregnancy (2016 WHO guidelines)',
                'formula': '(ANC 8 contacts/visits for women / Expected pregnancies) × 100',
                'target': '100% and above (Green), 70-99.9% (Yellow), <70% (Red)',
                'importance': 'Eight contacts provide comprehensive care based on updated WHO recommendations',
                'data_element': '105-AN04. ANC 8 contacts/visits for women'
            },
            'ipt3_coverage': {
                'name': 'IPT 3 Coverage',
                'definition': 'Percentage of pregnant women who received the third dose of Intermittent Preventive Treatment using Sulfadoxine-Pyrimethamine (SP)',
                'formula': '(Third dose IPT (IPT3) / Expected pregnancies) × 100',
                'target': '85% and above (Green), 65-84.9% (Yellow), <65% (Red)',
                'importance': 'IPT3 prevents malaria in pregnancy, reducing maternal and perinatal mortality',
                'data_element': '105-AN010. Third dose IPT (IPT3)'
            },
            'hb_testing_coverage': {
                'name': 'Hb Testing Coverage',
                'definition': 'Proportion of pregnant women tested for anemia using Hemoglobin (Hb) test at ANC 1st contact',
                'formula': '(Pregnant women tested for Anemia using Hb Test at ANC 1st contact / Expected pregnancies) × 100',
                'target': '75-100% (Green), 60-74.9% (Yellow), <60% (Red)',
                'importance': 'Early detection of anemia allows timely treatment and prevents complications',
                'data_element': '105-AN17. Pregnant women who were tested for Anaemia using Hb Test at ANC 1st contact'
            },
            'llin_coverage': {
                'name': 'LLIN Coverage',
                'definition': 'Proportion of pregnant women who received a Long-Lasting Insecticidal Net (LLIN) at ANC 1st visit',
                'formula': '(Pregnant Women receiving LLINs at ANC 1st visit / Expected pregnancies) × 100',
                'target': '85% and above (Green), 65-84.9% (Yellow), <65% (Red)',
                'importance': 'LLINs prevent malaria transmission, protecting both mother and fetus',
                'data_element': '105-AN23. Pregnant Women receiving LLINs at ANC 1st visit'
            },
            'iron_folic_anc1': {
                'name': 'Iron/Folic Acid at ANC1',
                'definition': 'Proportion of pregnant women who received at least 30 tablets of iron and folic acid supplements at ANC 1st contact',
                'formula': '(Pregnant Women receiving atleast 30 tablets Iron/Folic Acid at ANC 1st contact / Expected pregnancies) × 100',
                'target': '75-100% (Green), 60-74.9% (Yellow), <60% (Red)',
                'importance': 'Iron/folic acid supplementation prevents anemia and neural tube defects',
                'data_element': '105-AN21. Pregnant Women receiving atleast 30 tablets of Iron/Folic Acid at ANC 1st contact'
            },
            'ultrasound_coverage': {
                'name': 'Obstetric Ultrasound Coverage',
                'definition': 'Proportion of pregnant women who received obstetric ultrasound scan during any ANC visit',
                'formula': '(Pregnant women who received obstetric ultra sound scan during any ANC visits / ANC 1st Visit for women) × 100',
                'target': '60% and above (Green), 40-59.9% (Yellow), <40% (Red)',
                'importance': 'Ultrasound helps detect fetal abnormalities and pregnancy complications early',
                'data_element': '105-AN24a. Pregnant women who received obstetric ultra sound scan during any ANC visits'
            }
        }
