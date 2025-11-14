#!/bin/bash
# Database Migration Script - Grade S++
# Usage: ./scripts/db-migrate.sh [command] [args]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_header() {
    echo ""
    echo "=================================================="
    echo "  $1"
    echo "=================================================="
    echo ""
}

# Commands
case "$1" in
    "init")
        print_header "Initialize Alembic"
        alembic init alembic
        print_success "Alembic initialized"
        ;;
    
    "generate")
        if [ -z "$2" ]; then
            print_error "Please provide a migration message"
            echo "Usage: ./scripts/db-migrate.sh generate 'migration message'"
            exit 1
        fi
        print_header "Generate Migration: $2"
        alembic revision --autogenerate -m "$2"
        print_success "Migration generated"
        print_warning "Please review the migration file before applying!"
        ;;
    
    "upgrade")
        print_header "Apply Migrations"
        alembic upgrade head
        print_success "Migrations applied"
        ;;
    
    "downgrade")
        STEPS="${2:--1}"
        print_header "Rollback Migrations"
        print_warning "Rolling back $STEPS migration(s)"
        alembic downgrade "$STEPS"
        print_success "Rollback completed"
        ;;
    
    "current")
        print_header "Current Migration"
        alembic current
        ;;
    
    "history")
        print_header "Migration History"
        alembic history --verbose
        ;;
    
    "reset")
        print_header "Reset Database"
        print_warning "This will drop all tables and reapply migrations"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            alembic downgrade base
            alembic upgrade head
            print_success "Database reset completed"
        else
            print_error "Reset cancelled"
        fi
        ;;
    
    *)
        echo "Database Migration Tool - SaaS-IA MVP"
        echo ""
        echo "Usage: ./scripts/db-migrate.sh [command] [args]"
        echo ""
        echo "Commands:"
        echo "  init                  Initialize Alembic"
        echo "  generate 'message'    Generate new migration"
        echo "  upgrade               Apply all pending migrations"
        echo "  downgrade [-1]        Rollback migrations (default: -1)"
        echo "  current               Show current migration"
        echo "  history               Show migration history"
        echo "  reset                 Reset database (downgrade + upgrade)"
        echo ""
        echo "Examples:"
        echo "  ./scripts/db-migrate.sh generate 'add user table'"
        echo "  ./scripts/db-migrate.sh upgrade"
        echo "  ./scripts/db-migrate.sh downgrade -1"
        ;;
esac

