# Sistema RSVP para Casamento - Versão Completa

## Overview

This is an advanced wedding RSVP (Répondez s'il vous plaît) web system built with Flask and PostgreSQL. The system features intelligent guest group synchronization, comprehensive venue management, gift registry, and a sophisticated admin panel. Guests can confirm attendance for entire family groups through a smart search interface, while administrators have full control over all aspects of the wedding event management.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11) with SQLAlchemy ORM
- **Database**: PostgreSQL with automatic schema creation and relationships
- **Authentication**: Session-based authentication with Werkzeug password hashing
- **Security**: ProxyFix middleware for proper header handling, CSRF protection through Flask's secret key
- **API Endpoints**: RESTful endpoints for dynamic guest search and group synchronization

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's built-in templating)
- **CSS Framework**: Bootstrap 5 with Replit dark theme
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla JavaScript for interactive RSVP forms and AJAX guest search
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **Interactive Features**: Multi-step RSVP process with real-time guest group loading

### Database Schema
Enhanced relational schema with five main entities:
1. **Admin**: Stores administrator credentials (id, username, password_hash, created_at)
2. **GuestGroup**: Manages guest families/groups (id, name, description, created_at)
3. **Guest**: Enhanced guest information (id, name, phone, rsvp_status, group_id, created_at, updated_at)
4. **VenueInfo**: Complete venue details (id, name, address, map_link, description, date, time, timestamps)
5. **GiftRegistry**: Gift list management (id, item_name, description, price, store_link, is_active, created_at)

## Key Components

### Enhanced Models (models.py)
- `Admin`: Handles administrator authentication data
- `GuestGroup`: Manages guest families and groups for intelligent synchronization
- `Guest`: Enhanced with phone numbers and group relationships (pendente, confirmado, nao_confirmado)
- `VenueInfo`: Complete venue management with maps and event details
- `GiftRegistry`: Gift list with pricing, store links, and activation status

### Advanced Routes (routes.py)
- **Public routes**: Enhanced home page with venue info and gift preview, intelligent RSVP with group search
- **Admin routes**: Comprehensive dashboard, group management, venue configuration, gift registry management
- **API endpoints**: Guest search with group synchronization (`/search_guest`)
- **Session management**: Secure admin authentication with discrete access

### Enhanced Templates
- `base.html`: Updated navigation with gift registry link and admin menu expansion
- `index.html`: Integrated venue information and gift registry preview
- `rsvp.html`: Multi-step intelligent form with AJAX guest search and group selection
- `rsvp_success.html`: Enhanced success page for multiple guests with detailed status
- `gifts.html`: Public gift registry with store links and elegant presentation
- `admin_dashboard.html`: Enhanced with group management, venue, and gift registry access
- `admin_groups.html`: Complete group management interface
- `admin_venue.html`: Venue information management with live preview
- `admin_gifts.html`: Full gift registry administration
- `admin_login.html`: Discrete admin access

### Enhanced Static Assets
- `style.css`: Wedding theme with improved responsiveness, hover effects, and group interface styling

## Enhanced Data Flow

1. **Guest Flow** (Intelligent Group Synchronization):
   - Guest visits enhanced home page with venue info and gift preview
   - Uses smart search to find their name
   - System automatically displays all guests in their group/family
   - Guest confirms attendance for each person individually
   - System updates all selected guests' statuses simultaneously
   - Enhanced success page shows detailed confirmation summary

2. **Admin Flow** (Comprehensive Management):
   - Admin accesses discrete login (URL or small footer link)
   - Dashboard shows enhanced statistics and quick access to all management areas
   - **Group Management**: Create and organize guest families/groups
   - **Guest Management**: Add guests with phone numbers and group assignments
   - **Venue Management**: Configure complete event location details with maps
   - **Gift Registry**: Manage gift list with prices, descriptions, and store links
   - Real-time updates across all modules with data integrity

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

### July 05, 2025 - Major System Enhancement
- **Enhanced Database Schema**: Added GuestGroup, VenueInfo, and GiftRegistry models with relationships
- **Intelligent Guest Synchronization**: Implemented smart guest search with automatic family/group display
- **Multi-Step RSVP Process**: AJAX-powered guest search with individual confirmation options for groups
- **Comprehensive Admin Panel**: Added group management, venue configuration, and gift registry administration
- **Venue Management**: Complete venue information system with maps and event details
- **Gift Registry**: Full gift list management with store links, pricing, and activation status
- **Enhanced UI/UX**: Improved responsive design with intelligent forms and better navigation
- **Phone Number Support**: Added optional phone field for all guests
- **Discrete Admin Access**: Non-intrusive admin login placement for better public interface
- **PostgreSQL Migration**: Upgraded from SQLite to PostgreSQL for better scalability
- **API Endpoints**: Added REST endpoints for dynamic guest search and group synchronization

### July 05, 2025 - Initial Setup
- Basic RSVP system with Flask and SQLite
- Simple guest management and admin authentication