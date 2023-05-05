from flask import Flask, render_template, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
# Add Database
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Zarvan39#@localhost/users"
# Secret Key
app.config['SECRET_KEY'] = "pass"

# Initialize the database
db = SQLAlchemy(app)



# Create Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Create a string

    def __repr__(self):
        return f'Full Name {self.full_name}'



# Create Form Class
class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

# Update Database Record
@app.route('/update/<int:id>', methods=['GET','POST'])
def update(id):
    form = RegisterForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.full_name = request.form["full_name"]
        name_to_update.email = request.form["email"]
        name_to_update.password = request.form["password"]
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html", form=form, name_to_update=name_to_update)
        except:
            flash("ERROR!")
            return render_template("update.html", form=form, name_to_update=name_to_update)

    else:
        return render_template("update.html", form=form, name_to_update=name_to_update)





@app.route('/user/register', methods=['GET','POST'])
def add_user():
    full_name = None
    form = RegisterForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Users(full_name=form.full_name.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
        full_name=form.full_name.data
        form.full_name.data = ''
        form.email.data = ''
        form.password.data = ''
        flash("User added successfully")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html", form=form,
                           full_name=full_name,
                           our_users=our_users)


@app.route('/')
def index():
    first_name = "John"
    stuff = "This is <strong>Bold</strong> Text"
    return render_template("index.html", first_name=first_name,
                           stuff=stuff)

@app.route('/user/<name>')
def user(name):
    return render_template("user.html", name=name)


# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    full_name = None
    form = RegisterForm()
    # Validate Form
    if form.validate_on_submit():
        full_name = form.full_name.data
        form.full_name.data = ''
        flash("Account registered successfully!")

    return render_template("register.html", full_name=full_name, form=form)



