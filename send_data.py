from flask import Flask, redirect, url_for, request, jsonify, render_template, request
from user_form import SignUpForm
import json
app = Flask(__name__, template_folder='/home/razvan/Disertatie/disertatie/HTMLpages')
app.config["SECRET_KEY"] = 'disertatie'

def set_username(username: str):
    return username

@app.route('/homepage')
def homepage():
    topologies = [
        {'id': 1, 'name': 'topologie1'},
        {'id': 2, 'name': 'topologie2'},
        {'id': 3, 'name': 'topologie3'}
    ]
    username = set_username("putza")
    return render_template('home.html', user = username, admin=True, topologies=topologies)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.is_submitted():
        result = request.form.to_dict()
        result.pop("submit")
        return render_template("user.html", result = result)
    return render_template('signup.html', form=form)




if __name__ == '__main__':
    app.run()