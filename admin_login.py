#dependecies
from flask import Flask, render_template, url_for, redirect,request,flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField,SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from datetime import datetime
from zipfile import ZipFile
import io

# objective of the flask app
app = Flask(__name__)
# creating flask Bcrypt object  for user password encryption 
bcrypt = Bcrypt(app)
# flask app configuration for mysql database connection
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3306/decode_biome_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@0.0.0.0:3306/decode_biome_db' #for server IP address
# aws mysql server 
# app.config['SQLALCHEMY_DATABASE_URI'] ='mysql://root:J96)TJ1tO5I_(Kj#@34.100.193.69/dabiomedb' 
#disable SQLAlchemy's default behavior of tracking modification to the database object
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#creating an object for SQLAlchemy class and binds to the Flask application
db = SQLAlchemy(app)

#a crypographic key that is used to encrypt and sign data such as session cookies and other secure tokens
app.config['SECRET_KEY'] = 'thisisasecretkey'

from server_main import db, app
# creating an ibject for login user authenticaton and session manangenment functionality for flask web applications
login_manager = LoginManager()
#init_app() method binds the login_manager object to the flask application instance, allowing to work the application's request and response
login_manager.init_app(app)
#login_view sets the name of  the view that should be used for login
login_manager.login_view = 'login'

#Flask login helps to load the user from the database in order to verify their credentials
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def validate_decodeage_email(form,field):
    if not field.data.endswith('@decodeage.com'):
        raise ValidationError("Email id doesnot belong to DecodeAge")
  
#flask class for user id email password
#db.Model class is provided by Flask-SQLAlchemy and is used as the base class for all database models
#db.UserMixin class is provided by Flask-Login and adds methods and attributes that are used for authenticatoin and session management
class User(db.Model, UserMixin):
   # __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.Text, nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

# FlakForm is a class provided by Flak-WTF that is used for creating class that should include some html paramters
#creating registration form usnig flask form
class RegisterForm(FlaskForm):
    email = EmailField(validators=[InputRequired(), Length(min=4, max=30),validate_decodeage_email], render_kw={"placeholder": "Email"})

    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), Length(min=5, max=20)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(validators=[InputRequired(), Length(min=5, max=20)], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Register')
# validating username,email using flask Validation error method
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')
        
    def validate_email(self, email):
        existing_user_email = User.query.filter_by(
            email=email.data).first()
        if existing_user_email:
            raise ValidationError('That email already exists. Please choose a different one.')
#creating login page using flask-form 
class LoginForm(FlaskForm):
    # username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    email=StringField(validators=[InputRequired(),Length(min=4,max=50)],render_kw={"placeholder":"Email"})

    password = PasswordField(validators=[InputRequired(), Length(min=5, max=20)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField('Login')
 #Creating Metadata  class for mysql database 
 # Class name and entry field should match with database  
class Metadata(db.Model):
    Barcode = db.Column(db.String(53), primary_key=True, nullable=True)
    #curated_by=db.Column(db.String(53),nullable=True)


@app.route('/')
def home():
    return render_template('home.html')

#creating route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        #object creating for LoginForm class 
        form = LoginForm()
        user=User.query.filter_by(email=form.email.data).first()
        print(f"Email:{form.email.data}")
        print(f"form.validate_on_submit:{form.validate_on_submit()}")
        print(f"Form errors:{form.errors}")
        #checking user credential validation using user_name
        if form.validate_on_submit():
           #fetching user name from the database
            # user = User.query.filter_by(username=form.username.data).first()
            user=User.query.filter_by(email=form.email.data).first()
            #checking password which is encrypted if it is there with fellow username 
            if user:
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user)
                    # return redirect('dashboard')
                    return render_template("dashboard.html")
                else:
                    #print("Else error")
                    #return redirect('login')
                    return "wrong password for this email"
            else:
                # return "No account found with this email"
                raise ValidationError("No account for this email")
            # return redirect("dashboard")
        else:
            print("this is coming from else statement")
        
    except Exception as e:
        return f"An error has occured: {str(e)}"
    return render_template('login.html', form=form)

#creating dashboard route, methods GET and POST helps to send the data from html to the flask end 
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

#creating logout route
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')

#creating register route for register page
@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    print("form.validate_on_submit()",form.validate_on_submit())
    if form.validate_on_submit():
        #generating password in hash code 
        hashed_password = bcrypt.generate_password_hash(form.password.data)   
        new_user = User(email=form.email.data,username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')

    return render_template('register.html', form=form)