"""
Enhanced Patient Routes with Upload Monitoring
Provides comprehensive monitoring, logging, and error handling for patient file uploads.
"""

import uuid
import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models import Patient, PatientFile
from services.upload_monitoring_service import upload_monitoring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])

def extract_request_info(request: Request) -> Dict[str, Any]:
    """Extract relevant information from the request for monitoring."""
    return {
        'user_agent': request.headers.get('user-agent'),
        'ip_address': request.client.host if request.client else None,
        'content_length': request.headers.get('content-length'),
        'content_type': request.headers.get('content-type'),
        'origin': request.headers.get('origin'),
        'referer': request.headers.get('referer')
    }

def validate_patient_exists(patient_id: str, db: Session) -> Patient:
    """Validate that a patient exists and return the patient object."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    return patient

def validate_file_upload(file: UploadFile, max_size: int = 100 * 1024 * 1024) -> None:
    """Validate file upload requirements."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must have a filename"
        )
    
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file.size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        )
    
    if file.size == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is empty"
        )

def validate_dicom_file(file: UploadFile) -> bool:
    """Validate that a file appears to be a DICOM file."""
    if not file.filename:
        return False
    
    filename_lower = file.filename.lower()
    return (
        filename_lower.endswith(('.dcm', '.dicom')) or
        'dicom' in filename_lower or
        filename_lower.startswith(('mr', 'ct', 'us', 'dx', 'cr', 'mg')) or
        filename_lower.endswith('.ima') or
        ('.' not in filename_lower and len(filename_lower) > 3)  # DICOM files often have no extension
    )

