"""
Analysis Views
This module handles the analysis interface for viewing MNCAH indicators,
trends, and detailed breakdowns.
"""

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import logging

from ..models.upload import DataUpload, UploadStatus
from ..services.calculation_service import MNCHACalculationService
from ..services.validation_service import DataValidationService
from .. import db


# Create analysis blueprint
analysis_bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)


@analysis_bp.route('/')
@login_required
def index():
    """
    Main analysis page showing all categories
    """
    try:
        # Get filter parameters
        facility_filter = request.args.get('facility')
        district_filter = request.args.get('district')
        period_filter = request.args.get('period')
        
        # Get analysis data
        analysis_data = get_analysis_overview(facility_filter, district_filter, period_filter)
        
        # Get filters data
        filters_data = get_filters_data()
        
        return render_template('analysis/index.html',
                             analysis_data=analysis_data,
                             filters_data=filters_data,
                             current_filters={
                                 'facility': facility_filter,
                                 'district': district_filter,
                                 'period': period_filter
                             })
    
    except Exception as e:
        logger.error(f"Error loading analysis page: {str(e)}")
        return render_template('analysis/index.html',
                             analysis_data={},
                             filters_data={},
                             current_filters={},
                             error="Error loading analysis data")


@analysis_bp.route('/anc')
@login_required
def anc_analysis():
    """
    Antenatal Care indicators analysis
    """
    try:
        # Get filter parameters
        facility_filter = request.args.get('facility')
        district_filter = request.args.get('district')
        period_filter = request.args.get('period')
        
        # Get ANC-specific data
        anc_data = get_category_analysis('anc', facility_filter, district_filter, period_filter)
        
        # Get filters data
        filters_data = get_filters_data()
        
        return render_template('analysis/anc.html',
                             anc_data=anc_data,
                             filters_data=filters_data,
                             current_filters={
                                 'facility': facility_filter,
                                 'district': district_filter,
                                 'period': period_filter
                             })
    
    except Exception as e:
        logger.error(f"Error loading ANC analysis: {str(e)}")
        return render_template('analysis/anc.html',
                             anc_data={},
                             filters_data={},
                             current_filters={},
                             error="Error loading ANC analysis")


@analysis_bp.route('/intrapartum')
@login_required
def intrapartum_analysis():
    """
    Intrapartum care indicators analysis
    """
    try:
        # Get filter parameters
        facility_filter = request.args.get('facility')
        district_filter = request.args.get('district')
        period_filter = request.args.get('period')
        
        # Get Intrapartum-specific data
        intrapartum_data = get_category_analysis('intrapartum', facility_filter, district_filter, period_filter)
        
        # Get filters data
        filters_data = get_filters_data()
        
        return render_template('analysis/intrapartum.html',
                             intrapartum_data=intrapartum_data,
                             filters_data=filters_data,
                             current_filters={
                                 'facility': facility_filter,
                                 'district': district_filter,
                                 'period': period_filter
                             })
    
    except Exception as e:
        logger.error(f"Error loading Intrapartum analysis: {str(e)}")
        return render_template('analysis/intrapartum.html',
                             intrapartum_data={},
                             filters_data={},
                             current_filters={},
                             error="Error loading Intrapartum analysis")


@analysis_bp.route('/pnc')
@login_required
def pnc_analysis():
    """
    Postnatal Care indicators analysis
    """
    try:
        # Get filter parameters
        facility_filter = request.args.get('facility')
        district_filter = request.args.get('district')
        period_filter = request.args.get('period')
        
        # Get PNC-specific data
        pnc_data = get_category_analysis('pnc', facility_filter, district_filter, period_filter)
        
        # Get filters data
        filters_data = get_filters_data()
        
        return render_template('analysis/pnc.html',
                             pnc_data=pnc_data,
                             filters_data=filters_data,
                             current_filters={
                                 'facility': facility_filter,
                                 'district': district_filter,
                                 'period': period_filter
                             })
    
    except Exception as e:
        logger.error(f"Error loading PNC analysis: {str(e)}")
        return render_template('analysis/pnc.html',
                             pnc_data={},
                             filters_data={},
                             current_filters={},
                             error="Error loading PNC analysis")


