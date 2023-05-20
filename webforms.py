from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length, Email
from wtforms.widgets import TextArea


# Create Search Form
class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create Login Form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


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


# Create a Topology Form
class TopologyForm(FlaskForm):
    topology_name = StringField("Topology Name", validators=[DataRequired()])
    topology_description = StringField("Topology Description", validators=[DataRequired()], widget=TextArea())
    topology_creator = StringField("Topology Creator")
    submit = SubmitField("Submit")