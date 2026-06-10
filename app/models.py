#ORM
#Describes the shape of your database in Python — so you never have to write SQL by hand.


from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin

#never store plain text passwords. These functions scramble the password before saving, 
# and safely check it on login
from werkzeug.security import generate_password_hash, check_password_hash

#creates the SQLAlchemy instance.
db = SQLAlchemy()

#set user table in postgretable.
# Each class = one database table. Each instance of the class = one row in that table.

# @param : db.Model — tells SQLAlchemy this class represents a database table
# @param : UserMixin — adds these properties automatically so Flask-Login works: 
# is_authenticated, is_active, is_anonymous, get_id()
class User(UserMixin, db.Model):
    """A person who can log in."""

    # sets the actual table name in PostgreSQL. Without this SQLAlchemy would guess a name, 
    # so always set it explicitly.
    __tablename__ = "users"

    #primary_key=True — this is the unique ID for each row. PostgreSQL auto-increments it (1, 2, 3...)
    #every time you add a new user
    id         = db.Column(db.Integer, primary_key=True)

    #unique=True — no two users can have the same username or email. PostgreSQL will reject duplicates.
    #nullable=False — this field is required. PostgreSQL will reject any row that tries to leave it empty.
    username   = db.Column(db.String(100), unique=True, nullable=False)
    email      = db.Column(db.String(200), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(50), default="user")  # "user" or "admin"
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    #The real password never gets stored anywhere. Even if someone steals your database, 
    #they only get the scrambled hash — useless without the original.
    #call this when creating or changing a password.
    def set_password(self, raw): self.password = generate_password_hash(raw)
    #call this on login.
    def check_password(self, raw): return check_password_hash(self.password, raw)


class ExcelTable(db.Model):
    """Metadata about one imported or manually created table."""
    __tablename__ = "excel_tables"

    #db.Text — unlimited length text. Used for description since it could be long. 
    #No nullable=False so description is optional.
    id          = db.Column(db.Integer, primary_key=True)

    name        = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # columns stored as JSON: [{"name": "col1", "type": "text"}, ...]
    columns     = db.Column(db.JSON, nullable=False)
    row_count   = db.Column(db.Integer, default=0)

    #ForeignKey("users.id") — links this table to the User who created it. 
    # The value stored here is the user's id number. PostgreSQL enforces this — 
    # you can't set created_by to a user ID that doesn't exist.
    created_by  = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                        onupdate=lambda: datetime.now(timezone.utc))

    #This tells SQLAlchemy about the connection between ExcelTable and User. It lets you do:
    # pythontable.creator        # returns the User object who created this table
    # user.tables          # returns all ExcelTable objects this user created (backref)
    creator = db.relationship("User", backref="tables")

    #cascade="all, delete-orphan" — this is important: when you delete an ExcelTable, 
    # PostgreSQL automatically deletes all its rows too. No orphaned data left behind.
    rows    = db.relationship("TableRow", back_populates="table",
                              cascade="all, delete-orphan")

class TableRow(db.Model):
    """One row of data. Data stored as JSON so any Excel schema works."""
    __tablename__ = "table_rows"
    id        = db.Column(db.Integer, primary_key=True)
    table_id  = db.Column(db.Integer, db.ForeignKey("excel_tables.id"),
                          nullable=False, index=True)
    row_index = db.Column(db.Integer, nullable=False)
    data      = db.Column(db.JSON, nullable=False)  # {"col1": "val", "col2": 123}
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                       onupdate=lambda: datetime.now(timezone.utc))
    table = db.relationship("ExcelTable", back_populates="rows")