@analysis_bp.route('/trends')
@login_required
def trends_analysis():
    """
    Trends analysis across time periods
    """
    try:
        facility_name = request.args.get('facility')
        indicator = request.args.get('indicator')
        
        # Get trends data
        trends_data = get_trends_analysis(facility_name, indicator)
        
        # Get available facilities and indicators for filters
        facilities = get_available_facilities()
        indicators = get_available_indicators()
        
        return render_template('analysis/trends.html',
                             trends_data=trends_data,
                             facilities=facilities,
                             indicators=indicators,
                             current_facility=facility_name,
                             current_indicator=indicator)
    
    except Exception as e:
        logger.error(f"Error loading trends analysis: {str(e)}")
        return render_template('analysis/trends.html',
                             trends_data={},
                             facilities=[],
                             indicators=[],
                             error="Error loading trends analysis")


@analysis_bp.route('/upload/<int:upload_id>')
@login_required
def view_upload(upload_id):
    """
    View detailed analysis for a specific upload
    """
    try:
        upload = DataUpload.query.get_or_404(upload_id)
        
        # Get detailed analysis
        detailed_analysis = get_upload_detailed_analysis(upload)
        
        return render_template('analysis/upload_detail.html',
                             upload=upload,
                             analysis=detailed_analysis)
    
    except Exception as e:
        logger.error(f"Error viewing upload {upload_id}: {str(e)}")
        abort(404)


@analysis_bp.route('/indicator/<string:indicator_name>')
@login_required
def indicator_detail(indicator_name):
    """
    Detailed view of a specific indicator across facilities
    """
    try:
        # Get indicator definition and data
        indicator_data = get_indicator_detailed_analysis(indicator_name)
        
        return render_template('analysis/indicator_detail.html',
                             indicator_name=indicator_name,
                             indicator_data=indicator_data)
    
    except Exception as e:
        logger.error(f"Error loading indicator detail for {indicator_name}: {str(e)}")
        return render_template('analysis/indicator_detail.html',
                             indicator_name=indicator_name,
                             indicator_data={},
                             error="Error loading indicator details")


@analysis_bp.route('/compare')
@login_required
def facility_comparison():
    """
    Compare multiple facilities
    """
    try:
        selected_facilities = request.args.getlist('facilities')
        
        if not selected_facilities:
            # Show facility selection page
            available_facilities = get_available_facilities()
            return render_template('analysis/facility_selection.html',
                                 facilities=available_facilities)
        
        # Get comparison data
        comparison_data = get_facility_comparison_data(selected_facilities)
        
        return render_template('analysis/facility_comparison.html',
                             comparison_data=comparison_data,
                             selected_facilities=selected_facilities)
    
    except Exception as e:
        logger.error(f"Error loading facility comparison: {str(e)}")
        return render_template('analysis/facility_comparison.html',
                             comparison_data={},
                             selected_facilities=[],
                             error="Error loading comparison data")


# API Endpoints for AJAX requests

@analysis_bp.route('/api/category/<string:category>')
@login_required
def api_category_data(category):
    """
    API endpoint for category-specific data
    """
    try:
        facility_filter = request.args.get('facility')
        district_filter = request.args.get('district')
        period_filter = request.args.get('period')
        
        data = get_category_analysis(category, facility_filter, district_filter, period_filter)
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Error getting category data for {category}: {str(e)}")
        return jsonify({'error': 'Error retrieving data'}), 500


@analysis_bp.route('/api/trends/<string:facility_name>')
@login_required
def api_facility_trends(facility_name):
    """
    API endpoint for facility trends
    """
    try:
        indicator = request.args.get('indicator')
        trends_data = get_trends_analysis(facility_name, indicator)
        return jsonify(trends_data)
    
    except Exception as e:
        logger.error(f"Error getting trends for {facility_name}: {str(e)}")
        return jsonify({'error': 'Error retrieving trends'}), 500


