# from flask import Flask, redirect, url_for, request, jsonify, render_template, request
# from user_form import SignUpForm
# import json
# app = Flask(__name__, template_folder='/home/razvan/Disertatie/disertatie/HTMLpages')
# app.config["SECRET_KEY"] = 'disertatie'
#
# def set_username(username: str):
#     return username
#
# @app.route('/homepage')
# def homepage():
#     topologies = [
#         {'id': 1, 'name': 'topologie1'},
#         {'id': 2, 'name': 'topologie2'},
#         {'id': 3, 'name': 'topologie3'}
#     ]
#     username = set_username("putza")
#     return render_template('home.html', user = username, admin=True, topologies=topologies)
#
# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     form = SignUpForm()
#     if form.is_submitted():
#         result = request.form.to_dict()
#         result.pop("submit")
#         return render_template("user.html", result = result)
#     return render_template('signup.html', form=form)


import re

def parse_input(text_user):
    # Check if input is a string
    if not isinstance(text_user, str):
        raise TypeError("Input must be a string.")

    # Validate input format using regex
    pattern = r"^(?=.*[a-zA-Z])(?:[a-zA-Z0-9]+(?:,[a-zA-Z0-9]+)*)$"
    if not re.match(pattern, text_user):
        raise ValueError("The provided values are not correct, please try again")

    # Split the input string into a list
    values = text_user.split(',')

    return values


user_input = input("Enter values separated by commas: ")
try:
    parsed_values = parse_input(user_input)
    print(parsed_values)
except (TypeError, ValueError) as e:
    print("Error:", str(e))

# if __name__ == '__main__':
#     app.run()