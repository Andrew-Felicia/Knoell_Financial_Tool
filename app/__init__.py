

from flask import Flask, render_template
from flask_login import LoginManager


#handles database migrations (when you change models.py, this tool updates the real PostgreSQL tables to match)
from flask_migrate import Migrate

# imports the database object and User class from models.py. 
# The dot in .models means "from the same folder as this file"
from .models import db, User

from config import DevelopmentConfig, ProductionConfig
import os

login_manager = LoginManager()


#create_app() is called
    #    │
    #    ├── creates Flask app object
    #    ├── loads config (dev or prod settings)
    #    ├── connects SQLAlchemy to PostgreSQL
    #    ├── connects LoginManager (handles sessions)
    #    ├── connects Migrate (handles DB changes)
    #    ├── tells LoginManager where the login page is
    #    ├── tells LoginManager how to find a user by ID
    #    ├── registers auth routes   (/login, /logout)
    #    ├── registers table routes  (/tables/...)
    #    ├── registers excel routes  (/excel/...)
    #    └── returns the fully configured app
#Think of create_app() as the assembly line — it takes all the separate pieces (database, login system, routes)
# and wires them together into one working application.
def create_app(env=None):
    """
    Create and configure the Flask app. env: 'development' or 'production'.
    You can call create_app("development") or create_app("production") to get different versions.
    """

    
    app = Flask(__name__)
    #If env was passed in (create_app("production")), use that
    # Otherwise check the FLASK_ENV environment variable
    # If neither exists, default to "development"
    env = env or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(ProductionConfig if env == "production" else DevelopmentConfig)

    # tells SQLAlchemy "use this Flask app's database URL to connect to PostgreSQL"
    db.init_app(app)
    #tells Flask-Login "use this Flask app to manage sessions and cookies"
    login_manager.init_app(app)
    #connects Flask-Migrate so it can compare your models.py against the real 
    # database and generate migration scripts when things change
    Migrate(app, db)

    #If someone tries to visit a protected page without being logged in, Flask-Login automatically redirects them. This line tells it where to redirect — to the login function inside the auth blueprint (which you'll write in routes/auth.py).
    # Without this line, Flask-Login wouldn't know where your login page is and would crash
    login_manager.login_view = "auth.login"


    #When a user logs in, Flask stores their id in a cookie in the browser (like user_id=5). On every future request, Flask reads that cookie and needs to look up the full User object from the database.
    # This function tells Flask-Login exactly how to do that lookup:

    # user_id comes in as a string from the cookie (e.g. "5")
    # int(user_id) converts it to an integer (5)
    # User.query.get(5) fetches that user from the database
    # Returns the full User object so the rest of the app can use current_user.username etc.

    # Flask-Login calls this function automatically on every single request — you never call it yourself.
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    #Registering blueprints
    #What is a blueprint? A blueprint is a mini Flask app — a group of related routes bundled together.
    # Instead of putting all your routes in one giant file, you split them up:
    #auth_bp    handles:  /login, /logout, /register
    # tables_bp  handles:  /tables/, /tables/create, /tables/delete/5
    # excel_bp   handles:  /excel/import, /excel/export/5
    from .routes.auth import auth_bp
    from .routes.tables import tables_bp
    from .routes.excel import excel_bp
    app.register_blueprint(auth_bp)
    #The url_prefix adds a prefix to every route in that blueprint automatically. 
    # So if tables_bp has a route /create, the full URL becomes /tables/create.
    app.register_blueprint(tables_bp, url_prefix="/tables")
    app.register_blueprint(excel_bp,  url_prefix="/excel")

    @app.route("/")
    def home():
        return render_template("home.html")

    return app