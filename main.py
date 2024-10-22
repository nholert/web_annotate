from werkzeug.middleware.proxy_fix import ProxyFix
import json,os,hashlib,datetime,time,logging
import flask,requests,uuid,datetime,random,statistics
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
if os.path.isfile('.cred.json'):
    with open('.cred.json') as f:
        cred = json.load(f)
        app.config["MONGO_URI"] = cred['mongodb']
        app.secret_key = cred['secret']
        hidden_service = cred['hidden_service']
else:
    app.config["MONGO_URI"] = os.environ['mongodb']
    app.secret_key = os.environ['secret']
    hidden_service = os.environ['hidden_service']
app.config['MONGO_DBNAME'] = 'annotation'

app.config['LOGIN_URL'] = "/login"

mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = u"Bonvolu ensaluti por uzi tiun paĝon."
csrf = CSRFProtect(app)

survey = json.load(open('survey.json'))
calendar_instructions = json.load(open('calendar_instructions.json'))
START_DATE = datetime.date(2024,10,22)
def process_calendar_data():
    data = json.load(open('calendar.json'))
    #start_date = datetime.date(2022,10,25) #Round 1
    start_date = START_DATE #Round 2
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
    return request.environ.get('HTTP_DO_CONNECTING_IP', request.environ.get("REMOTE_ADDR",request.remote_addr))

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
    
    def is_terminated(self):
        user = mongo.db.users.find_one({'token': self.token})
        return user is not None and 'terminated' in user and user['terminated']    
    
    def set_old(self,is_old=True):
        update = {"$set": { 'is_old': is_old } }
        mongo.db.users.update_one({'token': self.token},update)
        
    def is_old(self):
        user = mongo.db.users.find_one({'token': self.token})
        return user is not None and 'is_old' in user and user['is_old']
    
    def get_token(self):
        return self.token
    
    def get_id(self):
        return self.token
    
    #TODO: Rewrite previous getting keys to use the get_key function for coupling.
    def get_key(self,key):
        user = mongo.db.users.find_one({'token': self.token})
        return user is not None and key in user and user[key]
    
    def get_read_calendar_instructions(self):
        return self.get_key('read_calendar_instructions')
    
    def set_read_calendar_instructions(self):
        return self.set_answer('read_calendar_instructions',True)
    
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
        
    def get_progress(self):
        user = mongo.db.users.find_one({'token': self.token})
        return {key: value for key,value in user.items() if 'calendar' in key}
    
    def get_total_duration(self):
        user = mongo.db.users.find_one({'token': self.token})
        return sum([d for key,d in user.items() if 'duration' in key and d!=-1])
    
    #Defines the completion of a calendar page
    def set_discount(self,index,form,duration):
        if not self.get_read_calendar_instructions(): return
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
        token = request.args.get('transaction_id')  # Ensure we always use the provided transaction_id
        if not token:
        # Log and handle the error if no transaction_id is provided by Pure Spectrum
            logging.error("No transaction_id provided by Pure Spectrum")
            return {'error': 'Failed to login.'}
        
        session['token'] = token
        session['terminate'] = f"https://spectrumsurveys.com/surveydone?st=18&transaction_id={session['token']}"
        session['finish'] = f"https://spectrumsurveys.com/surveydone?st=21&transaction_id={session['token']}"
        session['quality'] = f"https://spectrumsurveys.com/surveydone?st=20&transaction_id={session['token']}"
        session['dedupe'] = f"https://spectrumsurveys.com/surveydone?st=30&transaction_id={session['token']}"
        logging.error(f"Generated Finish Redirect URL: {session['finish']}")
        logged_in = User.login_user(token)
        if logged_in:
            return redirect('/')
        else:
            return redirect('/login/failed')

    @app.route('/', methods=['GET'])
    def root_redirect():
    # If transaction_id is present in the root URL, redirect to /login with it
        token = request.args.get('transaction_id')
        if token:
            logging.error(f"transaction_id found in root URL: {token}")
            return redirect(f'/login?transaction_id={token}')
        return redirect('/login')

    @app.route('/login/failed', methods=['GET'])
    def failed_login():
        return {'error': 'Failed to login.'}
        
    #Find user,then call login_user
    @staticmethod
    def login_user(token):
        user = mongo.db.users.find_one({'token': token})
        timestamp = datetime.datetime.now()
        ip_addr = get_ip()
        agent = request.headers.get('User-Agent')
        if user is None:
            mongo.db.users.insert_one({
                'token': token,
                'created_ip': ip_addr,
                'created_at': timestamp,
                'accessed_ip': ip_addr,
                'accessed_at': timestamp,
                'created_user_agent': agent,
                'round': 2,
                'last_user_agent': agent,
                'login_ips': [ip_addr],
                'login_timestamps': [timestamp],
                'user_agents': [agent]
            })
            login_user(User(token))
        else: 
            mongo.db.users.update_one({'token': token},{
                '$push': {
                    'login_ips': ip_addr,
                    'login_timestamps': timestamp,
                    'user_agents': agent
                },
                '$set': {
                    'accessed_at': timestamp,
                    'accessed_ip': ip_addr,
                    'last_user_agent': user_agent
                }
            })
            login_user(User(token))
        
        return True
        
    def get_terminate_redirect(self):
        token = self.get_token()
        return f"https://spectrumsurveys.com/surveydone?st=18&transaction_id={token}"
    def get_finish_redirect(self):
        token = self.get_token()
        return f"https://spectrumsurveys.com/surveydone?st=21&transaction_id={token}"
    def get_quality_redirect(self):
        token = self.get_token()
        return f"https://spectrumsurveys.com/surveydone?st=20&transaction_id={token}"
    def get_dedupe_redirect(self):
        token = self.get_token()
        return f"https://spectrumsurveys.com/surveydone?st=30&transaction_id={token}"


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
    return render_template('landing_page.html',total_questions=len(survey))

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
    if current_user.is_terminated():
        return redirect(current_user.get_dedupe_redirect())
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
            current_user.set_answer('terminated',True)
            return redirect(session['terminate'])
    elif 'head_of_house' in key:
        if 'Financial Dependent' in answer:
            current_user.set_answer(key,answer)
            current_user.set_answer('terminated',True)
            return redirect(session['terminate'])
    elif 'alive' in key:
        if 'eagle' not in answer.lower():
            current_user.set_answer(key,answer)
            current_user.set_answer('terminated',True)
            return redirect(session['quality'])
    index = int(index) + 1
    duration = time.time()-float(request.form.get('start_time',None))
    current_user.set_answer(key,answer,duration)
    if index == len(survey):
        current_user.completed_survey()
        return redirect('/calendar')
    progress = f'{round(index/len(survey)*100)}%'
    start=time.time()
    return render_template('question.html',progress=progress,index=index,start=start,**survey[index])

