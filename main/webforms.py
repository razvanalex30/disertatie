from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField, ValidationError, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, Email, ValidationError, NumberRange, Optional, InputRequired
from flask_ckeditor import CKEditorField
import re
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
    topology_description = CKEditorField("Description", validators=[DataRequired()])
    topology_controllers_nr = IntegerField("Controllers Number", validators=[InputRequired(), NumberRange(min=0)])
    topology_controllers_names = StringField("Controllers Names", validators=[Optional()])
    topology_routers_nr = IntegerField("Routers Number", validators=[InputRequired(), NumberRange(min=0)])
    topology_routers_names = StringField("Routers Names", validators=[Optional()])
    topology_switches_nr = IntegerField("Switches Number", validators=[DataRequired(), NumberRange(min=1)])
    topology_switches_names = StringField("Switches Names", validators=[DataRequired()])
    topology_hosts_nr = IntegerField("Hosts Number", validators=[DataRequired(), NumberRange(min=1)])
    topology_hosts_names = StringField("Hosts Names", validators=[DataRequired()])
    topology_connections_text = CKEditorField("Topology Connections", validators=[DataRequired()])
    topology_setup_text = CKEditorField("Topology Setup", validators=[DataRequired()])
    topology_creator = StringField("Topology Creator")
    submit = SubmitField("Submit")

    def validate_topology_controllers_names(self, topology_controllers_names):
        # Check if input is a string
        controllers_names = topology_controllers_names.data
        controllers_nr = self.topology_controllers_nr.data


        if not isinstance(controllers_names, str):
            raise ValidationError("Input must be a string.")
        if not isinstance(controllers_nr, int):
            raise ValidationError("Input must be an integer.")

        if controllers_nr == 0 and controllers_names:
            raise ValidationError("You have entered 0 controllers, please leave this field empty!")

        # Validate input format using regex
        if controllers_nr > 0:
            pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
            if not re.match(pattern, controllers_names):
                raise ValidationError("The provided values are not correct, please try again!")


        # Split the input string into a list
        controller_values = controllers_names.split(',')
        duplicates_controllers = list(set(controller_values))
        controller_values.sort()
        duplicates_controllers.sort()
        print(f"DUPLICATES CONTROLLERS IS :{duplicates_controllers}")
        if duplicates_controllers != controller_values:
            raise ValidationError("There are duplicates in names, please try again!")
        if len(controller_values) != controllers_nr and controllers_nr > 0:
            raise ValidationError("You have provided too many or too few controllers names, please try again!")


        print(f">>>>>>>>>>>CONTROLLER VALUES ARE: {controller_values}")
        return controller_values
    #
    #

    def validate_topology_routers_names(self, topology_routers_names):
        # Check if input is a string
        routers_names = topology_routers_names.data
        routers_nr = self.topology_routers_nr.data


        if not isinstance(routers_names, str):
            raise ValidationError("Input must be a string.")
        if not isinstance(routers_nr, int):
            raise ValidationError("Input must be an integer.")

        if routers_nr == 0 and routers_names:
            raise ValidationError("You have entered 0 routers, please leave this field empty!")

        # Validate input format using regex
        if routers_nr > 0:
            pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
            if not re.match(pattern, routers_names):
                raise ValidationError("The provided values are not correct, please try again!")


        # Split the input string into a list
        router_values = routers_names.split(',')
        duplicates_routers = list(set(router_values))
        router_values.sort()
        duplicates_routers.sort()
        # print(f"DUPLICATES ROUTERS IS :{duplicates_routers}")
        if duplicates_routers != router_values:
            raise ValidationError("There are duplicates in names, please try again!")
        if len(router_values) != routers_nr and routers_nr > 0:
            raise ValidationError("You have provided too many or too few controllers names, please try again!")


        # print(f">>>>>>>>>>>ROUTER VALUES ARE: {router_values}")
        return router_values




    def validate_topology_switches_names(self, topology_switches_names):
        # Check if input is a string
        switches_names = topology_switches_names.data
        switches_nr = self.topology_switches_nr.data



        if not isinstance(switches_names, str):
            raise ValidationError("Input must be a string.")
        if not isinstance(switches_nr, int):
            raise ValidationError("Input must be an integer.")

        # Validate input format using regex
        pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
        if not re.match(pattern, switches_names):
            raise ValidationError("The provided values are not correct, please try again!")

        # Split the input string into a list
        switches_values = switches_names.split(',')
        duplicates_switches = list(set(switches_values))
        switches_values.sort()
        duplicates_switches.sort()
        # print(f"DUPLICATES SWITCHES IS :{duplicates_switches}")
        if duplicates_switches != switches_values:
            raise ValidationError("There are duplicates in names, please try again!")
        if len(switches_values) != switches_nr:
            raise ValidationError("You have provided too many or too few switches names, please try again!")

        # print(f">>>>>>>>>>>SWITCHES VALUES ARE: {switches_values}")
        return switches_values


    def validate_topology_hosts_names(self, topology_hosts_names):
        # Check if input is a string
        hosts_names = topology_hosts_names.data
        hosts_nr = self.topology_hosts_nr.data


        if not isinstance(hosts_names, str):
            raise ValidationError("Input must be a string.")
        if not isinstance(hosts_nr, int):
            raise ValidationError("Input must be an integer.")

        # Validate input format using regex
        pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
        if not re.match(pattern, hosts_names):
            raise ValidationError("The provided values are not correct, please try again!")

        # Split the input string into a list
        hosts_values = hosts_names.split(',')
        duplicates_hosts = list(set(hosts_values))
        hosts_values.sort()
        duplicates_hosts.sort()
        # print(f"DUPLICATES HOSTS IS :{duplicates_hosts}")
        if duplicates_hosts != hosts_values:
            raise ValidationError("There are duplicates in names, please try again!")

        if len(hosts_values) != hosts_nr:
            raise ValidationError("You have provided too many or too few hosts names, please try again!")
        # print(f">>>>>>>>>>>HOSTS VALUES ARE: {hosts_values}")
        return hosts_values

    def validate_controllers_routers_switches_hosts_names(self):
        controllers_names = self.validate_topology_controllers_names(self.topology_controllers_names)
        routers_names = self.validate_topology_routers_names(self.topology_routers_names)
        switches_names = self.validate_topology_switches_names(self.topology_switches_names)
        hosts_names = self.validate_topology_hosts_names(self.topology_hosts_names)

        controllers_names = ['No Controllers'] if controllers_names == [''] else controllers_names
        routers_names = ['No Routers'] if routers_names == [''] else routers_names

        nodes_names_list = controllers_names + routers_names + switches_names + hosts_names
        duplicates_names_list = list(set(nodes_names_list))
        nodes_names_list.sort()
        duplicates_names_list.sort()
        # print(f"############## NODES LIST IS: {nodes_names_list}")
        # print(f"############## DUPLICATE VALUES ARE: {duplicates_names_list}")
        if nodes_names_list == duplicates_names_list:
            return True
        else:
            return False

    # def validate_topology_connections_text(self):
    #     pass
    #
    # def validate_topology_setup_text(self):
    #     pass
    #
    #
