from flask import Flask, render_template, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length, Email
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.widgets import TextArea


app = Flask(__name__)
# Add Database
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Zarvan39#@localhost/users"
# Secret Key
app.config['SECRET_KEY'] = "pass"

# Initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create Topology Model
class Topologies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topology_name = db.Column(db.String(255))
    topology_description = db.Column(db.Text)
    topology_creator = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Create a Topology Form

class TopologyForm(FlaskForm):
    topology_name = StringField("Topology Name", validators=[DataRequired()])
    topology_description = StringField("Topology Description", validators=[DataRequired()], widget=TextArea())
    topology_creator = StringField("Topology Creator", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Show Topologies

@app.route("/topologies")
def topologies():
    # Grab all the topologies from the database
    topologies = Topologies.query.order_by(Topologies.date_created)

    return render_template("topologies.html", topologies=topologies)


@app.route("/topologies/<int:id>")
def topology(id):
    topology = Topologies.query.get_or_404(id)
    return render_template("topology.html", topology=topology)

@app.route("/topologies/edit/<int:id>", methods=["GET", "POST"])
def edit_topology(id):
    topology = Topologies.query.get_or_404(id)
    form = TopologyForm()
    if form.validate_on_submit():
        topology.topology_name = form.topology_name.data
        topology.topology_description = form.topology_description.data
        topology.topology_creator = form.topology_creator.data
        # Update database
        db.session.add(topology)
        db.session.commit()
        flash("Topology updated successfully!")
        return redirect(url_for('topology', id= topology.id))

    form.topology_name.data = topology.topology_name
    form.topology_description.data = topology.topology_description
    form.topology_creator.data = topology.topology_creator

    return render_template("edit_topology.html", form=form)



@app.route("/add_topology", methods=["GET","POST"])
def add_topology():
    form = TopologyForm()

    if form.validate_on_submit():
        post = Topologies(topology_name=form.topology_name.data, topology_description=form.topology_description.data, topology_creator=form.topology_creator.data)
        # Clear the form
        form.topology_name.data = ''
        form.topology_description.data = ''
        form.topology_creator.data = ''

        # Add topology to database
        db.session.add(post)
        db.session.commit()

        # Return message
        flash("Topology submitted successfully!")

    return render_template("add_topology.html", form=form)





# Create Users Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    master_name = db.Column(db.String(200))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Create a string

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


    def __repr__(self):
        return f'Full Name {self.full_name}'


class PasswordForm(FlaskForm):
    email = StringField("What's your email", validators=[DataRequired()])
    password_hash = PasswordField("What's your password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create Form Class
class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password_hash = PasswordField("Password", validators=[DataRequired(), EqualTo("password_hash2", message="Passwords must match!")])
    password_hash2 = PasswordField("Confirm Password", validators=[DataRequired()])
    master_name = StringField("Master Programme Name")
    submit = SubmitField("Register")


@app.route('/delete/<int:id>')
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    full_name = None
    form = RegisterForm()
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully!")
        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html", form=form,
                               full_name=full_name,
                               our_users=our_users)
    except:
        flash("ERROR! There was a problem deleting the user")
        return render_template("add_user.html", form=form,
                               full_name=full_name,
                               our_users=our_users)



# Update Database Record
@app.route('/update/<int:id>', methods=['GET','POST'])
def update(id):
    form = RegisterForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.full_name = request.form["full_name"]
        name_to_update.email = request.form["email"]
        name_to_update.password = request.form["password"]
        name_to_update.master_name = request.form["master_name"]
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html", form=form, name_to_update=name_to_update)
        except:
            flash("ERROR!")
            return render_template("update.html", form=form, name_to_update=name_to_update)

    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id = id)





@app.route('/user/register', methods=['GET','POST'])
def add_user():
    full_name = None
    form = RegisterForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_passwrd = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(full_name=form.full_name.data, email=form.email.data, password_hash=hashed_passwrd, master_name=form.master_name.data)
            db.session.add(user)
            db.session.commit()
        full_name=form.full_name.data
        form.full_name.data = ''
        form.email.data = ''
        form.password_hash.data = ''
        form.master_name.data = ''
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


@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None

    form = PasswordForm()
    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        # Clear the form
        form.email.data = ''
        form.password_hash.data = ''

        # Lookup user by email address
        pw_to_check = Users.query.filter_by(email=email).first()

        # Check Hashed password
        passed = check_password_hash(pw_to_check.password_hash, password)



        # flash("Account registered successfully!")

    return render_template("test_pw.html", email=email, password=password,
                           pw_to_check=pw_to_check,
                           passed=passed,
                           form=form)


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



