from flask import render_template, flash, request, redirect, url_for, session, Response, jsonify, send_file
from main import app
from main import db
import os
import shutil
import re
import time
import logging
import signal

import subprocess
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, current_user
from main.models import Users, Topologies, TopologiesUploaded
from main.webforms import RegisterForm, LoginForm, PasswordForm, TopologyForm, SearchForm, FileForm, RequestResetForm, ResetPasswordForm
from main import login_manager
from bs4 import BeautifulSoup
from datetime import datetime
from main import app, mail
from flask_mail import Message
from sqlalchemy import and_

log_content = ""
log = logging.getLogger('werkzeug')
log.disabled = True


@app.template_filter('remove_tags')
def remove_tags_text(text):
    soup = BeautifulSoup(text, 'html.parser')
    plain_text = soup.get_text()

    return plain_text


@app.template_filter('file_no_extension')
def file_extension_removal(filename):
    formatted_name = filename.split(".")[0]

    return formatted_name

@app.template_filter('file_creation_date')
def file_creation_date_filter(filename):
    creation_time = os.path.getctime(os.path.join(captures_dir_path, filename))
    formatted_date = datetime.fromtimestamp(creation_time)

    month = formatted_date.month if formatted_date.month >= 10 else f"{formatted_date.month}"
    day = formatted_date.day if formatted_date.day >= 10 else f"{formatted_date.day}"
    formatted_date = f"{month}/{day}/{formatted_date.year}, {formatted_date.strftime('%-I:%M:%S %p')}"
    return formatted_date


def is_valid_capture_name(name):
    # Use a regular expression to check if the name contains only letters, numbers, and underscores
    return re.match(r'^[a-zA-Z0-9_]+$', name) is not None


def remove_duplicate_lines(valid_lines):
    unique_lines = []
    duplicate_lines = []

    for line in valid_lines:
        # Split the line into device1 and device2
        device1, device2 = line.split('<->')

        reversed_line = f"{device2}<->{device1}"

        # Check if the normalized line or its reverse line exists in the set
        if line not in unique_lines and reversed_line not in unique_lines:
            unique_lines.append(line)
        else:
            duplicate_lines.append(line)

    return duplicate_lines




def parse_controllers_info(topo_setup_text):
    topo_text = topo_setup_text.strip().split("\n")


    controllers_created_lines = []

    valid_controller_line = re.compile(r'^(c\d+)\s*-\s*(?:([\d.]+):)?(\d+)$')

    for line in topo_text:
        controller_match = valid_controller_line.match(line)
        if controller_match:
            controller_name, ip_port, port_number = controller_match.groups()
            if ip_port:
                ip_address = ip_port.split(":")[0]
                line = f"{controller_name} = net.addController( name='{controller_name}', controller=Controller, ip='{ip_address}', port={port_number} )"
                controllers_created_lines.append(line)
            else:
                line = f"{controller_name} = net.addController( name='{controller_name}', controller=Controller, port={port_number} )"
                controllers_created_lines.append(line)
        else:
            continue

    return controllers_created_lines

def parse_routers_info(topo_setup_text):
    topo_text = topo_setup_text.strip().split("\n")

    routers_created_lines = []
    router_created_lines_intf = []

    valid_router_line = re.compile(r'^(r\d+)\s*-\s*(\w+\s+)?([\d.]+)/([\d.]+)$')

    for line in topo_text:
        router_match = valid_router_line.match(line)
        if router_match:
            router_name, interface_name, ip_address, netmask = router_match.groups()
            if not interface_name:  # creating a router with default IP for interface eth1 of the router
                router_line = f"{router_name} = net.addHost('{router_name}', cls=Node, ip='{ip_address}/{netmask}')"
                routers_created_lines.append(router_line)
                router_line_forward = f"{router_name}.cmd('sysctl -w net.ipv4.ip_forward=1')"
                routers_created_lines.append(router_line_forward)
            else:
                router_line = f"{router_name} = net.addHost('{router_name}', cls=Node)"
                router_line_intf_1 = f"{router_name}.cmd('sysctl -w net.ipv4.ip_forward=1')"
                routers_created_lines.append(router_line)
                routers_created_lines.append(router_line_intf_1)
                router_line_intf_2 = f"{router_name}.cmd('ip link add {router_name}-{interface_name} type dummy')"
                router_line_intf_3 = f"{router_name}.cmd('ip addr add {ip_address}/{netmask} dev {router_name}-{interface_name}')"
                router_line_intf_4 = f"{router_name}.cmd('ip link set dev {router_name}-{interface_name} up')"
                router_created_lines_intf.append(router_line_intf_2)
                router_created_lines_intf.append(router_line_intf_3)
                router_created_lines_intf.append(router_line_intf_4)
        else:
            continue

    return routers_created_lines, router_created_lines_intf




