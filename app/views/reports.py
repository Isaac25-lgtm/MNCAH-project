"""
Reports Views
This module handles report generation, export functionality, and data quality reports
for the MOH MNCAH Dashboard System.
"""

import os
import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
import logging

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from ..models.upload import DataUpload, UploadStatus
from ..services.validation_service import DataValidationService
from ..services.calculation_service import MNCHACalculationService
from .. import db


# Create reports blueprint
reports_bp = Blueprint('reports', __name__)
logger = logging.getLogger(__name__)


@reports_bp.route('/')
@login_required
def index():
    """
    Reports dashboard - shows available reports and generation options
    """
    try:
        # Get report statistics
        report_stats = get_report_statistics()
        
        # Get recent reports (if we were tracking them)
        recent_activity = get_recent_report_activity()
        
        return render_template('reports/index.html',
                             report_stats=report_stats,
                             recent_activity=recent_activity)
    
    except Exception as e:
        logger.error(f"Error loading reports page: {str(e)}")
        return render_template('reports/index.html',
                             report_stats={},
                             recent_activity=[],
                             error="Error loading reports data")


@reports_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_report():
    """
    Generate comprehensive MNCAH report
    """
    if request.method == 'GET':
        # Show report generation form
        filters_data = get_report_filters_data()
        return render_template('reports/generate.html', filters_data=filters_data)
    
    try:
        # Get form parameters
        report_type = request.form.get('report_type', 'comprehensive')
        facilities = request.form.getlist('facilities') or None
        districts = request.form.getlist('districts') or None
        period_from = request.form.get('period_from')
        period_to = request.form.get('period_to')
        format_type = request.form.get('format', 'html')
        include_charts = request.form.get('include_charts') == 'on'
        include_validation = request.form.get('include_validation') == 'on'
        
        # Generate report data
        report_data = generate_report_data(
            report_type=report_type,
            facilities=facilities,
            districts=districts,
            period_from=period_from,
            period_to=period_to,
            include_validation=include_validation
        )
        
        if format_type == 'pdf':
            return generate_pdf_report(report_data, include_charts)
        elif format_type == 'excel':
            return generate_excel_report(report_data)
        else:
            # HTML report
            return render_template('reports/generated_report.html',
                                 report_data=report_data,
                                 include_charts=include_charts)
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'success': False, 'message': f'Error generating report: {str(e)}'}), 500


@reports_bp.route('/data-quality')
@login_required
def data_quality_report():
    """
    Comprehensive data quality report
    """
    try:
        # Get filter parameters
        facility_filter = request.args.get('facility')
        district_filter = request.args.get('district')
        period_filter = request.args.get('period')
        
        # Generate data quality report
        validation_service = DataValidationService()
        quality_report = generate_data_quality_report(
            facility_filter, district_filter, period_filter
        )
        
        # Get filters data
        filters_data = get_report_filters_data()
        
        return render_template('reports/data_quality.html',
                             quality_report=quality_report,
                             filters_data=filters_data,
                             current_filters={
                                 'facility': facility_filter,
                                 'district': district_filter,
                                 'period': period_filter
                             })
    
    except Exception as e:
        logger.error(f"Error generating data quality report: {str(e)}")
        return render_template('reports/data_quality.html',
                             quality_report={},
                             filters_data={},
                             current_filters={},
                             error="Error generating data quality report")


@reports_bp.route('/performance-summary')
@login_required
def performance_summary():
    """
    Performance summary report across all indicators
    """
    try:
        # Get performance data
        performance_data = generate_performance_summary()
        
        return render_template('reports/performance_summary.html',
                             performance_data=performance_data)
    
    except Exception as e:
        logger.error(f"Error generating performance summary: {str(e)}")
        return render_template('reports/performance_summary.html',
                             performance_data={},
                             error="Error generating performance summary")


@reports_bp.route('/facility/<string:facility_name>')
@login_required
def facility_report(facility_name):
    """
    Detailed report for a specific facility
    """
    try:
        # Generate facility-specific report
        facility_data = generate_facility_report(facility_name)
        
        return render_template('reports/facility_report.html',
                             facility_name=facility_name,
                             facility_data=facility_data)
    
    except Exception as e:
        logger.error(f"Error generating facility report for {facility_name}: {str(e)}")
        return render_template('reports/facility_report.html',
                             facility_name=facility_name,
                             facility_data={},
                             error="Error generating facility report")


