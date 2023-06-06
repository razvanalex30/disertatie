from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_ckeditor import CKEditor




app = Flask(__name__)
# Add ckeditor
ckeditor = CKEditor(app)
# Add Database
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Zarvan39#@localhost/users"
# Secret Key
app.config['SECRET_KEY'] = "pass"

# Initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from main import routes

