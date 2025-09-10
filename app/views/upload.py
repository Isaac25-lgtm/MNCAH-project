"""
Data Upload Views
This module handles file uploads, data processing, and validation for the MOH MNCAH Dashboard.
"""

import os
import uuid
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

from ..models.upload import DataUpload, DataProcessor, UploadStatus
from ..models.base import PeriodType
from ..services.validation_service import DataValidationService
from ..utils.decorators import admin_required
from .. import db


# Create upload blueprint
upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)


@upload_bp.route('/')
@login_required
@admin_required
def index():
    """
    Upload page - shows upload form and recent uploads
    """
    try:
        # Get recent uploads for this user or all if admin
        recent_uploads = DataUpload.query.order_by(
            DataUpload.uploaded_at.desc()
        ).limit(10).all()
        
        return render_template('upload/index.html', 
                             recent_uploads=recent_uploads,
                             max_file_size=current_app.config['MAX_CONTENT_LENGTH'])
    
    except Exception as e:
        logger.error(f"Error loading upload page: {str(e)}")
        flash('Error loading upload page', 'error')
        return redirect(url_for('dashboard.index'))


@upload_bp.route('/upload', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """
    Handle file upload and data processing
    """
    try:
        # Validate form data
        facility_name = request.form.get('facility_name', '').strip()
        district = request.form.get('district', '').strip()
        population = request.form.get('population', type=int)
        period_type = request.form.get('period_type', '').strip()
        reporting_period = request.form.get('reporting_period', '').strip()
        
        # Validate required fields
        if not facility_name:
            return jsonify({'success': False, 'message': 'Facility name is required'}), 400
        
        if not population or population <= 0:
            return jsonify({'success': False, 'message': 'Valid population number is required'}), 400
        
        if period_type not in ['annual', 'quarterly', 'monthly']:
            return jsonify({'success': False, 'message': 'Valid period type is required'}), 400
        
        if not reporting_period:
            return jsonify({'success': False, 'message': 'Reporting period is required'}), 400
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'message': 'Invalid file type. Please upload CSV or Excel files only.'
            }), 400
        
        # Generate unique filename
        original_filename = file.filename
        filename = secure_filename(f"{uuid.uuid4().hex}_{original_filename}")
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save uploaded file
        file.save(file_path)
        
        # Create upload record and process data
        upload = DataProcessor.create_upload_record(
            file_path=file_path,
            original_filename=original_filename,
            facility_name=facility_name,
            population=population,
            period_type=period_type,
            reporting_period=reporting_period,
            user_id=current_user.id,
            district=district
        )
        
        # Add to database
        db.session.add(upload)
        db.session.commit()
        
        # Process the upload
        success, message = upload.process_upload()
        
        if success:
            db.session.commit()
            logger.info(f"Successfully processed upload {upload.id} for {facility_name}")
            
            return jsonify({
                'success': True,
                'message': 'File uploaded and processed successfully!',
                'upload_id': upload.id,
                'redirect': url_for('analysis.view_upload', upload_id=upload.id)
            })
        else:
            db.session.rollback()
            logger.error(f"Failed to process upload {upload.id}: {message}")
            
            return jsonify({
                'success': False,
                'message': f'File uploaded but processing failed: {message}'
            }), 500
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in file upload: {str(e)}")
        
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        return jsonify({
            'success': False,
            'message': f'Error processing upload: {str(e)}'
        }), 500


@upload_bp.route('/validate/<int:upload_id>')
@login_required
@admin_required
def validate_upload(upload_id):
    """
    Validate uploaded data and show validation results
    """
    try:
        upload = DataUpload.query.get_or_404(upload_id)
        
        # Run validation service
        validation_service = DataValidationService()
        
        if upload.processed_data:
            validation_report = validation_service.validate_upload_data(upload.processed_data)
            
            # Update upload with validation results
            upload.validation_results = validation_report
            db.session.commit()
            
            return render_template('upload/validation.html',
                                 upload=upload,
                                 validation_report=validation_report)
        else:
            flash('Upload has not been processed yet', 'warning')
            return redirect(url_for('upload.view_upload', upload_id=upload_id))
    
    except Exception as e:
        logger.error(f"Error validating upload {upload_id}: {str(e)}")
        flash('Error validating upload', 'error')
        return redirect(url_for('upload.index'))