@reports_bp.route('/export/excel')
@login_required
def export_excel():
    """
    Export data to Excel format
    """
    try:
        # Get filter parameters
        facilities = request.args.getlist('facilities')
        districts = request.args.getlist('districts')
        categories = request.args.getlist('categories') or ['anc', 'intrapartum', 'pnc']
        
        # Generate Excel file
        excel_file = create_excel_export(facilities, districts, categories)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f'MNCAH_Data_Export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return jsonify({'success': False, 'message': 'Error generating Excel export'}), 500


@reports_bp.route('/export/pdf')
@login_required
def export_pdf():
    """
    Export report to PDF format
    """
    try:
        # Get parameters
        report_type = request.args.get('report_type', 'summary')
        facility = request.args.get('facility')
        
        # Generate PDF
        pdf_file = create_pdf_export(report_type, facility)
        
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f'MNCAH_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error exporting to PDF: {str(e)}")
        return jsonify({'success': False, 'message': 'Error generating PDF export'}), 500


@reports_bp.route('/validation-dashboard')
@login_required
def validation_dashboard():
    """
    Interactive validation dashboard
    """
    try:
        validation_service = DataValidationService()
        
        # Get all completed uploads
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        # Generate validation dashboard data
        dashboard_data = validation_service.generate_validation_dashboard_data([
            upload.to_dict(include_data=True) for upload in uploads
        ])
        
        return render_template('reports/validation_dashboard.html',
                             dashboard_data=dashboard_data)
    
    except Exception as e:
        logger.error(f"Error generating validation dashboard: {str(e)}")
        return render_template('reports/validation_dashboard.html',
                             dashboard_data={},
                             error="Error generating validation dashboard")


# API Endpoints

@reports_bp.route('/api/report-data')
@login_required
def api_report_data():
    """
    API endpoint for report data
    """
    try:
        report_type = request.args.get('type', 'summary')
        facilities = request.args.getlist('facilities')
        
        data = generate_api_report_data(report_type, facilities)
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Error getting report data: {str(e)}")
        return jsonify({'error': 'Error retrieving report data'}), 500


@reports_bp.route('/api/validation-summary')
@login_required
def api_validation_summary():
    """
    API endpoint for validation summary
    """
    try:
        summary = get_system_validation_summary()
        return jsonify(summary)
    
    except Exception as e:
        logger.error(f"Error getting validation summary: {str(e)}")
        return jsonify({'error': 'Error retrieving validation summary'}), 500


# Helper functions

def get_report_statistics():
    """Get statistics for reports dashboard"""
    try:
        stats = {
            'total_facilities': db.session.query(DataUpload.facility_name).distinct().count(),
            'total_uploads': DataUpload.query.filter_by(status=UploadStatus.COMPLETED).count(),
            'districts_covered': db.session.query(DataUpload.district).filter(
                DataUpload.district.isnot(None)
            ).distinct().count(),
            'latest_period': db.session.query(DataUpload.reporting_period).order_by(
                DataUpload.reporting_period.desc()
            ).first()
        }
        
        # Data quality stats
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        if uploads:
            total_indicators = sum(upload.total_indicators for upload in uploads)
            valid_indicators = sum(upload.valid_indicators for upload in uploads)
            stats['overall_quality_rate'] = (valid_indicators / total_indicators * 100) if total_indicators > 0 else 0
        else:
            stats['overall_quality_rate'] = 0
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting report statistics: {str(e)}")
        return {}


def get_recent_report_activity():
    """Get recent report generation activity"""
    try:
        # Get recent uploads as proxy for report activity
        recent_uploads = DataUpload.query.filter_by(
            status=UploadStatus.COMPLETED
        ).order_by(
            DataUpload.uploaded_at.desc()
        ).limit(10).all()
        
        activity = []
        for upload in recent_uploads:
            activity.append({
                'type': 'data_upload',
                'facility': upload.facility_name,
                'period': upload.reporting_period,
                'date': upload.uploaded_at,
                'quality_score': upload.get_validation_summary().get('validation_rate', 0)
            })
        
        return activity
    
    except Exception as e:
        logger.error(f"Error getting recent report activity: {str(e)}")
        return []


