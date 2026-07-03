# TonerTrack - Printer Toner Inventory System with Security Features

A full-featured inventory management system with real-time monitoring, smart alerts, and secure backend architecture. Built with security and DevSecOps practices in mind.

## Tech Stack & Security Focus
- **Backend:** Python + FastAPI
- **Frontend:** TypeScript + React
- **Database:** SQLite / PostgreSQL
- **Security:** JWT Authentication, Input Validation, Rate Limiting, Structured Logging
- **Tools:** Docker, GitHub Actions

## Key Features & Security Implementation
- Role-based access control (Admin, Staff)
- Real-time toner level monitoring and low-stock alerts
- Secure API endpoints with proper authentication
- Input sanitization to prevent injection attacks
- Audit logging for all critical actions

## Architecture
The application follows a clean, layered architecture:
- API Layer with FastAPI
- Service Layer for business logic
- Repository Layer for data access
- Security middleware for request validation

## Local Setup
```bash
git clone https://github.com/FADAREC/Tonertrack.git
cd Tonertrack
pip install -r requirements.txt
uvicorn main:app --reload
Frontend:
Bashcd frontend
npm install
npm run dev
```


## Security Practices Applied

- JWT token authentication with expiration
- Password hashing with bcrypt
- CORS protection
- Environment variable management for secrets
- Basic rate limiting on auth endpoints

## Future Enhancements (DevSecOps Roadmap)

- GitHub Actions CI/CD with security scanning (Bandit, Trufflehog)
- Docker container security
- Integration with AI-based anomaly detection for inventory fraud

## Live Demo: ``Print Track Backend Docs``
