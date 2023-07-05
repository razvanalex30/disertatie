from flask import render_template, flash, request, redirect, url_for
from main import app
from main import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from main.models import Users, Topologies
from main.webforms import RegisterForm, LoginForm, PasswordForm, TopologyForm, SearchForm
from main import login_manager




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
def search():
    form = SearchForm()
    topologies = Topologies.query
    if form.validate_on_submit():
        topology.searched = form.searched.data
        topologies = topologies.filter(Topologies.topology_description.like('%' + topology.searched + '%'))
        topologies = topologies.order_by(Topologies.topology_name).all()
        return render_template("search.html", form=form, searched=topology.searched, topologies=topologies)



# Show Topologies

@app.route("/topologies")
@login_required
def topologies():
    # Grab all the topologies from the database
    topologies = Topologies.query.order_by(Topologies.date_created)

    return render_template("topologies.html", topologies=topologies)


@app.route("/topologies/<int:id>")
@login_required
def topology(id):
    topology = Topologies.query.get_or_404(id)
    return render_template("topology.html", topology=topology)

@app.route("/topologies/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_topology(id):
    topology = Topologies.query.get_or_404(id)
    form = TopologyForm()
    if form.validate_on_submit():
        topology.topology_name = form.topology_name.data
        topology.topology_description = form.topology_description.data
        # topology.topology_creator = form.topology_creator.data
        # Update database
        db.session.add(topology)
        db.session.commit()
        flash("Topology updated successfully!")
        return redirect(url_for('topology', id=topology.id))

    if current_user.id == topology.topology_creator_id:
        form.topology_name.data = topology.topology_name
        form.topology_description.data = topology.topology_description
        # form.topology_creator.data = topology.topology_creator

        return render_template("edit_topology.html", form=form)

    else:
        flash("You are not authorized to edit this post!")
        topologies = Topologies.query.order_by(Topologies.date_created)

        return render_template("topologies.html", topologies=topologies)

@app.route("/topologies/delete/<int:id>")
@login_required
def delete_topology(id):
    topology_to_delete = Topologies.query.get_or_404(id)
    id = current_user.id
    if id == topology_to_delete.topology_creator.id:

        try:
            db.session.delete(topology_to_delete)
            db.session.commit()
            # Return a message
            flash("Topology was deleted!")
            topologies = Topologies.query.order_by(Topologies.date_created)
            return render_template("topologies.html", topologies=topologies)

        except:
            # Return error message
            flash("ERROR when deleting Topology, please try again")
            topologies = Topologies.query.order_by(Topologies.date_created)

            return render_template("topologies.html", topologies=topologies)
    else:
        # Return a message
        flash("You are not authorized to delete this topology!")
        topologies = Topologies.query.order_by(Topologies.date_created)
        return render_template("topologies.html", topologies=topologies)


@app.route("/add_topology", methods=["GET","POST"])
@login_required
def add_topology():
    form = TopologyForm()

    if form.validate_on_submit():
        topology_creator = current_user.id
        post = Topologies(topology_name=form.topology_name.data, topology_description=form.topology_description.data,
                          topology_creator_id=topology_creator,
                          topology_controllers_nr=form.topology_controllers_nr.data,
                          topology_controllers_names=form.topology_controllers_names.data,
                          topology_switches_nr=form.topology_switches_nr.data,
                          topology_switches_names=form.topology_switches_names.data,
                          topology_hosts_nr=form.topology_hosts_nr.data,
                          topology_hosts_names=form.topology_hosts_names.data,
                          topology_connections_text=form.topology_connections_text.data,
                          topology_setup_text=form.topology_setup_text.data
                          )



        if form.validate_controllers_switches_hosts_names():
            # Add topology to database
            db.session.add(post)
            db.session.commit()

            # Clear the form
            form.topology_name.data = ''
            form.topology_description.data = ''
            form.topology_controllers_nr.raw_data = ['']
            form.topology_controllers_names.data = ''
            form.topology_switches_nr.raw_data = ['']
            form.topology_switches_names.data = ''
            form.topology_hosts_nr.raw_data = ['']
            form.topology_hosts_names.data = ''
            form.topology_connections_text.data = ''
            form.topology_setup_text.data = ''
            # form.topology_creator.data = ''

            # Return message
            flash("Topology submitted successfully!")
        else:
            flash("There are duplicates, please check the names entered for your nodes!")

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
        name_to_update.email = request.form["email"]
        name_to_update.master_name = request.form["master_name"]
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
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


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     full_name = None
#     form = RegisterForm()
#     # Validate Form
#     if form.validate_on_submit():
#         full_name = form.full_name.data
#         form.full_name.data = ''
#         flash("Account registered successfully!")
#
#     return render_template("register.html", full_name=full_name, form=form)