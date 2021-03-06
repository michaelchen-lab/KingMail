import pandas as pd
import os, requests
from collections import OrderedDict
import itertools
from email_mod import send_email_mod

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=['GET','POST'])
def login():
    """
    Function: Sign-in page
    """
    success = request.args.get('success',False)
    update_settings = request.args.get('update',False)
    if request.method == 'GET':
        if 'username' in session:
            session.clear()
        return render_template("login.html", error=False, success=success, update=update_settings)
    else:
        email, password = request.form.get("Email"), request.form.get("Password")
        df = pd.read_sql('SELECT * from "users"',con=engine)
        if not df[((df['email'] == email) & (df['password'] == password))].empty:
            user = df[((df['email'] == email) & (df['password'] == password))]
            first, last, email_password, email_type = user['first_name'].tolist()[0], user['last_name'].tolist()[0], user['email_password'].tolist()[0], user['email_type'].tolist()[0]

            ## add user settings to session for future use
            session['username'], session['email'] = first + ' ' + last, email
            session['email_password'], session['email_type'] = email_password, email_type

            return redirect(url_for("home"), code=307) ## change to POST request
        else:
            return render_template("login.html", error=True, success=success, update=update_settings)

@app.route("/register", methods=['GET','POST'])
def register():
    """
    Function: Registration page
    """
    if request.method == 'GET':
        return render_template("register.html", error=False)
    else:
        ## Add username and password to database
        first, last, email, pass01, pass02 = request.form.get('FirstName'), request.form.get('LastName'), request.form.get('Email'), request.form.get('Password01'), request.form.get('Password02')
        if pass01 != pass02:
            return render_template("register.html", error=True)
        else:
            db.execute("INSERT INTO users VALUES ('{}','{}','{}','{}','{}','{}')".format(str(first), str(last), str(email), '', str(pass01),'None'))
            db.commit()
            return redirect(url_for('login', success=True))

@app.route("/home", methods=["GET", "POST"])
def home():
    """
    Function: Search bar to find movies
    """
    if 'username' in session:
        username = session['username']
        return render_template("home.html", user=username)
    else:
        return redirect(url_for('login'))

@app.route("/class/all", methods=["GET","POST"])
def class_list():
    """
    Function: Show all of user's classes
    """
    if 'username' in session:
        df = pd.read_sql('SELECT * from "email_lists"',con=engine)
        if df.empty:
            classes = ''
        else:
            classes = dict(zip(df[df['user_email'] == session['email']]['class'].tolist(), df[df['user_email'] == session['email']]['total'].tolist()))
        message = request.args.get("message", default=None)
        return render_template("class_list.html", classes=classes, message=message, user=session['username'])
    else:
        return redirect(url_for('login'))

@app.route("/class/add", methods=["GET","POST"])
def add_class():
    """
    Function: Add class (names and emails)
        1. GET request --- shows form to create a table (inputs: table name, first student name and email)
        2. POST request --- either shows another form to add a student name and email or saves table to database
    """
    if 'username' in session:
        if request.method == "GET":
            if 'student_list_name' not in session:
                return render_template("add_class.html", user=session['username'], initial=True, alert=None)
            else:
                edit = request.args.get('edit','no')
                if edit == 'no':
                    return render_template("add_class.html", user=session['username'], initial=False, class_name=session['student_list_name'], name_list=session['student_list'], alert=None)

                if edit == 'delete_last':
                    od = OrderedDict(session['student_list'])
                    od.popitem()
                    session['student_list'] = dict(od)

                    return render_template("add_class.html", user=session['username'], initial=False, class_name=session['student_list_name'], name_list=session['student_list'], alert='delete_last')

                elif edit == 'delete_all':
                    del session['student_list_name'], session['student_list']

                    return render_template("add_class.html", user=session['username'], initial=True, alert='delete_all')
        else:

            ## Save form data
            data = request.form.to_dict()
            name, email = data['name'], data['email']
            if 'class_name' in data:
                session['student_list_name'] = data['class_name']
                session['student_list'] = {name:email}
            else:
                session['student_list'][name] = email

            if 'add' in data.keys():
                ## Add another student and email
                return render_template("add_class.html", user=session['username'], initial=False, class_name=session['student_list_name'], name_list=session['student_list'], alert=None)
            else:
                ## commit student_list to database
                student_list_name = session['student_list_name']
                students = ','.join(map(str, [student for student in session['student_list'].keys()]))
                emails = ','.join(map(str, [email for email in session['student_list'].values()]))
                db.execute("INSERT INTO email_lists VALUES ('{}','{}','{}','{}','{}')".format(session['email'], session['student_list_name'], students, emails, str(len(session['student_list']))))
                db.commit()

                del session['student_list_name'], session['student_list']

                return redirect(url_for("particular_class", one_class=student_list_name, action='new', show_editor=False))

    else:
        return redirect(url_for('login'))