def get_report_filters_data():
    """Get data for report filters"""
    try:
        # Get unique facilities
        facilities = db.session.query(DataUpload.facility_name).distinct().order_by(DataUpload.facility_name).all()
        
        # Get unique districts
        districts = db.session.query(DataUpload.district).filter(
            DataUpload.district.isnot(None)
        ).distinct().order_by(DataUpload.district).all()
        
        # Get unique periods
        periods = db.session.query(DataUpload.reporting_period).distinct().order_by(
            DataUpload.reporting_period.desc()
        ).all()
        
        return {
            'facilities': [f[0] for f in facilities],
            'districts': [d[0] for d in districts],
            'periods': [p[0] for p in periods]
        }
    
    except Exception as e:
        logger.error(f"Error getting report filters data: {str(e)}")
        return {'facilities': [], 'districts': [], 'periods': []}


def generate_report_data(report_type='comprehensive', facilities=None, districts=None, 
                        period_from=None, period_to=None, include_validation=True):
    """Generate comprehensive report data"""
    try:
        # Build query
        query = DataUpload.query.filter_by(status=UploadStatus.COMPLETED)
        
        if facilities:
            query = query.filter(DataUpload.facility_name.in_(facilities))
        
        if districts:
            query = query.filter(DataUpload.district.in_(districts))
        
        if period_from:
            query = query.filter(DataUpload.reporting_period >= period_from)
        
        if period_to:
            query = query.filter(DataUpload.reporting_period <= period_to)
        
        uploads = query.order_by(DataUpload.uploaded_at.desc()).all()
        
        if not uploads:
            return {'message': 'No data available for the selected criteria'}
        
        # Generate report sections based on type
        report_data = {
            'metadata': {
                'generated_at': datetime.utcnow(),
                'generated_by': current_user.username,
                'report_type': report_type,
                'total_uploads': len(uploads),
                'date_range': {
                    'from': min(upload.uploaded_at for upload in uploads),
                    'to': max(upload.uploaded_at for upload in uploads)
                }
            },
            'executive_summary': generate_executive_summary(uploads),
            'data_overview': generate_data_overview(uploads)
        }
        
        # Add category-specific data based on report type
        if report_type in ['comprehensive', 'anc']:
            report_data['anc_analysis'] = generate_category_report(uploads, 'anc')
        
        if report_type in ['comprehensive', 'intrapartum']:
            report_data['intrapartum_analysis'] = generate_category_report(uploads, 'intrapartum')
        
        if report_type in ['comprehensive', 'pnc']:
            report_data['pnc_analysis'] = generate_category_report(uploads, 'pnc')
        
        # Add validation data if requested
        if include_validation:
            report_data['data_quality'] = generate_validation_report(uploads)
        
        return report_data
    
    except Exception as e:
        logger.error(f"Error generating report data: {str(e)}")
        return {'error': str(e)}


def generate_executive_summary(uploads):
    """Generate executive summary for report"""
    try:
        # Calculate key metrics
        total_facilities = len(set(upload.facility_name for upload in uploads))
        total_indicators = sum(upload.total_indicators for upload in uploads)
        valid_indicators = sum(upload.valid_indicators for upload in uploads)
        
        overall_quality = (valid_indicators / total_indicators * 100) if total_indicators > 0 else 0
        
        # Categorize performance
        excellent_facilities = 0
        good_facilities = 0
        poor_facilities = 0
        
        facility_performance = {}
        for upload in uploads:
            facility = upload.facility_name
            if facility not in facility_performance:
                facility_performance[facility] = []
            
            summary = upload.get_validation_summary()
            facility_performance[facility].append(summary.get('validation_rate', 0))
        
        for facility, rates in facility_performance.items():
            avg_rate = sum(rates) / len(rates)
            if avg_rate >= 85:
                excellent_facilities += 1
            elif avg_rate >= 70:
                good_facilities += 1
            else:
                poor_facilities += 1
        
        return {
            'total_facilities': total_facilities,
            'overall_quality_rate': overall_quality,
            'performance_distribution': {
                'excellent': excellent_facilities,
                'good': good_facilities,
                'needs_improvement': poor_facilities
            },
            'key_findings': generate_key_findings(uploads),
            'recommendations': generate_recommendations(uploads)
        }
    
    except Exception as e:
        logger.error(f"Error generating executive summary: {str(e)}")
        return {}