"""
Decisions
Tokens Left and Right
Lines and Values
Tabs and Dates
Navigation and Submitting
Payment
Example
"""
@app.route('/calendar/instructions',methods=["GET"])
def goto_calendar_instructions():
    return render_template('calendar_instructions.html')


@app.route('/calendar/<int:index>',methods=["GET"])
def goto_date(index):
    session['calendar_index'] = index
    return redirect('/calendar')


@app.route('/calendar/instruction/next',methods=["GET"])
@login_required
def next_cal_instruction():
    index = session.get('calendar_instruction_index',0)
    index += 1
    session['calendar_instruction_index'] = index
    if index >= len(calendar_instructions)-1:
        #Completed calendar instructions
        current_user.set_read_calendar_instructions()
    return redirect('/calendar')

@app.route('/calendar/instruction/prev',methods=["GET"])
@login_required
def previous_cal_instruction():
    index = session.get('calendar_instruction_index',0)
    index = (index-1)%len(calendar_instructions)
    session['calendar_instruction_index'] = index
    return redirect('/calendar')

@app.route('/calendar/instruction/<int:index>',methods=["GET"])
@login_required
def set_cal_instruction(index):
    session['calendar_instruction_index'] = index
    return redirect('/calendar')


@app.route('/calendar',methods=["GET"])
@login_required
def calendar_page():
    if not current_user.has_consent():
        return redirect('/landing')
    index = session.get('calendar_index',0)
    index = int(index)%len(calendar)
    return process_calendar(index)