@analysis_bp.route('/api/indicator/<string:indicator_name>/data')
@login_required
def api_indicator_data(indicator_name):
    """
    API endpoint for indicator-specific data
    """
    try:
        data = get_indicator_detailed_analysis(indicator_name)
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Error getting indicator data for {indicator_name}: {str(e)}")
        return jsonify({'error': 'Error retrieving indicator data'}), 500


# Helper functions

def get_analysis_overview(facility_filter=None, district_filter=None, period_filter=None):
    """Get overview analysis data with filters"""
    try:
        # Build query with filters
        query = DataUpload.query.filter_by(status=UploadStatus.COMPLETED)
        
        if facility_filter:
            query = query.filter(DataUpload.facility_name.ilike(f'%{facility_filter}%'))
        
        if district_filter:
            query = query.filter(DataUpload.district.ilike(f'%{district_filter}%'))
        
        if period_filter:
            query = query.filter(DataUpload.reporting_period.ilike(f'%{period_filter}%'))
        
        uploads = query.order_by(desc(DataUpload.uploaded_at)).all()
        
        if not uploads:
            return {'message': 'No data available for the selected filters'}
        
        # Process uploads into analysis format
        analysis_data = {
            'total_uploads': len(uploads),
            'categories': {
                'anc': process_category_data(uploads, 'anc'),
                'intrapartum': process_category_data(uploads, 'intrapartum'),
                'pnc': process_category_data(uploads, 'pnc')
            },
            'summary_stats': calculate_summary_stats(uploads),
            'recent_uploads': [upload.to_dict() for upload in uploads[:10]]
        }
        
        return analysis_data
    
    except Exception as e:
        logger.error(f"Error getting analysis overview: {str(e)}")
        return {}


def get_category_analysis(category, facility_filter=None, district_filter=None, period_filter=None):
    """Get analysis data for a specific category"""
    try:
        # Build query
        query = DataUpload.query.filter_by(status=UploadStatus.COMPLETED)
        
        if facility_filter:
            query = query.filter(DataUpload.facility_name.ilike(f'%{facility_filter}%'))
        
        if district_filter:
            query = query.filter(DataUpload.district.ilike(f'%{district_filter}%'))
        
        if period_filter:
            query = query.filter(DataUpload.reporting_period.ilike(f'%{period_filter}%'))
        
        uploads = query.order_by(desc(DataUpload.uploaded_at)).all()
        
        if not uploads:
            return {'message': 'No data available for the selected filters'}
        
        # Process category-specific data
        category_data = {
            'uploads': process_category_data(uploads, category),
            'indicators_summary': get_category_indicators_summary(uploads, category),
            'performance_analysis': get_category_performance_analysis(uploads, category),
            'validation_summary': get_category_validation_summary(uploads, category)
        }
        
        return category_data
    
    except Exception as e:
        logger.error(f"Error getting category analysis for {category}: {str(e)}")
        return {}


def get_trends_analysis(facility_name=None, indicator=None):
    """Get trends analysis data"""
    try:
        calculation_service = MNCHACalculationService()
        
        # Get uploads for trends
        query = DataUpload.query.filter_by(status=UploadStatus.COMPLETED)
        
        if facility_name:
            query = query.filter_by(facility_name=facility_name)
        
        uploads = query.order_by(DataUpload.uploaded_at).all()
        
        if len(uploads) < 2:
            return {'message': 'Need at least 2 data points for trend analysis'}
        
        # Convert to format expected by calculation service
        upload_dicts = [upload.to_dict(include_data=True) for upload in uploads]
        
        if facility_name:
            trends_data = calculation_service.get_indicator_trends(facility_name, upload_dicts)
        else:
            # System-wide trends
            trends_data = calculate_system_trends(upload_dicts)
        
        return trends_data
    
    except Exception as e:
        logger.error(f"Error getting trends analysis: {str(e)}")
        return {}