def generate_data_overview(uploads):
    """Generate data overview section"""
    try:
        # Geographic distribution
        districts = {}
        for upload in uploads:
            if upload.district:
                districts[upload.district] = districts.get(upload.district, 0) + 1
        
        # Temporal distribution
        periods = {}
        for upload in uploads:
            period = upload.reporting_period
            periods[period] = periods.get(period, 0) + 1
        
        # Facility types (based on naming patterns)
        facility_types = {
            'National Referral': 0,
            'Regional Referral': 0,
            'District Hospital': 0,
            'Health Center': 0,
            'Other': 0
        }
        
        for upload in uploads:
            facility_name = upload.facility_name.lower()
            if 'national' in facility_name:
                facility_types['National Referral'] += 1
            elif 'regional' in facility_name:
                facility_types['Regional Referral'] += 1
            elif 'district' in facility_name:
                facility_types['District Hospital'] += 1
            elif 'health center' in facility_name or 'hc' in facility_name:
                facility_types['Health Center'] += 1
            else:
                facility_types['Other'] += 1
        
        return {
            'geographic_distribution': districts,
            'temporal_distribution': periods,
            'facility_types': facility_types,
            'data_completeness': calculate_data_completeness(uploads)
        }
    
    except Exception as e:
        logger.error(f"Error generating data overview: {str(e)}")
        return {}