@router.post("/{patient_id}/upload/dicom")
async def upload_dicom_files_enhanced(
    patient_id: str,
    files: List[UploadFile] = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Enhanced DICOM file upload with comprehensive monitoring and error handling.
    """
    upload_id = str(uuid.uuid4())
    request_info = extract_request_info(request) if request else {}
    
    logger.info(f"🏥 DICOM upload request: {upload_id} - Patient: {patient_id}, Files: {len(files)}")
    
    # Validate patient exists
    patient = validate_patient_exists(patient_id, db)
    
    # Pre-upload validation
    total_size = 0
    dicom_files = []
    
    for file in files:
        validate_file_upload(file)
        
        if not validate_dicom_file(file):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File {file.filename} does not appear to be a DICOM file"
            )
        
        file_size = file.size or 0
        total_size += file_size
        dicom_files.append({
            'filename': file.filename,
            'size': file_size,
            'content_type': file.content_type
        })
    
    # Check total upload size
    max_total_size = 500 * 1024 * 1024  # 500MB
    if total_size > max_total_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Total upload size ({total_size} bytes) exceeds maximum allowed ({max_total_size} bytes)"
        )
    
    # Log diagnostic information
    upload_monitoring_service.log_diagnostic_info(upload_id, {
        'patient_id': patient_id,
        'file_count': len(files),
        'total_size': total_size,
        'files': dicom_files,
        'request_info': request_info
    })
    
    # Process each file with monitoring
    uploaded_files = []
    processing_results = []
    
    for i, file in enumerate(files):
        file_upload_id = f"{upload_id}_file_{i}"
        file_size = file.size or 0
        
        async with upload_monitoring_service.monitor_upload(
            upload_id=file_upload_id,
            patient_id=patient_id,
            filename=file.filename,
            file_size=file_size,
            request_info=request_info
        ) as metrics:
            
            try:
                # Stage 1: File validation and preparation
                stage_start = time.time()
                
                # Reset file pointer
                await file.seek(0)
                file_content = await file.read()
                
                upload_monitoring_service.log_upload_stage(
                    file_upload_id, 
                    "file_reading", 
                    (time.time() - stage_start) * 1000
                )
                
                # Stage 2: DICOM validation
                stage_start = time.time()
                
                # Basic DICOM header validation
                is_valid_dicom = len(file_content) > 132 and file_content[128:132] == b'DICM'
                if not is_valid_dicom and file.filename.lower().endswith(('.dcm', '.dicom')):
                    logger.warning(f"⚠️ File {file.filename} has DICOM extension but no DICOM header")
                
                upload_monitoring_service.log_upload_stage(
                    file_upload_id, 
                    "dicom_validation", 
                    (time.time() - stage_start) * 1000
                )
                
                # Stage 3: File storage
                stage_start = time.time()
                
                # Import here to avoid circular imports
                from services.file_upload_service import file_upload_service
                
                # Create a new UploadFile object with the content
                import io
                from fastapi import UploadFile as FastAPIUploadFile
                
                file_obj = FastAPIUploadFile(
                    filename=file.filename,
                    file=io.BytesIO(file_content),
                    size=len(file_content),
                    headers=file.headers
                )
                
                # Upload the file
                result = await file_upload_service.upload_files(
                    patient_id=patient_id,
                    files=[file_obj],
                    db=db,
                    file_category="dicom",
                    description=f"DICOM file upload - {file.filename}",
                    tags=["dicom", "medical_imaging", "enhanced_upload"]
                )
                
                upload_monitoring_service.log_upload_stage(
                    file_upload_id, 
                    "file_storage", 
                    (time.time() - stage_start) * 1000
                )
                
                # Update progress
                upload_monitoring_service.update_upload_progress(file_upload_id, file_size)
                
                # Track successful upload
                uploaded_files.append({
                    'filename': file.filename,
                    'size': file_size,
                    'upload_id': file_upload_id,
                    'result': result
                })
                
                processing_results.append({
                    'filename': file.filename,
                    'status': 'success',
                    'message': 'DICOM file uploaded successfully',
                    'file_size': file_size,
                    'is_valid_dicom': is_valid_dicom
                })
                
                logger.info(f"✅ DICOM file uploaded: {file.filename} ({file_size} bytes)")
                
            except Exception as error:
                logger.error(f"❌ DICOM upload failed: {file.filename} - {error}")
                
                processing_results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(error),
                    'error_type': type(error).__name__
                })
                
                # Continue with other files even if one fails
                continue
    
    # Generate response
    success_count = len([r for r in processing_results if r['status'] == 'success'])
    total_count = len(processing_results)
    
    response = {
        'message': f'DICOM upload completed: {success_count}/{total_count} files successful',
        'upload_id': upload_id,
        'patient_id': patient_id,
        'total_files': total_count,
        'successful_files': success_count,
        'failed_files': total_count - success_count,
        'total_size': total_size,
        'uploaded_files': uploaded_files,
        'processing_results': processing_results,
        'processing_time_ms': sum(
            sum(metrics.processing_stages.values()) 
            for metrics in upload_monitoring_service.active_uploads.values()
            if metrics.upload_id.startswith(upload_id)
        )
    }
    
    # Log final result
    if success_count == total_count:
        logger.info(f"🎉 DICOM upload completed successfully: {upload_id}")
    else:
        logger.warning(f"⚠️ DICOM upload partially failed: {upload_id} - {success_count}/{total_count} successful")
    
    return response

@router.post("/{patient_id}/upload")
async def upload_general_files_enhanced(
    patient_id: str,
    files: List[UploadFile] = File(...),
    description: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Enhanced general file upload with comprehensive monitoring and error handling.
    """
    upload_id = str(uuid.uuid4())
    request_info = extract_request_info(request) if request else {}
    
    logger.info(f"📁 General upload request: {upload_id} - Patient: {patient_id}, Files: {len(files)}")
    
    # Validate patient exists
    patient = validate_patient_exists(patient_id, db)
    
    # Pre-upload validation
    total_size = 0
    file_info = []
    
    for file in files:
        validate_file_upload(file)
        
        file_size = file.size or 0
        total_size += file_size
        file_info.append({
            'filename': file.filename,
            'size': file_size,
            'content_type': file.content_type
        })
    
    # Check total upload size
    max_total_size = 500 * 1024 * 1024  # 500MB
    if total_size > max_total_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Total upload size ({total_size} bytes) exceeds maximum allowed ({max_total_size} bytes)"
        )
    
    # Log diagnostic information
    upload_monitoring_service.log_diagnostic_info(upload_id, {
        'patient_id': patient_id,
        'file_count': len(files),
        'total_size': total_size,
        'files': file_info,
        'description': description,
        'request_info': request_info
    })
    
    # Process files with monitoring
    uploaded_files = []
    processing_results = []
    
    for i, file in enumerate(files):
        file_upload_id = f"{upload_id}_file_{i}"
        file_size = file.size or 0
        
        async with upload_monitoring_service.monitor_upload(
            upload_id=file_upload_id,
            patient_id=patient_id,
            filename=file.filename,
            file_size=file_size,
            request_info=request_info
        ) as metrics:
            
            try:
                # Import here to avoid circular imports
                from services.file_upload_service import file_upload_service
                
                # Upload the file
                result = await file_upload_service.upload_files(
                    patient_id=patient_id,
                    files=[file],
                    db=db,
                    file_category="general",
                    description=description or f"General file upload - {file.filename}",
                    tags=["general", "enhanced_upload"]
                )
                
                # Update progress
                upload_monitoring_service.update_upload_progress(file_upload_id, file_size)
                
                # Track successful upload
                uploaded_files.append({
                    'filename': file.filename,
                    'size': file_size,
                    'upload_id': file_upload_id,
                    'result': result
                })
                
                processing_results.append({
                    'filename': file.filename,
                    'status': 'success',
                    'message': 'File uploaded successfully',
                    'file_size': file_size
                })
                
                logger.info(f"✅ File uploaded: {file.filename} ({file_size} bytes)")
                
            except Exception as error:
                logger.error(f"❌ File upload failed: {file.filename} - {error}")
                
                processing_results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(error),
                    'error_type': type(error).__name__
                })
                
                # Continue with other files even if one fails
                continue
    
    # Generate response
    success_count = len([r for r in processing_results if r['status'] == 'success'])
    total_count = len(processing_results)
    
    response = {
        'message': f'File upload completed: {success_count}/{total_count} files successful',
        'upload_id': upload_id,
        'patient_id': patient_id,
        'total_files': total_count,
        'successful_files': success_count,
        'failed_files': total_count - success_count,
        'total_size': total_size,
        'uploaded_files': uploaded_files,
        'processing_results': processing_results
    }
    
    # Log final result
    if success_count == total_count:
        logger.info(f"🎉 File upload completed successfully: {upload_id}")
    else:
        logger.warning(f"⚠️ File upload partially failed: {upload_id} - {success_count}/{total_count} successful")
    
    return response

