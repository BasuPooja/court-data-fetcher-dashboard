import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 🟡 Replace with your actual PostgreSQL credentials
# SQLALCHEMY_DATABASE_URI = 'postgresql://postgresql:Post%401234@localhost:5432/courtData'

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Post%401234@localhost:5432/courtData'


SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'your_secret_key_here'