@app.route("/<one_class>/<show_editor>", methods=["GET","POST"])
def particular_class(one_class, show_editor):
    """
    Function:
        1. Show names and emails of a particular class
        2. 'delete' action --- delete one name and its corresponding email
        3. 'delete_all' action --- deletes the entire table
        4. 'class_name' form --- changes the name of table
        5. 'student_name' and 'student_email' form --- adds one name and email to table
    """
    if 'username' in session:
        if request.method == 'GET':
            action = request.args.get('action', default=None)
            data = request.args.to_dict()

            ## import student list from sql database
            df = pd.read_sql('SELECT * from "email_lists"',con=engine)
            current_class = df[((df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')))]
            student_list = dict(zip(current_class['names'].tolist()[0].split(','), current_class['emails'].tolist()[0].split(',')))

            if action == 'delete':
                student, email = request.args.get('student'), request.args.get('email')
                ## delete one student and email from database
                if student_list[student] == email:
                    del student_list[student]
                    df.loc[(df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')), "names"] = ','.join(map(str, [student for student in student_list.keys()]))
                    df.loc[(df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')), "emails"] = ','.join(map(str, [email for email in student_list.values()]))
                    df.loc[(df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')), "total"] = len(student_list)

                    df.to_sql('email_lists', engine, index=False, method='multi', if_exists='replace')
            elif action == 'delete_all':
                ## delete whole list from database
                db.execute("DELETE FROM email_lists WHERE user_email='{0}' AND class='{1}'".format(session['email'], one_class.replace('_',' ')))
                db.commit()

                return redirect(url_for('class_list', message='deleted'))

            ## Execute forms from class editor
            if 'class_name' in data:
                db.execute("UPDATE email_lists SET class='{0}' WHERE user_email='{1}' AND class='{2}'".format(data['class_name'], session['email'], one_class.replace('_',' ')))
                db.commit()

                one_class = data['class_name']
            elif 'student_name' in data and 'student_email' in data:
                student_list[data['student_name']] = data['student_email']
                df.loc[(df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')), "names"] = ','.join(map(str, [student for student in student_list.keys()]))
                df.loc[(df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')), "emails"] = ','.join(map(str, [email for email in student_list.values()]))
                df.loc[(df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')), "total"] = len(student_list)

                df.to_sql('email_lists', engine, index=False, method='multi', if_exists='replace')

            ## return for action == None, 'new', 'delete', 'show_editor'
            return render_template('class.html', one_class=one_class, student_list=student_list, action=action, user=session['username'], show_editor=show_editor)
        else:
            pass
    else:
        return redirect(url_for('login'))

@app.route("/send_email", methods=["GET","POST"])
def send_email():
    """
    Function: Send email to classes
        1. GET request --- Displays email form to user
        2. POST request --- Sends email using inputs from GET request form
    """
    if "username" in session:
        df = pd.read_sql('SELECT * from "email_lists"',con=engine)
        if request.method == 'GET':
            ## Email form
            classes = df.loc[df['user_email'] == session['email'], 'class'].tolist()

            return render_template('send_email.html', classes=classes, sucess=False, user=session['username'])
        else:
            ## Send email to recipients
            data = request.form.to_dict()
            subject, body, attachment = data['subject'], data['body'], data['attachments']
            del data['subject'], data['body'], data['attachments']

            classes = [one_class.replace('_',' ') for one_class in data.keys()]
            email_lists = df[((df['user_email'] == session['email']) & (df['class'].isin(classes)))]['emails'].tolist()
            email_lists = [email_list.split(',') for email_list in email_lists]
            receiver_emails = list(itertools.chain.from_iterable(email_lists))

            ## send email through module
            send_email_mod(
                sender_email=session['email'],
                sender_password=session['email_password'],
                receiver_emails=receiver_emails,
                email_type=session['email_type'],
                subject=subject, body=body, attachment=attachment
            )

            return render_template('send_email.html', classes=classes, sucess=False, user=session['username'])

    else:
        return redirect(url_for("login"))

@app.route("/settings", methods=["GET","POST"])
def email_settings():
    """
    Function: User Email Settings
        1. GET request --- Allows user to edit current settings through form
        2. POST request --- Enters new settings from GET request form to database. Returns to Login page.
    """
    if "username" in session:
        df = pd.read_sql('SELECT * from "users"',con=engine)
        if request.method == 'GET':
            user_settings = dict(zip(df.columns.values.tolist(), df.loc[df['email'] == session['email']].values.tolist()[0]))
            return render_template('settings.html', user_settings=user_settings, user=session['username'])
        else:
            new_user_settings = request.form.to_dict()
            df.loc[df['email'] == session['email'], list(df.columns.values)] = [setting for setting in new_user_settings.values()]
            df.to_sql('users', engine, index=False, method='multi', if_exists='replace')

            return redirect(url_for("login", success=True))
    else:
        return redirect(url_for("login"))
