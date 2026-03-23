#!/usr/bin/env python3
"""
Database initialization script
Run this to create all tables and initialize the database
"""

import logging
from database import init_db, engine
from models.cve import CVE
from models.user import User
from models.audit_log import AuditLog
from models.subscription import Subscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with schema"""
    logger.info("Initializing database...")
    
    try:
        # Create all tables
        init_db()
        logger.info("✓ Database schema created successfully")
        
        # Verify tables exist
        inspector = __import__('sqlalchemy').inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"✓ Created tables: {', '.join(tables)}")
        
        logger.info("✓ Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    init_database()
