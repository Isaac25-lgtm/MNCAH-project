"""
Dashboard Views
This module handles the main dashboard interface for the MOH MNCAH Dashboard System.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import logging

from ..models.upload import DataUpload, UploadStatus
from ..models.user import User, UserType
from ..services.calculation_service import MNCHACalculationService
from ..services.validation_service import DataValidationService
from .. import db


# Create dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)


@dashboard_bp.route('/')
@login_required
def index():
    """
    Main dashboard view showing overview statistics and recent activity
    """
    try:
        # Get dashboard statistics
        stats = get_dashboard_statistics()
        
        # Get recent uploads
        recent_uploads = get_recent_uploads(limit=10)
        
        # Get validation summary
        validation_summary = get_validation_summary()
        
        # Get facilities summary
        facilities_summary = get_facilities_summary()
        
        return render_template('dashboard/index.html',
                             stats=stats,
                             recent_uploads=recent_uploads,
                             validation_summary=validation_summary,
                             facilities_summary=facilities_summary,
                             user_type=current_user.user_type.value)
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        return render_template('dashboard/index.html',
                             stats={},
                             recent_uploads=[],
                             validation_summary={},
                             facilities_summary={},
                             error="Error loading dashboard data")


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """
    API endpoint to get dashboard statistics
    """
    try:
        stats = get_dashboard_statistics()
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'error': 'Error retrieving statistics'}), 500


@dashboard_bp.route('/api/recent-uploads')
@login_required
def api_recent_uploads():
    """
    API endpoint to get recent uploads
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        uploads = get_recent_uploads(limit=limit)
        
        return jsonify({
            'uploads': [upload.to_dict() for upload in uploads],
            'total': len(uploads)
        })
    
    except Exception as e:
        logger.error(f"Error getting recent uploads: {str(e)}")
        return jsonify({'error': 'Error retrieving recent uploads'}), 500


@dashboard_bp.route('/api/validation-summary')
@login_required
def api_validation_summary():
    """
    API endpoint to get validation summary
    """
    try:
        summary = get_validation_summary()
        return jsonify(summary)
    
    except Exception as e:
        logger.error(f"Error getting validation summary: {str(e)}")
        return jsonify({'error': 'Error retrieving validation summary'}), 500


@dashboard_bp.route('/overview')
@login_required
def overview():
    """
    Detailed overview page with comprehensive statistics
    """
    try:
        # Get comprehensive statistics
        stats = get_comprehensive_statistics()
        
        # Get performance trends
        trends = get_performance_trends()
        
        # Get facility comparison
        facility_comparison = get_facility_comparison()
        
        return render_template('dashboard/overview.html',
                             stats=stats,
                             trends=trends,
                             facility_comparison=facility_comparison)
    
    except Exception as e:
        logger.error(f"Error loading overview: {str(e)}")
        return render_template('dashboard/overview.html',
                             stats={},
                             trends={},
                             facility_comparison={},
                             error="Error loading overview data")


@dashboard_bp.route('/facilities')
@login_required
def facilities():
    """
    Facilities performance view
    """
    try:
        # Get all facilities with their latest data
        facilities_data = get_all_facilities_data()
        
        # Get facility performance comparison
        performance_comparison = get_facilities_performance_comparison()
        
        return render_template('dashboard/facilities.html',
                             facilities_data=facilities_data,
                             performance_comparison=performance_comparison)
    
    except Exception as e:
        logger.error(f"Error loading facilities data: {str(e)}")
        return render_template('dashboard/facilities.html',
                             facilities_data=[],
                             performance_comparison={},
                             error="Error loading facilities data")


@dashboard_bp.route('/api/facilities-performance')
@login_required
def api_facilities_performance():
    """
    API endpoint for facilities performance data
    """
    try:
        performance_data = get_facilities_performance_comparison()
        return jsonify(performance_data)
    
    except Exception as e:
        logger.error(f"Error getting facilities performance: {str(e)}")
        return jsonify({'error': 'Error retrieving facilities performance'}), 500


@dashboard_bp.route('/search')
@login_required
def search():
    """
    Search functionality for dashboard data
    """
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')
    
    if not query:
        return jsonify({'results': [], 'message': 'No search query provided'})
    
    try:
        results = perform_search(query, category)
        return jsonify({
            'results': results,
            'query': query,
            'category': category,
            'total': len(results)
        })
    
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        return jsonify({'error': 'Error performing search'}), 500


def get_dashboard_statistics():
    """Get basic dashboard statistics"""
    try:
        stats = {
            'total_uploads': db.session.query(DataUpload).count(),
            'total_facilities': db.session.query(DataUpload.facility_name).distinct().count(),
            'total_users': db.session.query(User).count(),
            'active_users': db.session.query(User).filter_by(status='active').count(),
            'completed_uploads': db.session.query(DataUpload).filter_by(status=UploadStatus.COMPLETED).count(),
            'pending_uploads': db.session.query(DataUpload).filter_by(status=UploadStatus.PENDING).count(),
            'failed_uploads': db.session.query(DataUpload).filter_by(status=UploadStatus.FAILED).count(),
        }

        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        stats['recent_uploads'] = db.session.query(DataUpload).filter(
            DataUpload.uploaded_at >= thirty_days_ago
        ).count()

        # Calculate upload success rate
        stats['success_rate'] = (
            (stats['completed_uploads'] / stats['total_uploads']) * 100
            if stats['total_uploads'] > 0 else 0
        )

        return stats
    except Exception as e:
        logger.error(f"Error calculating dashboard statistics: {str(e)}")
        return {}


