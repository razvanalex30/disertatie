from flask_wtf import FlaskForm
from flask import flash, request, session

from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField, ValidationError, IntegerField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Email, ValidationError, NumberRange, Optional, InputRequired
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
import re
import os
import signal
import time
from multiprocessing import Process, Queue
import subprocess
import ipaddress
from bs4 import BeautifulSoup
from collections import Counter
from main.models import Users, Topologies, TopologiesUploaded




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == "py"


def run_python_script(file_path):
    try:
        # Run the 'sudo mn -c' command before executing the Python script
        subprocess.run(["sudo", 'mn', '-c'])

        command = ["sudo", "/home/razvan/Disertatie/disertatie/virt/bin/python", file_path]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        print(f"PRIMUL PROCESS ID: {process.pid}")
        time.sleep(15)
        print("AM DORMIT 15 SECUNDE")
        process.stdin.write('\nexit\n'.encode())
        process.stdin.flush()
        process.terminate()
        return True


    except Exception as e:
        return False




# def is_valid_python_file(file_path):  ######NOT USED####
#     try:
#         result_queue = Queue()
#         process = Process(target=run_python_script, args=(file_path, result_queue))
#         process.start()
#         process.join()
#         result = result_queue.get()
#         if isinstance(result, subprocess.CompletedProcess):
#             print(f"RESULT RETURN CODE: {result.returncode}")
#             if result.returncode == 0:
#                 return True, None
#             else:
#                 error_message = result.stderr.strip() or result.stdout.strip()
#                 return False, error_message
#         else:
#             return False, str(result)
#     except Exception as e:
#         return False, str(e)




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


class FileForm(FlaskForm):
    topology_name = StringField('Topology Name', validators=[DataRequired()])
    topology_description = TextAreaField('Topology Description', validators=[DataRequired()])
    topology_python_file = FileField('Python File (Only .py)', validators=[FileAllowed(['py'])])
    submit = SubmitField('Submit')


    def __init__(self, obj=None, *args, **kwargs):
        super(FileForm, self).__init__(obj=obj, *args, **kwargs)
        self.topology_name_changed = False
        self.edit_topology = obj is not None
        self.meta.obj = obj


    def validate_topology_name(self, field):


        if self._is_add_topology_route():
            topology_created = Topologies.query.filter_by(topology_name=field.data, topology_creator_id=current_user.id).first()
            topology_uploaded = TopologiesUploaded.query.filter_by(topology_name=field.data, topology_creator_id=current_user.id).first()
            if self.topology_name.data != field.data:
                if topology_created or topology_uploaded:
                    raise ValidationError("Error - Topology name already used! Please use another name!")

        elif self._is_edit_topology_route():

            if field.data != self.topology_name.default and Topologies.query.filter(

                    Topologies.topology_name == field.data,

                    Topologies.topology_creator_id == current_user.id,

                    Topologies.id != self.meta.obj.id if self.meta.obj else None

            ).first() or TopologiesUploaded.query.filter(

                TopologiesUploaded.topology_name == field.data,

                TopologiesUploaded.topology_creator_id == current_user.id,

                TopologiesUploaded.id != self.meta.obj.id if self.meta.obj else None

            ).first():
                raise ValidationError("Error - Topology name already used! Please use another name.")


    def validate_topology_python_file(self, field):

        if field.data is None and self._is_add_topology_route():
            raise ValidationError('Please upload a valid .py file.')


        if field.data is None and self._is_edit_topology_route():
            return


        if not allowed_file(field.data.filename):
            raise ValidationError('Please upload a valid .py file.')
        print("SUNTEM IN VALIDATE PYTHON FILE")
        file_path = os.path.join("/home/razvan/Disertatie/disertatie/uploads", field.data.filename)
        field.data.save(file_path)


        run_python = run_python_script(file_path)
        print(f">>>> VALOARE {run_python}")
        if not run_python:
            os.remove(file_path)
            raise ValidationError("Python file has errors, please check!")


        session['file_path'] = file_path



    def _is_add_topology_route(self):
        return request.path == "/add_topology_file"

    def _is_edit_topology_route(self):
        return request.path.startswith("/edit_topology_uploaded")