def parse_hosts_info(topo_setup_text):
    topo_text = topo_setup_text.strip().split("\n")

    hosts_created_lines = []


    valid_host_line = re.compile(
        r'^(h\d+)\s*-\s*(\d+\.\d+\.\d+\.\d+/\d+)\s*default_route:\s*(\d+\.\d+\.\d+\.\d+|None)\s+MAC:\s*(random|(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})$')
    for line in topo_text:
        host_match = valid_host_line.match(line)
        if host_match:
            host_name, ip_address_netmask, default_route, mac_address = host_match.groups()
            if default_route == "None" and mac_address == "random":
                host_line = f"{host_name} = net.addHost('{host_name}', cls=Host, ip = '{ip_address_netmask}')"
                hosts_created_lines.append(host_line)
            elif default_route != "None" and mac_address == "random":
                host_line = f"{host_name} = net.addHost('{host_name}', cls=Host, ip = '{ip_address_netmask}', defaultRoute='via {default_route}')"
                hosts_created_lines.append(host_line)
            elif default_route != "None" and mac_address != "random":
                host_line = f"{host_name} = net.addHost('{host_name}', cls=Host, ip = '{ip_address_netmask}', mac = '{mac_address}', defaultRoute='via {default_route}')"
                hosts_created_lines.append(host_line)
            elif default_route == "None" and mac_address != "random":
                host_line = f"{host_name} = net.addHost('{host_name}', cls=Host, ip = '{ip_address_netmask}', mac = '{mac_address}')"
                hosts_created_lines.append(host_line)
        else:
            continue

    return hosts_created_lines




def create_topology_script(**kwargs):
    connections_text = kwargs.get("topo_conn_text")
    setup_text = kwargs.get("topo_setup_text")
    directory_path = kwargs.get("directory_path")
    file_name = kwargs.get("file_name")

    controllers_names = kwargs.get("controllers_names")
    routers_names = kwargs.get("routers_names")
    switches_names = kwargs.get("switches_names")
    hosts_names = kwargs.get("hosts_names")

    all_devices_names = controllers_names + routers_names + switches_names + hosts_names


    switch_controller_conn_lines = []
    connection_text_lines = []
    conn_text = connections_text.strip().split("\n")
    for line in conn_text:
        conn_line = line.split("<->")
        if conn_line[0] in switches_names and conn_line[1] in controllers_names:
            link_line = f"net.get('{conn_line[0]}').start([{conn_line[1]}])"
            switch_controller_conn_lines.append(link_line)
        elif conn_line[0] in controllers_names and conn_line[1] in switches_names:
            link_line = f"net.get('{conn_line[1]}').start([{conn_line[0]}])"
            switch_controller_conn_lines.append(link_line)
        else:
            link_line = f"net.addLink({conn_line[0]}, {conn_line[1]})"
            connection_text_lines.append(link_line)



    switches_lines = []
    for switch_name in switches_names:
        switch_line = f"{switch_name} = net.addSwitch('{switch_name}', cls=OVSKernelSwitch)"
        switches_lines.append(switch_line)


    router_created_lines, routers_created_intf = parse_routers_info(setup_text)

    controllers_lines = parse_controllers_info(setup_text)

    hosts_lines = parse_hosts_info(setup_text)

    with open('/home/razvan/Disertatie/disertatie/topologies_templates/switch_host_tmp_new.py', 'r') as f:
        existing_code = f.read()
        f.close()

    logfile = f'{directory_path}/logfile.log'

    # Append the new lines to the existing code

    # Adding Controllers
    if controllers_lines:
        new_code = re.sub(r'# Insert Controllers here', '\n    '.join(controllers_lines), existing_code)
    else:
        new_code = existing_code

    # Adding Switches
    new_code = re.sub(r'# Insert Switches here', '\n    '.join(switches_lines), new_code)

    # Adding Routers
    if router_created_lines:
        new_code = re.sub(r'# Insert Routers here', '\n    '.join(router_created_lines), new_code)

    # Adding Hosts
    new_code = re.sub(r'# Insert Hosts here', '\n    '.join(hosts_lines), new_code)

    # Adding links
    new_code = re.sub(r'# Insert links here', '\n    '.join(connection_text_lines), new_code)

    # Adding Switches-Controllers connections
    if switch_controller_conn_lines:
        new_code = re.sub(r'# Insert switches controllers links here',
                          '\n    '.join(switch_controller_conn_lines), new_code)

    # Adding Routers Config
    if routers_created_intf:
        new_code = re.sub(r'# Insert router config here',
                          '\n    '.join(routers_created_intf), new_code)

    new_code = re.sub(r'#LOGFILE', logfile, new_code)

    # Write the modified code back to the script
    with open(f'{directory_path}/{file_name}.py', 'w') as f:
        f.write(new_code)
        f.close()


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create Admin Page
@app.route('/admin')
@login_required
def admin():
    email = current_user.email
    if email == "test@test.com":
        return render_template("admin.html")
    else:
        flash("Restricted Access!")
        return redirect(url_for('dashboard'))




# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            # Check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash("Login successfully!")
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash("Wrong Password - Try again!")
        else:
            flash("User doesn't exist!")
    return render_template("login.html", form=form)


# Create Logout Function
@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out!")
    return redirect(url_for('login'))


# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template("dashboard.html")


# Pass info to navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

# Create Search Function
@app.route('/search', methods=["POST"])
@login_required
def search():
    form = SearchForm()
    topologies_created = Topologies.query
    topologies_uploaded = TopologiesUploaded.query
    topology_creator = current_user.id
    if form.validate_on_submit():
        topology.searched = form.searched.data
        topologies_created = topologies_created.filter(and_(
                                                            Topologies.topology_name.like('%' + topology.searched + '%'),
                                                            Topologies.topology_creator_id == topology_creator))
        topologies_created = topologies_created.order_by(Topologies.topology_name).all()
        topologies_uploaded = topologies_uploaded.filter(and_(
                                                              TopologiesUploaded.topology_name.like('%' + topology.searched + '%'),
                                                              TopologiesUploaded.topology_creator_id == topology_creator))
        topologies_uploaded = topologies_uploaded.order_by(TopologiesUploaded.topology_name).all()

        topologies = topologies_created + topologies_uploaded
        topologies_nr = len(topologies)
        # TO DO -> DE ADAUGAT REDIRECT LINK CATRE TOPOLOGIES UPLOADED/CREATED
        return render_template("search.html", form=form,
                               searched=topology.searched,
                               topologies_created=topologies_created,
                               topologies_uploaded=topologies_uploaded,
                               topologies=topologies,
                               topologies_nr=topologies_nr)



# Show Topologies

@app.route("/topologies_uploaded")
@login_required
def topologies_uploaded():
    topology_creator = current_user.id
    # Grab all the topologies from the database for the current user
    page = request.args.get('page', 1, type=int)
    topologies_uploaded = TopologiesUploaded.query.filter_by(topology_creator_id=topology_creator).order_by(TopologiesUploaded.date_created.desc()).paginate(page=page, per_page=5)

    return render_template("topologies_uploaded.html", topologies_uploaded=topologies_uploaded)



@app.route("/topologies")
@login_required
def topologies():
    topology_creator = current_user.id
    # Grab all the topologies from the database for the current user
    page = request.args.get('page', 1, type=int)
    topologies_created = Topologies.query.filter_by(topology_creator_id=topology_creator).order_by(Topologies.date_created.desc()).paginate(page=page, per_page=5)

    return render_template("topologies.html", topologies_created=topologies_created)

@app.route("/topologies/<int:id>")
@login_required
def topology(id):
    topology = Topologies.query.get_or_404(id)
    return render_template("topology.html", topology=topology)


@app.template_filter('strip_lines')
def strip_lines_filter(text):
    lines = text.strip().split('\n')
    filtered_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(filtered_lines)


