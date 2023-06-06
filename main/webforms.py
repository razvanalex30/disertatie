from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length, Email, ValidationError
from flask_ckeditor import CKEditorField
from main.models import Users

# Create Search Form
class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create Login Form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class PasswordForm(FlaskForm):
    email = StringField("What's your email", validators=[DataRequired()])
    password_hash = PasswordField("What's your password", validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create Form Class
class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=70)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password_hash = PasswordField("Password", validators=[DataRequired(), EqualTo("password_hash2", message="Passwords must match!")])
    password_hash2 = PasswordField("Confirm Password", validators=[DataRequired()])
    master_name = StringField("Master Programme Name", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Error - Email already used! Please use another email address!")


# Create a Topology Form
class TopologyForm(FlaskForm):
    topology_name = StringField("Topology Name", validators=[DataRequired()])
    topology_description = CKEditorField("Topology Description", validators=[DataRequired()])
    topology_creator = StringField("Topology Creator")
    submit = SubmitField("Submit")