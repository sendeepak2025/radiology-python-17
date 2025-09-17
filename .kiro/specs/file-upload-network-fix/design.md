# Design Document

## Overview

This design addresses the network connectivity issues in the DICOM file upload system by implementing comprehensive error handling, connectivity diagnostics, retry mechanisms, and improved user feedback. The solution focuses on identifying and resolving the root causes of upload failures while providing a robust, user-friendly upload experience.

## Architecture

### Current System Analysis
- Frontend: React application running on port 3000
- Backend: FastAPI server running on port 8000 
- Upload endpoints: `/patients/{patient_id}/upload/dicom` and `/patients/{patient_id}/upload`
- Current issue: Network errors at 90% upload progress

### Root Cause Analysis
Based on code analysis, the likely causes of network errors are:
1. **Timeout Issues**: Large DICOM files may exceed the 30-second timeout
2. **CORS Configuration**: Potential preflight request failures
3. **FormData Handling**: Inconsistent field naming between frontend and backend
4. **Error Propagation**: Backend errors not properly communicated to frontend
5. **Connection Pooling**: Axios client may be reusing failed connections

## Components and Interfaces

### 1. Network Diagnostics Service
**Purpose**: Proactive connectivity testing and health monitoring

**Interface**:
```typescript
interface NetworkDiagnosticsService {
  checkBackendConnectivity(): Promise<ConnectivityStatus>
  performUploadPrecheck(fileSize: number): Promise<PreCheckResult>
  monitorUploadHealth(uploadId: string): Promise<HealthMetrics>
  getDiagnosticReport(): Promise<DiagnosticReport>
}

interface ConnectivityStatus {
  isConnected: boolean
  latency: number
  serverVersion: string
  corsEnabled: boolean
  errors: string[]
}
```

### 2. Enhanced Upload Service
**Purpose**: Robust file upload with retry logic and better error handling

**Interface**:
```typescript
interface EnhancedUploadService {
  uploadWithRetry(file: File, options: UploadOptions): Promise<UploadResult>
  queueUpload(file: File, options: UploadOptions): Promise<string>
  resumeQueuedUploads(): Promise<UploadResult[]>
  cancelUpload(uploadId: string): Promise<void>
}

interface UploadOptions {
  patientId: string
  description?: string
  maxRetries?: number
  timeout?: number
  chunkSize?: number
}
```

### 3. Upload Progress Manager
**Purpose**: Real-time progress tracking with detailed status updates

**Interface**:
```typescript
interface UploadProgressManager {
  trackUpload(uploadId: string, file: File): Promise<void>
  updateProgress(uploadId: string, progress: ProgressUpdate): void
  getUploadStatus(uploadId: string): UploadStatus
  subscribeToProgress(uploadId: string, callback: ProgressCallback): void
}

interface ProgressUpdate {
  bytesUploaded: number
  totalBytes: number
  stage: 'preparing' | 'uploading' | 'processing' | 'complete' | 'error'
  message: string
}
```

### 4. Backend Health Monitor
**Purpose**: Server-side monitoring and diagnostics

**Interface**:
```python
class BackendHealthMonitor:
    async def check_system_health(self) -> HealthStatus
    async def validate_upload_endpoints(self) -> EndpointStatus
    async def monitor_upload_performance(self) -> PerformanceMetrics
    async def log_upload_diagnostics(self, upload_data: dict) -> None
```

## Data Models

### Upload Queue Entry
```typescript
interface QueuedUpload {
  id: string
  file: File
  patientId: string
  description: string
  attempts: number
  maxRetries: number
  status: 'queued' | 'uploading' | 'failed' | 'completed'
  lastError?: string
  createdAt: Date
  lastAttemptAt?: Date
}
```

### Diagnostic Report
```typescript
interface DiagnosticReport {
  timestamp: Date
  connectivity: ConnectivityStatus
  systemHealth: SystemHealth
  recentErrors: ErrorLog[]
  performanceMetrics: PerformanceMetrics
  recommendations: string[]
}
```

