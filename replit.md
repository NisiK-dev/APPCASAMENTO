# Wedding RSVP System

## Overview

This is a comprehensive wedding RSVP (Répondez s'il vous plaît) management system built with Flask and SQLAlchemy. The application provides a complete solution for managing wedding guests, venue information, gift registries, and WhatsApp communications. It features both a public-facing interface for guests to confirm their attendance and an administrative dashboard for managing all aspects of the wedding event.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with declarative base model
- **Authentication**: Session-based authentication with password hashing using Werkzeug
- **Database**: Configurable via environment variable (DATABASE_URL) - supports PostgreSQL, SQLite, etc.
- **Session Management**: Flask sessions with configurable secret key
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla JavaScript for interactive features
- **Responsive Design**: Mobile-first approach using Bootstrap's grid system

### Database Schema
The system uses a relational database with the following key entities:
- **Admin**: Administrative users with hashed passwords
- **GuestGroup**: Groups of related guests (families, couples)
- **Guest**: Individual guests with RSVP status and group associations
- **VenueInfo**: Wedding venue details and event information
- **GiftRegistry**: Wedding gift registry items

## Key Components

### Models (models.py)
- **Admin Model**: Stores administrative login credentials with password hashing
- **GuestGroup Model**: Organizes guests into logical groups (families, couples)
- **Guest Model**: Individual guest records with RSVP status tracking
- **VenueInfo Model**: Wedding venue and event details
- **GiftRegistry Model**: Gift registry items (partially implemented)

### Routes and Views
- **Public Routes**: Home page, RSVP confirmation, gift registry viewing
- **Administrative Routes**: Login/logout, dashboard, guest management, venue management
- **API Endpoints**: Guest search, RSVP updates, bulk operations

### Authentication System
- Session-based authentication for administrators
- Password hashing using Werkzeug's security utilities
- Default admin account creation on first run
- Session protection for administrative functions

### WhatsApp Integration
- Twilio-based WhatsApp messaging system
- Bulk message sending capabilities
- Guest notification system
- Configurable message templates

## Data Flow

### Guest RSVP Process
1. Guest visits public RSVP page
2. Guest searches for their name in the system
3. System returns guest and associated group members
4. Guest confirms/declines attendance for each person
5. System updates database and shows confirmation

### Administrative Workflow
1. Admin logs into secure dashboard
2. Manages guest lists and groups
3. Updates venue and event information
4. Sends WhatsApp notifications to guests
5. Monitors RSVP statistics and responses

### Group-Based Guest Management
- Guests are organized into logical groups (families, couples)
- When one guest searches, all group members are displayed
- Individual RSVP status tracking within groups
- Bulk operations possible on guest groups

## External Dependencies

### Required Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Werkzeug**: Security utilities and middleware
- **Twilio**: WhatsApp messaging service

### Frontend Dependencies (CDN)
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6**: Icon library

### Environment Variables
- `DATABASE_URL`: Database connection string
- `SESSION_SECRET`: Session encryption key
- `TWILIO_ACCOUNT_SID`: Twilio account identifier
- `TWILIO_AUTH_TOKEN`: Twilio authentication token
- `TWILIO_PHONE_NUMBER`: Twilio WhatsApp number

## Deployment Strategy

### Configuration
- Environment-based configuration for database and external services
- Proxy-ready with ProxyFix middleware
- Production-ready session management
- Automatic database table creation on startup

### Database Management
- Automatic table creation on application startup
- Default admin user creation if none exists
- Database connection pooling for performance
- Support for multiple database backends through SQLAlchemy

### Security Considerations
- Password hashing for all admin accounts
- Session-based authentication
- Environment variable configuration for sensitive data
- SQL injection prevention through ORM usage

### Scalability Features
- Database connection pooling
- Modular route organization
- Configurable external service integration
- Responsive frontend design for multiple devices

The system is designed to be easily deployable on platforms like Replit, Heroku, or any environment that supports Flask applications, with minimal configuration required through environment variables.

## Recent Changes

### July 09, 2025 - Migration to Replit Environment
- **Migration Completed**: Successfully migrated from Replit Agent to standard Replit environment
- **PostgreSQL Integration**: Configured PostgreSQL database with automatic environment variables
- **Security Enhancements**: Proper session secret configuration for production readiness
- **Documentation**: Created comprehensive README.md with setup, deployment, and troubleshooting guides
- **Replit Deployment Ready**: Application now fully compatible with Replit Deployments