@app.route("/topologies/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_topology(id):
    topology = Topologies.query.get_or_404(id)
    form = TopologyForm(obj=topology)
    topology_name_begin = topology.topology_name

    if current_user.id == topology.topology_creator_id:
            if form.validate():

                soup = BeautifulSoup(form.topology_connections_text.data, 'html.parser')
                plain_text = soup.get_text(separator='\n')
                lines = plain_text.split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                cleaned_lines = [''.join(line.split()) for line in non_empty_lines]
                cleaned_text = '\n'.join(cleaned_lines)

                topo_conn_text = cleaned_text
                print(f">>>CONNECTIONS TEXT: {cleaned_text}")

                controllers_list = form.topology_controllers_names.data.split(",")
                routers_list = form.topology_routers_names.data.split(",")
                switches_list = form.topology_switches_names.data.split(",")
                hosts_list = form.topology_hosts_names.data.split(",")

                valid_lines, invalid_lines, unused_devices = form.validate_connection_text(cleaned_text=cleaned_text,
                                                                                           controllers_list=controllers_list,
                                                                                           routers_list=routers_list,
                                                                                           switches_list=switches_list,
                                                                                           hosts_list=hosts_list)

                # print(f">>>>>>> VALID LINES: {valid_lines}")
                if unused_devices and invalid_lines:
                    flash("Unused devices found: {}".format(", ".join(unused_devices)), 'error')
                    flash("Invalid lines found: {}".format(", ".join(invalid_lines)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif not unused_devices and invalid_lines:
                    flash("Invalid lines found: {}".format(", ".join(invalid_lines)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif unused_devices and not invalid_lines:
                    flash("Unused devices found: {}".format(", ".join(unused_devices)), 'error')
                    return render_template('edit_topology.html', form=form)

                duplicate_lines = remove_duplicate_lines(valid_lines)
                if duplicate_lines:
                    flash("Duplicate lines found: {}".format(", ".join(duplicate_lines)), 'error')
                    return render_template('edit_topology.html', form=form)

                form.topology_connections_text.data = cleaned_text

                soup = BeautifulSoup(form.topology_setup_text.data, 'html.parser')
                plain_text = soup.get_text(separator='\n')
                lines = plain_text.split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                cleaned_lines = [' '.join(line.split()) for line in non_empty_lines]
                cleaned_text = '\n'.join(cleaned_lines)
                print(f">>>>cleaned text: {cleaned_text}")

                topo_setup_text = cleaned_text

                ##### metoda de apelat aici ####
                valid_lines_setup, invalid_lines_setup, unused_hosts_setup, duplicate_lines_setup = form.validate_setup_text(
                    cleaned_text=cleaned_text,
                    controllers_list=controllers_list,
                    routers_list=routers_list,
                    hosts_list=hosts_list)

                if invalid_lines_setup and duplicate_lines_setup and unused_hosts_setup:
                    flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
                    flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
                    flash("Duplicate lines found: {}".format(", ".join(duplicate_lines_setup)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif invalid_lines_setup and duplicate_lines_setup:
                    flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
                    flash("Duplicate lines found: {}".format(", ".join(duplicate_lines)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif invalid_lines_setup and unused_hosts_setup:
                    flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
                    flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif duplicate_lines_setup and unused_hosts_setup:
                    flash("Duplicate lines found: {}".format(", ".join(duplicate_lines_setup)), 'error')
                    flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif duplicate_lines_setup and not unused_hosts_setup and not invalid_lines_setup:
                    flash("Duplicate lines found: {}".format(", ".join(duplicate_lines_setup)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif unused_hosts_setup and not invalid_lines_setup and not duplicate_lines_setup:
                    flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
                    return render_template('edit_topology.html', form=form)
                elif invalid_lines_setup and not unused_hosts_setup and not duplicate_lines_setup:
                    flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
                    return render_template('edit_topology.html', form=form)

                form.topology_setup_text.data = cleaned_text




                topology.topology_name = form.topology_name.data
                topology.topology_description = form.topology_description.data
                topology.topology_controllers_nr = form.topology_controllers_nr.data
                topology.topology_controllers_names = form.topology_controllers_names.data
                topology.topology_routers_nr = form.topology_routers_nr.data
                topology.topology_routers_names = form.topology_routers_names.data
                topology.topology_switches_nr = form.topology_switches_nr.data
                topology.topology_switches_names = form.topology_switches_names.data
                topology.topology_hosts_nr = form.topology_hosts_nr.data
                topology.topology_hosts_names = form.topology_hosts_names.data
                topology.topology_connections_text = form.topology_connections_text.data
                topology.topology_setup_text = form.topology_setup_text.data
                db.session.add(topology)
                db.session.commit()


                # Update
                if topology_name_begin != topology.topology_name:
                    directory_path_old = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                                 f"user_{topology.topology_creator_id}",
                                                 f"created/{topology_name_begin}")
                    directory_path_new = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                                 f"user_{topology.topology_creator_id}",
                                                 f"created/{topology.topology_name}")

                    file_path_old = os.path.join(directory_path_old, f"{topology_name_begin}.py")
                    file_path_new = os.path.join(directory_path_old, f"{topology.topology_name}.py")
                    os.rename(file_path_old, file_path_new)
                    os.rename(directory_path_old, directory_path_new)

                directory_path = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                              f"user_{topology.topology_creator_id}", f"created/{form.topology_name.data}")
                if not os.path.exists(directory_path):
                    os.makedirs(directory_path)

                create_topology_script(topo_conn_text=topo_conn_text,
                                       topo_setup_text=topo_setup_text,
                                       hosts_names=hosts_list,
                                       controllers_names=controllers_list,
                                       switches_names=switches_list,
                                       routers_names=routers_list,
                                       directory_path=directory_path,
                                       file_name=form.topology_name.data)


                flash("Topology updated successfully!")
                return redirect(url_for('topologies'))

            return render_template("edit_topology.html", form=form)
    else:
        flash("You are not authorized to edit this post!")
        topologies = Topologies.query.filter_by(topology_creator_id=current_user.id).order_by(
            Topologies.date_created.desc())
        return render_template("topologies.html", topologies=topologies)

@app.route("/topologies/delete/<int:id>", methods=['GET', 'POST'])
@login_required
def delete_topology(id):
    topology_to_delete = Topologies.query.get_or_404(id)
    id = current_user.id
    if id == topology_to_delete.topology_creator.id:

        try:
            directory_path = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                          f"user_{current_user.id}", f"created/{topology_to_delete.topology_name}")
            shutil.rmtree(directory_path)
            db.session.delete(topology_to_delete)
            db.session.commit()
            # Return a message
            flash("Topology was deleted!")
            return redirect(url_for('topologies'))

        except:
            # Return error message
            flash("ERROR when deleting Topology, please try again")

            return redirect(url_for('topologies'))
    else:
        # Return a message
        flash("You are not authorized to delete this topology!")
        return redirect(url_for('topologies'))


@app.route("/topologies/delete_uploaded/<int:id>", methods=['GET', 'POST'])
@login_required
def delete_topology_uploaded(id):
    topology_to_delete = TopologiesUploaded.query.get_or_404(id)
    id = current_user.id
    if id == topology_to_delete.topology_creator_id:

        try:
            directory_path = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                          f"user_{current_user.id}", f"uploaded/{topology_to_delete.topology_name}")
            shutil.rmtree(directory_path)
            db.session.delete(topology_to_delete)
            db.session.commit()
            # Return a message
            flash("Topology was deleted!")
            return redirect(url_for('topologies_uploaded'))

        except:
            # Return error message
            flash("ERROR when deleting Topology, please try again")
            return redirect(url_for('topologies_uploaded'))
    else:
        # Return a message
        flash("You are not authorized to delete this topology!")
        return redirect(url_for('topologies_uploaded'))



@app.route("/edit_topology_uploaded/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_topology_uploaded(id):
    # Fetch the existing topology from the database
    topology = TopologiesUploaded.query.get_or_404(id)
    # Create an instance of FileForm and pass the topology to prepopulate the form
    form = FileForm(obj=topology)
    topology_creator = current_user.id
    file_name = topology.topology_file_path.split("/")[-1]
    topology_name_begin = topology.topology_name

    directory_path = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                  f"user_{topology_creator}", f"uploaded/{form.topology_name.data}")


    if form.validate_on_submit():
        topology.topology_name = form.topology_name.data
        topology.topology_description = form.topology_description.data


        if topology_name_begin != topology.topology_name:
            directory_path_old = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                              f"user_{topology.topology_creator_id}",
                                              f"uploaded/{topology_name_begin}")
            directory_path_new = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                              f"user_{topology.topology_creator_id}",
                                              f"uploaded/{topology.topology_name}")
            script_file = None
            files = os.listdir(directory_path_old)
            for file in files:
                if file.endswith(".py"):
                    script_file = file
                    break
            file_path = os.path.join(directory_path_old, script_file)
            old_directory_name = directory_path_old.split("/")[-1]
            new_directory_name = directory_path_new.split("/")[-1]
            with open(file_path, 'r') as file:
                existing_code = file.read()
                file.close()

            new_code = re.sub(r'{}'.format(old_directory_name), new_directory_name, existing_code)
            with open(file_path, 'w') as file:
                file.write(new_code)
                file.close()


            os.rename(directory_path_old, directory_path_new)


        # Check if the user has uploaded a new file
        if form.topology_python_file.data is not None:
            # Save the new file and update the topology_file_path in the database
            files = os.listdir(directory_path)
            for file in files:
                if file.endswith(".py"):
                    os.remove(os.path.join(directory_path, file))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(form.topology_python_file.data.filename))
            file_name_new = file_path.split("/")[-1]
            shutil.move(file_path, directory_path)
            form.topology_python_file.data.save(file_path)
            topology.topology_file_path = file_path
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                if not f.endswith(".py"):
                    continue
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))

            logfile = f'{directory_path}/logfile.log'
            file_path_new = os.path.join(directory_path, file_name_new)
            with open(file_path_new, 'r') as file:
                existing_code = file.read()
                file.close()

            new_code = re.sub(r'#LOGFILE', logfile, existing_code)

            with open(file_path_new, 'w') as file:
                file.write(new_code)
                file.close()


        # Commit the changes to the database
        db.session.add(topology)
        db.session.commit()

        flash("Topology updated successfully!")
        return redirect(url_for('topologies_uploaded'))

    return render_template('edit_topology_uploaded.html', form=form, file_name=file_name)





@app.route("/add_topology_file", methods=['GET', 'POST'])
@login_required
def create_topology():
    form = FileForm()
    if form.validate_on_submit():
        topology_creator = current_user.id




        file_path = session.get('file_path')
        file_name = file_path.split("/")[-1]

        directory_path = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                      f"user_{topology_creator}", f"uploaded/{form.topology_name.data}")
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        shutil.move(file_path, directory_path)
        file_path_new = os.path.join(directory_path, file_name)
        logfile = f'{directory_path}/logfile.log'

        with open(file_path_new, 'r') as file:
            existing_code = file.read()
            file.close()

        new_code = re.sub(r'#LOGFILE', logfile, existing_code)

        with open(file_path_new, 'w') as file:
            file.write(new_code)
            file.close()


        post = TopologiesUploaded(topology_name=form.topology_name.data,
                          topology_description=form.topology_description.data,
                          topology_file_path=file_path_new,
                          topology_creator_id=topology_creator,
                          )

        # Add topology to database
        db.session.add(post)
        db.session.commit()


        # Clear the form
        form.topology_name.data = ''
        form.topology_description.data = ''

        flash('Topology created successfully!', 'success')
        return redirect(url_for('topologies_uploaded'))


    return render_template('create_topology.html', form=form)