def get_upload_detailed_analysis(upload):
    """Get detailed analysis for a specific upload"""
    try:
        if not upload.processed_data:
            return {'message': 'Upload has not been processed yet'}
        
        # Get validation results
        validation_service = DataValidationService()
        validation_report = validation_service.validate_upload_data(upload.processed_data)
        
        # Prepare detailed analysis
        analysis = {
            'basic_info': {
                'facility_name': upload.facility_name,
                'district': upload.district,
                'reporting_period': upload.reporting_period,
                'population': upload.total_population,
                'adjusted_population': upload.adjusted_population,
                'expected_pregnancies': upload.expected_pregnancies,
                'expected_deliveries': upload.expected_deliveries
            },
            'indicators': upload.processed_data,
            'validation': validation_report,
            'summary': upload.get_validation_summary()
        }
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error getting detailed analysis for upload {upload.id}: {str(e)}")
        return {}


def get_indicator_detailed_analysis(indicator_name):
    """Get detailed analysis for a specific indicator"""
    try:
        # Get all uploads with this indicator
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return {'message': 'No data available'}
        
        # Extract indicator values across facilities
        indicator_data = []
        
        for upload in uploads:
            if upload.processed_data:
                # Search for indicator in all categories
                for category in ['anc', 'intrapartum', 'pnc']:
                    if category in upload.processed_data:
                        indicators = upload.processed_data[category].get('indicators', {})
                        if indicator_name in indicators:
                            indicator_data.append({
                                'facility_name': upload.facility_name,
                                'district': upload.district,
                                'reporting_period': upload.reporting_period,
                                'value': indicators[indicator_name],
                                'validation': upload.processed_data[category].get('validations', {}).get(indicator_name),
                                'upload_date': upload.uploaded_at
                            })
        
        if not indicator_data:
            return {'message': f'No data found for indicator: {indicator_name}'}
        
        # Calculate statistics
        values = [item['value'] for item in indicator_data]
        
        analysis = {
            'indicator_name': indicator_name,
            'data_points': indicator_data,
            'statistics': {
                'count': len(values),
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'range': max(values) - min(values)
            },
            'performance_distribution': {
                'green': sum(1 for item in indicator_data if item['validation'] == 'green'),
                'yellow': sum(1 for item in indicator_data if item['validation'] == 'yellow'),
                'red': sum(1 for item in indicator_data if item['validation'] == 'red'),
                'blue': sum(1 for item in indicator_data if item['validation'] == 'blue')
            }
        }
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error getting indicator analysis for {indicator_name}: {str(e)}")
        return {}


def get_facility_comparison_data(facility_names):
    """Get comparison data for multiple facilities"""
    try:
        calculation_service = MNCHACalculationService()
        
        # Get latest upload for each facility
        facility_data = []
        
        for facility_name in facility_names:
            latest_upload = DataUpload.query.filter_by(
                facility_name=facility_name,
                status=UploadStatus.COMPLETED
            ).order_by(desc(DataUpload.uploaded_at)).first()
            
            if latest_upload:
                facility_data.append(latest_upload.to_dict(include_data=True))
        
        if len(facility_data) < 2:
            return {'message': 'Need at least 2 facilities for comparison'}
        
        # Use calculation service for comparison
        comparison_results = calculation_service.compare_facilities(facility_data)
        
        return comparison_results
    
    except Exception as e:
        logger.error(f"Error getting facility comparison: {str(e)}")
        return {}


def get_filters_data():
    """Get data for filter dropdowns"""
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
        logger.error(f"Error getting filters data: {str(e)}")
        return {'facilities': [], 'districts': [], 'periods': []}


def get_available_facilities():
    """Get list of available facilities"""
    try:
        facilities = db.session.query(DataUpload.facility_name).distinct().order_by(DataUpload.facility_name).all()
        return [f[0] for f in facilities]
    
    except Exception as e:
        logger.error(f"Error getting available facilities: {str(e)}")
        return []


