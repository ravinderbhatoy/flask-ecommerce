import os
import secrets
from dotenv import load_dotenv
load_dotenv()

# Generate a random secret key
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

# Database settings
MYSQL_HOST = os.environ.get('RDS_HOSTNAME')
MYSQL_USER = os.environ.get('RDS_USERNAME')
MYSQL_PASSWORD = os.environ.get('RDS_PASSWORD')
MYSQL_DB = os.environ.get('RDS_DB_NAME')
MYSQL_PORT = int(os.environ.get('RDS_PORT'))
print(MYSQL_PASSWORD, MYSQL_USER)
# File upload settings
UPLOAD_FOLDER = 'static/images'