@app.route("/add_topology", methods=["GET","POST"])
@login_required
def add_topology():
    form = TopologyForm()
    form.topology_name_changed = True

    if form.validate():
        topology_creator = current_user.id

        if form.topology_controllers_nr.data == 0:
            form.topology_controllers_names.data = "No Controllers"
        if form.topology_routers_nr.data == 0:
            form.topology_routers_names.data = "No Routers"

        soup = BeautifulSoup(form.topology_connections_text.data, 'html.parser')
        plain_text = soup.get_text(separator='\n')
        lines = plain_text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        cleaned_lines = [''.join(line.split()) for line in non_empty_lines]
        cleaned_text = '\n'.join(cleaned_lines)
        # form.topology_connections_text.data = cleaned_text

        controllers_list = form.topology_controllers_names.data.split(",")
        routers_list = form.topology_routers_names.data.split(",")
        switches_list = form.topology_switches_names.data.split(",")
        hosts_list = form.topology_hosts_names.data.split(",")


        valid_lines, invalid_lines, unused_devices = form.validate_connection_text(cleaned_text=cleaned_text,
                                                                                   controllers_list=controllers_list,
                                                                                   routers_list=routers_list,
                                                                                   switches_list=switches_list,
                                                                                   hosts_list=hosts_list)

        if unused_devices and invalid_lines:
            flash("Unused devices found: {}".format(", ".join(unused_devices)), 'error')
            flash("Invalid lines found: {}".format(", ".join(invalid_lines)), 'error')
            return render_template('add_topology.html', form=form)
        elif not unused_devices and invalid_lines:
            flash("Invalid lines found: {}".format(", ".join(invalid_lines)), 'error')
            return render_template('add_topology.html', form=form)
        elif unused_devices and not invalid_lines:
            flash("Unused devices found: {}".format(", ".join(unused_devices)), 'error')
            return render_template('add_topology.html', form=form)


        duplicate_lines = remove_duplicate_lines(valid_lines)
        if duplicate_lines:
            flash("Duplicate lines found: {}".format(", ".join(duplicate_lines)), 'error')
            return render_template('add_topology.html', form=form)


        form.topology_connections_text.data = cleaned_text


        topo_conn_text = cleaned_text

        soup = BeautifulSoup(form.topology_setup_text.data, 'html.parser')
        plain_text = soup.get_text(separator='\n')
        lines = plain_text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        cleaned_lines = [' '.join(line.split()) for line in non_empty_lines]
        cleaned_text = '\n'.join(cleaned_lines)

        valid_lines_setup, invalid_lines_setup, unused_hosts_setup, duplicate_lines_setup = form.validate_setup_text(cleaned_text=cleaned_text,
                                                                                             controllers_list=controllers_list,
                                                                                             routers_list=routers_list,
                                                                                             hosts_list=hosts_list)

        if invalid_lines_setup and duplicate_lines_setup and unused_hosts_setup:
            flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
            flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
            flash("Duplicate lines found: {}".format(", ".join(duplicate_lines_setup)), 'error')
            return render_template('add_topology.html', form=form)
        elif invalid_lines_setup and duplicate_lines_setup:
            flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
            flash("Duplicate lines found: {}".format(", ".join(duplicate_lines)), 'error')
            return render_template('add_topology.html', form=form)
        elif invalid_lines_setup and unused_hosts_setup:
            flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
            flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
            return render_template('add_topology.html', form=form)
        elif duplicate_lines_setup and unused_hosts_setup:
            flash("Duplicate lines found: {}".format(", ".join(duplicate_lines_setup)), 'error')
            flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
            return render_template('add_topology.html', form=form)
        elif duplicate_lines_setup and not unused_hosts_setup and not invalid_lines_setup:
            flash("Duplicate lines found: {}".format(", ".join(duplicate_lines_setup)), 'error')
            return render_template('add_topology.html', form=form)
        elif unused_hosts_setup and not invalid_lines_setup and not duplicate_lines_setup:
            flash("Unused hosts found: {}".format(", ".join(unused_hosts_setup)), 'error')
            return render_template('add_topology.html', form=form)
        elif invalid_lines_setup and not unused_hosts_setup and not duplicate_lines_setup:
            flash("Invalid lines found: {}".format(", ".join(invalid_lines_setup)), 'error')
            return render_template('add_topology.html', form=form)

        form.topology_setup_text.data = cleaned_text

        topo_setup_text = cleaned_text

        post = Topologies(topology_name=form.topology_name.data,
                          topology_description=form.topology_description.data,
                          topology_creator_id=topology_creator,
                          topology_controllers_nr=form.topology_controllers_nr.data,
                          topology_controllers_names=form.topology_controllers_names.data,
                          topology_routers_nr=form.topology_routers_nr.data,
                          topology_routers_names=form.topology_routers_names.data,
                          topology_switches_nr=form.topology_switches_nr.data,
                          topology_switches_names=form.topology_switches_names.data,
                          topology_hosts_nr=form.topology_hosts_nr.data,
                          topology_hosts_names=form.topology_hosts_names.data,
                          topology_connections_text=form.topology_connections_text.data,
                          topology_setup_text=form.topology_setup_text.data
                          )

        # Add topology to database
        db.session.add(post)
        db.session.commit()

        # Create topology file with .py extension

        directory_path = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                      f"user_{topology_creator}", f"created/{form.topology_name.data}")
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        create_topology_script(topo_conn_text=topo_conn_text,
                               topo_setup_text=topo_setup_text,
                               hosts_names=hosts_list,
                               controllers_names=controllers_list,
                               switches_names=switches_list,
                               routers_names=routers_list,
                               directory_path=directory_path,
                               file_name=form.topology_name.data)


        # Clear the form
        form.topology_name.data = ''
        form.topology_description.data = ''
        form.topology_controllers_nr.raw_data = ['']
        form.topology_controllers_names.data = ''
        form.topology_routers_nr.raw_data = ['']
        form.topology_routers_names.data = ''
        form.topology_switches_nr.raw_data = ['']
        form.topology_switches_names.data = ''
        form.topology_hosts_nr.raw_data = ['']
        form.topology_hosts_names.data = ''
        form.topology_connections_text.data = ''
        form.topology_setup_text.data = ''
        # form.topology_creator.data = ''

        # Return message
        flash("Topology submitted successfully!")
        return redirect(url_for('topologies'))
        # return render_template("topologies.html", topologies=topologies)

    else:
        return render_template("add_topology.html", form=form)




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
@login_required
def update(id):
    form = RegisterForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.full_name = request.form["full_name"]
        name_to_update.master_name = request.form["master_name"]
        try:
            db.session.commit()
            flash("User information updated successfully!")
            return redirect(url_for('dashboard'))
        except:
            flash("ERROR!")
            return render_template("update.html", form=form, name_to_update=name_to_update, id=id)

    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)





