"""Test SQL Server connection script."""
import os
import pyodbc
import sqlalchemy
from dotenv import load_dotenv
from urllib.parse import quote_plus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sql_server_connection():
    """Test connection to SQL Server database."""
    # Load environment variables
    load_dotenv()
    
    # Get connection details
    server = os.getenv('MYSQL_HOST')  # Actually SQL Server host
    database = os.getenv('MYSQL_DATABASE')
    username = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    port = os.getenv('MYSQL_PORT', '1433')
    
    logger.info("🔍 Testing SQL Server Connection...")
    logger.info(f"Server: {server}")
    logger.info(f"Database: {database}")
    logger.info(f"Username: {username}")
    logger.info(f"Port: {port}")
    
    # Test 1: Raw pyodbc connection
    try:
        logger.info("📡 Testing raw pyodbc connection...")
        
        # Connection string for SQL Server
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        # Test query
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        logger.info(f"✅ Raw connection successful!")
        logger.info(f"SQL Server Version: {version[:100]}...")
        
        # List tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        logger.info(f"Found {len(tables)} tables in database")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        connection.close()
        logger.info("✅ Raw pyodbc test completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Raw pyodbc connection failed: {e}")
        return False
    
    # Test 2: SQLAlchemy connection
    try:
        logger.info("🔗 Testing SQLAlchemy connection...")
        
        # URL encode password for special characters
        encoded_password = quote_plus(password)
        
        # SQLAlchemy connection string for SQL Server
        connection_url = (
            f"mssql+pyodbc://{username}:{encoded_password}@{server}:{port}/{database}"
            f"?driver=ODBC+Driver+18+for+SQL+Server"
            f"&Encrypt=yes"
            f"&TrustServerCertificate=no"
        )
        
        engine = sqlalchemy.create_engine(
            connection_url,
            pool_timeout=20,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1 as test")).fetchone()
            logger.info(f"✅ SQLAlchemy connection successful! Test result: {result[0]}")
            
            # Test table existence
            result = conn.execute(sqlalchemy.text("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)).fetchone()
            logger.info(f"Database contains {result[0]} tables")
        
        logger.info("✅ SQLAlchemy test completed successfully")
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ SQLAlchemy connection failed: {e}")
        return False
    
    # Test 3: Check for mg_ tables
    try:
        logger.info("🔍 Checking for mg_ prefixed tables...")
        
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        # Check for mg_ tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_NAME LIKE 'mg_%'
            ORDER BY TABLE_NAME
        """)
        mg_tables = cursor.fetchall()
        
        if mg_tables:
            logger.info(f"Found {len(mg_tables)} mg_ tables:")
            for table in mg_tables:
                logger.info(f"  ✅ {table[0]}")
        else:
            logger.info("⚠️  No mg_ tables found - may need to run migration")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"❌ mg_ table check failed: {e}")
    
    return True

def test_flask_app_connection():
    """Test Flask app database connection."""
    try:
        logger.info("🌐 Testing Flask app database connection...")
        
        from app import create_app
        from utils.database import db
        
        app = create_app()
        with app.app_context():
            # Test database connection
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT 1")).fetchone()
                logger.info("✅ Flask app database connection successful!")
                
                # Check configuration
                logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
                
    except Exception as e:
        logger.error(f"❌ Flask app connection failed: {e}")
        return False
    
    return True

def check_odbc_drivers():
    """Check available ODBC drivers."""
    try:
        logger.info("🔍 Checking available ODBC drivers...")
        drivers = pyodbc.drivers()
        
        sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
        if sql_server_drivers:
            logger.info("✅ SQL Server ODBC drivers found:")
            for driver in sql_server_drivers:
                logger.info(f"  - {driver}")
        else:
            logger.error("❌ No SQL Server ODBC drivers found!")
            logger.info("Available drivers:")
            for driver in drivers:
                logger.info(f"  - {driver}")
        
    except Exception as e:
        logger.error(f"❌ Error checking ODBC drivers: {e}")

if __name__ == '__main__':
    logger.info("🚀 Starting SQL Server connection tests...")
    
    # Check ODBC drivers first
    check_odbc_drivers()
    print("-" * 50)
    
    # Test raw connection
    if test_sql_server_connection():
        print("-" * 50)
        # Test Flask app connection
        test_flask_app_connection()
    
    logger.info("🏁 Connection tests completed!")