def get_recent_uploads(limit=10):
    """Get recent data uploads"""
    try:
        uploads = db.session.query(DataUpload).order_by(
            desc(DataUpload.uploaded_at)
        ).limit(limit).all()
        return uploads
    except Exception as e:
        logger.error(f"Error getting recent uploads: {str(e)}")
        return []


def get_validation_summary():
    """Get validation summary across all uploads"""
    try:
        # Get completed uploads with validation data
        uploads = db.session.query(DataUpload).filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return {
                'total_indicators': 0,
                'valid_indicators': 0,
                'warning_indicators': 0,
                'error_indicators': 0,
                'validation_rate': 0
            }
        
        total_indicators = sum(upload.total_indicators for upload in uploads)
        valid_indicators = sum(upload.valid_indicators for upload in uploads)
        warning_indicators = sum(upload.warning_indicators for upload in uploads)
        error_indicators = sum(upload.error_indicators for upload in uploads)
        
        validation_rate = (valid_indicators / total_indicators * 100) if total_indicators > 0 else 0
        
        return {
            'total_indicators': total_indicators,
            'valid_indicators': valid_indicators,
            'warning_indicators': warning_indicators,
            'error_indicators': error_indicators,
            'validation_rate': validation_rate,
            'uploads_analyzed': len(uploads)
        }
    
    except Exception as e:
        logger.error(f"Error getting validation summary: {str(e)}")
        return {}


def get_facilities_summary():
    """Get summary of facilities and their performance"""
    try:
        # Get unique facilities with their latest upload
        facilities_query = db.session.query(
            DataUpload.facility_name,
            DataUpload.district,
            func.max(DataUpload.uploaded_at).label('latest_upload'),
            func.count(DataUpload.id).label('total_uploads')
        ).filter_by(status=UploadStatus.COMPLETED).group_by(
            DataUpload.facility_name, DataUpload.district
        ).all()

        facilities_data = []
        for facility in facilities_query:
            # Get latest upload data for this facility
            latest_upload = db.session.query(DataUpload).filter_by(
                facility_name=facility.facility_name,
                status=UploadStatus.COMPLETED
            ).order_by(desc(DataUpload.uploaded_at)).first()

            if latest_upload:
                validation_summary = latest_upload.get_validation_summary()
                facilities_data.append({
                    'name': facility.facility_name,
                    'district': facility.district,
                    'latest_upload': facility.latest_upload,
                    'total_uploads': facility.total_uploads,
                    'validation_rate': validation_summary.get('validation_rate', 0),
                    'has_critical_issues': validation_summary.get('has_critical_issues', False)
                })

        return {
            'total_facilities': len(facilities_data),
            'facilities': sorted(facilities_data, key=lambda x: x['latest_upload'], reverse=True)[:10]
        }
    except Exception as e:
        logger.error(f"Error getting facilities summary: {str(e)}")
        return {}


def get_comprehensive_statistics():
    """Get comprehensive statistics for overview page"""
    try:
        stats = get_dashboard_statistics()
        
        # Add more detailed statistics
        uploads_by_period = db.session.query(
            DataUpload.period_type,
            func.count(DataUpload.id)
        ).group_by(DataUpload.period_type).all()
        
        stats['uploads_by_period'] = {period.value: count for period, count in uploads_by_period}
        
        # Districts statistics
        districts = db.session.query(
            DataUpload.district,
            func.count(DataUpload.id)
        ).filter(DataUpload.district.isnot(None)).group_by(DataUpload.district).all()
        
        stats['districts'] = len(districts)
        stats['uploads_by_district'] = dict(districts)
        
        # Monthly upload trends (last 12 months)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        monthly_uploads = db.session.query(
            func.strftime('%Y-%m', DataUpload.uploaded_at).label('month'),
            func.count(DataUpload.id)
        ).filter(DataUpload.uploaded_at >= twelve_months_ago).group_by(
            func.strftime('%Y-%m', DataUpload.uploaded_at)
        ).all()
        
        stats['monthly_trends'] = dict(monthly_uploads)
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting comprehensive statistics: {str(e)}")
        return get_dashboard_statistics()


