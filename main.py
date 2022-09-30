from werkzeug.middleware.proxy_fix import ProxyFix
import json,os,hashlib,datetime,time,logging
import flask,requests,uuid,datetime
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

"""
Endpoint: https://spectrumsurveys.com/surveydone
st: {
    21: completed
    17: over quota
    18: termination
    30: dedupe
    20: quality
}
transaction_id: user.get_id() or token
"""

app = Flask(__name__)
application = app
app.secret_key = '9TMZDPzyUpnu7ZN4X88k6mFiW4L3a4Lsijnv9CxFL4vBZcjzAxGvEtbwSJxCZY'
app.config['MONGO_DBNAME'] = 'annotation'
if os.path.isfile('.cred.json'):
    app.config["MONGO_URI"] = json.load(open('.cred.json'))['mongodb']
else:
    app.config["MONGO_URI"] = os.environ['mongodb']
    
app.config['LOGIN_URL'] = "/login"

mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = u"Bonvolu ensaluti por uzi tiun paĝon."
csrf = CSRFProtect(app)

survey = json.load(open('survey.json'))

def process_calendar_data():
    data = json.load(open('calendar.json'))
    start_date = datetime.date(2022,10,25)
    calendar = []
    fmt = "%b %d"
    for period in data:
        early_weeks = datetime.timedelta(weeks=int(period['early_start']))
        late_weeks = datetime.timedelta(weeks=int(period['late_start']))
        early = start_date + early_weeks
        late = start_date + late_weeks
        
        early_label = early.strftime(fmt)
        late_label=late.strftime(fmt)
        days = round((late-early).total_seconds()/(60*60*24))
        calendar.append({
            'early': early,
            'early_label': early_label,
            'late': late,
            'late_label': late_label,
            'days': days,
            'weeks': round(days/7),
            'label': f'{early_label} - {late_label}',
            'rates': period['rates']
        })
    return data,calendar
raw_calendar,calendar = process_calendar_data()
        

def get_ip():
    logging.error(str(request.environ))
    logging.warning(str(request.remote_addr))
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

class User(UserMixin):
    def __init__(self, token):
        self.token = token

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False
    
    def set_consent(self):
        update = {"$set": { 'consented': True } }
        mongo.db.users.update_one({'token': self.token},update)
        
    def has_consent(self):
        user = mongo.db.users.find_one({'token': self.token})
        return user is not None and 'consented' in user and user['consented']
    
    def set_old(self,is_old=True):
        update = {"$set": { 'is_old': is_old } }
        mongo.db.users.update_one({'token': self.token},update)
        
    def is_old(self):
        user = mongo.db.users.find_one({'token': self.token})
        return user is not None and 'is_old' in user and user['is_old']
    
    def get_id(self):
        return self.token
    
    def set_answer(self,key,answer,duration=-1):
        update = {
                    "$set": {
                        key: answer,
                        f"{key}_duration": duration
                    }
                }
        mongo.db.users.update_one({'token': self.token},update)
    def completed_survey(self):
        update = {
            "$set": {"completed_survey": True}
        }
        mongo.db.users.update_one({'token': self.token},update)
        
    def set_discount(self,index,form,duration):
        print(list(form))
        date = calendar[index]
        answers = {}
        answers[f'calendar_{index}'] = raw_calendar[index]
        answers[f'calendar_{index}_duration'] = duration
        for i,rate in enumerate(date['rates']):
            early,late = rate
            print(f'{index}-{i}-{early}',f'{index}-{i}-{late}')
            answers[f'calendar_{index}_{i}_{early}'] = form.get(f'{index}-{i}-{early}',None)
            answers[f'calendar_{index}_{i}_{late}'] = form.get(f'{index}-{i}-{late}',None)
        update = {
            "$set": {
                f"completed_calendar_{index}": True,
            } | answers
        }
        mongo.db.users.update_one({'token': self.token},update)
        
    @app.route('/login', methods=['GET'])
    def login():
        token = request.args.get('transaction_id',request.args.get('token',str(uuid.uuid4())))
        session['token'] = token
        session['terminate'] = f"https://spectrumsurveys.com/surveydone?st=18&transaction_id={session['token']}"
        logged_in = User.login_user(token)
        if logged_in:
            return redirect('/')
        else:
            return redirect('/login/failed')

    @app.route('/login/failed', methods=['GET'])
    def failed_login():
        return {'error': 'Failed to login.'}
        
    #Find user,then call login_user
    @staticmethod
    def login_user(token):
        user = mongo.db.users.find_one({'token': token})
        timestamp = datetime.datetime.now()
        ip_addr = get_ip()
        if user is None:
            mongo.db.users.insert_one({
                'token': token,
                'created_ip': ip_addr,
                'created_at': timestamp,
                'accessed_ip': ip_addr,
                'accessed_at': timestamp,
                'login_ips': [ip_addr],
                'login_timestamps': [timestamp]
            })
            login_user(User(token))
        elif password == user['password']:
            mongo.db.users.update_one({'token': token},{
                '$push': {
                    'login_ips': ip_addr,
                    'login_timestamps': timestamp,
                },
                '$set': {
                    'accessed_at': timestamp,
                    'accessed_ip': ip_addr
                }
            })
            login_user(User(token))
        else:
            return False
        return True


