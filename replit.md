# Laboratory Management System

## Overview

This is a modern, full-stack laboratory management system designed for research environments. The application provides a comprehensive suite of tools for managing laboratory workflows, tracking experiments, maintaining equipment registries, and conducting statistical analyses. It combines a React frontend with a Node.js/Express backend, utilizing PostgreSQL for data persistence and featuring both local data storage capabilities and server-side data management.

The system serves as a digital replacement for traditional paper-based lab notebooks and manual tracking systems, offering real-time data entry, search capabilities, and automated statistical analysis tools specifically tailored for scientific research workflows.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The frontend is built using React 18 with TypeScript, utilizing a modern component-based architecture. Key architectural decisions include:

- **Component Library**: Implements shadcn/ui components with Radix UI primitives for accessibility and consistent design
- **Styling**: Uses Tailwind CSS for utility-first styling with a custom design system based on CSS variables
- **State Management**: Employs TanStack Query (React Query) for server state management, eliminating the need for complex global state solutions
- **Routing**: Uses Wouter for lightweight client-side routing
- **Form Handling**: Integrates React Hook Form with Zod for type-safe form validation
- **Build Tool**: Vite for fast development and optimized production builds

The frontend follows a page-based architecture with dedicated routes for each laboratory tool (notebook, animal logs, experiment scheduler, etc.), supported by reusable UI components and utility functions.

### Backend Architecture
The backend uses Node.js with Express.js in a RESTful API architecture:

- **Framework**: Express.js with TypeScript for type safety
- **Database Integration**: Drizzle ORM for type-safe database operations with PostgreSQL
- **File Handling**: Multer middleware for CSV file uploads and processing
- **API Design**: RESTful endpoints with consistent error handling and response formatting
- **Statistical Computing**: Server-side statistical analysis using basic mathematical functions for t-tests, ANOVA, and Kruskal-Wallis tests

The backend implements a service layer pattern with separate route handlers, storage abstractions, and utility functions for statistical computations.

### Data Storage Solutions
The system employs a hybrid data storage approach:

- **Primary Database**: PostgreSQL with Drizzle ORM for structured data persistence
- **Schema Management**: Shared TypeScript schemas between frontend and backend using Zod for validation
- **Local Storage**: Browser localStorage for offline functionality and temporary data caching
- **File Exports**: CSV generation and download capabilities for data portability
- **Migration Support**: Drizzle migrations for database schema evolution

### Authentication and Authorization
Currently implements a basic user system with:
- User registration and authentication endpoints
- Session-based authentication (preparation for future implementation)
- Role-based access patterns in the data model
- Placeholder authentication UI components

### Development and Deployment Architecture
- **Development Environment**: Vite dev server with HMR and error overlay
- **Build Process**: ESBuild for server compilation, Vite for client bundling
- **Environment Configuration**: Environment-based configuration for database connections and development tools
- **Error Handling**: Comprehensive error boundaries and toast notifications for user feedback

The system prioritizes developer experience with TypeScript throughout, automated type generation from database schemas, and hot reload capabilities during development.

## External Dependencies

### Database Services
- **Neon Database**: Serverless PostgreSQL database service (@neondatabase/serverless)
- **Connection Management**: PostgreSQL session store (connect-pg-simple) for session persistence

### UI and Component Libraries
- **Design System**: Radix UI components (@radix-ui/*) for accessible, unstyled UI primitives
- **Styling**: Tailwind CSS with custom configuration and design tokens
- **Icons**: Lucide React for consistent iconography
- **Carousel**: Embla Carousel for media presentation components

### Development and Build Tools
- **Build System**: Vite with React plugin and runtime error modal
- **TypeScript**: Full TypeScript support with strict configuration
- **Linting**: PostCSS with Autoprefixer for CSS processing
- **Development**: Replit-specific plugins for cloud development environment

### Data Processing and Analysis
- **Validation**: Zod for runtime type validation and schema generation
- **CSV Processing**: Multer for file uploads, custom CSV parsing and generation utilities
- **Statistical Analysis**: Custom statistical functions for common laboratory analyses (t-tests, ANOVA, non-parametric tests)

### State Management and API
- **Server State**: TanStack React Query for caching, synchronization, and background updates
- **Client State**: React hooks and local storage utilities
- **HTTP Client**: Fetch API with custom request/response wrappers
- **Form Management**: React Hook Form with Zod resolvers for validated forms

### Utility Libraries
- **Class Management**: clsx and tailwind-merge for conditional styling
- **Date Handling**: date-fns for date manipulation and formatting
- **Developer Experience**: Various development utilities for error handling, debugging, and development workflow optimization

The application is designed to work in both connected and offline modes, with local storage fallbacks for critical functionality and CSV export capabilities for data portability.