@app.route('/user/register', methods=['GET','POST'])
def add_user():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    full_name = None
    form = RegisterForm()
    if form.validate_on_submit():
        # user = Users.query.filter_by(email=form.email.data).first()
        # if user is None:
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
        return redirect(url_for('login'))
    return render_template("add_user.html", form=form,
                           full_name=full_name)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

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


@app.route("/run_script/<string:topology_name>")
@login_required
def run_script(topology_name):
    user_scripts_dir = os.path.join("/home/razvan/Disertatie/disertatie/TopologiesScripts",
                                      f"user_{current_user.id}")

    query_created = Topologies.query.filter_by(topology_name=topology_name)
    query_uploaded = TopologiesUploaded.query.filter_by(topology_name=topology_name)
    topologies_created = query_created.all()
    topologies_uploaded = query_uploaded.all()
    global script_dir_path
    global script_path
    if topologies_created != []:
        script_dir_path = os.path.join(user_scripts_dir, f"created/{topology_name}")
        files = os.listdir(script_dir_path)
        for file in files:
            if file.endswith(".py"):
                script_path = os.path.join(script_dir_path, file)
                break
    elif topologies_uploaded != []:
        script_dir_path = os.path.join(user_scripts_dir, f"uploaded/{topology_name}")
        files = os.listdir(script_dir_path)
        for file in files:
            if file.endswith(".py"):
                script_path = os.path.join(script_dir_path, file)
                break

    global captures_dir_path
    if topologies_created != []:
        captures_dir_path = os.path.join(user_scripts_dir, f"created/{topology_name}/captures")
    elif topologies_uploaded != []:
        captures_dir_path = os.path.join(user_scripts_dir, f"uploaded/{topology_name}/captures")

    if not os.path.exists(captures_dir_path):
        os.mkdir(captures_dir_path)

    capture_files = [file for file in os.listdir(captures_dir_path) if file.endswith('.pcap')]
    if capture_files:
        capture_files.sort(key=lambda x: os.path.getctime(os.path.join(captures_dir_path, x)), reverse=True)



    with open(f"{script_dir_path}/logfile.log", "w") as logfile:
        logfile.close()


    return render_template('run_script.html', topology_name=topology_name, capture_files=capture_files)


