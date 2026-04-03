import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

#Try to connect to the RDS, if fails connect to the local database 
def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("RDS_HOST"),
        port=os.getenv("RDS_PORT"),
        database=os.getenv("RDS_NAME"),    
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD",),
    )
    return conn