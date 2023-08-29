import json
import psycopg2
import os

# Environment variables
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']

def lambda_handler(event, context):
    try:
        # Connect to the database
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = connection.cursor()
        
        # Execute SQL query
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        
        # Close connections
        cursor.close()
        connection.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Database version: {record[0]}")
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }

if __name__ == "__main__":
    lambda_handler()