@app.route('/start_script', methods=['GET'])
@login_required
def start_script():
    print(">>>> AM APASAT START SCRIPT")

    subprocess.run(["sudo", 'fuser', '-k', '6653/tcp'])
    subprocess.run(["sudo", 'mn', '-c'])
    # DE PUS LOGICA SA FAC RESTART DE SCRIPT DACA PORNESC IAR
    with open(f"{script_dir_path}/logfile.log", "w") as logfile:
        logfile.close()

    global proc
    proc = subprocess.Popen(["sudo", "python3", f"{script_path}"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    return 'Script started'

@app.route('/update_log')
@login_required
def stream_logfile():
    with open(f"{script_dir_path}/logfile.log", 'r') as file:
        while True:
            line = file.readline()
            if not line:
                time.sleep(1)  # Sleep for a second if the file is empty
                continue
            yield f"data: {line}\n\n"


@app.route('/stream')
@login_required
def stream():
    return Response(stream_logfile(), mimetype='text/event-stream')


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message = request.form['message']
    logging.basicConfig(format='%(message)s', filename=f"{script_dir_path}/logfile.log", filemode='a', level=logging.INFO)
    logging.info(f"\nCOMMAND: {message}\n")
    if message.startswith("sh "):
        message = message.rstrip() + f" >> {script_dir_path}/logfile.log"
        proc.stdin.write(message.encode())
        proc.stdin.flush()
        proc.stdin.write("\n".encode())
        proc.stdin.flush()
    else:
        proc.stdin.write(message.encode())
        proc.stdin.flush()
        proc.stdin.write("\n".encode())
        proc.stdin.flush()
    # logging.basicConfig(format='%(message)s', filename='logfile.log', filemode='a', level=logging.INFO)
    # logging.info(f"\nCOMMAND: {message}\n")
    # Do something with the message, e.g., log it
    # with open('logfile.log', 'a') as file:
    #     file.write(f'User: {message}\n')

    return 'Message sent'


@app.route('/stop_script', methods=['GET'])
@login_required
def stop_script():
    if proc:
        proc.stdin.write('\x03'.encode())
        proc.stdin.flush()
        return 'Command Stopped'
    else:
        return 'No running script to stop'


@app.route('/stop_process', methods=['GET'])
@login_required
def stop_process():
    if proc:
        logging.basicConfig(format='%(message)s', filename=f"{script_dir_path}/logfile.log", filemode='a', level=logging.INFO)
        proc.stdin.write('\x03'.encode())
        proc.stdin.flush()
        logging.info(f"\nCOMMAND: exit\n")
        proc.stdin.write('\nexit\n'.encode())
        proc.stdin.flush()
        proc.terminate()
        subprocess.run(["sudo", 'mn', '-c'])
        return 'Process stopped'
    else:
        return 'No running process to stop'



@app.route("/get_interfaces", methods=["GET"])
@login_required
def get_interfaces():
    result = subprocess.run(["ifconfig"], stdout=subprocess.PIPE, text=True)
    interfaces = result.stdout.split("\n\n")

    available_interfaces = []
    for interface in interfaces:
        if "ens33" in interface or "lo" in interface:
            continue
        interface_name = interface.split(":")[0]
        available_interfaces.append(interface_name)
    available_interfaces.append("lo")
    available_interfaces.remove("")

    return jsonify(available_interfaces)



@app.route('/start_capture', methods=['POST'])
@login_required
def start_capture():
    interface = request.form['interface']
    capture_name = request.form['name']

    if interface == "Loopback":
        interface_name = "lo"
    else:
        interface_name = interface

    # Check if the capture name is valid
    if not is_valid_capture_name(capture_name):
        return 'Invalid capture name'

    # captures_output_dir = os.path.join(f"{script_dir_path}", "captures")
    print(f">>>>CAPTURES DIR: {captures_dir_path}")
    # if not os.path.exists(captures_output_dir):
    #     print("SUNT IN IF")
    #     os.mkdir(captures_output_dir)

    global output_path
    output_path = f"{captures_dir_path}/{interface}_{capture_name}.pcap"
    global capture_proc
    capture_proc = subprocess.Popen(["tshark", "-i", interface_name, "-w", output_path], preexec_fn=os.setpgrp)
    return output_path


@app.route('/stop_capture', methods=['GET'])
@login_required
def stop_capture():
    global capture_proc
    if capture_proc:
        os.killpg(os.getpgid(capture_proc.pid), signal.SIGTERM)
        print("executing command")
        commandus = f"sudo chmod 777 {output_path}"
        os.system(commandus)
        print("command executed")
        return output_path
    else:
        return 'No active capture to stop'

@app.route('/download_capture/<filename>', methods=['GET'])
@login_required
def download_capture(filename):
    capture_name = filename + ".pcap"
    file_path = os.path.join(captures_dir_path, capture_name)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

@app.route('/delete_capture', methods=['POST'])
@login_required
def delete_capture():
    capture_name = request.form['filepath']
    capture_name = capture_name + ".pcap"
    file_path = os.path.join(captures_dir_path, capture_name)
    try:
        os.remove(file_path)
        return f"Capture {capture_name} was deleted"
    except Exception as e:
        return f'Error deleting capture: {str(e)}'



def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])

    msg.body = f''' To reset your password, please access the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request, please ignore this request and no changes will be made to you account.

Regards,
Disertatie Demo - Razvan Alexandru
'''
    mail.send(msg)

@app.route('/reset_password', methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('login'))



    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    user = Users.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():

        hashed_passwrd = generate_password_hash(form.password_hash.data, "sha256")
        user.password_hash = hashed_passwrd
        db.session.commit()
        flash("Your password has been updated successfully! You are now able to login into your account")
        return redirect(url_for('login'))

    return render_template('reset_token.html', title='Reset Password', form=form)