@upload_bp.route('/view/<int:upload_id>')
@login_required
def view_upload(upload_id):
    """
    View upload details and processing results
    """
    try:
        upload = DataUpload.query.get_or_404(upload_id)
        
        return render_template('upload/view.html', upload=upload)
    
    except Exception as e:
        logger.error(f"Error viewing upload {upload_id}: {str(e)}")
        flash('Error loading upload details', 'error')
        return redirect(url_for('upload.index'))


@upload_bp.route('/reprocess/<int:upload_id>', methods=['POST'])
@login_required
@admin_required
def reprocess_upload(upload_id):
    """
    Reprocess failed upload
    """
    try:
        upload = DataUpload.query.get_or_404(upload_id)
        
        if upload.status not in [UploadStatus.FAILED, UploadStatus.PENDING]:
            return jsonify({
                'success': False,
                'message': 'Only failed or pending uploads can be reprocessed'
            }), 400
        
        # Reset status and reprocess
        upload.status = UploadStatus.PENDING
        upload.error_log = None
        db.session.commit()
        
        success, message = upload.process_upload()
        
        if success:
            db.session.commit()
            logger.info(f"Successfully reprocessed upload {upload_id}")
            
            return jsonify({
                'success': True,
                'message': 'Upload reprocessed successfully!',
                'redirect': url_for('analysis.view_upload', upload_id=upload_id)
            })
        else:
            db.session.commit()  # Commit the failed status
            logger.error(f"Failed to reprocess upload {upload_id}: {message}")
            
            return jsonify({
                'success': False,
                'message': f'Reprocessing failed: {message}'
            }), 500
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reprocessing upload {upload_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'message': 'Error during reprocessing'
        }), 500


@upload_bp.route('/delete/<int:upload_id>', methods=['POST'])
@login_required
@admin_required
def delete_upload(upload_id):
    """
    Delete upload and associated files
    """
    try:
        upload = DataUpload.query.get_or_404(upload_id)
        
        # Delete associated file
        if upload.file_path and os.path.exists(upload.file_path):
            try:
                os.remove(upload.file_path)
            except Exception as e:
                logger.warning(f"Could not delete file {upload.file_path}: {str(e)}")
        
        # Delete database record
        db.session.delete(upload)
        db.session.commit()
        
        logger.info(f"Deleted upload {upload_id} - {upload.facility_name}")
        
        return jsonify({
            'success': True,
            'message': 'Upload deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting upload {upload_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'message': 'Error deleting upload'
        }), 500


