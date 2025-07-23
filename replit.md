# Wedding RSVP System

## Project Overview
A complete wedding RSVP web application built with Flask and SQLAlchemy. This system allows couples to manage guest confirmations, organize guests into groups, maintain a gift registry, and send WhatsApp notifications to guests.

## Architecture
- **Backend**: Flask web framework with SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development fallback)
- **Frontend**: Server-side rendered HTML templates with Bootstrap
- **Messaging**: Twilio WhatsApp integration for guest notifications
- **Deployment**: Replit with Gunicorn WSGI server

## Key Features
- Guest management with group organization
- RSVP confirmation system
- Wedding gift registry
- Venue information display
- WhatsApp messaging integration
- Admin dashboard for wedding management
- Responsive design for mobile devices

## Models
- **Admin**: Administrative user authentication
- **Guest**: Wedding guest information and RSVP status
- **GuestGroup**: Organize guests into families/friend groups
- **VenueInfo**: Wedding venue details and event information
- **GiftRegistry**: Wedding gift wish list with store links

## Current State
- Project migrated from Replit Agent to Replit environment
- Using SQLite fallback database (configured for PostgreSQL compatibility)
- Admin credentials: admin/admin123
- Sample data populated for demonstration

## Recent Changes
- 2025-07-23: Migration to Replit environment completed successfully
- Fixed Flask application structure and database initialization
- Added responsive button layout (side by side on desktop, stacked on mobile)
- Security enhancements: Removed hardcoded external database references
- Updated workflow configuration for Gunicorn deployment

## User Preferences
- Brazilian Portuguese interface
- Simple, elegant wedding theme
- Mobile-first responsive design
- WhatsApp integration for guest communication

## Development Notes
- Uses Flask development guidelines for Replit
- Secret key configured via SESSION_SECRET environment variable
- Database URL configurable via DATABASE_URL environment variable
- Proper security practices implemented for password hashing