@router.get("/upload/status/{upload_id}")
async def get_upload_status(upload_id: str):
    """Get the status of an upload operation."""
    status = upload_monitoring_service.get_upload_status(upload_id)
    
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_id} not found"
        )
    
    return status

@router.get("/upload/health")
async def get_upload_health():
    """Get upload system health metrics."""
    health_metrics = upload_monitoring_service.get_health_metrics()
    error_stats = upload_monitoring_service.get_error_statistics()
    performance_metrics = upload_monitoring_service.get_performance_metrics()
    
    return {
        'status': 'healthy',
        'timestamp': health_metrics.timestamp.isoformat(),
        'health_metrics': {
            'total_uploads': health_metrics.total_uploads,
            'successful_uploads': health_metrics.successful_uploads,
            'failed_uploads': health_metrics.failed_uploads,
            'error_rate': health_metrics.error_rate,
            'average_upload_time': health_metrics.average_upload_time,
            'throughput_mbps': health_metrics.throughput_mbps,
            'active_uploads': health_metrics.active_uploads
        },
        'error_statistics': error_stats,
        'performance_metrics': performance_metrics,
        'upload_config': {
            'max_file_size': '100MB',
            'max_total_size': '500MB',
            'supported_formats': ['dcm', 'dicom', 'pdf', 'jpg', 'jpeg', 'png', 'txt'],
            'timeout': '60s'
        }
    }

@router.get("/upload/metrics")
async def get_upload_metrics():
    """Get detailed upload metrics and statistics."""
    health_metrics = upload_monitoring_service.get_health_metrics()
    error_stats = upload_monitoring_service.get_error_statistics()
    performance_metrics = upload_monitoring_service.get_performance_metrics()
    
    return {
        'timestamp': health_metrics.timestamp.isoformat(),
        'system_health': {
            'total_uploads': health_metrics.total_uploads,
            'successful_uploads': health_metrics.successful_uploads,
            'failed_uploads': health_metrics.failed_uploads,
            'error_rate': health_metrics.error_rate,
            'active_uploads': health_metrics.active_uploads,
            'system_load': health_metrics.system_load
        },
        'performance': performance_metrics,
        'errors': error_stats,
        'trends': {
            'hourly_uploads': health_metrics.total_uploads,  # Would be more detailed in production
            'success_rate': 100 - health_metrics.error_rate,
            'average_throughput': health_metrics.throughput_mbps
        }
    }

@router.post("/upload/cleanup")
async def cleanup_old_upload_data(max_age_hours: int = 24):
    """Clean up old upload monitoring data."""
    upload_monitoring_service.clear_old_data(max_age_hours)
    
    return {
        'message': f'Cleaned up upload data older than {max_age_hours} hours',
        'timestamp': time.time()
    }