def get_performance_trends():
    """Get performance trends over time"""
    try:
        calculation_service = MNCHACalculationService()
        
        # Get uploads from last 6 months for trend analysis
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        uploads = DataUpload.query.filter(
            DataUpload.uploaded_at >= six_months_ago,
            DataUpload.status == UploadStatus.COMPLETED
        ).order_by(DataUpload.uploaded_at).all()
        
        if len(uploads) < 2:
            return {'message': 'Insufficient data for trend analysis'}
        
        # Group uploads by month
        monthly_data = {}
        for upload in uploads:
            month_key = upload.uploaded_at.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(upload.to_dict(include_data=True))
        
        trends_data = {}
        for month, month_uploads in monthly_data.items():
            # Calculate average validation rates for the month
            total_validation_rate = sum(
                upload.get('validation_summary', {}).get('validation_rate', 0) 
                for upload in month_uploads
            )
            avg_validation_rate = total_validation_rate / len(month_uploads) if month_uploads else 0
            
            trends_data[month] = {
                'validation_rate': avg_validation_rate,
                'upload_count': len(month_uploads),
                'facilities_count': len(set(upload.get('facility_name') for upload in month_uploads))
            }
        
        return {
            'monthly_trends': trends_data,
            'total_months': len(trends_data)
        }
    
    except Exception as e:
        logger.error(f"Error getting performance trends: {str(e)}")
        return {}


def get_facility_comparison():
    """Get facility performance comparison"""
    try:
        calculation_service = MNCHACalculationService()
        
        # Get latest upload for each facility
        latest_uploads = db.session.query(
            DataUpload.facility_name,
            func.max(DataUpload.uploaded_at).label('latest_date')
        ).filter_by(status=UploadStatus.COMPLETED).group_by(DataUpload.facility_name).all()
        
        facility_data = []
        for facility_name, latest_date in latest_uploads:
            upload = db.session.query(DataUpload).filter_by(
                facility_name=facility_name,
                uploaded_at=latest_date,
                status=UploadStatus.COMPLETED
            ).first()
            
            if upload:
                facility_data.append(upload.to_dict(include_data=True))
        
        if len(facility_data) < 2:
            return {'message': 'Need at least 2 facilities for comparison'}
        
        # Use calculation service for comparison
        comparison_results = calculation_service.compare_facilities(facility_data)
        
        return comparison_results
    
    except Exception as e:
        logger.error(f"Error getting facility comparison: {str(e)}")
        return {}


def get_all_facilities_data():
    """Get data for all facilities"""
    try:
        facilities = db.session.query(DataUpload.facility_name).distinct().all()
        facilities_data = []
        
        for (facility_name,) in facilities:
            # Get latest upload for this facility
            latest_upload = db.session.query(DataUpload).filter_by(
                facility_name=facility_name,
                status=UploadStatus.COMPLETED
            ).order_by(desc(DataUpload.uploaded_at)).first()
            
            if latest_upload:
                facility_info = {
                    'name': facility_name,
                    'district': latest_upload.district,
                    'latest_upload_date': latest_upload.uploaded_at,
                    'reporting_period': latest_upload.reporting_period,
                    'validation_summary': latest_upload.get_validation_summary(),
                'total_uploads': db.session.query(DataUpload).filter_by(facility_name=facility_name).count()
                }
                facilities_data.append(facility_info)
        
        return sorted(facilities_data, key=lambda x: x['latest_upload_date'], reverse=True)
    
    except Exception as e:
        logger.error(f"Error getting all facilities data: {str(e)}")
        return []


def get_facilities_performance_comparison():
    """Get detailed facility performance comparison"""
    try:
        return get_facility_comparison()
    
    except Exception as e:
        logger.error(f"Error getting facilities performance comparison: {str(e)}")
        return {}


def perform_search(query, category):
    """Perform search across dashboard data"""
    try:
        results = []
        query_lower = query.lower()
        
        # Search facilities
        if category in ['all', 'facilities']:
            facilities = db.session.query(DataUpload.facility_name, DataUpload.district).filter(
                DataUpload.facility_name.ilike(f'%{query}%') |
                DataUpload.district.ilike(f'%{query}%')
            ).distinct().all()
            
            for facility_name, district in facilities:
                results.append({
                    'type': 'facility',
                    'title': facility_name,
                    'subtitle': district,
                    'url': f'/analysis?facility={facility_name}'
                })
        
        # Search uploads by reporting period
        if category in ['all', 'uploads']:
            uploads = DataUpload.query.filter(
                DataUpload.reporting_period.ilike(f'%{query}%') |
                DataUpload.facility_name.ilike(f'%{query}%')
            ).limit(10).all()
            
            for upload in uploads:
                results.append({
                    'type': 'upload',
                    'title': f"{upload.facility_name} - {upload.reporting_period}",
                    'subtitle': f"Uploaded {upload.uploaded_at.strftime('%Y-%m-%d')}",
                    'url': f'/analysis/upload/{upload.id}'
                })
        
        return results
    
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        return []


# Context processor for dashboard templates
@dashboard_bp.app_context_processor
def inject_dashboard_globals():
    """Inject global variables for dashboard templates"""
    return {
        'current_time': datetime.utcnow(),
        'user_can_upload': current_user.can_upload_data() if current_user.is_authenticated else False,
        'user_permissions': current_user.get_permissions() if current_user.is_authenticated else []
    }
