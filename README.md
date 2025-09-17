# Kiro-mini: AI-Powered Medical Imaging Workflow System

Kiro-mini is a comprehensive medical imaging workflow system that provides AI-assisted report generation, automated billing, and seamless integration with healthcare standards (FHIR, X12). The system is designed to reduce reporting time from hours to under 1 minute while maintaining clinical accuracy and regulatory compliance.

## 🚀 Key Features

### Core Capabilities
- **AI-Assisted Reporting**: Generate comprehensive radiology reports in under 10 seconds
- **Automated Billing**: Create accurate superbills with real-time code validation
- **FHIR Integration**: Export data in FHIR R4 format for interoperability
- **X12 Claims**: Generate X12 837P claims for billing systems
- **Audit Trail**: Complete audit logging for compliance and security
- **Webhook Notifications**: Real-time notifications for workflow events

### Performance Targets
- **1-Minute Workflow**: Complete study-to-billing workflow in under 60 seconds
- **Sub-5s Study Ingestion**: Process incoming studies in under 5 seconds
- **Sub-10s AI Generation**: AI report generation in under 10 seconds
- **Real-time Validation**: Billing code validation in under 2 seconds

### Supported Modalities
- Echocardiography (Complete & Limited)
- Vascular Ultrasound (Carotid, Venous, Arterial)
- Abdominal Ultrasound
- Obstetric & Gynecologic Ultrasound
- Musculoskeletal Ultrasound

## 📋 Requirements

### System Requirements
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (recommended)

### External Integrations
- Orthanc DICOM Server (for DICOM storage)
- AI Service API (for report generation)
- Webhook endpoints (for notifications)

## 🛠️ Installation

### Quick Start with Docker

```bash
# Clone the repository
git clone <repository-url>
cd kiro-mini

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Verify installation
curl http://localhost:8000/integration/status
```

### Manual Installation

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Set up database
createdb kiro_mini
alembic upgrade head

# Start Redis
redis-server

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/kiro_mini

# Redis
REDIS_URL=redis://localhost:6379

# External Services
ORTHANC_URL=http://localhost:8042
AI_SERVICE_URL=http://localhost:8080
AI_SERVICE_API_KEY=your_api_key

# Security
SECRET_KEY=your_secret_key
WEBHOOK_SECRET=your_webhook_secret

# Performance
MAX_WORKERS=4
QUEUE_BATCH_SIZE=10
```

### Orthanc Integration

```json
{
  "DicomWeb": {
    "Enable": true,
    "Root": "/dicom-web/",
    "EnableWado": true,
    "WadoRoot": "/wado",
    "Ssl": false,
    "StowMaxInstances": 10,
    "StowMaxSize": 100
  },
  "Plugins": ["libOrthancDicomWeb.so"],
  "HttpPort": 8042,
  "DicomPort": 4242
}
```

## 📖 API Documentation

### Study Management

#### Ingest Study
```http
POST /studies/{study_uid}/ingest
Content-Type: application/json

{
  "patient_id": "PAT001",
  "study_date": "2024-01-15",
  "modality": "US",
  "exam_type": "echo_complete",
  "study_description": "Complete Echocardiogram"
}
```

#### Get Study
```http
GET /studies/{study_uid}
```

### Report Generation

#### AI-Assisted Report
```http
POST /ai/assist-report
Content-Type: application/json

{
  "study_uid": "1.2.3.4.5.6.7.8.9",
  "exam_type": "echo_complete"
}
```

#### Create Report
```http
POST /reports
Content-Type: application/json

{
  "study_uid": "1.2.3.4.5.6.7.8.9",
  "radiologist_id": "radiologist_001",
  "exam_type": "echo_complete",
  "findings": "Normal cardiac function...",
  "impressions": "Normal echocardiogram",
  "recommendations": "No follow-up required",
  "diagnosis_codes": ["Z01.818"],
  "cpt_codes": ["93306"]
}
```

### Billing

#### Generate Superbill
```http
POST /superbills
Content-Type: application/json

{
  "report_id": "report_123"
}
```

#### Validate Codes
```http
POST /billing/validate
Content-Type: application/json

{
  "cpt_codes": ["93306"],
  "icd10_codes": ["Z01.818"]
}
```

### FHIR Export

#### Export DiagnosticReport
```http
GET /fhir/DiagnosticReport/{report_id}
```

#### Export ImagingStudy
```http
GET /fhir/ImagingStudy/{study_uid}
```

#### Export Bundle
```http
GET /fhir/Bundle/{study_uid}
```

### X12 Export

#### Export 837P Claim
```http
GET /x12/837p/{superbill_id}
```

## 🧪 Testing

### Run All Tests
```bash
cd backend
python tests/run_tests.py
```

### Run Specific Test Types
```bash
# Unit tests only
python tests/run_tests.py --unit

# Integration tests
python tests/run_tests.py --integration

# Performance tests
python tests/run_tests.py --performance

# API tests
python tests/run_tests.py --api
```

### Run with Coverage
```bash
python tests/run_tests.py --coverage
```

## 📊 Monitoring & Observability

### Health Checks
```http
GET /health
GET /integration/status
```

### Metrics Endpoints
```http
GET /metrics/performance
GET /metrics/usage
GET /audit/compliance/report
```

### Audit Trail
```http
GET /audit/trail
GET /audit/user/{user_id}/activity
```

## 🔒 Security & Compliance

### HIPAA Compliance
- All PHI is encrypted at rest and in transit
- Complete audit logging of all data access
- Role-based access controls
- Secure webhook signatures

### Data Protection
- Database encryption
- API authentication and authorization
- Secure configuration management
- Regular security audits

## 🚀 Deployment

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with SSL
docker-compose -f docker-compose.prod.yml up -d

# Set up monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Scaling

```bash
# Scale backend workers
docker-compose up -d --scale backend=3

# Scale Redis workers
docker-compose up -d --scale redis-worker=5
```

## 📈 Performance Optimization

### Database Optimization
- Proper indexing on frequently queried fields
- Connection pooling
- Query optimization
- Regular maintenance

### Caching Strategy
- Redis caching for frequently accessed data
- Application-level caching
- CDN for static assets

### Monitoring
- Application performance monitoring
- Database performance monitoring
- Infrastructure monitoring
- Alert configuration

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd kiro-mini
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements-dev.txt

# Run tests
cd backend
python tests/run_tests.py

# Start development server
uvicorn main:app --reload
```

### Code Quality
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Document all public APIs
- Use type hints

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Configuration Reference](docs/configuration.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

### Getting Help
- Create an issue for bug reports
- Use discussions for questions
- Check the troubleshooting guide
- Review the FAQ

## 🗺️ Roadmap

### Version 1.1
- [ ] Advanced AI models for specialized exams
- [ ] Multi-language support
- [ ] Enhanced performance monitoring
- [ ] Additional FHIR resources

### Version 1.2
- [ ] Machine learning model training interface
- [ ] Advanced analytics dashboard
- [ ] Integration with more PACS systems
- [ ] Mobile application support

---

**Kiro-mini** - Transforming medical imaging workflows with AI-powered automation.#   r a d i o l o g y - p y t h o n  
 #   r a d i o l o g y - p y t h o n - 1 7  
 