# Create a Topology Form
class TopologyForm(FlaskForm):
    topology_name = StringField("Topology Name", validators=[DataRequired()])
    topology_description = CKEditorField("Description", validators=[DataRequired()])
    topology_controllers_nr = IntegerField("Controllers Number", validators=[InputRequired(), NumberRange(min=0)])
    topology_controllers_names = StringField("Controllers Names", validators=[DataRequired()])
    topology_routers_nr = IntegerField("Routers Number", validators=[InputRequired(), NumberRange(min=0)])
    topology_routers_names = StringField("Routers Names", validators=[DataRequired()])
    topology_switches_nr = IntegerField("Switches Number", validators=[DataRequired(), NumberRange(min=1)])
    topology_switches_names = StringField("Switches Names", validators=[DataRequired()])
    topology_hosts_nr = IntegerField("Hosts Number", validators=[DataRequired(), NumberRange(min=1)])
    topology_hosts_names = StringField("Hosts Names", validators=[DataRequired()])
    topology_connections_text = TextAreaField("Topology Connections", validators=[DataRequired()])
    topology_setup_text = TextAreaField("Topology Setup", validators=[DataRequired()])
    topology_creator = StringField("Topology Creator")
    submit = SubmitField("Submit")

    def __init__(self, obj=None, *args, **kwargs):
        super(TopologyForm, self).__init__(obj=obj, *args, **kwargs)
        self.topology_name_changed = False
        self.edit_topology = obj is not None
        self.meta.obj = obj  # Store the object in the form meta
        if request.path == "/add_topology":
            self.topology_controllers_names.default = "No Controllers"
            self.topology_routers_names.default = "No Routers"
        else:
            self.topology_controllers_names.default = obj.topology_controllers_names or "No Controllers"
            self.topology_routers_names.default = obj.topology_routers_names or "No Routers"

        self.topology_controllers_names.process(request.form)
        self.topology_routers_names.process(request.form)




    def validate_topology_name(self, field):
        # if not self.topology_name_changed:
        #     return
        if self._is_add_topology_route():
            topology_created = Topologies.query.filter_by(topology_name=field.data, topology_creator_id=current_user.id).first()
            topology_uploaded = TopologiesUploaded.query.filter_by(topology_name=field.data, topology_creator_id=current_user.id).first()
            if topology_created or topology_uploaded:
                raise ValidationError("Error - Topology name already used! Please use another name!")


        elif self._is_edit_topology_route():

            if field.data != self.topology_name.default and Topologies.query.filter(

                    Topologies.topology_name == field.data,

                    Topologies.topology_creator_id == current_user.id,

                    Topologies.id != self.meta.obj.id if self.meta.obj else None

            ).first() or TopologiesUploaded.query.filter(

                    TopologiesUploaded.topology_name == field.data,

                    TopologiesUploaded.topology_creator_id == current_user.id,

                    TopologiesUploaded.id != self.meta.obj.id if self.meta.obj else None

            ).first():
                raise ValidationError("Error - Topology name already used! Please use another name.")

    def _is_add_topology_route(self):
        return request.path == "/add_topology"

    def _is_edit_topology_route(self):
        return request.path.startswith("/topologies/edit/")

    def populate_obj(self, obj):
        super(TopologyForm, self).populate_obj(obj)
        if self.topology_name.data != obj.topology_name:
            self.topology_name.changed = True

    def validate_topology_controllers_names(self, field):
        if self.topology_controllers_nr.data is None:
            # Handle case when topology_controllers_nr is not submitted or not set to an integer value
            return

        # if self.topology_controllers_nr.data == 0 and field.data != "No Controllers":
        #     raise ValidationError("Controllers Names field should be empty when Controllers Number is 0.")
        if self.topology_controllers_nr.data > 0 and not field.data.strip():
            raise ValidationError("Controllers Names field is required when Controllers Number is greater than 0.")

        if field.data and self.topology_controllers_nr.data > 0:
            names = field.data.split(",")
            names = [name.strip() for name in names if name.strip()]

            # Validate input format using regex
            pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
            for name in names:
                if not re.match(pattern, name):
                    raise ValidationError("The provided values are not correct, please try again!")

            if len(names) != self.topology_controllers_nr.data:
                raise ValidationError(f"Number of Controllers Names should be {self.topology_controllers_nr.data}.")
            if len(names) != len(set(names)):
                raise ValidationError("Controllers Names should not contain duplicates.")

            # if self.topology_controllers_nr.data == 0:
                # raise War("Controllers Names field is required when Controllers Number is greater than 0.")


    def validate_topology_routers_names(self, field):

        if self.topology_controllers_nr.data is None:
            # Handle case when topology_controllers_nr is not submitted or not set to an integer value
            return

        # if self.topology_routers_nr.data == 0 and field.data:
        #     field.data = "No Routers"
            # raise ValidationError("Routers Names field should be empty when Routers Number is 0.")
        if self.topology_routers_nr.data > 0 and not field.data.strip():
            raise ValidationError("Routers Names field is required when Routers Number is greater than 0.")
        if field.data and self.topology_routers_nr.data > 0:
            names = field.data.split(",")
            names = [name.strip() for name in names if name.strip()]

            # Validate input format using regex
            pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
            for name in names:
                if not re.match(pattern, name):
                    raise ValidationError("The provided values are not correct, please try again!")

            if len(names) != self.topology_routers_nr.data:
                raise ValidationError(f"Number of Routers Names should be {self.topology_routers_nr.data}.")
            if len(names) != len(set(names)):
                raise ValidationError("Routers Names should not contain duplicates.")

            # if self.topology_routers_nr.data > 0:
            #     raise ValidationError("Routers Names field is required when Controllers Number is greater than 0.")


    def validate_topology_switches_names(self, field):
        if self.topology_switches_nr.data > 0:
            if not field.data.strip():
                raise ValidationError("Switches Names field is required when Switches Number is greater than 0.")

            names = field.data.split(",")
            names = [name.strip() for name in names if name.strip()]
            # Validate input format using regex
            pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
            for name in names:
                if not re.match(pattern, name):
                    raise ValidationError("The provided values are not correct, please try again!")

            if len(names) != self.topology_switches_nr.data:
                raise ValidationError(f"Number of Switches Names should be {self.topology_switches_nr.data}.")
            if len(names) != len(set(names)):
                raise ValidationError("Switches Names should not contain duplicates.")

    def validate_topology_hosts_names(self, field):
        if self.topology_hosts_nr.data > 0:
            if not field.data.strip():
                raise ValidationError("Hosts Names field is required when Hosts Number is greater than 0.")

            names = field.data.split(",")
            names = [name.strip() for name in names if name.strip()]

            # Validate input format using regex
            pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
            for name in names:
                if not re.match(pattern, name):
                    raise ValidationError("The provided values are not correct, please try again!")


            if len(names) != self.topology_hosts_nr.data:
                raise ValidationError(f"Number of Hosts Names should be {self.topology_hosts_nr.data}.")
            if len(names) != len(set(names)):
                raise ValidationError("Hosts Names should not contain duplicates.")



    def validate_connection_text(self, **kwargs):
        valid_lines = []
        invalid_lines = []


        connections_text = kwargs.get("cleaned_text")

        controllers_names_list = kwargs.get("controllers_list")
        routers_names_list = kwargs.get("routers_list")
        switches_names_list = kwargs.get("switches_list")
        hosts_names_list = kwargs.get("hosts_list")

        # Track unused devices
        unused_devices = {
            'controllers': set(controllers_names_list),
            'routers': set(routers_names_list),
            'switches': set(switches_names_list),
            'hosts': set(hosts_names_list)
        }



        for line in connections_text.split('\n'):
            line = line.strip()

            # Check if the line follows the valid format
            if '<->' in line and line.count('<->') == 1:
                device1, device2 = line.split('<->')
                device1 = device1.strip()
                device2 = device2.strip()
                # Check if device1 and device2 are present in the respective lists
                if (device1 in controllers_names_list or device1 in routers_names_list or device1 in switches_names_list or device1 in hosts_names_list) \
                        and (device2 in controllers_names_list or device2 in routers_names_list or device2 in switches_names_list or device2 in hosts_names_list):

                    # Check if device1 and device2 are not "no controllers" or "no routers"
                    if device1 == 'no controllers' or device1 == 'no routers' or device2 == 'no controllers' or device2 == 'no routers':
                        invalid_lines.append(line)
                        continue

                    # Perform the specific validations based on the rules you provided
                    if device1 in controllers_names_list and (device2 in switches_names_list or device2 in routers_names_list):
                        valid_lines.append(line)
                    elif device1 in routers_names_list and (device2 in switches_names_list or device2 in controllers_names_list):
                        valid_lines.append(line)
                    elif device1 in switches_names_list and (device2 in controllers_names_list or device2 in routers_names_list or device2 in hosts_names_list or device2 in switches_names_list):
                        valid_lines.append(line)
                    elif device1 in hosts_names_list and device2 in switches_names_list:
                        valid_lines.append(line)
                    elif device2 in controllers_names_list and (device1 in switches_names_list or device1 in routers_names_list):
                        valid_lines.append(line)
                    elif device2 in hosts_names_list and (device1 in switches_names_list or device1 in controllers_names_list):
                        valid_lines.append(line)
                    elif device2 in switches_names_list and (device1 in controllers_names_list or device1 in routers_names_list or device1 in hosts_names_list or device1 in switches_names_list):
                        valid_lines.append(line)
                    elif device2 in hosts_names_list and device1 in switches_names_list:
                        valid_lines.append(line)
                    else:
                        invalid_lines.append(line)

                    # Remove used devices from unused_devices
                    if device1 in unused_devices['controllers']:
                        unused_devices['controllers'].remove(device1)
                    if device1 in unused_devices['routers']:
                        unused_devices['routers'].remove(device1)
                    if device1 in unused_devices['switches']:
                        unused_devices['switches'].remove(device1)
                    if device1 in unused_devices['hosts']:
                        unused_devices['hosts'].remove(device1)
                    if device2 in unused_devices['controllers']:
                        unused_devices['controllers'].remove(device2)
                    if device2 in unused_devices['routers']:
                        unused_devices['routers'].remove(device2)
                    if device2 in unused_devices['switches']:
                        unused_devices['switches'].remove(device2)
                    if device2 in unused_devices['hosts']:
                        unused_devices['hosts'].remove(device2)

                else:
                    invalid_lines.append(line)
            else:
                invalid_lines.append(line)

        # Remove duplicates from the valid lines
        # print(type(valid_lines))
        # valid_lines = list(set(valid_lines))

        # Check for unused devices
        unused_devices_list = [device for device_type, devices in unused_devices.items() for device in devices]
        for elem in unused_devices_list.copy():
            if elem == "No Controllers" or elem == "No Routers":
                unused_devices_list.remove(elem)

        return valid_lines, invalid_lines, unused_devices_list


    def validate_setup_text(self, **kwargs):

        valid_host_line = re.compile(
            r'^(h\d+)\s*-\s*(\d+\.\d+\.\d+\.\d+/\d+)\s*default_route:\s*(\d+\.\d+\.\d+\.\d+|None)\s+MAC:\s*(random|(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})$')
        valid_router_line = re.compile(r'^(r\d+)\s*-\s*(\w+\s+)?([\d.]+)/([\d.]+)$')
        valid_controller_line = re.compile(r'^(c\d+)\s*-\s*(?:([\d.]+):)?(\d+)$')

        setup_text = kwargs.get("cleaned_text")
        controllers_names_list = kwargs.get("controllers_list")
        routers_names_list = kwargs.get("routers_list")
        # switches_names_list = kwargs.get("switches_list")
        hosts_names_list = kwargs.get("hosts_list")

        seen_host_names = set()
        valid_lines = []
        invalid_lines = []
        duplicate_lines = []
        unused_hosts = []

        for line in setup_text.split('\n'):
            # print(f">>>LINIA ESTE: {line}")
            # Handle hosts
            host_match = valid_host_line.match(line)
            router_match = valid_router_line.match(line)
            controller_match = valid_controller_line.match(line)
            # print(f">>>HOST MATCH ESTE: {host_match}")
            # print(f">>>ROUTER MATCH ESTE: {router_match}")
            # print(f">>>CONTROLLER MATCH ESTE: {controller_match}")
            if host_match and not router_match and not controller_match:
                host_name, ip_address_netmask, default_route, mac_address = host_match.groups()
                print(host_name, ip_address_netmask, default_route, mac_address)
                if host_name not in hosts_names_list:
                    invalid_lines.append(line)
                    continue
                else:
                    if host_name in seen_host_names:
                        duplicate_lines.append(line)
                        continue
                    else:
                        seen_host_names.add(host_name)
                        try:
                            ipaddress.IPv4Interface(f"{ip_address_netmask}")
                            valid_lines.append(line)
                        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                            invalid_lines.append(line)
                            continue
            elif router_match and not host_match and not controller_match:
                router_name, interface_name, ip_address, netmask = router_match.groups()
                if router_name not in routers_names_list:
                    invalid_lines.append(line)
                    continue
                else:
                    # Validate IP address
                    try:
                        ipaddress.IPv4Interface(f"{ip_address}/{netmask}")
                        valid_lines.append(line)
                    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                        invalid_lines.append(line)
                        continue
            elif controller_match and not host_match and not router_match:
                controller_name, ip_port, port_number = controller_match.groups()
                if controller_name not in controllers_names_list:
                    invalid_lines.append(line)
                    continue
                else:
                    if ip_port:
                        try:
                            ipaddress.IPv4Address(ip_port.split(":")[0])
                            port_number = int(port_number)
                            if not 1 <= port_number <= 65535:
                                invalid_lines.append(line)
                                continue
                            valid_lines.append(line)
                        except ipaddress.AddressValueError:
                            invalid_lines.append(line)
                            continue
            else:
                invalid_lines.append(line)


        seen_host_names = list(seen_host_names)
        if set(seen_host_names) ^ set(hosts_names_list):
            hosts_not_used = list(set(seen_host_names) ^ set(hosts_names_list))
            unused_hosts.extend(hosts_not_used)

        # print(f"VALID LINES SETUP: {valid_lines}")
        # print(f"DUPLICATE LINES SETUP: {duplicate_lines}")
        # print(f"INVALID LINES SETUP: {invalid_lines}")
        # print(f"UNSED HOSTS SETUP: {unused_hosts}")
        return valid_lines, invalid_lines, unused_hosts, duplicate_lines












    def validate(self, extra_validators=None):
        if not super().validate():
            return False

        # List which will contain all devices names
        all_names = []

        # Get switches and hosts names -> they are mandatory
        switches_names_list = []
        hosts_names_list = []
        for field_name in ['topology_switches_names', 'topology_hosts_names']:
            field = getattr(self, field_name)
            names = field.data.split(",")
            names = [name.strip() for name in names if name.strip()]
            all_names.extend(names)
            if "switches" in field_name:
                switches_names_list.extend(names)
            else:
                hosts_names_list.extend(names)

        controllers_names_list = []
        # Get Controllers names -> they are optional, if the controllers nr. is 0, we ignore this field
        if self.topology_controllers_nr.data > 0:
            names = self.topology_controllers_names.data.split(",")
            names = [name.strip() for name in names if name.strip()]
            all_names.extend(names)
            controllers_names_list.extend(names)

        routers_names_list = []
        # Get Routers names -> they are optional, if the routers nr. is 0, we ignore this field
        if self.topology_routers_nr.data > 0:
            names = self.topology_routers_names.data.split(",")
            names = [name.strip() for name in names if name.strip()]
            all_names.extend(names)
            routers_names_list.extend(names)

        # print(f">>>>>DEVICES NAMES: {all_names}")

        if len(all_names) != len(set(all_names)):
            duplicates = Counter(all_names)
            duplicates_list = list([elem for elem in duplicates if duplicates[elem] > 1])
            flash(f"There are duplicates in devices names: {duplicates_list}")
            return False


        soup = BeautifulSoup(self.topology_connections_text.data, 'html.parser')
        plain_text = soup.get_text(separator='\n')
        lines = plain_text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        cleaned_lines = [''.join(line.split()) for line in non_empty_lines]
        cleaned_text = '\n'.join(cleaned_lines)
        print(f">>>>> CONNECTIONS TEXT: {cleaned_text}")


        return True




class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError("Error - There is no account with this email. Please register first!")


class ResetPasswordForm(FlaskForm):
    password_hash = PasswordField("Password", validators=[DataRequired(),
                                                          EqualTo("password_hash2", message="Passwords must match!")])
    password_hash2 = PasswordField("Confirm Password", validators=[DataRequired()])

    submit = SubmitField("Reset Password")