@login_manager.user_loader
def load_user(username):
    return User(username)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

@app.route('/',methods=["GET"])
@login_required
def index():
    return redirect('/landing')

@app.route('/landing',methods=["GET"])
@login_required
def landing():
    return render_template('landing_page.html')

@app.route('/landing/accept',methods=["POST"])
@login_required
def accept_consent():
    current_user.set_consent()
    return redirect('/survey')


#Entry point to the survey
@app.route('/survey/<int:index>',methods=["GET"])
@login_required
def survey_page_specific(index):
    session['survey_index'] = index
    return redirect('/survey')

#Entry point to the survey
@app.route('/survey',methods=["GET"])
@login_required
def survey_page():
    if not current_user.has_consent():
        return redirect('/landing')
    index = session.get('survey_index',0)
    question = survey[index]
    progress = f'{round(index/len(survey)*100)}%'
    start=time.time()
    return render_template(f'question.html',progress=progress,index=index,start=start,**question)


#Must be refferred from previous survey question
@app.route('/survey',methods=["POST"])
@login_required
def survey_page_index():
    #Parse the answer
    index = request.form.get('index',None)
    key = request.form.get('key',None)
    answer = request.form.get('answer',None)
    
    #Check if malformed response
    if index is None or answer is None or answer is None:
        return {'error': "Something went wrong with your survey!","index": index,"key":key,"answer":answer}
    
    #Key specific control code
    if 'zipcode' in key and len(answer.strip()) != 5:
        start_time = float(request.form.get('start_time',None))
        error = "You must enter a proper zipcode!"
        index = int(index)
        return render_template('question.html',index=index,start=start_time,error=error,**survey[index])
    elif 'age' in key:
        current_user.set_old(int(answer)>=18)
        if int(answer) < 18:
            current_user.set_answer(key,answer)
            return redirect(session['terminate'])
    index = int(index) + 1
    duration = time.time()-float(request.form.get('start_time',None))
    current_user.set_answer(key,answer,duration)
    if index == len(survey):
        current_user.completed_survey()
        return redirect('/calendar/instructions')
    progress = f'{round(index/len(survey)*100)}%'
    start=time.time()
    return render_template('question.html',progress=progress,index=index,start=start,**survey[index])


@app.route('/calendar/instructions',methods=["GET"])
def calendar_instructions():
    return render_template('calendar_instructions.html')



@app.route('/calendar/<int:index>',methods=["GET"])
def goto_date(index):
    session['calendar_index'] = index
    return redirect('/calendar')


@app.route('/calendar',methods=["GET"])
@login_required
def calendar_page():
    if not current_user.has_consent():
        return redirect('/landing')
    index = session.get('calendar_index',0)
    date = calendar[index]
    start = time.time()
    return render_template('calendar.html',start_time=start,index=index,calendar=calendar,**date)

@app.route('/calendar',methods=["POST"])
@login_required
def submit_calendar_page():
    index = request.form.get('index',None)
    if index is None:
        return {'error': "Something went wrong with your survey!","index": index,"key":key,"answer":answer}
    duration = time.time()-float(request.form.get('start_time',None))
    
    current_user.set_discount(int(index),request.form,duration)
    
    index = int(index) + 1
    date = calendar[index]
    start = time.time()
    return render_template('calendar.html',start_time=start,index=index,calendar=calendar,**date)



@app.route('/test',methods=["GET"])
def test_page():
    return dict(os.environ)


if __name__=="__main__":
    app.run(host='0.0.0.0',port='8976',debug=True)
