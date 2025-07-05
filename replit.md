# Sistema RSVP para Casamento

## Overview

This is a complete wedding RSVP (Répondez s'il vous plaît) web system built with Flask and SQLite. The system allows wedding guests to confirm their attendance through a public interface, while administrators can manage the guest list and view confirmation statistics through a secure admin dashboard.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python) with SQLAlchemy ORM
- **Database**: SQLite with automatic schema creation
- **Authentication**: Session-based authentication with Werkzeug password hashing
- **Security**: ProxyFix middleware for proper header handling, CSRF protection through Flask's secret key

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's built-in templating)
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla JavaScript for interactive elements
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

### Database Schema
Two main entities:
1. **Admin**: Stores administrator credentials (id, username, password_hash, created_at)
2. **Guest**: Stores guest information and RSVP status (id, name, rsvp_status, created_at, updated_at)

## Key Components

### Models (models.py)
- `Admin`: Handles administrator authentication data
- `Guest`: Manages guest information with RSVP status tracking (pendente, confirmado, nao_confirmado)

### Routes (routes.py)
- Public routes: Home page, guest RSVP interface
- Admin routes: Login, dashboard, guest management
- Session management for admin authentication

### Templates
- `base.html`: Main layout with navigation and flash message handling
- `index.html`: Landing page with options for guests and admin
- `rsvp.html`: Guest confirmation form
- `rsvp_success.html`: Confirmation success page
- `admin_login.html`: Administrator login form
- `admin_dashboard.html`: Admin panel for guest management

### Static Assets
- `style.css`: Custom styling for wedding theme with gradients and animations

## Data Flow

1. **Guest Flow**:
   - Guest visits public RSVP page
   - Enters full name and confirmation choice
   - System validates name against guest list
   - Updates guest status in database
   - Shows confirmation message

2. **Admin Flow**:
   - Admin logs in with credentials
   - Accesses dashboard with guest statistics
   - Can add, edit, or remove guests
   - Views real-time RSVP status updates

## External Dependencies

### Python Packages
- Flask: Web framework
- Flask-SQLAlchemy: ORM for database operations
- Werkzeug: Password hashing and security utilities

### Frontend Dependencies (CDN)
- Bootstrap 5: UI framework with dark theme
- Font Awesome 6.0: Icon library

## Deployment Strategy

### Environment Configuration
- `SESSION_SECRET`: Environment variable for Flask secret key (fallback: "wedding-rsvp-secret-key-2025")
- `DATABASE_URL`: Database connection string (fallback: SQLite local file)

### Database Setup
- Automatic table creation on application startup
- Default admin user creation (username: 'admin', password: 'admin123')
- Connection pooling with 300-second recycle time

### Server Configuration
- WSGI application with ProxyFix for proper header handling
- Debug mode enabled for development
- Host: 0.0.0.0, Port: 5000

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 05, 2025. Initial setup