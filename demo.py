#!/usr/bin/env python3
"""
Demo script for the MNCAH Data Analysis System.

This script demonstrates the OOP system that auto-analyzes MNCAH data from raw input.
"""

import sys
import os
from pathlib import Path

# Add the mncah package to the path
sys.path.append(str(Path(__file__).parent))

from mncah import MNCAHSystem


def main():
    """Main demo function."""
    print("=" * 60)
    print("MNCAH DATA ANALYSIS SYSTEM DEMO")
    print("Object-Oriented Programming System for Auto-Analyzing")
    print("Maternal, Newborn, Child and Adolescent Health Data")
    print("=" * 60)
    
    # Initialize the MNCAH system
    print("\\n1. Initializing MNCAH Analysis System...")
    system = MNCAHSystem(output_dir='demo_output')
    print("✓ System initialized successfully!")
    
    # Path to sample data
    sample_data_path = Path(__file__).parent / 'data' / 'sample_mncah_data.csv'
    
    if not sample_data_path.exists():
        print(f"❌ Sample data file not found: {sample_data_path}")
        return
    
    print(f"\\n2. Loading sample MNCAH data from: {sample_data_path}")
    
    try:
        # Perform complete auto-analysis
        print("\\n3. Performing auto-analysis of MNCAH data...")
        print("   - Loading and validating data")
        print("   - Analyzing trends over time")
        print("   - Comparing countries performance") 
        print("   - Assessing progress towards global targets")
        print("   - Generating comprehensive reports")
        print("   - Creating visualizations")
        
        results = system.auto_analyze(
            source=sample_data_path,
            file_type='csv',
            report_formats=['html', 'json', 'text'],
            include_visualizations=True
        )
        
        if not results['processing_summary']['success']:
            print(f"❌ Analysis failed: {results['processing_summary']['error']}")
            return
        
        print("\\n✓ Auto-analysis completed successfully!")
        
        # Display results summary
        print("\\n" + "=" * 50)
        print("ANALYSIS RESULTS SUMMARY")
        print("=" * 50)
        
        summary = results['data_summary']
        print(f"📊 Data Overview:")
        print(f"   • Records processed: {summary['records']}")
        print(f"   • Countries analyzed: {summary['countries']}")
        print(f"   • Years of data: {summary['years']}")
        print(f"   • MNCAH indicators: {summary['indicators']}")
        
        # Analysis results
        analysis = results['analysis_results']
        print(f"\\n🔍 Analysis Results:")
        
        if 'trends' in analysis:
            trends = analysis['trends']
            print(f"   • Trend analysis: {len(trends)} indicators")
            for indicator, trend_data in list(trends.items())[:3]:  # Show first 3
                direction = trend_data.get('overall_trend', 'unknown')
                latest = trend_data.get('latest_value', 'N/A')
                print(f"     - {indicator.replace('_', ' ').title()}: {direction} trend (latest: {latest:.1f})")
        
        if 'country_comparison' in analysis:
            comparisons = analysis['country_comparison']
            print(f"   • Country comparison: {len(comparisons)} indicators")
            
        if 'target_assessment' in analysis:
            targets = analysis['target_assessment']
            print(f"   • Target assessment: {len(targets)} indicators")
            for indicator, target_data in list(targets.items())[:2]:  # Show first 2
                percentage = target_data.get('percentage_meeting_target', 0)
                print(f"     - {indicator.replace('_', ' ').title()}: {percentage:.1f}% of countries meeting target")
        
        # Generated files
        files = results['generated_files']
        print(f"\\n📄 Generated Reports & Visualizations:")
        for format_type, file_path in files.items():
            if format_type == 'visualizations':
                print(f"   • Visualizations: {len(file_path)} charts created")
                for viz_file in file_path[:2]:  # Show first 2
                    print(f"     - {Path(viz_file).name}")
            else:
                print(f"   • {format_type.upper()} report: {Path(file_path).name}")
        
        print(f"\\n📁 All output files saved to: demo_output/")
        
        # Demonstrate individual component usage
        print("\\n" + "=" * 50)
        print("INDIVIDUAL COMPONENT DEMONSTRATION")
        print("=" * 50)
        
        # Show how to use individual components
        print("\\n🔧 Using Individual Components:")
        
        # Data info
        data_info = system.get_data_info()
        print(f"   • Data Info: {data_info['status']}")
        print(f"     Countries: {', '.join(data_info['countries'][:5])}")
        
        # Analysis info
        analysis_info = system.get_analysis_info()
        print(f"   • Analysis Info: {analysis_info['status']}")
        print(f"     Analyses performed: {', '.join(analysis_info['analyses_performed'])}")
        
        print("\\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("\\nThe MNCAH system has successfully demonstrated:")
        print("✓ Object-Oriented Programming design")
        print("✓ Auto-analysis of MNCAH data from raw input")
        print("✓ Comprehensive trend and comparative analysis")
        print("✓ Target assessment against global health goals")
        print("✓ Multi-format report generation")
        print("✓ Data visualization capabilities")
        print("✓ Modular and extensible architecture")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()