def generate_category_report(uploads, category):
    """Generate report for a specific MNCAH category"""
    try:
        category_data = []
        
        for upload in uploads:
            if upload.processed_data and category in upload.processed_data:
                upload_category_data = {
                    'facility': upload.facility_name,
                    'district': upload.district,
                    'period': upload.reporting_period,
                    'indicators': upload.processed_data[category].get('indicators', {}),
                    'validations': upload.processed_data[category].get('validations', {})
                }
                category_data.append(upload_category_data)
        
        if not category_data:
            return {'message': f'No {category.upper()} data available'}
        
        # Calculate category statistics
        all_indicators = {}
        for data in category_data:
            for indicator, value in data['indicators'].items():
                if indicator not in all_indicators:
                    all_indicators[indicator] = []
                all_indicators[indicator].append(value)
        
        statistics = {}
        for indicator, values in all_indicators.items():
            statistics[indicator] = {
                'count': len(values),
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'median': sorted(values)[len(values)//2]
            }
        
        return {
            'category': category.upper(),
            'facilities_data': category_data,
            'statistics': statistics,
            'performance_analysis': analyze_category_performance(category_data)
        }
    
    except Exception as e:
        logger.error(f"Error generating {category} report: {str(e)}")
        return {}


def generate_data_quality_report(facility_filter=None, district_filter=None, period_filter=None):
    """Generate comprehensive data quality report"""
    try:
        validation_service = DataValidationService()
        
        # Build query with filters
        query = DataUpload.query.filter_by(status=UploadStatus.COMPLETED)
        
        if facility_filter:
            query = query.filter(DataUpload.facility_name.ilike(f'%{facility_filter}%'))
        
        if district_filter:
            query = query.filter(DataUpload.district.ilike(f'%{district_filter}%'))
        
        if period_filter:
            query = query.filter(DataUpload.reporting_period.ilike(f'%{period_filter}%'))
        
        uploads = query.all()
        
        if not uploads:
            return {'message': 'No data available for the selected filters'}
        
        # Generate validation reports for each upload
        validation_results = []
        for upload in uploads:
            if upload.processed_data:
                validation_report = validation_service.validate_upload_data(upload.processed_data)
                validation_report['facility'] = upload.facility_name
                validation_report['district'] = upload.district
                validation_report['period'] = upload.reporting_period
                validation_results.append(validation_report)
        
        # Generate dashboard data
        dashboard_data = validation_service.generate_validation_dashboard_data([
            upload.to_dict(include_data=True) for upload in uploads
        ])
        
        return {
            'validation_results': validation_results,
            'dashboard_data': dashboard_data,
            'summary': {
                'total_uploads': len(uploads),
                'uploads_analyzed': len(validation_results),
                'average_quality_score': sum(
                    upload.get_validation_summary().get('validation_rate', 0) 
                    for upload in uploads
                ) / len(uploads) if uploads else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating data quality report: {str(e)}")
        return {}


def generate_performance_summary():
    """Generate performance summary across all indicators"""
    try:
        calculation_service = MNCHACalculationService()
        
        # Get all completed uploads
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return {'message': 'No data available'}
        
        # Convert to format for calculation service
        facility_data = []
        for upload in uploads:
            facility_data.append(upload.to_dict(include_data=True))
        
        # Generate facility comparison
        if len(facility_data) >= 2:
            comparison_results = calculation_service.compare_facilities(facility_data)
        else:
            comparison_results = {'message': 'Need at least 2 facilities for comparison'}
        
        # Generate system-wide statistics
        system_stats = {
            'total_facilities': len(set(upload.facility_name for upload in uploads)),
            'total_indicators_analyzed': sum(upload.total_indicators for upload in uploads),
            'overall_performance': calculate_overall_performance(uploads),
            'category_performance': calculate_category_performance(uploads)
        }
        
        return {
            'system_statistics': system_stats,
            'facility_comparison': comparison_results,
            'performance_trends': calculate_performance_trends(uploads)
        }
    
    except Exception as e:
        logger.error(f"Error generating performance summary: {str(e)}")
        return {}


def generate_facility_report(facility_name):
    """Generate detailed report for a specific facility"""
    try:
        calculation_service = MNCHACalculationService()
        
        # Get all uploads for this facility
        uploads = DataUpload.query.filter_by(
            facility_name=facility_name,
            status=UploadStatus.COMPLETED
        ).order_by(DataUpload.uploaded_at.desc()).all()
        
        if not uploads:
            return {'message': f'No data available for facility: {facility_name}'}
        
        # Convert to format for trend analysis
        upload_dicts = [upload.to_dict(include_data=True) for upload in uploads]
        
        # Get trends analysis
        trends_data = calculation_service.get_indicator_trends(facility_name, upload_dicts)
        
        # Get latest performance
        latest_upload = uploads[0]
        latest_summary = latest_upload.get_validation_summary()
        
        return {
            'facility_name': facility_name,
            'district': latest_upload.district,
            'latest_period': latest_upload.reporting_period,
            'total_uploads': len(uploads),
            'latest_performance': latest_summary,
            'trends_analysis': trends_data,
            'historical_data': [upload.to_dict() for upload in uploads[:12]]  # Last 12 uploads
        }
    
    except Exception as e:
        logger.error(f"Error generating facility report for {facility_name}: {str(e)}")
        return {}


def create_excel_export(facilities=None, districts=None, categories=None):
    """Create Excel export file"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Build query
        query = DataUpload.query.filter_by(status=UploadStatus.COMPLETED)
        
        if facilities:
            query = query.filter(DataUpload.facility_name.in_(facilities))
        
        if districts:
            query = query.filter(DataUpload.district.in_(districts))
        
        uploads = query.all()
        
        if not uploads:
            raise ValueError("No data available for export")
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for upload in uploads:
                summary_data.append({
                    'Facility': upload.facility_name,
                    'District': upload.district,
                    'Period': upload.reporting_period,
                    'Population': upload.total_population,
                    'Upload Date': upload.uploaded_at,
                    'Validation Rate': upload.get_validation_summary().get('validation_rate', 0)
                })
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Category-specific sheets
            for category in categories or ['anc', 'intrapartum', 'pnc']:
                category_data = []
                
                for upload in uploads:
                    if upload.processed_data and category in upload.processed_data:
                        row_data = {
                            'Facility': upload.facility_name,
                            'District': upload.district,
                            'Period': upload.reporting_period
                        }
                        
                        indicators = upload.processed_data[category].get('indicators', {})
                        validations = upload.processed_data[category].get('validations', {})
                        
                        for indicator, value in indicators.items():
                            row_data[f'{indicator}_value'] = value
                            row_data[f'{indicator}_status'] = validations.get(indicator, 'unknown')
                        
                        category_data.append(row_data)
                
                if category_data:
                    pd.DataFrame(category_data).to_excel(
                        writer, sheet_name=category.upper(), index=False
                    )
        
        output.seek(0)
        return output
    
    except Exception as e:
        logger.error(f"Error creating Excel export: {str(e)}")
        raise


def create_pdf_export(report_type, facility=None):
    """Create PDF export file"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is required for PDF generation")
    
    try:
        from io import BytesIO
        
        output = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=30
        )
        
        story = []
        
        # Title
        story.append(Paragraph("MOH MNCAH Dashboard Report", title_style))
        story.append(Spacer(1, 20))
        
        # Report metadata
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(Paragraph(f"Generated by: {current_user.username}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Report content based on type
        if facility:
            facility_data = generate_facility_report(facility)
            story.extend(create_pdf_facility_content(facility_data, styles))
        else:
            # Summary report
            report_data = generate_report_data(report_type)
            story.extend(create_pdf_summary_content(report_data, styles))
        
        # Build PDF
        doc.build(story)
        output.seek(0)
        return output
    
    except Exception as e:
        logger.error(f"Error creating PDF export: {str(e)}")
        raise


def create_pdf_facility_content(facility_data, styles):
    """Create PDF content for facility report"""
    content = []
    
    content.append(Paragraph(f"Facility Report: {facility_data.get('facility_name', 'Unknown')}", styles['Heading2']))
    content.append(Spacer(1, 12))
    
    # Basic info
    if 'district' in facility_data:
        content.append(Paragraph(f"District: {facility_data['district']}", styles['Normal']))
    
    content.append(Paragraph(f"Total Uploads: {facility_data.get('total_uploads', 0)}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Performance summary
    latest_perf = facility_data.get('latest_performance', {})
    if latest_perf:
        content.append(Paragraph("Latest Performance Summary:", styles['Heading3']))
        content.append(Paragraph(f"Validation Rate: {latest_perf.get('validation_rate', 0):.1f}%", styles['Normal']))
        content.append(Paragraph(f"Total Indicators: {latest_perf.get('total_indicators', 0)}", styles['Normal']))
        content.append(Spacer(1, 12))
    
    return content


def create_pdf_summary_content(report_data, styles):
    """Create PDF content for summary report"""
    content = []
    
    content.append(Paragraph("Executive Summary", styles['Heading2']))
    content.append(Spacer(1, 12))
    
    # Executive summary
    exec_summary = report_data.get('executive_summary', {})
    if exec_summary:
        content.append(Paragraph(f"Total Facilities: {exec_summary.get('total_facilities', 0)}", styles['Normal']))
        content.append(Paragraph(f"Overall Quality Rate: {exec_summary.get('overall_quality_rate', 0):.1f}%", styles['Normal']))
        content.append(Spacer(1, 12))
        
        # Performance distribution
        perf_dist = exec_summary.get('performance_distribution', {})
        if perf_dist:
            content.append(Paragraph("Performance Distribution:", styles['Heading3']))
            content.append(Paragraph(f"Excellent: {perf_dist.get('excellent', 0)} facilities", styles['Normal']))
            content.append(Paragraph(f"Good: {perf_dist.get('good', 0)} facilities", styles['Normal']))
            content.append(Paragraph(f"Needs Improvement: {perf_dist.get('needs_improvement', 0)} facilities", styles['Normal']))
    
    return content


# Additional helper functions

def generate_key_findings(uploads):
    """Generate key findings from uploads data"""
    findings = []
    
    try:
        # Calculate overall metrics
        total_facilities = len(set(upload.facility_name for upload in uploads))
        
        # Quality analysis
        quality_rates = [upload.get_validation_summary().get('validation_rate', 0) for upload in uploads]
        avg_quality = sum(quality_rates) / len(quality_rates) if quality_rates else 0
        
        if avg_quality >= 85:
            findings.append("Overall data quality is excellent across participating facilities")
        elif avg_quality >= 70:
            findings.append("Data quality is generally good but has room for improvement")
        else:
            findings.append("Data quality issues identified that require immediate attention")
        
        # Geographic coverage
        districts = set(upload.district for upload in uploads if upload.district)
        findings.append(f"Data covers {len(districts)} districts across Uganda")
        
        # Temporal coverage
        periods = set(upload.reporting_period for upload in uploads)
        findings.append(f"Reporting spans {len(periods)} time periods")
        
        return findings
    
    except Exception as e:
        logger.error(f"Error generating key findings: {str(e)}")
        return []


def generate_recommendations(uploads):
    """Generate recommendations based on data analysis"""
    recommendations = []
    
    try:
        # Analyze common issues
        validation_issues = []
        for upload in uploads:
            if upload.processed_data:
                for category in ['anc', 'intrapartum', 'pnc']:
                    if category in upload.processed_data:
                        validations = upload.processed_data[category].get('validations', {})
                        for indicator, status in validations.items():
                            if status in ['red', 'blue']:
                                validation_issues.append((indicator, status))
        
        # Count most common issues
        issue_counts = {}
        for indicator, status in validation_issues:
            issue_counts[indicator] = issue_counts.get(indicator, 0) + 1
        
        # Generate recommendations based on common issues
        if issue_counts:
            most_problematic = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            for indicator, count in most_problematic:
                recommendations.append(f"Focus improvement efforts on {indicator} indicator (issues in {count} facilities)")
        
        # General recommendations
        quality_rates = [upload.get_validation_summary().get('validation_rate', 0) for upload in uploads]
        low_quality_facilities = sum(1 for rate in quality_rates if rate < 70)
        
        if low_quality_facilities > 0:
            recommendations.append(f"Provide targeted data quality training to {low_quality_facilities} facilities with quality rates below 70%")
        
        recommendations.append("Implement regular data quality monitoring and feedback mechanisms")
        recommendations.append("Establish peer learning networks between high and low performing facilities")
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return []


def calculate_data_completeness(uploads):
    """Calculate data completeness metrics"""
    try:
        completeness_data = {
            'total_expected_indicators': len(uploads) * 25,  # 25 MNCAH indicators per upload
            'total_actual_indicators': sum(upload.total_indicators for upload in uploads),
            'completeness_rate': 0
        }
        
        if completeness_data['total_expected_indicators'] > 0:
            completeness_data['completeness_rate'] = (
                completeness_data['total_actual_indicators'] / 
                completeness_data['total_expected_indicators'] * 100
            )
        
        return completeness_data
    
    except Exception as e:
        logger.error(f"Error calculating data completeness: {str(e)}")
        return {}


def analyze_category_performance(category_data):
    """Analyze performance for a category"""
    try:
        performance_analysis = {
            'total_facilities': len(category_data),
            'indicator_performance': {},
            'facility_rankings': []
        }
        
        # Analyze each indicator
        all_indicators = {}
        for facility_data in category_data:
            validations = facility_data.get('validations', {})
            for indicator, status in validations.items():
                if indicator not in all_indicators:
                    all_indicators[indicator] = {'green': 0, 'yellow': 0, 'red': 0, 'blue': 0}
                all_indicators[indicator][status] = all_indicators[indicator].get(status, 0) + 1
        
        performance_analysis['indicator_performance'] = all_indicators
        
        # Rank facilities by performance
        facility_scores = []
        for facility_data in category_data:
            validations = facility_data.get('validations', {})
            green_count = sum(1 for status in validations.values() if status == 'green')
            total_indicators = len(validations)
            score = (green_count / total_indicators * 100) if total_indicators > 0 else 0
            
            facility_scores.append({
                'facility': facility_data['facility'],
                'district': facility_data['district'],
                'score': score,
                'green_indicators': green_count,
                'total_indicators': total_indicators
            })
        
        # Sort by score
        facility_scores.sort(key=lambda x: x['score'], reverse=True)
        performance_analysis['facility_rankings'] = facility_scores
        
        return performance_analysis
    
    except Exception as e:
        logger.error(f"Error analyzing category performance: {str(e)}")
        return {}


def calculate_overall_performance(uploads):
    """Calculate overall system performance"""
    try:
        total_indicators = sum(upload.total_indicators for upload in uploads)
        valid_indicators = sum(upload.valid_indicators for upload in uploads)
        
        overall_rate = (valid_indicators / total_indicators * 100) if total_indicators > 0 else 0
        
        # Categorize performance
        if overall_rate >= 90:
            performance_level = "Excellent"
        elif overall_rate >= 75:
            performance_level = "Good"
        elif overall_rate >= 60:
            performance_level = "Acceptable"
        else:
            performance_level = "Needs Improvement"
        
        return {
            'overall_validation_rate': overall_rate,
            'performance_level': performance_level,
            'total_indicators_analyzed': total_indicators,
            'valid_indicators': valid_indicators
        }
    
    except Exception as e:
        logger.error(f"Error calculating overall performance: {str(e)}")
        return {}


def calculate_category_performance(uploads):
    """Calculate performance by MNCAH category"""
    try:
        category_performance = {}
        
        for category in ['anc', 'intrapartum', 'pnc']:
            category_indicators = 0
            category_valid = 0
            
            for upload in uploads:
                if upload.processed_data and category in upload.processed_data:
                    validations = upload.processed_data[category].get('validations', {})
                    category_indicators += len(validations)
                    category_valid += sum(1 for status in validations.values() if status == 'green')
            
            category_rate = (category_valid / category_indicators * 100) if category_indicators > 0 else 0
            
            category_performance[category] = {
                'validation_rate': category_rate,
                'total_indicators': category_indicators,
                'valid_indicators': category_valid
            }
        
        return category_performance
    
    except Exception as e:
        logger.error(f"Error calculating category performance: {str(e)}")
        return {}


def calculate_performance_trends(uploads):
    """Calculate performance trends over time"""
    try:
        # Group uploads by period
        period_performance = {}
        
        for upload in uploads:
            period = upload.reporting_period
            if period not in period_performance:
                period_performance[period] = []
            
            summary = upload.get_validation_summary()
            period_performance[period].append(summary.get('validation_rate', 0))
        
        # Calculate average for each period
        trends = {}
        for period, rates in period_performance.items():
            trends[period] = {
                'average_rate': sum(rates) / len(rates),
                'facility_count': len(rates),
                'min_rate': min(rates),
                'max_rate': max(rates)
            }
        
        return trends
    
    except Exception as e:
        logger.error(f"Error calculating performance trends: {str(e)}")
        return {}


def generate_api_report_data(report_type, facilities):
    """Generate report data for API endpoints"""
    try:
        # This is a simplified version for API consumption
        query = DataUpload.query.filter_by(status=UploadStatus.COMPLETED)
        
        if facilities:
            query = query.filter(DataUpload.facility_name.in_(facilities))
        
        uploads = query.limit(100).all()  # Limit for API performance
        
        api_data = {
            'report_type': report_type,
            'total_uploads': len(uploads),
            'facilities': [upload.facility_name for upload in uploads],
            'summary_statistics': calculate_overall_performance(uploads)
        }
        
        return api_data
    
    except Exception as e:
        logger.error(f"Error generating API report data: {str(e)}")
        return {'error': str(e)}


def get_system_validation_summary():
    """Get system-wide validation summary"""
    try:
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return {'message': 'No data available'}
        
        total_indicators = sum(upload.total_indicators for upload in uploads)
        valid_indicators = sum(upload.valid_indicators for upload in uploads)
        warning_indicators = sum(upload.warning_indicators for upload in uploads)
        error_indicators = sum(upload.error_indicators for upload in uploads)
        
        return {
            'total_uploads': len(uploads),
            'total_indicators': total_indicators,
            'valid_indicators': valid_indicators,
            'warning_indicators': warning_indicators,
            'error_indicators': error_indicators,
            'overall_validation_rate': (valid_indicators / total_indicators * 100) if total_indicators > 0 else 0,
            'facilities_covered': len(set(upload.facility_name for upload in uploads)),
            'districts_covered': len(set(upload.district for upload in uploads if upload.district))
        }
    
    except Exception as e:
        logger.error(f"Error getting system validation summary: {str(e)}")
        return {'error': str(e)}


def generate_validation_report(uploads):
    """Generate validation report section"""
    try:
        validation_service = DataValidationService()
        
        validation_data = {
            'overall_summary': get_system_validation_summary(),
            'category_validation': {},
            'common_issues': [],
            'quality_distribution': {
                'excellent': 0,
                'good': 0,
                'needs_improvement': 0,
                'poor': 0
            }
        }
        
        # Category-specific validation
        for category in ['anc', 'intrapartum', 'pnc']:
            category_validation = {
                'total_indicators': 0,
                'valid_indicators': 0,
                'validation_rate': 0,
                'common_issues': []
            }
            
            category_issues = []
            for upload in uploads:
                if upload.processed_data and category in upload.processed_data:
                    validations = upload.processed_data[category].get('validations', {})
                    category_validation['total_indicators'] += len(validations)
                    category_validation['valid_indicators'] += sum(
                        1 for status in validations.values() if status == 'green'
                    )
                    
                    # Collect issues
                    for indicator, status in validations.items():
                        if status in ['red', 'blue']:
                            category_issues.append(indicator)
            
            # Calculate validation rate
            if category_validation['total_indicators'] > 0:
                category_validation['validation_rate'] = (
                    category_validation['valid_indicators'] / 
                    category_validation['total_indicators'] * 100
                )
            
            # Find common issues
            issue_counts = {}
            for issue in category_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            category_validation['common_issues'] = sorted(
                issue_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
            
            validation_data['category_validation'][category] = category_validation
        
        # Quality distribution
        for upload in uploads:
            summary = upload.get_validation_summary()
            rate = summary.get('validation_rate', 0)
            
            if rate >= 90:
                validation_data['quality_distribution']['excellent'] += 1
            elif rate >= 75:
                validation_data['quality_distribution']['good'] += 1
            elif rate >= 60:
                validation_data['quality_distribution']['needs_improvement'] += 1
            else:
                validation_data['quality_distribution']['poor'] += 1
        
        return validation_data
    
    except Exception as e:
        logger.error(f"Error generating validation report: {str(e)}")
        return {}


def generate_pdf_report(report_data, include_charts):
    """Generate PDF report with ReportLab"""
    try:
        pdf_file = create_pdf_export('comprehensive')
        
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f'MNCAH_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return jsonify({'success': False, 'message': 'Error generating PDF report'}), 500


def generate_excel_report(report_data):
    """Generate Excel report with data"""
    try:
        excel_file = create_excel_export()
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f'MNCAH_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        return jsonify({'success': False, 'message': 'Error generating Excel report'}), 500
