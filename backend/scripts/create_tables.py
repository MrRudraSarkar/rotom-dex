# sys - built into python, lets us modify the Python path at runtime
import sys

# os - lets us navigate the filesystem to build the correct path
import os

# our script lives in backend/scripts/ but our models live in backend/
# without this, python won't find database.py or models.py when we import them
# __file__ is the path to this script
# os.path.dirname goes up one level to scripts/ , then up again to backend/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# engine - the active connection to PostgreSQL
# Base - holds metadata about all tables defined in models.py
from database import engine, Base

# importing models registers all the table classes with Base
# without this import, Base.metadata won't know any tables exist
# even though we don't use 'models' directly, this line is essential
import models

# create_all looks at Base.metadata, finds all registered tables,
# and issues CREATE TABLE statements to PostgreSQL for any that don't exist yet
# it's safe to run multiple times - it won't overwrite the existing tables
Base.metadata.create_all(bind=engine)

print("All tables created successfully")