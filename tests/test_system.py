"""
Simple test to verify the MNCAH system functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mncah import MNCAHSystem


def test_basic_functionality():
    """Test basic functionality of the MNCAH system."""
    print("Testing MNCAH System...")
    
    # Initialize system
    system = MNCAHSystem(output_dir='test_output')
    
    # Test with sample data
    sample_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_mncah_data.csv')
    
    try:
        # Test auto-analysis
        print("\\nRunning auto-analysis...")
        results = system.auto_analyze(
            source=sample_data_path,
            file_type='csv',
            report_formats=['html', 'json'],
            include_visualizations=True
        )
        
        if results['processing_summary']['success']:
            print("✓ Auto-analysis completed successfully!")
            
            # Print summary
            summary = results['data_summary']
            print(f"✓ Loaded {summary['records']} records")
            print(f"✓ {summary['countries']} countries analyzed")
            print(f"✓ {summary['years']} years of data")
            print(f"✓ {summary['indicators']} indicators processed")
            
            # Print analysis results
            analysis = results['analysis_results']
            if 'trends' in analysis:
                print(f"✓ Trend analysis completed for {len(analysis['trends'])} indicators")
            
            if 'country_comparison' in analysis:
                print(f"✓ Country comparison completed for {len(analysis['country_comparison'])} indicators")
            
            if 'target_assessment' in analysis:
                print(f"✓ Target assessment completed for {len(analysis['target_assessment'])} indicators")
            
            # Print generated files
            files = results['generated_files']
            print(f"\\nGenerated files:")
            for format_type, file_path in files.items():
                if format_type != 'visualizations':
                    print(f"  - {format_type.upper()}: {file_path}")
                else:
                    print(f"  - Visualizations: {len(file_path)} files")
            
            print("\\n✓ All tests passed! MNCAH system is working correctly.")
            return True
            
        else:
            print(f"✗ Auto-analysis failed: {results['processing_summary']['error']}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with error: {str(e)}")
        return False


def test_individual_components():
    """Test individual components of the system."""
    print("\\nTesting individual components...")
    
    try:
        # Test data loading
        from mncah.data_loader import DataLoader
        loader = DataLoader()
        
        sample_data = {
            'country': ['TestCountry1', 'TestCountry2'],
            'year': [2020, 2020],
            'maternal_mortality_ratio': [100, 150],
            'under5_mortality_rate': [30, 40]
        }
        
        data = loader.load_from_dict(sample_data)
        print(f"✓ DataLoader: Loaded {len(data)} records")
        
        # Test analyzer
        from mncah.analyzer import MNCAHAnalyzer
        analyzer = MNCAHAnalyzer()
        
        trends = analyzer.analyze_trends(data)
        print(f"✓ MNCAHAnalyzer: Analyzed trends for {len(trends)} indicators")
        
        # Test report generator
        from mncah.report_generator import ReportGenerator
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = ReportGenerator(temp_dir)
            report_file = reporter.generate_summary_report(data, {'trends': trends}, 'text')
            print(f"✓ ReportGenerator: Generated report at {report_file}")
        
        print("✓ All component tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Component test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = True
    
    # Run component tests
    success &= test_individual_components()
    
    # Run integration test
    success &= test_basic_functionality()
    
    if success:
        print("\\n🎉 All tests completed successfully! The MNCAH system is ready to use.")
    else:
        print("\\n❌ Some tests failed. Please check the error messages above.")