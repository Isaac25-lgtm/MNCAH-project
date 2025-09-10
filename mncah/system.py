"""
MNCAHSystem - Main coordinator class for the MNCAH data analysis system.
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

from .data_loader import DataLoader
from .mncah_data import MNCAHData
from .analyzer import MNCAHAnalyzer
from .report_generator import ReportGenerator


class MNCAHSystem:
    """
    Main coordinator class for the MNCAH (Maternal, Newborn, Child and Adolescent Health) 
    data analysis system.
    
    This class provides a high-level interface for auto-analyzing MNCAH data from raw input,
    orchestrating the entire analysis pipeline from data loading to report generation.
    """
    
    def __init__(self, output_dir: str = 'output'):
        """
        Initialize the MNCAH Analysis System.
        
        Args:
            output_dir: Directory for output files and reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.data_loader = DataLoader()
        self.analyzer = MNCAHAnalyzer()
        self.report_generator = ReportGenerator(str(self.output_dir / 'reports'))
        
        # Set up logging
        self.logger = self._setup_logging()
        
        # Storage for current data and results
        self.current_data = None
        self.analysis_results = {}
        
        self.logger.info("MNCAH Analysis System initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('mncah_system')
        logger.setLevel(logging.INFO)
        
        # Create console handler if not exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_data(self, source: Union[str, Path, Dict], 
                  file_type: Optional[str] = None,
                  preprocessing: bool = True,
                  **kwargs) -> MNCAHData:
        """
        Load MNCAH data from various sources.
        
        Args:
            source: Data source (file path, URL, or dictionary)
            file_type: File type ('csv', 'json', 'excel'). Auto-detected if None
            preprocessing: Whether to apply data preprocessing
            **kwargs: Additional arguments for data loading
            
        Returns:
            MNCAHData object
        """
        self.logger.info(f"Loading data from: {source}")
        
        try:
            # Load data based on source type
            if isinstance(source, dict):
                data = self.data_loader.load_from_dict(source)
            elif isinstance(source, (str, Path)):
                source_path = Path(source)
                
                # Auto-detect file type if not provided
                if file_type is None:
                    file_type = source_path.suffix.lower().lstrip('.')
                
                # Load based on file type
                if file_type == 'csv':
                    data = self.data_loader.load_from_csv(source_path, **kwargs)
                elif file_type == 'json':
                    data = self.data_loader.load_from_json(source_path)
                elif file_type in ['xlsx', 'xls', 'excel']:
                    data = self.data_loader.load_from_excel(source_path, **kwargs)
                else:
                    raise ValueError(f"Unsupported file type: {file_type}")
            else:
                raise ValueError("Source must be a file path, URL, or dictionary")
            
            # Apply preprocessing if requested
            if preprocessing:
                processed_df = self.data_loader.preprocess_data(
                    data.data, 
                    drop_duplicates=True,
                    fill_missing=False  # Conservative approach for health data
                )
                data = MNCAHData(processed_df, data.metadata)
            
            self.current_data = data
            self.logger.info(f"Successfully loaded {len(data)} records")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load data: {str(e)}")
            raise
    
    def analyze_data(self, data: Optional[MNCAHData] = None,
                    include_trends: bool = True,
                    include_comparisons: bool = True,
                    include_targets: bool = True,
                    include_composite: bool = False,
                    custom_targets: Optional[Dict] = None,
                    composite_indicators: Optional[List[str]] = None) -> Dict:
        """
        Perform comprehensive analysis of MNCAH data.
        
        Args:
            data: MNCAHData object (uses current_data if None)
            include_trends: Whether to perform trend analysis
            include_comparisons: Whether to perform country comparisons
            include_targets: Whether to assess progress towards targets
            include_composite: Whether to calculate composite index
            custom_targets: Custom target values for assessment
            composite_indicators: Indicators to include in composite index
            
        Returns:
            Dictionary containing all analysis results
        """
        # Use provided data or current data
        analysis_data = data or self.current_data
        if analysis_data is None:
            raise ValueError("No data available for analysis. Load data first.")
        
        self.logger.info("Starting comprehensive MNCAH data analysis")
        
        results = {}
        
        try:
            # Trend analysis
            if include_trends:
                self.logger.info("Performing trend analysis...")
                trends = self.analyzer.analyze_trends(analysis_data)
                results['trends'] = trends
                self.logger.info(f"Analyzed trends for {len(trends)} indicators")
            
            # Country comparisons
            if include_comparisons:
                self.logger.info("Performing country comparisons...")
                comparisons = self.analyzer.compare_countries(analysis_data)
                results['country_comparison'] = comparisons
                self.logger.info(f"Compared countries for {len(comparisons)} indicators")
            
            # Target assessment
            if include_targets:
                self.logger.info("Assessing progress towards targets...")
                targets = self.analyzer.assess_targets(analysis_data, custom_targets)
                results['target_assessment'] = targets
                self.logger.info(f"Assessed targets for {len(targets)} indicators")
            
            # Composite index
            if include_composite and composite_indicators:
                self.logger.info("Calculating composite index...")
                composite = self.analyzer.calculate_composite_index(
                    analysis_data, composite_indicators
                )
                results['composite_index'] = composite
                self.logger.info("Composite index calculated")
            
            # Generate summary report
            summary = self.analyzer.get_summary_report(analysis_data)
            results['summary'] = summary
            
            # Store results
            self.analysis_results = results
            
            self.logger.info("Analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def generate_reports(self, analysis_results: Optional[Dict] = None,
                        formats: List[str] = ['html'],
                        include_visualizations: bool = True,
                        visualization_indicators: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate comprehensive reports from analysis results.
        
        Args:
            analysis_results: Analysis results (uses stored results if None)
            formats: Report formats to generate ('html', 'json', 'text')
            include_visualizations: Whether to generate visualizations
            visualization_indicators: Specific indicators to visualize
            
        Returns:
            Dictionary mapping format to file path
        """
        # Use provided results or stored results
        results = analysis_results or self.analysis_results
        if not results:
            raise ValueError("No analysis results available. Run analysis first.")
        
        if self.current_data is None:
            raise ValueError("No data available for reporting. Load data first.")
        
        self.logger.info("Generating reports...")
        
        generated_files = {}
        
        try:
            # Generate reports in requested formats
            for format_type in formats:
                self.logger.info(f"Generating {format_type.upper()} report...")
                report_file = self.report_generator.generate_summary_report(
                    self.current_data, results, format_type
                )
                generated_files[format_type] = report_file
                self.logger.info(f"{format_type.upper()} report saved: {report_file}")
            
            # Generate visualizations
            if include_visualizations:
                self.logger.info("Generating visualizations...")
                
                # Determine indicators to visualize
                if visualization_indicators is None:
                    available_indicators = [col for col in self.current_data.data.columns 
                                          if col in self.current_data.ALL_INDICATORS]
                    visualization_indicators = available_indicators[:5]  # Limit to first 5
                
                viz_files = []
                for indicator in visualization_indicators:
                    if indicator in self.current_data.data.columns:
                        try:
                            # Create trend plot
                            trend_file = self.report_generator.create_visualization(
                                self.current_data, indicator, 'trend'
                            )
                            if trend_file:
                                viz_files.append(trend_file)
                            
                            # Create bar plot for latest year
                            bar_file = self.report_generator.create_visualization(
                                self.current_data, indicator, 'bar'
                            )
                            if bar_file:
                                viz_files.append(bar_file)
                                
                        except Exception as e:
                            self.logger.warning(f"Failed to create visualization for {indicator}: {e}")
                
                # Create dashboard summary
                try:
                    dashboard_file = self.report_generator.create_dashboard_summary(
                        self.current_data, results
                    )
                    if dashboard_file:
                        viz_files.append(dashboard_file)
                except Exception as e:
                    self.logger.warning(f"Failed to create dashboard: {e}")
                
                generated_files['visualizations'] = viz_files
                self.logger.info(f"Generated {len(viz_files)} visualizations")
            
            self.logger.info("Report generation completed successfully")
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            raise
    
    def auto_analyze(self, source: Union[str, Path, Dict],
                    file_type: Optional[str] = None,
                    report_formats: List[str] = ['html'],
                    include_visualizations: bool = True,
                    custom_targets: Optional[Dict] = None,
                    **kwargs) -> Dict:
        """
        Perform complete auto-analysis of MNCAH data from raw input.
        
        This is the main entry point for the system, providing end-to-end analysis.
        
        Args:
            source: Data source (file path, URL, or dictionary)
            file_type: File type ('csv', 'json', 'excel')
            report_formats: Formats for generated reports
            include_visualizations: Whether to generate visualizations
            custom_targets: Custom target values for assessment
            **kwargs: Additional arguments for data loading
            
        Returns:
            Dictionary containing analysis results and generated file paths
        """
        self.logger.info("Starting auto-analysis of MNCAH data")
        
        try:
            # Step 1: Load data
            data = self.load_data(source, file_type, **kwargs)
            
            # Step 2: Analyze data
            analysis_results = self.analyze_data(
                data,
                include_trends=True,
                include_comparisons=True,
                include_targets=True,
                custom_targets=custom_targets
            )
            
            # Step 3: Generate reports
            generated_files = self.generate_reports(
                analysis_results,
                formats=report_formats,
                include_visualizations=include_visualizations
            )
            
            # Prepare final results
            final_results = {
                'data_summary': {
                    'records': len(data),
                    'countries': len(data.get_countries()),
                    'years': len(data.get_years()),
                    'indicators': len([col for col in data.data.columns if col in data.ALL_INDICATORS])
                },
                'analysis_results': analysis_results,
                'generated_files': generated_files,
                'processing_summary': {
                    'success': True,
                    'message': 'Auto-analysis completed successfully'
                }
            }
            
            self.logger.info("Auto-analysis completed successfully")
            return final_results
            
        except Exception as e:
            error_message = f"Auto-analysis failed: {str(e)}"
            self.logger.error(error_message)
            
            return {
                'processing_summary': {
                    'success': False,
                    'error': error_message
                }
            }
    
    def get_data_info(self) -> Dict:
        """Get information about currently loaded data."""
        if self.current_data is None:
            return {'status': 'no_data_loaded'}
        
        return {
            'status': 'data_loaded',
            'records': len(self.current_data),
            'countries': self.current_data.get_countries(),
            'years': self.current_data.get_years(),
            'indicators': [col for col in self.current_data.data.columns 
                         if col in self.current_data.ALL_INDICATORS],
            'metadata': self.current_data.metadata
        }
    
    def get_analysis_info(self) -> Dict:
        """Get information about last analysis performed."""
        if not self.analysis_results:
            return {'status': 'no_analysis_performed'}
        
        return {
            'status': 'analysis_available',
            'analyses_performed': list(self.analysis_results.keys()),
            'last_analysis_date': self.analyzer.last_analysis_date.isoformat() 
                                if self.analyzer.last_analysis_date else None
        }
    
    def reset(self):
        """Reset the system state."""
        self.current_data = None
        self.analysis_results = {}
        self.analyzer = MNCAHAnalyzer()
        self.logger.info("System state reset")