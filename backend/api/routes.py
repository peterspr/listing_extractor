"""
API routes for PDF extraction web service
"""
import os
import uuid
import logging
import csv
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

from backend.config.settings import settings
from backend.services.storage_service import LocalStorageService
from backend.services.extractor_service import PDFExtractorService
from backend.services.llm_service import LLMService
from backend.services.progress_tracker import progress_tracker, ExtractionStatus
from backend.models.schemas import (
    validate_file_extension,
    validate_file_size,
    parse_csv_row_to_dict
)

logger = logging.getLogger(__name__)

# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Initialize services
storage_service = LocalStorageService(settings.UPLOAD_FOLDER, settings.RESULTS_FOLDER)
config = settings.load_llm_config()
extractor_service = PDFExtractorService(config)
llm_service = LLMService(config)


@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


@api.route('/upload', methods=['POST'])
def upload_files():
    """
    Upload PDF files for extraction

    Expects: multipart/form-data with 'files' field containing PDF files
    Returns: Session ID and file metadata
    """
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')

        if not files or len(files) == 0:
            return jsonify({'error': 'No files provided'}), 400

        # Generate session ID
        session_id = str(uuid.uuid4())

        uploaded_files = []
        errors = []

        for file in files:
            # Validate file
            if file.filename == '':
                errors.append({'filename': 'unknown', 'error': 'Empty filename'})
                continue

            if not validate_file_extension(file.filename, settings.ALLOWED_EXTENSIONS):
                errors.append({'filename': file.filename, 'error': 'Invalid file type. Only PDF files are allowed'})
                continue

            # Check file size (approximate check)
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            if not validate_file_size(file_size, settings.MAX_FILE_SIZE):
                errors.append({
                    'filename': file.filename,
                    'error': f'File too large. Maximum size is {settings.MAX_FILE_SIZE / (1024 * 1024):.0f}MB'
                })
                continue

            # Save file
            try:
                file_path = storage_service.save_file(file, session_id, file.filename)
                file_id = str(uuid.uuid4())

                uploaded_files.append({
                    'file_id': file_id,
                    'filename': file.filename,
                    'size': file_size,
                    'upload_time': datetime.utcnow().isoformat(),
                    'path': file_path
                })
            except Exception as e:
                logger.error(f"Error saving file {file.filename}: {str(e)}")
                errors.append({'filename': file.filename, 'error': str(e)})

        if not uploaded_files:
            return jsonify({
                'error': 'No valid files uploaded',
                'details': errors
            }), 400

        logger.info(f"Uploaded {len(uploaded_files)} files for session {session_id}")

        return jsonify({
            'session_id': session_id,
            'files': uploaded_files,
            'total_files': len(uploaded_files),
            'errors': errors if errors else None
        }), 200

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@api.route('/extract', methods=['POST'])
def extract_pdfs():
    """
    Extract data from uploaded PDFs

    Expects: JSON with session_id and optional file_ids list
    Returns: Extraction results
    """
    try:
        data = request.get_json()

        if not data or 'session_id' not in data:
            return jsonify({'error': 'session_id is required'}), 400

        session_id = data['session_id']
        file_ids = data.get('file_ids')
        files_data = data.get('files', [])

        # Validate session exists
        if not storage_service.session_exists(session_id):
            return jsonify({'error': 'Invalid session_id'}), 404

        # If file_ids not provided, use all files from request
        if not files_data:
            return jsonify({'error': 'No files data provided'}), 400

        # Initialize progress tracking
        file_ids_list = [f['file_id'] for f in files_data]
        filenames_list = [f['filename'] for f in files_data]
        progress_tracker.initialize_session(session_id, file_ids_list, filenames_list)

        # Process each file
        results = []
        errors = []
        successful = 0
        failed = 0

        for file_data in files_data:
            file_id = file_data['file_id']
            filename = file_data['filename']

            try:
                # Update progress: extracting
                progress_tracker.update_file_progress(
                    session_id, file_id, ExtractionStatus.EXTRACTING.value, 25
                )

                # Get file path
                file_path = storage_service.get_file_path(session_id, filename)

                # Extract PDF
                extraction_result = extractor_service.extract_pdf(file_path)

                if not extraction_result.success:
                    progress_tracker.update_file_progress(
                        session_id, file_id, ExtractionStatus.FAILED.value, 100,
                        extraction_result.error_message
                    )
                    failed += 1
                    errors.append({
                        'file_id': file_id,
                        'filename': filename,
                        'error': extraction_result.error_message
                    })
                    results.append({
                        'file_id': file_id,
                        'filename': filename,
                        'success': False,
                        'error_message': extraction_result.error_message
                    })
                    continue

                # Update progress: processing with LLM
                progress_tracker.update_file_progress(
                    session_id, file_id, ExtractionStatus.PROCESSING.value, 50
                )

                # Get combined content
                combined_content = extractor_service.get_combined_content(extraction_result)

                # Process with LLM
                llm_result = llm_service.process_extraction(filename, combined_content)

                if not llm_result.success:
                    progress_tracker.update_file_progress(
                        session_id, file_id, ExtractionStatus.FAILED.value, 100,
                        llm_result.error_message
                    )
                    failed += 1
                    errors.append({
                        'file_id': file_id,
                        'filename': filename,
                        'error': llm_result.error_message
                    })
                    results.append({
                        'file_id': file_id,
                        'filename': filename,
                        'success': False,
                        'error_message': llm_result.error_message
                    })
                    continue

                # Parse CSV row to dict
                data_dict = parse_csv_row_to_dict(llm_result.csv_row, llm_service.csv_headers)

                # Update progress: completed
                progress_tracker.update_file_progress(
                    session_id, file_id, ExtractionStatus.COMPLETED.value, 100
                )

                successful += 1
                results.append({
                    'file_id': file_id,
                    'filename': filename,
                    'success': True,
                    'csv_row': llm_result.csv_row,
                    'data': data_dict
                })

            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                progress_tracker.update_file_progress(
                    session_id, file_id, ExtractionStatus.FAILED.value, 100, str(e)
                )
                failed += 1
                errors.append({
                    'file_id': file_id,
                    'filename': filename,
                    'error': str(e)
                })
                results.append({
                    'file_id': file_id,
                    'filename': filename,
                    'success': False,
                    'error_message': str(e)
                })

        logger.info(f"Extraction complete for session {session_id}: {successful} successful, {failed} failed")

        return jsonify({
            'session_id': session_id,
            'total_files': len(files_data),
            'successful': successful,
            'failed': failed,
            'results': results,
            'errors': errors
        }), 200

    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@api.route('/progress/<session_id>', methods=['GET'])