@app.route('/calendar',methods=["POST"])
@login_required
def submit_calendar_page():
    index = request.form.get('index',None)
    next_index = request.form.get('next_index',None)
    if index is None or next_index is None:
        return {'error': "Something went wrong with your survey!","index": index,"next_index": next_index}
    duration = time.time()-float(request.form.get('start_time',None))
    
    current_user.set_discount(int(index)%len(calendar),request.form,duration)
    index = int(next_index)
    
    return process_calendar(index)
    
    
def process_calendar(index):  
    calendar_enabled = current_user.get_read_calendar_instructions()
    calendar_instruction_index = session.get('calendar_instruction_index',0)
    index = int(index)%len(calendar)
    date = calendar[index]
    
    #General Progress
    progress = current_user.get_progress()
    completed_count = sum([1 for key,value in progress.items() if "completed_calendar_" in key and value==True])
    progress['percentage'] = f'{completed_count/len(calendar):2.0%}'
    completed = completed_count >= len(calendar)
    
    #Refreshing Users Progress
    calendar_name = f"completed_calendar_{index}"
    this_calender_is_completed = calendar_name in progress and progress[calendar_name]==True
    user_tokens = get_user_tokens(progress,index) if this_calender_is_completed else {}
    
    start = time.time()
    return render_template('calendar.html',user_tokens=user_tokens,progress=progress,calendar_enabled=calendar_enabled,survey_date=START_DATE,start_time=start,index=index,calendar=calendar,completed=completed,calendar_instructions=calendar_instructions,calendar_instruction_index=calendar_instruction_index,**date)


@app.route(f'/completed',methods=['GET','POST'])
@login_required
def completed_calendar():
    progress = current_user.get_progress()
    completed_count = sum([1 for key,value in progress.items() if "completed_calendar_" in key and value==True])
    progress['percentage'] = f'{completed_count/len(calendar):2.0%}'
    completed = completed_count >= len(calendar)
    validation = validate_user(progress)
    current_user.set_answer('validation',validation)
    if validation['error'] and validation['key']=="invalid_calendar":
        return redirect(session['quality'])
    elif completed:
        col = random.randint(0,len(calendar)-1)
        row = random.randint(0,len(calendar[col]['rates'])-1)
        cal = calendar[col]
        early_rate,late_rate = calendar[col]['rates'][row]
        payout = {
            'col': col,
            'row': row,
            'early_rate': early_rate,
            'late_rate': late_rate,
            'early_tokens': progress[f'calendar_{col}_{row}_{early_rate}'],
            'late_tokens': progress[f'calendar_{col}_{row}_{late_rate}']
        }
        current_user.set_answer('payout',payout)
        current_user.set_answer('completed_calendar',True)
        total_duration = current_user.get_total_duration()
        return render_template('final_page.html',progress=progress,cal=cal,**payout)
    else:
        return redirect("/calendar")

def get_user_tokens(progress,index):
    user_tokens = {}
    for key,value in progress.items():
            if f'calendar_{index%len(calendar)}' not in key: continue
            if key == f'calendar_{index%len(calendar)}': continue
            if 'completed' in key or 'duration' in key: continue
            row,rate = key.replace(f'calendar_{index%len(calendar)}_','').split('_')
            if row not in user_tokens: user_tokens[row] = {}
            user_tokens[row][rate]=value
    return user_tokens