def get_available_indicators():
    """Get list of available indicators"""
    # This would normally come from the models, but for simplicity, we'll hardcode
    return [
        # ANC indicators
        'anc_1_coverage', 'anc_1st_trimester', 'anc_4_coverage', 'anc_8_coverage',
        'ipt3_coverage', 'hb_testing_coverage', 'iron_folic_anc1', 'llin_coverage', 'ultrasound_coverage',
        
        # Intrapartum indicators
        'institutional_deliveries', 'lbw_proportion', 'lbw_kmc_proportion', 'birth_asphyxia_proportion',
        'successful_resuscitation_proportion', 'fresh_stillbirths_rate', 'neonatal_mortality_rate',
        'perinatal_mortality_rate', 'maternal_mortality_ratio',
        
        # PNC indicators
        'breastfeeding_1hour', 'pnc_24hours', 'pnc_6days', 'pnc_6weeks'
    ]


def process_category_data(uploads, category):
    """Process uploads data for a specific category"""
    category_uploads = []
    
    for upload in uploads:
        if upload.processed_data and category in upload.processed_data:
            upload_data = upload.to_dict()
            upload_data['category_data'] = upload.processed_data[category]
            category_uploads.append(upload_data)
    
    return category_uploads


def calculate_summary_stats(uploads):
    """Calculate summary statistics for uploads"""
    if not uploads:
        return {}
    
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
        'validation_rate': (valid_indicators / total_indicators * 100) if total_indicators > 0 else 0
    }


def get_category_indicators_summary(uploads, category):
    """Get summary of indicators for a category"""
    indicators_data = {}
    
    for upload in uploads:
        if upload.processed_data and category in upload.processed_data:
            category_data = upload.processed_data[category]
            indicators = category_data.get('indicators', {})
            
            for indicator, value in indicators.items():
                if indicator not in indicators_data:
                    indicators_data[indicator] = []
                indicators_data[indicator].append(value)
    
    # Calculate statistics for each indicator
    summary = {}
    for indicator, values in indicators_data.items():
        if values:
            summary[indicator] = {
                'count': len(values),
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
    
    return summary


def get_category_performance_analysis(uploads, category):
    """Get performance analysis for a category"""
    performance_data = {
        'excellent': 0,
        'good': 0,
        'needs_improvement': 0,
        'critical': 0
    }
    
    for upload in uploads:
        summary = upload.get_validation_summary()
        validation_rate = summary.get('validation_rate', 0)
        
        if validation_rate >= 90:
            performance_data['excellent'] += 1
        elif validation_rate >= 75:
            performance_data['good'] += 1
        elif validation_rate >= 60:
            performance_data['needs_improvement'] += 1
        else:
            performance_data['critical'] += 1
    
    return performance_data


def get_category_validation_summary(uploads, category):
    """Get validation summary for a category"""
    validation_counts = {
        'green': 0,
        'yellow': 0,
        'red': 0,
        'blue': 0
    }
    
    for upload in uploads:
        if upload.processed_data and category in upload.processed_data:
            validations = upload.processed_data[category].get('validations', {})
            for status in validations.values():
                if status in validation_counts:
                    validation_counts[status] += 1
    
    return validation_counts


def calculate_system_trends(upload_dicts):
    """Calculate system-wide trends"""
    # Group uploads by period
    period_data = {}
    
    for upload in upload_dicts:
        period = upload.get('reporting_period', 'Unknown')
        if period not in period_data:
            period_data[period] = []
        period_data[period].append(upload)
    
    # Calculate trends
    trends = {}
    for period, uploads in period_data.items():
        # Calculate average validation rate for the period
        total_rate = sum(
            upload.get('validation_summary', {}).get('validation_rate', 0) 
            for upload in uploads
        )
        avg_rate = total_rate / len(uploads) if uploads else 0
        
        trends[period] = {
            'validation_rate': avg_rate,
            'upload_count': len(uploads),
            'facilities': len(set(upload.get('facility_name') for upload in uploads))
        }
    
    return {
        'system_trends': trends,
        'total_periods': len(trends)
    }
