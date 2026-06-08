"""Application configuration and settings."""

import os
from pathlib import Path
from datetime import timedelta

# Get the root directory of the project
BASE_DIR = Path(__file__).parent.parent.absolute()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR}/controle-financeiro.db"
)

# SQLAlchemy configuration
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT/Authentication configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(hours=24)
JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=7)

# API Configuration
API_TITLE = "Controle Financeiro API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Financial management API for tracking accounts, payments, subscriptions, and investments"

# CORS Configuration
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5000"
).split(",")

# Security
BCRYPT_LOG_ROUNDS = 12

# Pagination defaults
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if ENVIRONMENT == "production" else "DEBUG")