def progress_stream(session_id):
    """
    Server-Sent Events endpoint for real-time progress updates

    Returns: SSE stream of progress updates
    """
    def generate():
        """Generate SSE messages"""
        try:
            import time

            # Send initial progress
            yield progress_tracker.to_sse_message(session_id)

            # Continue sending updates until extraction is complete
            max_iterations = 600  # 10 minutes timeout (1 update per second)
            iteration = 0

            while iteration < max_iterations:
                session_progress = progress_tracker.get_session_progress(session_id)

                if not session_progress:
                    yield f"data: {{'error': 'Session not found'}}\n\n"
                    break

                # Send progress update
                yield progress_tracker.to_sse_message(session_id)

                # Check if complete
                if session_progress.status in [ExtractionStatus.COMPLETED.value, ExtractionStatus.FAILED.value]:
                    break

                time.sleep(1)
                iteration += 1

            # Send final update
            yield progress_tracker.to_sse_message(session_id)

        except GeneratorExit:
            logger.info(f"Client disconnected from progress stream for session {session_id}")
        except Exception as e:
            logger.error(f"Error in progress stream: {str(e)}")
            yield f"data: {{'error': 'Stream error: {str(e)}'}}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no',
                        'Connection': 'keep-alive'
                    })


@api.route('/download/<session_id>', methods=['GET'])
def download_results(session_id):
    """
    Download extraction results as CSV

    Query params:
        - file_ids: Comma-separated list of file IDs (optional, defaults to all)
        - combine: true/false - combine into single CSV or zip of individual files

    Returns: CSV file or ZIP file
    """
    try:
        # Get query parameters
        file_ids_param = request.args.get('file_ids')
        combine = request.args.get('combine', 'true').lower() == 'true'

        # Get session progress to retrieve results
        session_progress = progress_tracker.get_session_progress(session_id)

        if not session_progress:
            return jsonify({'error': 'Session not found'}), 404

        # Get all files progress
        files_progress = progress_tracker.get_all_files_progress(session_id)

        if not files_progress:
            return jsonify({'error': 'No files found for session'}), 404

        # Filter by file_ids if provided
        if file_ids_param:
            file_ids_list = file_ids_param.split(',')
            files_progress = {k: v for k, v in files_progress.items() if k in file_ids_list}

        # For now, return a note that results need to be retrieved from extraction response
        # In a full implementation, we'd store results and retrieve them here
        return jsonify({
            'message': 'Download functionality requires storing results. Please use extraction response data.',
            'session_id': session_id
        }), 501

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@api.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete a session and all associated files

    Returns: Success message
    """
    try:
        # Check if session exists
        if not storage_service.session_exists(session_id):
            return jsonify({'error': 'Session not found'}), 404

        # Delete files
        storage_service.delete_session(session_id)

        # Remove from progress tracker
        progress_tracker.remove_session(session_id)

        logger.info(f"Deleted session {session_id}")

        return jsonify({'message': 'Session deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Delete session error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
