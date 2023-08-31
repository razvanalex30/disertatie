from main import db, app
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# Create Topology Model
class Topologies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topology_name = db.Column(db.String(255))
    topology_description = db.Column(db.Text)
    topology_controllers_nr = db.Column(db.Integer)
    topology_controllers_names = db.Column(db.String(255))
    topology_routers_nr = db.Column(db.Integer)
    topology_routers_names = db.Column(db.String(255))
    topology_switches_nr = db.Column(db.Integer)
    topology_switches_names = db.Column(db.String(255))
    topology_hosts_nr = db.Column(db.Integer)
    topology_hosts_names = db.Column(db.String(255))
    topology_connections_text = db.Column(db.Text)
    topology_setup_text = db.Column(db.Text)
    #topology_creator = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    # Foreign key to link users (refer to primary key)
    topology_creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return f"Topologies('{self.topology_name}', 'TOPOPLOGY CONNECTIONS TEXT: {self.topology_connections_text}', 'CONTROLLERS NAMES: {self.topology_controllers_names}', 'ROUTERS NAMES: {self.topology_routers_names}')"


class TopologiesUploaded(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topology_name = db.Column(db.String(255))
    topology_description = db.Column(db.Text)
    topology_file_path = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    # Foreign key to link users (refer to primary key)
    topology_creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))


    def __repr__(self):
        return f"TopologiesUploaded('{self.topology_name}', 'TOPOLOGY DESCRIPTION: {self.topology_description}', 'TOPOLOGY FILEPATH: {self.topology_file_path}')"



# Create Users Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    master_name = db.Column(db.String(200))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    # A user can have many topologies
    topologies = db.relationship("Topologies", backref="topology_creator", lazy=True)


    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None

        return Users.query.get(user_id)


    @property
    def password(self):
        raise AttributeError("password is not a readable attribute!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


    def __repr__(self):
        return f'Id: {self.id} - Full Name: {self.full_name} - Email: {self.email}'