# python-dotenv library - loads variables from our .env file and system environment into the os.environ dictionary
# os.environ -  a dictionary like object that holds all the environment variables pulled in from the .env file and the system environment variables
from dotenv import load_dotenv

# os module - built into Python, let's us read environment variables
import os

# create_engine - creates the connection pool to PostgreSQL
# think of it as the phone line between our Python code and the PostgreSQL database
from sqlalchemy import create_engine

# sessionmaker - a factoryh that creates individual database sessions
# each session is like a single conversation with the database
# DeclarativeBse - the base class that all our models will inherit from
# it's what makes SQLAlchemy aware of our tables
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# read the .env file and loads all the variables in os.environ
load_dotenv()

# fetch the database connection string/url from the .env file
# format: postgrsql://username:password@host:port/database_name
# for our usecase we will use os.getnv to load the value from the os.environ 
# but a good practice is to use os.environ.get() when the variable absolutely must exist
DATABASE_URL = os.getenv("DATABASE_URL")

# create the engine using our connection url
# the engine manages the actual connection pool to PostgreSQL
# it doesn't open a connection immediately - it waits until we need one
engine = create_engine(DATABASE_URL)

# create a session factory bound to our engine
# autocommit=False - we manually control when changes are saved
# autoflush=False - changes aren't sent to the DB until we explicitly commit
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# define our Base class by inheriting from DeclarativeBase
# all models (tables) in models.py will inherit from this Base
# this is how SQLAlchemy knows which classes represent database tables
class Base(DeclarativeBase):
    pass

# this is the FastAPI dependency - it will be injected into route functions
# yield gives the session to the route, then cleanup runs after the request
# the try/finally ensures the session is ALWAYS closed, even if an error occurs
def get_db():
    db = SessionLocal()
    try:
        yield db       # hands the session to the route function 
    finally:
        db.close()     # always close the session when request is done

