import pandas as pd
import os, requests
import statistics as stats

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
    if request.method == 'GET':
        if 'username' in session:
            del session['username'] ## remove previous sign-in (if applicable)
        return render_template("login.html")
    else:
        email, password = request.form.get("Email"), request.form.get("Password")
        df = pd.read_sql('SELECT * from "users"',con=engine)
        if not df[((df['email'] == email) & (df['password'] == password))].empty:
            user = df[((df['email'] == email) & (df['password'] == password))]
            first, last = user['first_name'].tolist()[0], user['last_name'].tolist()[0]
            session['username'] = first + ' ' + last
            session['email'] = email
            return redirect(url_for("home"), code=307) ## change to POST request
        else:
            return render_template("retry_login.html")

@app.route("/register", methods=['GET','POST'])
def register():
    """
    Function: Registration page
    """
    if request.method == 'GET':
        return render_template("register.html")
    else:
        ## Add username and password to database
        first, last, email, pass01, pass02 = request.form.get('FirstName'), request.form.get('LastName'), request.form.get('Email'), request.form.get('Password01'), request.form.get('Password02')
        if pass01 != pass02:
            return render_template("retry_sign_up.html")
        else:
            db.execute("INSERT INTO users VALUES ('{}','{}','{}','{}')".format(str(first), str(last), str(email), str(pass01)))
            db.commit()
            return redirect(url_for('login'))

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
        classes = dict(zip(df[df['user_email'] == session['email']]['class'].tolist(), df[df['user_email'] == session['email']]['total'].tolist()))
        return render_template("class_list.html", classes=classes, user=session['username'])
    else:
        return redirect(url_for('login'))

@app.route("/class/add", methods=["GET","POST"])
def add_class():
    """
    Function: Add class (names and emails)
    """
    if 'username' in session:
        if request.method == "GET":
            return render_template("add_class.html", user=session['username'], message=False)
        else:
            return render_template("add_class.html", user=session['username'], message=True)
    else:
        return redirect(url_for('login'))

@app.route("/<one_class>", methods=["GET","POST"])
def particular_class(one_class, action=None, **data):
    """
    Function: Show names and emails of a particular class
    """
    if 'username' in session:
        if request.method == 'GET':
            if action == None:
                df = pd.read_sql('SELECT * from "email_lists"',con=engine)
                current_class = df[((df['user_email'] == session['email']) & (df['class'] == one_class.replace('_',' ')))]
                name_list = dict(zip(current_class['names'].tolist()[0].split(','), current_class['emails'].tolist()[0].split(',')))
                return render_template('class.html', one_class=one_class, name_list=name_list, action=action, user=session['username'])
            elif action == 'delete':
                return render_template('class.html', one_class=one_class, action=action, user=session['username'])
        else:
            pass
    else:
        return redirect(url_for('login'))
