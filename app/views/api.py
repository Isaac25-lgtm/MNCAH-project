"""
REST API Views
This module provides REST API endpoints for external integrations and modern frontend
applications to interact with the MOH MNCAH Dashboard System.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import logging

from ..models.upload import DataUpload, UploadStatus
from ..models.user import User, UserType
from ..services.calculation_service import MNCHACalculationService
from ..services.validation_service import DataValidationService
from ..utils.decorators import admin_required, stakeholder_or_admin_required
from .. import db


# Create API blueprint
api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


# API Version and Info
@api_bp.route('/info')
def api_info():
    """API information endpoint"""
    return jsonify({
        'api_version': '1.0.0',
        'service': 'MOH MNCAH Dashboard API',
        'description': 'Maternal, Neonatal, Child and Adolescent Health Analytics API',
        'organization': 'Ministry of Health Uganda',
        'endpoints': {
            'authentication': '/api/auth/*',
            'uploads': '/api/uploads/*',
            'analysis': '/api/analysis/*',
            'reports': '/api/reports/*',
            'facilities': '/api/facilities/*',
            'indicators': '/api/indicators/*'
        },
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'operational'
    })


# Authentication Endpoints
@api_bp.route('/auth/status')
@login_required
def auth_status():
    """Get current authentication status"""
    return jsonify({
        'authenticated': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'user_type': current_user.user_type.value,
            'full_name': current_user.full_name,
            'organization': current_user.organization,
            'permissions': current_user.get_permissions(),
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        },
        'session_info': {
            'login_count': current_user.login_count,
            'can_upload_data': current_user.can_upload_data(),
            'can_view_data': current_user.can_view_data(),
            'can_generate_reports': current_user.can_generate_reports()
        }
    })


# Dashboard API Endpoints
@api_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = {
            'overview': {
                'total_uploads': DataUpload.query.count(),
                'completed_uploads': DataUpload.query.filter_by(status=UploadStatus.COMPLETED).count(),
                'total_facilities': db.session.query(DataUpload.facility_name).distinct().count(),
                'total_districts': db.session.query(DataUpload.district).filter(
                    DataUpload.district.isnot(None)
                ).distinct().count(),
                'active_users': User.query.filter_by(status='active').count()
            },
            'recent_activity': {
                'uploads_last_30_days': DataUpload.query.filter(
                    DataUpload.uploaded_at >= datetime.utcnow() - timedelta(days=30)
                ).count(),
                'uploads_last_7_days': DataUpload.query.filter(
                    DataUpload.uploaded_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
            },
            'data_quality': get_system_data_quality_stats(),
            'performance_summary': get_system_performance_summary()
        }
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve dashboard statistics',
            'message': str(e)
        }), 500


# Uploads API
@api_bp.route('/uploads')
@login_required
def get_uploads():
    """Get uploads with pagination and filtering"""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 items
        
        # Filter parameters
        status_filter = request.args.get('status')
        facility_filter = request.args.get('facility')
        district_filter = request.args.get('district')
        period_filter = request.args.get('period')
        
        # Build query
        query = DataUpload.query
        
        if status_filter:
            try:
                query = query.filter_by(status=UploadStatus(status_filter))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid status filter',
                    'valid_statuses': [status.value for status in UploadStatus]
                }), 400
        
        if facility_filter:
            query = query.filter(DataUpload.facility_name.ilike(f'%{facility_filter}%'))
        
        if district_filter:
            query = query.filter(DataUpload.district.ilike(f'%{district_filter}%'))
        
        if period_filter:
            query = query.filter(DataUpload.reporting_period.ilike(f'%{period_filter}%'))
        
        # Paginate results
        uploads = query.order_by(desc(DataUpload.uploaded_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'uploads': [upload.to_dict() for upload in uploads.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': uploads.total,
                    'pages': uploads.pages,
                    'has_prev': uploads.has_prev,
                    'has_next': uploads.has_next,
                    'prev_num': uploads.prev_num,
                    'next_num': uploads.next_num
                }
            },
            'filters_applied': {
                'status': status_filter,
                'facility': facility_filter,
                'district': district_filter,
                'period': period_filter
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting uploads: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve uploads',
            'message': str(e)
        }), 500


@api_bp.route('/uploads/<int:upload_id>')
@login_required
def get_upload(upload_id):
    """Get specific upload details"""
    try:
        upload = DataUpload.query.get_or_404(upload_id)
        
        return jsonify({
            'success': True,
            'data': upload.to_dict(include_data=True),
            'analysis': {
                'validation_summary': upload.get_validation_summary(),
                'processing_status': upload.status.value,
                'has_processed_data': upload.processed_data is not None
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting upload {upload_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Upload not found or access denied'
        }), 404


# Facilities API
@api_bp.route('/facilities')
@login_required
def get_facilities():
    """Get facilities list with performance data"""
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
            # Get latest upload data for performance metrics
            latest_upload = DataUpload.query.filter_by(
                facility_name=facility.facility_name,
                status=UploadStatus.COMPLETED
            ).order_by(desc(DataUpload.uploaded_at)).first()
            
            if latest_upload:
                validation_summary = latest_upload.get_validation_summary()
                facilities_data.append({
                    'name': facility.facility_name,
                    'district': facility.district,
                    'latest_upload_date': facility.latest_upload.isoformat(),
                    'total_uploads': facility.total_uploads,
                    'latest_period': latest_upload.reporting_period,
                    'performance': {
                        'validation_rate': validation_summary.get('validation_rate', 0),
                        'total_indicators': validation_summary.get('total_indicators', 0),
                        'valid_indicators': validation_summary.get('valid_indicators', 0),
                        'has_critical_issues': validation_summary.get('has_critical_issues', False)
                    }
                })
        
        return jsonify({
            'success': True,
            'data': {
                'facilities': sorted(facilities_data, key=lambda x: x['latest_upload_date'], reverse=True),
                'summary': {
                    'total_facilities': len(facilities_data),
                    'districts_covered': len(set(f['district'] for f in facilities_data if f['district'])),
                    'average_validation_rate': sum(f['performance']['validation_rate'] for f in facilities_data) / len(facilities_data) if facilities_data else 0
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting facilities: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve facilities data',
            'message': str(e)
        }), 500


@api_bp.route('/facilities/<string:facility_name>/performance')
@login_required
def get_facility_performance(facility_name):
    """Get performance data for a specific facility"""
    try:
        # Get all uploads for this facility
        uploads = DataUpload.query.filter_by(
            facility_name=facility_name,
            status=UploadStatus.COMPLETED
        ).order_by(DataUpload.uploaded_at.desc()).all()
        
        if not uploads:
            return jsonify({
                'success': False,
                'error': 'No data found for facility',
                'facility_name': facility_name
            }), 404
        
        # Get trends analysis
        calculation_service = MNCHACalculationService()
        upload_dicts = [upload.to_dict(include_data=True) for upload in uploads]
        trends_data = calculation_service.get_indicator_trends(facility_name, upload_dicts)
        
        # Latest performance
        latest_upload = uploads[0]
        latest_summary = latest_upload.get_validation_summary()
        
        return jsonify({
            'success': True,
            'data': {
                'facility_name': facility_name,
                'district': latest_upload.district,
                'latest_performance': latest_summary,
                'historical_summary': {
                    'total_uploads': len(uploads),
                    'date_range': {
                        'from': uploads[-1].uploaded_at.isoformat(),
                        'to': uploads[0].uploaded_at.isoformat()
                    },
                    'periods_covered': list(set(upload.reporting_period for upload in uploads))
                },
                'trends': trends_data,
                'recent_uploads': [upload.to_dict() for upload in uploads[:5]]
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting facility performance for {facility_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve facility performance data',
            'message': str(e)
        }), 500


# Indicators API
@api_bp.route('/indicators')
@login_required
def get_indicators_list():
    """Get list of all MNCAH indicators with definitions"""
    try:
        from ..models.anc import AntenatalCare
        from ..models.intrapartum import IntrapartumCare
        from ..models.pnc import PostnatalCare
        from ..models.base import PopulationData, PeriodType
        
        # Create dummy instances to get indicator definitions
        dummy_pop = PopulationData(1000, PeriodType.ANNUAL, "2025")
        dummy_data = {}
        
        anc_model = AntenatalCare(dummy_pop, dummy_data)
        intrapartum_model = IntrapartumCare(dummy_pop, dummy_data)
        pnc_model = PostnatalCare(dummy_pop, dummy_data)
        
        indicators = {
            'anc': anc_model.get_indicator_definitions(),
            'intrapartum': intrapartum_model.get_indicator_definitions(),
            'pnc': pnc_model.get_indicator_definitions()
        }
        
        # Count total indicators
        total_indicators = sum(len(category) for category in indicators.values())
        
        return jsonify({
            'success': True,
            'data': {
                'indicators': indicators,
                'summary': {
                    'total_indicators': total_indicators,
                    'anc_indicators': len(indicators['anc']),
                    'intrapartum_indicators': len(indicators['intrapartum']),
                    'pnc_indicators': len(indicators['pnc'])
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting indicators list: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve indicators list',
            'message': str(e)
        }), 500


@api_bp.route('/indicators/<string:indicator_name>/performance')
@login_required
def get_indicator_performance(indicator_name):
    """Get performance data for a specific indicator across facilities"""
    try:
        # Get all uploads with processed data
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404
        
        # Extract indicator values across facilities
        indicator_data = []
        
        for upload in uploads:
            if upload.processed_data:
                # Search for indicator in all categories
                for category in ['anc', 'intrapartum', 'pnc']:
                    if category in upload.processed_data:
                        indicators = upload.processed_data[category].get('indicators', {})
                        validations = upload.processed_data[category].get('validations', {})
                        
                        if indicator_name in indicators:
                            indicator_data.append({
                                'facility_name': upload.facility_name,
                                'district': upload.district,
                                'reporting_period': upload.reporting_period,
                                'category': category,
                                'value': indicators[indicator_name],
                                'validation_status': validations.get(indicator_name, 'unknown'),
                                'upload_date': upload.uploaded_at.isoformat()
                            })
        
        if not indicator_data:
            return jsonify({
                'success': False,
                'error': f'No data found for indicator: {indicator_name}'
            }), 404
        
        # Calculate statistics
        values = [item['value'] for item in indicator_data]
        
        statistics = {
            'count': len(values),
            'mean': sum(values) / len(values),
            'median': sorted(values)[len(values)//2],
            'min': min(values),
            'max': max(values),
            'range': max(values) - min(values),
            'std_dev': calculate_std_dev(values)
        }
        
        # Performance distribution
        performance_dist = {
            'green': sum(1 for item in indicator_data if item['validation_status'] == 'green'),
            'yellow': sum(1 for item in indicator_data if item['validation_status'] == 'yellow'),
            'red': sum(1 for item in indicator_data if item['validation_status'] == 'red'),
            'blue': sum(1 for item in indicator_data if item['validation_status'] == 'blue')
        }
        
        return jsonify({
            'success': True,
            'data': {
                'indicator_name': indicator_name,
                'data_points': indicator_data,
                'statistics': statistics,
                'performance_distribution': performance_dist,
                'facilities_count': len(set(item['facility_name'] for item in indicator_data)),
                'periods_covered': list(set(item['reporting_period'] for item in indicator_data))
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting indicator performance for {indicator_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve indicator performance data',
            'message': str(e)
        }), 500


# Analysis API
@api_bp.route('/analysis/summary')
@login_required
def get_analysis_summary():
    """Get comprehensive analysis summary"""
    try:
        # Get recent uploads for analysis
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        uploads = DataUpload.query.filter(
            DataUpload.uploaded_at >= thirty_days_ago,
            DataUpload.status == UploadStatus.COMPLETED
        ).all()
        
        if not uploads:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'No recent data available',
                    'period': 'last_30_days'
                }
            })
        
        # Generate comprehensive analysis
        analysis_summary = {
            'period': 'last_30_days',
            'data_overview': {
                'total_uploads': len(uploads),
                'facilities': len(set(upload.facility_name for upload in uploads)),
                'districts': len(set(upload.district for upload in uploads if upload.district)),
                'date_range': {
                    'from': min(upload.uploaded_at for upload in uploads).isoformat(),
                    'to': max(upload.uploaded_at for upload in uploads).isoformat()
                }
            },
            'performance_metrics': get_system_performance_summary(),
            'category_analysis': {
                'anc': get_category_analysis_summary(uploads, 'anc'),
                'intrapartum': get_category_analysis_summary(uploads, 'intrapartum'),
                'pnc': get_category_analysis_summary(uploads, 'pnc')
            },
            'data_quality': get_system_data_quality_stats()
        }
        
        return jsonify({
            'success': True,
            'data': analysis_summary,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting analysis summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve analysis summary',
            'message': str(e)
        }), 500


@api_bp.route('/analysis/trends')
@login_required
def get_trends_analysis():
    """Get trends analysis data"""
    try:
        facility_name = request.args.get('facility')
        indicator = request.args.get('indicator')
        months = request.args.get('months', 6, type=int)
        
        # Get uploads for trends
        start_date = datetime.utcnow() - timedelta(days=30 * months)
        query = DataUpload.query.filter(
            DataUpload.uploaded_at >= start_date,
            DataUpload.status == UploadStatus.COMPLETED
        )
        
        if facility_name:
            query = query.filter_by(facility_name=facility_name)
        
        uploads = query.order_by(DataUpload.uploaded_at).all()
        
        if len(uploads) < 2:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Insufficient data for trend analysis (minimum 2 data points required)',
                    'data_points_available': len(uploads)
                }
            })
        
        # Use calculation service for trends
        calculation_service = MNCHACalculationService()
        upload_dicts = [upload.to_dict(include_data=True) for upload in uploads]
        
        if facility_name:
            trends_data = calculation_service.get_indicator_trends(facility_name, upload_dicts)
        else:
            # System-wide trends would need additional implementation
            trends_data = {'message': 'System-wide trends not yet implemented'}
        
        return jsonify({
            'success': True,
            'data': trends_data,
            'analysis_parameters': {
                'facility': facility_name,
                'indicator': indicator,
                'months_analyzed': months,
                'data_points': len(uploads)
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting trends analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trends analysis',
            'message': str(e)
        }), 500


# Validation API
@api_bp.route('/validation/system-status')
@login_required
def get_validation_system_status():
    """Get system-wide validation status"""
    try:
        validation_service = DataValidationService()
        
        # Get all completed uploads
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'No data available for validation analysis'
                }
            })
        
        # Generate validation dashboard data
        dashboard_data = validation_service.generate_validation_dashboard_data([
            upload.to_dict(include_data=True) for upload in uploads
        ])
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting validation system status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve validation status',
            'message': str(e)
        }), 500


# Helper Functions

def get_system_data_quality_stats():
    """Get system-wide data quality statistics"""
    try:
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return {'message': 'No data available'}
        
        total_indicators = sum(upload.total_indicators for upload in uploads)
        valid_indicators = sum(upload.valid_indicators for upload in uploads)
        warning_indicators = sum(upload.warning_indicators for upload in uploads)
        error_indicators = sum(upload.error_indicators for upload in uploads)
        
        return {
            'overall_quality_rate': (valid_indicators / total_indicators * 100) if total_indicators > 0 else 0,
            'total_indicators': total_indicators,
            'valid_indicators': valid_indicators,
            'warning_indicators': warning_indicators,
            'error_indicators': error_indicators,
            'uploads_analyzed': len(uploads)
        }
    
    except Exception as e:
        logger.error(f"Error getting data quality stats: {str(e)}")
        return {'error': str(e)}


def get_system_performance_summary():
    """Get system-wide performance summary"""
    try:
        uploads = DataUpload.query.filter_by(status=UploadStatus.COMPLETED).all()
        
        if not uploads:
            return {'message': 'No data available'}
        
        quality_rates = [upload.get_validation_summary().get('validation_rate', 0) for upload in uploads]
        
        # Performance categorization
        excellent_count = sum(1 for rate in quality_rates if rate >= 90)
        good_count = sum(1 for rate in quality_rates if 75 <= rate < 90)
        acceptable_count = sum(1 for rate in quality_rates if 60 <= rate < 75)
        poor_count = sum(1 for rate in quality_rates if rate < 60)
        
        return {
            'average_performance': sum(quality_rates) / len(quality_rates) if quality_rates else 0,
            'performance_distribution': {
                'excellent': excellent_count,
                'good': good_count,
                'acceptable': acceptable_count,
                'poor': poor_count
            },
            'total_assessments': len(quality_rates)
        }
    
    except Exception as e:
        logger.error(f"Error getting performance summary: {str(e)}")
        return {'error': str(e)}


def get_category_analysis_summary(uploads, category):
    """Get analysis summary for a specific category"""
    try:
        category_uploads = [upload for upload in uploads 
                          if upload.processed_data and category in upload.processed_data]
        
        if not category_uploads:
            return {'message': f'No {category} data available'}
        
        # Calculate category-specific metrics
        category_indicators = 0
        category_valid = 0
        
        for upload in category_uploads:
            validations = upload.processed_data[category].get('validations', {})
            category_indicators += len(validations)
            category_valid += sum(1 for status in validations.values() if status == 'green')
        
        validation_rate = (category_valid / category_indicators * 100) if category_indicators > 0 else 0
        
        return {
            'uploads_with_data': len(category_uploads),
            'total_indicators': category_indicators,
            'valid_indicators': category_valid,
            'validation_rate': validation_rate,
            'facilities_covered': len(set(upload.facility_name for upload in category_uploads))
        }
    
    except Exception as e:
        logger.error(f"Error getting {category} analysis summary: {str(e)}")
        return {'error': str(e)}


def calculate_std_dev(values):
    """Calculate standard deviation"""
    if len(values) < 2:
        return 0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


# Error Handlers for API Blueprint
@api_bp.errorhandler(404)
def api_not_found(error):
    """Handle API 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'message': 'The requested API endpoint or resource was not found'
    }), 404


@api_bp.errorhandler(400)
def api_bad_request(error):
    """Handle API 400 errors"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request parameters or data format'
    }), 400


@api_bp.errorhandler(500)
def api_internal_error(error):
    """Handle API 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred while processing the request'
    }), 500
