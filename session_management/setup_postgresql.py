import os
import psycopg2
import subprocess
import sys

# Database configuration
DB_NAME = 'yourdb'
DB_USER = 'imperiouser'
DB_PASSWORD = ''  # No password needed
DB_PORT = '5432'  # Default PostgreSQL port
DB_HOST = 'localhost'
SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

def create_postgresql_database():
    try:
        # Connect to the default 'postgres' database to perform initial setup
        conn = psycopg2.connect(dbname='postgres', user='postgres', host=DB_HOST, port=DB_PORT)
        conn.autocommit = True
        cur = conn.cursor()

        # Create user without a password
        cur.execute(f"CREATE USER {DB_USER};")
        # Create database owned by the new user
        cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
        # Grant privileges
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")

        cur.close()
        conn.close()
        print(f"Database '{DB_NAME}' and user '{DB_USER}' created successfully without a password.")
    except Exception as e:
        print(f"Error creating database or user: {e}")

if __name__ == "__main__":
    create_postgresql_database()