@upload_bp.route('/template')
@login_required
def download_template():
    """
    Download data template file
    """
    try:
        # Create template data
        template_data = create_template_data()
        
        # Generate template file
        template_path = generate_template_file(template_data)
        
        return send_file(
            template_path,
            as_attachment=True,
            download_name='MNCAH_Data_Template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        flash('Error generating template file', 'error')
        return redirect(url_for('upload.index'))


@upload_bp.route('/api/uploads')
@login_required
def api_uploads():
    """
    API endpoint to get uploads list
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        facility_filter = request.args.get('facility')
        
        # Build query
        query = DataUpload.query
        
        if status_filter:
            query = query.filter_by(status=UploadStatus(status_filter))
        
        if facility_filter:
            query = query.filter(DataUpload.facility_name.ilike(f'%{facility_filter}%'))
        
        # Paginate results
        uploads = query.order_by(DataUpload.uploaded_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'uploads': [upload.to_dict() for upload in uploads.items],
            'pagination': {
                'page': page,
                'pages': uploads.pages,
                'per_page': per_page,
                'total': uploads.total,
                'has_prev': uploads.has_prev,
                'has_next': uploads.has_next
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting uploads via API: {str(e)}")
        return jsonify({'error': 'Error retrieving uploads'}), 500


@upload_bp.route('/api/upload/<int:upload_id>')
@login_required
def api_upload_details(upload_id):
    """
    API endpoint to get upload details
    """
    try:
        upload = DataUpload.query.get_or_404(upload_id)
        return jsonify(upload.to_dict(include_data=True))
    
    except Exception as e:
        logger.error(f"Error getting upload details via API: {str(e)}")
        return jsonify({'error': 'Error retrieving upload details'}), 500


@upload_bp.route('/bulk-upload', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_upload():
    """
    Handle bulk upload of multiple files
    """
    if request.method == 'GET':
        return render_template('upload/bulk_upload.html')
    
    try:
        files = request.files.getlist('files[]')
        facility_mappings = request.form.getlist('facility_mappings[]')
        
        if not files:
            return jsonify({'success': False, 'message': 'No files uploaded'}), 400
        
        results = []
        for i, file in enumerate(files):
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Process individual file (simplified for bulk upload)
                    # In a real implementation, you'd parse facility info from filename or form
                    result = process_bulk_file(file, facility_mappings[i] if i < len(facility_mappings) else None)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': str(e)
                    })
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(results)} files',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        return jsonify({'success': False, 'message': 'Error processing bulk upload'}), 500


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def create_template_data():
    """Create template data structure"""
    return {
        'indicators': [
            # ANC Indicators
            {'code': '105-AN01a', 'name': 'ANC 1st Visit for women', 'category': 'ANC', 'value': ''},
            {'code': '105-AN01b', 'name': 'ANC 1st Visit for women (1st Trimester)', 'category': 'ANC', 'value': ''},
            {'code': '105-AN02', 'name': 'ANC 4th Visit for women', 'category': 'ANC', 'value': ''},
            {'code': '105-AN04', 'name': 'ANC 8 contacts/visits for women', 'category': 'ANC', 'value': ''},
            {'code': '105-AN010', 'name': 'Third dose IPT (IPT3)', 'category': 'ANC', 'value': ''},
            {'code': '105-AN17', 'name': 'Pregnant women tested for Anaemia using Hb Test', 'category': 'ANC', 'value': ''},
            {'code': '105-AN21', 'name': 'Pregnant Women receiving atleast 30 tablets of Iron/Folic Acid', 'category': 'ANC', 'value': ''},
            {'code': '105-AN23', 'name': 'Pregnant Women receiving LLINs at ANC 1st visit', 'category': 'ANC', 'value': ''},
            {'code': '105-AN24a', 'name': 'Pregnant women who received obstetric ultra sound scan', 'category': 'ANC', 'value': ''},
            
            # Intrapartum Indicators
            {'code': '105-MA04a', 'name': 'Deliveries in unit - Total', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA04b1', 'name': 'Deliveries in unit - Live births - Total', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA04b2', 'name': 'Deliveries in unit - Live births - less than 2.5kg', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA04c1', 'name': 'Deliveries in unit - Fresh still birth - Total', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA04d1', 'name': 'Deliveries in unit - Macerated still birth - Total', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA07', 'name': 'Low birth weight babies initiated on kangaroo (KMC)', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA11', 'name': 'Newborn deaths (0-7 days)', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA12', 'name': 'Neonatal Death 8-28 days', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA13', 'name': 'Maternal deaths', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA24', 'name': 'No.of babies with Birth asphyxia', 'category': 'Intrapartum', 'value': ''},
            {'code': '105-MA25', 'name': 'No. of Live babies Successfully Resuscitated', 'category': 'Intrapartum', 'value': ''},
            
            # PNC Indicators
            {'code': 'bf_1hour', 'name': 'Mothers who initiated breastfeeding within 1st hour', 'category': 'PNC', 'value': ''},
            {'code': 'pnc_24hrs', 'name': 'Post Natal Attendances 24Hrs', 'category': 'PNC', 'value': ''},
            {'code': 'pnc_6days', 'name': 'Post Natal Attendances 6Dys', 'category': 'PNC', 'value': ''},
            {'code': 'pnc_6weeks', 'name': 'Post Natal Attendances 6Wks', 'category': 'PNC', 'value': ''}
        ]
    }


def generate_template_file(template_data):
    """Generate Excel template file"""
    try:
        import pandas as pd
        
        # Create DataFrame
        df = pd.DataFrame(template_data['indicators'])
        
        # Generate file path
        template_filename = f"MNCAH_Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        template_path = os.path.join(current_app.config['EXPORT_FOLDER'], template_filename)
        
        # Write to Excel
        with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='MNCAH_Data', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Instructions': [
                    'Fill in the Value column with actual numbers for each indicator',
                    'Do not modify the Code or Name columns',
                    'Leave empty cells as blank (do not use 0 unless actual value is 0)',
                    'Save as CSV or Excel format for upload',
                    'Contact system administrator for questions'
                ]
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        return template_path
    
    except Exception as e:
        logger.error(f"Error generating template file: {str(e)}")
        raise


def process_bulk_file(file, facility_mapping):
    """Process individual file in bulk upload"""
    # This is a simplified version - in reality you'd need more complex logic
    # to extract facility information and process each file
    return {
        'filename': file.filename,
        'success': True,
        'facility': facility_mapping or 'Unknown',
        'records': 1  # Placeholder
    }
