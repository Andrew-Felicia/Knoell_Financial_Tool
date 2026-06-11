

import os
from dotenv import load_dotenv

#load .env file.
load_dotenv()

# This is a plain Python class that acts as a container for all your app settings.
#  Flask will read from this class to configure itself.
class Config:
    """Base settings shared by all environments."""
    SECRET_KEY = os.environ["SECRET_KEY"] #Flask uses this to sign cookies and sessions. 
                                          #If someone gets this key they can fake logins

    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]  #tells SQLAlchemy exactly which 
                                                          #database to connect to

    SQLALCHEMY_TRACK_MODIFICATIONS = False  #turns off a SQLAlchemy feature that watches 
                                            #every object change in memory. It's not needed 
                                            #and wastes RAM, so we always turn it off

    CELERY_BROKER_URL = os.environ["REDIS_URL"] # tells Celery where Redis is, so it knows
                                                #where to send background jobs

    UPLOAD_FOLDER = os.environ["UPLOAD_FOLDER"] # the folder path where uploaded Excel files will be saved temporarily

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
                                           # limits upload size to 50MB. The math: 50 × 1024 = 51200 KB × 1024 = 52,428,800 bytes
                                           #  = 50MB. Flask will automatically reject any file larger than this.


# Both classes inherit everything from Config (all the settings above), and then add or override a 
# couple of settings depending on where the app is running.

# DevelopmentConfig (your laptop):
# DEBUG = True — Flask shows detailed error pages with full stack traces when something crashes. 
# Very useful when coding.
# SQLALCHEMY_ECHO = True — every SQL query gets printed to your terminal. Helps you see exactly what the 
# database is doing.

# ProductionConfig (the live server):
# DEBUG = False — never show error details to real users. A crash just shows a generic "500 error" page. 
# This is a security requirement — stack traces can reveal your file structure and code to attackers.
# SQLALCHEMY_ECHO = False — no SQL printing. The live server doesn't need it and it would just slow things down.


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True   # prints SQL to console — great for debugging




class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False