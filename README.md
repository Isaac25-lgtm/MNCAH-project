# MNCAH Data Analysis System

An Object-Oriented Programming (OOP) system that auto-analyzes MNCAH (Maternal, Newborn, Child and Adolescent Health) data from raw input.

## Overview

This system provides a comprehensive, automated solution for analyzing MNCAH health indicators, generating insights, and producing reports to support evidence-based decision making in public health.

## Features

### 🏗️ Object-Oriented Architecture
- **MNCAHData**: Data representation and validation class
- **DataLoader**: Multi-format data loading with preprocessing
- **MNCAHAnalyzer**: Comprehensive analysis engine
- **ReportGenerator**: Multi-format report and visualization generator
- **MNCAHSystem**: Main coordinator class for end-to-end analysis

### 📊 Analysis Capabilities
- **Trend Analysis**: Track indicator changes over time
- **Country Comparison**: Compare performance across countries
- **Target Assessment**: Evaluate progress towards global health targets
- **Composite Index**: Calculate multi-indicator performance scores
- **Data Quality Assessment**: Automated data validation and quality checks

### 📈 Supported MNCAH Indicators
- **Maternal Health**: Mortality ratio, antenatal care coverage, skilled birth attendance
- **Newborn Health**: Neonatal mortality rate, low birth weight prevalence
- **Child Health**: Under-5 mortality, vaccination coverage, stunting, wasting
- **Adolescent Health**: Birth rates, anemia prevalence

### 📄 Output Formats
- **Reports**: HTML, JSON, Plain Text
- **Visualizations**: Trend charts, bar plots, box plots, dashboard summaries
- **Data Exports**: Processed datasets with analysis results

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Isaac25-lgtm/MNCAH-project.git
cd MNCAH-project

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from mncah import MNCAHSystem

# Initialize the system
system = MNCAHSystem(output_dir='results')

# Auto-analyze MNCAH data from any source
results = system.auto_analyze(
    source='data/sample_mncah_data.csv',
    report_formats=['html', 'json'],
    include_visualizations=True
)

# Results include comprehensive analysis and generated files
print(f"Analyzed {results['data_summary']['records']} records")
print(f"Generated reports: {results['generated_files']}")
```

### Demo

Run the included demonstration:

```bash
python demo.py
```

## System Architecture

```
MNCAHSystem (Main Coordinator)
├── DataLoader (Multi-format data input)
├── MNCAHData (Data validation & representation)
├── MNCAHAnalyzer (Analysis engine)
└── ReportGenerator (Output generation)
```

## Data Input Formats

The system supports multiple input formats:

- **CSV**: Comma-separated values with headers
- **JSON**: Structured JSON data
- **Excel**: .xlsx and .xls files
- **Dictionary**: Python dictionaries for programmatic input

### Required Data Structure

```csv
country,year,maternal_mortality_ratio,neonatal_mortality_rate,under5_mortality_rate,...
Kenya,2020,435,17,39,...
Uganda,2020,281,22,54,...
```

## Analysis Types

### 1. Trend Analysis
Analyzes indicator changes over time:
- Linear trend calculation
- Direction assessment (improving/worsening)
- Country-specific trend analysis

### 2. Country Comparison
Compares countries across indicators:
- Best/worst performers identification
- Statistical summaries
- Ranking analysis

### 3. Target Assessment
Evaluates progress towards global targets:
- WHO/UNICEF target comparison
- Gap analysis
- Countries on/off track identification

### 4. Composite Index
Creates multi-indicator performance scores:
- Weighted indicator combination
- Country ranking
- Performance benchmarking

## Sample Analysis Results

```python
{
    'data_summary': {
        'records': 48,
        'countries': 8, 
        'years': 6,
        'indicators': 9
    },
    'analysis_results': {
        'trends': {...},
        'country_comparison': {...},
        'target_assessment': {...}
    },
    'generated_files': {
        'html': 'reports/mncah_report_20231210_143022.html',
        'json': 'reports/mncah_report_20231210_143022.json',
        'visualizations': ['chart1.png', 'chart2.png', ...]
    }
}
```

## Global Health Targets

The system includes reference targets from WHO/UNICEF:
- Maternal Mortality Ratio: ≤70 per 100,000 live births
- Neonatal Mortality Rate: ≤12 per 1,000 live births  
- Under-5 Mortality Rate: ≤25 per 1,000 live births
- Vaccination Coverage: ≥90% for key vaccines
- And more...

## Testing

Run the test suite:

```bash
python tests/test_system.py
```

## Project Structure

```
MNCAH-project/
├── mncah/                 # Main package
│   ├── __init__.py
│   ├── system.py          # Main coordinator
│   ├── data_loader.py     # Data loading
│   ├── mncah_data.py      # Data representation
│   ├── analyzer.py        # Analysis engine
│   └── report_generator.py # Report generation
├── data/                  # Sample data
│   └── sample_mncah_data.csv
├── tests/                 # Test suite
│   └── test_system.py
├── demo.py               # Demonstration script
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For questions or issues, please open a GitHub issue or contact the development team.
