# MOH MNCAH Dashboard

A comprehensive Flask-based dashboard system for analyzing Maternal, Neonatal, Child and Adolescent Health (MNCAH) indicators for the Uganda Ministry of Health.

## Overview

The MOH MNCAH Dashboard provides health administrators with tools to analyze, visualize, and report on 22 critical health indicators across three categories:

- **Antenatal Care (ANC)**: 9 indicators including coverage, IPT3, iron/folic supplementation
- **Intrapartum Care**: 9 indicators including deliveries, mortality rates, birth outcomes  
- **Postnatal Care (PNC)**: 4 indicators including breastfeeding and follow-up visits

## Features

### 📊 Data Analysis
- **Population-based calculations** with automatic adjustment for reporting periods (monthly/quarterly/annual)
- **Validation engine** with color-coded performance indicators (green/yellow/red/blue)
- **Trend analysis** and facility benchmarking
- **Real-time data quality assessment**

### 👥 User Management
- **Two-tier access control**:
  - **Admin users** (isaac/isaac): Upload data, manage system
  - **Stakeholders** (stakeholder/stakeholder123): View-only access
- **Session management** with security features

### 📁 File Processing
- **Excel/CSV upload support** with validation
- **HMIS 105 indicator code integration**
- **Template generation** for standardized data entry
- **Bulk processing** capabilities

### 📈 Reporting
- **PDF and Excel export** functionality
- **Comprehensive reports** with executive summaries
- **Category-specific analysis** (ANC/Intrapartum/PNC)
- **Facility performance reports**

### 🏥 Health System Integration
- **Uganda MOH branding** and styling
- **District-level analysis** capabilities
- **WHO guideline compliance** indicators
- **Multi-language support** (English, Luganda, Runyankole)

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/moh-uganda/mncah-dashboard.git
cd mncah-dashboard
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services**
```bash
# Development
docker-compose up -d

# Production with monitoring
docker-compose --profile production --profile monitoring up -d
```

4. **Access the application**
- Dashboard: http://localhost:5000
- Admin login: isaac/isaac
- Stakeholder login: stakeholder/stakeholder123

### Manual Installation

#### Prerequisites
- Python 3.11+
- PostgreSQL 13+ (optional, SQLite for development)
- Redis 6+ (optional, for production)

#### Installation Steps

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up configuration**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Initialize database**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. **Create default users**
```bash
python run.py init_db
```

6. **Run the application**
```bash
python run.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `SECRET_KEY` | Flask secret key | *required* |
| `DATABASE_URL` | Database connection string | sqlite:///moh_dashboard.db |
| `REDIS_URL` | Redis connection string | *optional* |
| `UPLOAD_FOLDER` | File upload directory | uploads/ |
| `MAX_CONTENT_LENGTH` | Max file size | 16MB |

### Database Configuration

#### SQLite (Development)
```bash
DATABASE_URL=sqlite:///moh_dashboard.db
```

#### PostgreSQL (Production)
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/moh_mncah_db
```

## Usage Guide

### Data Upload Process

1. **Login** as admin user (isaac/isaac)
2. **Navigate** to Upload section
3. **Download template** with MNCAH indicator codes
4. **Fill template** with facility data
5. **Upload file** with facility information and population
6. **Review results** and validation status

### MNCAH Indicators

#### Antenatal Care (ANC)
1. ANC 1 Coverage - First visit attendance
2. ANC 1st Trimester - Early booking (≤12 weeks)
3. ANC 4 Coverage - Minimum 4 visits
4. ANC 8 Coverage - WHO 2016 standard (8 contacts)
5. IPT3 Coverage - Malaria prevention
6. HB Testing - Anemia screening
7. Iron/Folic Acid - Supplementation at first visit
8. LLIN Coverage - Bed net distribution
9. Ultrasound - Obstetric scanning

#### Intrapartum Care
1. Institutional Deliveries - Facility-based births
2. Low Birth Weight - Babies <2.5kg
3. KMC Initiation - Kangaroo Mother Care for LBW
4. Birth Asphyxia - Oxygen deprivation at birth
5. Successful Resuscitation - Emergency response
6. Fresh Stillbirth Rate - Intrapartum deaths
7. Neonatal Mortality Rate - Deaths 0-28 days
8. Perinatal Mortality Rate - Combined measure
9. Institutional MMR - Maternal mortality ratio

#### Postnatal Care (PNC)
1. Breastfeeding at 1 Hour - Early initiation
2. PNC at 24 Hours - Immediate follow-up
3. PNC at 6 Days - Early detection
4. PNC at 6 Weeks - Final assessment

### Performance Targets