### Upload Configuration
```typescript
interface UploadConfig {
  maxFileSize: number
  allowedTypes: string[]
  timeout: number
  retryAttempts: number
  chunkSize: number
  endpoints: {
    dicom: string
    general: string
    health: string
  }
}
```

## Error Handling

### 1. Network Error Classification
- **Connection Errors**: Backend unreachable, DNS issues
- **Timeout Errors**: Request exceeds configured timeout
- **Server Errors**: 5xx responses from backend
- **Client Errors**: 4xx responses (authentication, validation)
- **CORS Errors**: Preflight failures, origin restrictions

### 2. Error Recovery Strategies
- **Automatic Retry**: Exponential backoff for transient errors
- **Queue Management**: Persist failed uploads for manual retry
- **Fallback Endpoints**: Alternative upload routes if available
- **User Guidance**: Specific troubleshooting steps for each error type

### 3. Error Reporting
- **User-Friendly Messages**: Clear, actionable error descriptions
- **Technical Details**: Detailed logs for developers
- **Error Tracking**: Persistent error history and patterns
- **Support Information**: Contact details and diagnostic data

## Testing Strategy

### 1. Unit Tests
- Network diagnostics service functionality
- Upload retry logic and queue management
- Error classification and handling
- Progress tracking accuracy

### 2. Integration Tests
- End-to-end upload workflows
- Backend connectivity scenarios
- CORS configuration validation
- File type and size handling

### 3. Error Simulation Tests
- Network disconnection scenarios
- Server timeout conditions
- Backend unavailability
- Large file upload stress tests

### 4. Performance Tests
- Upload speed benchmarks
- Concurrent upload handling
- Memory usage during large uploads
- Progress update frequency

## Implementation Phases

### Phase 1: Diagnostics and Monitoring
1. Implement network diagnostics service
2. Add backend health monitoring endpoints
3. Create diagnostic reporting interface
4. Add connectivity status indicators

### Phase 2: Enhanced Upload Service
1. Implement retry logic with exponential backoff
2. Add upload queue management
3. Improve error classification and handling
4. Enhance progress tracking

### Phase 3: User Experience Improvements
1. Add pre-upload connectivity checks
2. Implement real-time status updates
3. Create user-friendly error messages
4. Add troubleshooting guidance

### Phase 4: Backend Optimizations
1. Optimize upload endpoint performance
2. Improve CORS configuration
3. Add upload monitoring and logging
4. Implement chunked upload support

## Configuration Updates

### Frontend Environment Variables
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_UPLOAD_TIMEOUT=60000
REACT_APP_MAX_RETRY_ATTEMPTS=3
REACT_APP_CHUNK_SIZE=1048576
REACT_APP_ENABLE_UPLOAD_DIAGNOSTICS=true
```

### Backend Configuration
```python
# Upload settings
UPLOAD_TIMEOUT = 60  # seconds
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
CHUNK_SIZE = 1024 * 1024  # 1MB
ENABLE_UPLOAD_MONITORING = True

# CORS settings
CORS_ALLOW_ORIGINS = ["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["*"]
```

## Security Considerations

### 1. File Validation
- DICOM file format verification
- File size and type restrictions
- Malware scanning integration
- Content sanitization

### 2. Authentication and Authorization
- Patient ID validation
- User permission checks
- Upload rate limiting
- Session management

### 3. Data Protection
- Encrypted file transmission
- Secure temporary storage
- Audit logging for uploads
- HIPAA compliance measures

## Monitoring and Alerting

### 1. Upload Metrics
- Success/failure rates
- Average upload times
- File size distributions
- Error frequency by type

### 2. System Health Metrics
- Backend response times
- Connection pool status
- Memory and CPU usage
- Network bandwidth utilization

### 3. Alert Conditions
- Upload failure rate > 10%
- Backend response time > 5 seconds
- Connection errors > 5 per minute
- Queue size > 50 pending uploads