def validate_user(user):
    if 'tokens' not in user:
            user['tokens'] = [(cal['early_label'],cal['late_label'],get_user_tokens(user, i)) for i,cal in enumerate(calendar)]
    all_calendars = [cal for e,l,cal in user['tokens']]
    no_error = {"error": False, "message": "Valid data", "data": None}
    calendar_variance = []
    for i,cal in enumerate(all_calendars):
        tokens = []
        first_tokens = []
        second_tokens = []
        for row,rates in cal.items():
            for i,(rate,value) in enumerate(rates.items()):
                bucket = first_tokens if i==0 else second_tokens
                try:
                    value = float(value)
                    tokens.append(value)
                    bucket.append(value)
                except Exception as e:
                    return {
                        "error": True, 
                        "key": "invalid_calendar",
                        "message": "Invalid calendar data!",
                        "submessage": "Missing token allocations.",
                        }
                        
        calendar_variance.append(statistics.variance(first_tokens)*statistics.variance(second_tokens))
    if sum([var < .01 for var in calendar_variance]) > 0:
        bad_calendars = [f'#{i} ' for i,var in enumerate(calendar_variance) if var<.01]
        total_bad_calendars = len(bad_calendars)
        bad_calendars = "Calendars: "+','.join(bad_calendars)
        return {
                "error": False, 
                "key": "variance",
                "message": f"Zero variance detected! Count({total_bad_calendars})", 
                "submessage": bad_calendars,
                "data": calendar_variance
                }
    return no_error
    
        
        

@app.route(f'/{hidden_service}/test',methods=['GET'])
def test_stats():
    #dict(str(request.environ) | dict(os.environ))
    return str(request.environ)

@app.route(f'/{hidden_service}',methods=['GET'])
def summary_stats():
    #completed_filter = {'consented': True, 'is_old': True,payout 'completed_survey': True}
    total_visits = mongo.db.users.count_documents({})
    total_consented = mongo.db.users.count_documents({'consented': True})
    total_age = mongo.db.users.count_documents({'consented': True, 'is_old': True})
    total_survey = mongo.db.users.count_documents({'consented': True, 'is_old': True, 'completed_survey': True})
    completed_calendar = {f'completed_calendar_{i}': True for i,_ in  enumerate(raw_calendar)}
    total_calendar = mongo.db.users.count_documents(completed_calendar)
    completed = completed_calendar | {'consented': True, 'is_old': True, 'completed_survey': True}
    total_completed = mongo.db.users.count_documents(completed)
    completed_users = mongo.db.users.find(completed)
    completed_everything_but_not_finished = 0 
    durations = []
    users = []
    total_completed_without_error = 0
    for user in completed_users:
        duration = sum([d for key,d in user.items() if 'duration' in key and d!=-1])
        durations.append(duration)
        del user['_id']
        user['tokens'] = [(cal['early_label'],cal['late_label'],get_user_tokens(user, i)) for i,cal in enumerate(calendar)]
        user['validation'] = validate_user(user)
        payout={}
        if 'payout' not in user: 
            completed_everything_but_not_finished += 1
            payout['missing'] = True
        else:   
            payout=user['payout']
            payout['missing'] = False
            payout['early_label'] = calendar[payout['col']]['early_label']
            payout['late_label'] = calendar[payout['col']]['late_label']
            payout['bad'] = False
        try:
            payout['early_payout'] = f"${float(payout['early_tokens'])*float(payout['early_rate'])/100:.02f}"
            payout['late_payout'] = f"${float(payout['late_tokens'])*float(payout['late_rate'])/100:.02f}"
        except:
            payout['bad'] = True
        user['payout'] = payout
        if not payout['bad'] and not user['validation']['error']:
            total_completed_without_error+=1
        users.append(user)
    summmary = {
        'query': completed_calendar,
        'total_visits': total_visits, 
        'total_consented': total_consented, 
        'total_age': total_age, 
        'total_completed_survey': total_survey,
        'total_completed_calendar': total_calendar,
        'total_completed_everything': total_completed, 
        'total_completed_without_error': total_completed_without_error,
        'completed_everything_but_not_finished': completed_everything_but_not_finished,
        'durations': durations,
        'users': users
    }
    return render_template('summary.html',survey=survey,calendar=calendar,**summmary)

if __name__=="__main__":
    app.run(host='0.0.0.0',port='8976',debug=True)