| Indicator | Green (Target Met) | Yellow (Acceptable) | Red (Action Needed) |
|-----------|-------------------|-------------------|-------------------|
| ANC 1 Coverage | ≥100% | 70-99.9% | <70% |
| ANC 1st Trimester | 45-100% | 30-44.9% | <30% |
| IPT3 Coverage | ≥85% | 65-84.9% | <65% |
| Institutional Deliveries | ≥68% | 55-67.9% | <55% |
| LBW Proportion | ≤5% | 5.1-10% | >10% |
| Birth Asphyxia | ≤1% | 1.1-3% | >3% |
| PNC 24 Hours | 100% | 90-99.9% | <90% |

## API Documentation

### Authentication
```bash
POST /auth/login
Content-Type: application/json
{
  "username": "isaac",
  "password": "isaac"
}
```

### Dashboard Statistics
```bash
GET /api/dashboard/stats
Authorization: Bearer <token>
```

### Upload Data
```bash
POST /upload/process
Content-Type: multipart/form-data
Form data: facility_name, district, population, data_file
```

### Export Reports
```bash
GET /api/export/comprehensive/pdf
GET /api/export/anc/excel
```

## Development

### Project Structure
```
moh_mncah_dashboard/
├── app/
│   ├── models/          # MNCAH calculation models
│   ├── views/           # Flask blueprints
│   ├── services/        # Business logic
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS, JS, images
├── config/              # Configuration files
├── migrations/          # Database migrations
├── tests/               # Unit tests
├── uploads/             # File upload storage
└── docker-compose.yml   # Multi-service setup
```

### Adding New Indicators

1. **Update models** in `app/models/`
2. **Add validation rules** in `app/services/validation_service.py`
3. **Update templates** with new indicator display
4. **Add target thresholds** in color coding logic
5. **Update documentation**

### Running Tests
```bash
# Unit tests
python -m pytest tests/

# Coverage report
python -m pytest --cov=app tests/

# Specific test file
python -m pytest tests/test_anc_calculations.py
```

### Code Quality
```bash
# Linting
flake8 app/

# Code formatting
black app/

# Type checking
mypy app/
```

## Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching
- [ ] Configure SSL/HTTPS
- [ ] Set up backup procedures
- [ ] Configure monitoring
- [ ] Set up log rotation
- [ ] Review security headers

### Docker Deployment
```bash
# Build and deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker-compose up -d --scale worker=3

# View logs
docker-compose logs -f web
```

### Kubernetes Deployment
```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=moh-mncah-dashboard

# Access logs
kubectl logs deployment/moh-mncah-dashboard
```

## Monitoring

### Health Checks
- Application: `http://localhost:5000/api/health`
- Database: Built-in PostgreSQL health checks
- Redis: Connection and ping tests

### Metrics
- Prometheus metrics at `/metrics`
- Grafana dashboards for visualization
- Custom health system metrics

### Logging
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log rotation and archival

## Security

### Data Protection
- Health data encryption at rest and in transit
- Secure file upload with validation
- Session security with CSRF protection
- SQL injection prevention with ORM

### Access Control
- Two-tier user authentication
- Role-based permissions
- Session timeout management
- Account lockout protection

### Compliance
- GDPR-compliant data handling
- Audit logging for all actions
- Data retention policies
- Secure backup procedures

## Troubleshooting

### Common Issues

**Upload fails with "Invalid file format"**
- Ensure file is Excel (.xlsx) or CSV format
- Check file size is under 15MB
- Verify MNCAH indicator codes in template

**Database connection errors**
- Verify DATABASE_URL in .env
- Check PostgreSQL service is running
- Confirm database user permissions

**High memory usage**
- Monitor large file uploads
- Check for memory leaks in calculations
- Scale workers if needed

**Performance issues**
- Enable Redis caching
- Optimize database queries
- Scale application horizontally

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-indicator`)
3. Commit changes (`git commit -am 'Add new indicator'`)
4. Push to branch (`git push origin feature/new-indicator`)
5. Create Pull Request

### Development Guidelines
- Follow PEP 8 Python style guide
- Write unit tests for new features
- Document API changes
- Update README for new functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Technical Issues**: Create GitHub issue
- **Ministry of Health**: contact@health.go.ug
- **Documentation**: [Wiki](https://github.com/moh-uganda/mncah-dashboard/wiki)

## Acknowledgments

- Uganda Ministry of Health for requirements and testing
- World Health Organization for MNCAH guidelines
- Development partners for funding and support
- Health facility staff for data validation

---

**Ministry of Health Uganda**  
Plot 6 Lourdel Road, Wandegeya  
P.O. Box 7272, Kampala, Uganda  
Website: https://health.go.ug