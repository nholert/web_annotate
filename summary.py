from werkzeug.middleware.proxy_fix import ProxyFix
import json,os,hashlib,datetime,time,logging
import flask,requests,uuid,datetime,random
from flask import Blueprint,Flask,request,redirect,render_template,session,flash,abort,make_response
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager,login_required,login_user,UserMixin,current_user
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,RadioField,SelectMultipleField,widgets,HiddenField
from wtforms.validators import DataRequired
from wtforms import validators
from bson.objectid import ObjectId
from urllib.parse import urlparse, urljoin
from flask.sessions import SecureCookieSessionInterface

app = Flask(__name__)
application = app
if os.path.isfile('.cred.json'):
    with open('.cred.json') as f:
        cred = json.load(f)
        app.config["MONGO_URI"] = cred['mongodb']
        app.secret_key = cred['secret']
else:
    app.config["MONGO_URI"] = os.environ['mongodb']
    app.secret_key = os.environ['secret']
app.config['MONGO_DBNAME'] = 'annotation'

app.config['LOGIN_URL'] = "/login"

mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = u"Bonvolu ensaluti por uzi tiun paĝon."
csrf = CSRFProtect(app)

survey = json.load(open('survey.json'))

"""
if __name__=="__main__":
    app.run(host='0.0.0.0',port='8976',debug=True)
"""
