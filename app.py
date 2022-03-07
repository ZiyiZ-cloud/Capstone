from http.client import UNAUTHORIZED
from inspect import getmodule
from sqlalchemy import null
from flask import Flask, render_template, redirect, session, flash, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
import requests, json


from secret import API_KEY, API_SECRET
from model import connect_db, db, User, Likes
from forms import RegisterForm, LoginForm, DogSearchForm, CatSearchForm


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql:///yourpet'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = True
app.config["SECRET_KEY"] = 'abc123'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config.update(dict(
    SECRET_KEY="powerful secretkey",
    WTF_CSRF_SECRET_KEY="a csrf secret key"
))

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route('/')
def homepage():
    try:
        userprofile = session['username']
        return render_template('index.html',userprofile=userprofile)
    except:
        return render_template('index.html')
    
#This is the user register, log in and log out part#

@app.route('/register', methods=['GET','POST'])
def register_page():
    
    if "username" in session:
        return redirect(f"/user/{session['username']}")
    
    
    form = RegisterForm()
    
    if form.validate_on_submit():
         username = form.username.data
         password = form.password.data
         email = form.email.data
         first_name = form.first_name.data
         last_name = form.last_name.data
         
         try:
            user = User.register(username,password,email,first_name,last_name)
            db.session.add(user)
            db.session.commit()
            session['username'] = user.username
         
            flash('Welcome! Successfully Created Your Account!', 'primary')
            return redirect(f'/')
         except:
            flash('You need to change your username/email in order to register.', 'danger')
            return render_template('register.html', form = form)
    return render_template('register.html', form = form)

@app.route('/login', methods=['GET','POST'])
def login_page():
    
    if "username" in session:
        return redirect(f"/user/{session['username']}")
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username=form.username.data
        password = form.password.data
        
        user = User.authenticate(username,password)
        
        if user:
            flash(f'Welcome Back, {user.username}!','info')
            session['username']=user.username
            return redirect(f'/') 
        else:
            form.username.errors = ['Invlaid username/password.']
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    
    session.pop('username')
    flash('Goodbye!','info')
    return redirect('/')

# end for user register, log in and log out part #

# user profile page #

@app.route('/user/<username>')
def profile_page(username):
    try:
        if username == session['username']:
            user = User.query.get(username)
            likes = user.likes
            likelist = []
            for like in likes:
                token_url = 'https://api.petfinder.com/v2/oauth2/token'
                dog_url = f'https://api.petfinder.com/v2/animals/{like.pet_id}'
                
                data = {'grant_type': 'client_credentials'}
                
                token_response = requests.post(token_url,data = data,verify = False,
                                    allow_redirects=False,auth=(API_KEY,API_SECRET))
                
                token = json.loads(token_response.text)
                
                api_call_headers = {'Authorization': 'Bearer ' + token['access_token']}

                api_resp = requests.get(dog_url, headers=api_call_headers)

                pet_data = api_resp.json()
                
                likelist.append(pet_data)
            
            length = len(likelist)
            return render_template('userprofile.html',user=user,userprofile = username,likes=likes,likelist=likelist,length=length)
    except:
        flash('You Need To Log In First.','danger')
        return redirect('/login')
    
@app.route('/user/<username>/delete', methods=['POST'])
def delete_user(username):
    user = User.query.get_or_404(username)
    if user.username == session['username']:
        session.pop('username')
        db.session.delete(user)
        db.session.commit()
        flash('User Deleted!','success')
        return redirect('/')
    return redirect(f'/user/{username}')

# page for dogs and cats search tabs #
@app.route('/dogs', methods=['GET','POST'])
def doghomepage():
   
    form = DogSearchForm()
    if form.validate_on_submit():
            address = form.address.data
            radius = form.radius.data
        
            token_url = 'https://api.petfinder.com/v2/oauth2/token'
            dog_url = f'https://api.petfinder.com/v2/animals?type=dog&location={address}&distance={radius}&limit=25&page=1'
    
            data = {'grant_type': 'client_credentials'}
    
            token_response = requests.post(token_url,data = data,verify = False,
                         allow_redirects=False,auth=(API_KEY,API_SECRET))
    
            token = json.loads(token_response.text)
    
            api_call_headers = {'Authorization': 'Bearer ' + token['access_token']}

            api_resp = requests.get(dog_url, headers=api_call_headers)

            pet_data = api_resp.json()
            
            try: 
                next_page = pet_data['pagination']['_links']['next']['href']
                next_url = f'https://api.petfinder.com{next_page}'
                api_next = requests.get(next_url, headers=api_call_headers)
                next_data = api_next.json()
            except:
                next_data = []
            try: 
                prev_page = pet_data['pagination']['_links']['previous']['href']
                prev_url = f'https://api.petfinder.com{prev_page}'
                api_prev = requests.get(prev_url, headers=api_call_headers)
                prev_data=api_prev.json()

            except:
                prev_data = []


            try: 
                userprofile = session['username']
                user = User.query.get(userprofile)
                return render_template('search.html',pet_data=pet_data,userprofile=userprofile,user=user,next_data=next_data,prev_data=prev_data)
            except:
                return render_template('search.html',pet_data=pet_data,next_data=next_data,prev_data=prev_data)

    try:
        userprofile = session['username']
        user = User.query.get(userprofile)
        return render_template('dogs.html', form=form,userprofile=userprofile)
    except:
        return render_template('dogs.html', form=form)
    
@app.route('/pet')
def dogpages():
    
    token_url = 'https://api.petfinder.com/v2/oauth2/token'
    dog_url = f'https://api.petfinder.com//v2/animals?type=dog'

    data = {'grant_type': 'client_credentials'}

    token_response = requests.post(token_url,data = data,verify = False,
                    allow_redirects=False,auth=(API_KEY,API_SECRET))

    token = json.loads(token_response.text)

    api_call_headers = {'Authorization': 'Bearer ' + token['access_token']}

    api_resp = requests.get(dog_url, headers=api_call_headers)

    pet_data = api_resp.json()
        
    return jsonify(pet_data)
            
            

@app.route('/cats',methods=['GET','POST'])
def cathomepage():
    
    form = CatSearchForm()
    if form.validate_on_submit():
            address = form.address.data
            radius = form.radius.data
        
            token_url = 'https://api.petfinder.com/v2/oauth2/token'
            cat_url = f'https://api.petfinder.com/v2/animals?type=cat&location={address}&distance={radius}&limit=25&page=1'
    
            data = {'grant_type': 'client_credentials'}
    
            token_response = requests.post(token_url,data = data,verify = False,
                         allow_redirects=False,auth=(API_KEY,API_SECRET))
    
            token = json.loads(token_response.text)
    
            api_call_headers = {'Authorization': 'Bearer ' + token['access_token']}

            api_resp = requests.get(cat_url, headers=api_call_headers)

            pet_data = api_resp.json()
            
            # if pet_data['pagination']['_links']['next'] :
                
            # if pet_data['pagination']['_links']['previous'] :
    
            try: 
                userprofile = session['username']
                user = User.query.get(userprofile)
                return render_template('search.html',pet_data=pet_data,userprofile=userprofile,user=user)
            except:
                return render_template('search.html',pet_data=pet_data)

    try:
        userprofile = session['username']
        user = User.query.get(userprofile)
        return render_template('cats.html', form=form,userprofile=userprofile,user=user)
    except:
        return render_template('cats.html', form=form)   

# pet profile page 

@app.route('/dogs/<int:dog_id>')
def dogprofile(dog_id):
    token_url = 'https://api.petfinder.com/v2/oauth2/token'
    dog_url = f'https://api.petfinder.com/v2/animals/{dog_id}'
    
    data = {'grant_type': 'client_credentials'}
    
    token_response = requests.post(token_url,data = data,verify = False,
                         allow_redirects=False,auth=(API_KEY,API_SECRET))
    
    token = json.loads(token_response.text)
    
    api_call_headers = {'Authorization': 'Bearer ' + token['access_token']}

    api_resp = requests.get(dog_url, headers=api_call_headers)

    pet_data = api_resp.json()
    
    try:
        userprofile = session['username']
        return render_template('petprofile.html',pet_data=pet_data,userprofile=userprofile)
    except:
        return render_template('petprofile.html',pet_data=pet_data)

@app.route('/cats/<int:cat_id>')
def catprofile(cat_id):
    token_url = 'https://api.petfinder.com/v2/oauth2/token'
    cat_url = f'https://api.petfinder.com/v2/animals/{cat_id}'
    
    data = {'grant_type': 'client_credentials'}
    
    token_response = requests.post(token_url,data = data,verify = False,
                         allow_redirects=False,auth=(API_KEY,API_SECRET))
    
    token = json.loads(token_response.text)
    
    api_call_headers = {'Authorization': 'Bearer ' + token['access_token']}

    api_resp = requests.get(cat_url, headers=api_call_headers)

    pet_data = api_resp.json()
    
    try:
        userprofile = session['username']
        return render_template('petprofile.html',pet_data=pet_data,userprofile=userprofile)
    except:
        return render_template('petprofile.html',pet_data=pet_data)

# add and remove like on dogs
@app.route('/dogs/<int:dog_id>/like',methods=['POST'])
def doglike(dog_id):
    if "username" not in session:
        flash("You need to log in first to add this pet to your list", "danger")
        return redirect(f"/dogs/{dog_id}")
    try:
        userprofile = User.query.get(session['username'])
    
        like = Likes(user_username=userprofile.username,
                    pet_id = dog_id)
        
        db.session.add(like)
        db.session.commit()
        flash('You have successfully added this pet to your list!','success')
        return redirect(f"/dogs/{dog_id}")
    except:
        flash('You have already added this pet to your list.','danger')
        return redirect(f"/dogs/{dog_id}")

@app.route('/dogs/<int:dog_id>/dislike',methods=['POST'])
def dogdislike(dog_id):
    if "username" not in session:
        flash("You need to log in first to remove this pet from your list.", "danger")
        return redirect(f"/dogs/{dog_id}")
    usersession = session['username']
    
    like = (Likes
                .query
                .filter(Likes.user_username == usersession,
                        Likes.pet_id == dog_id)
                .all()
            )
    for item in like:
        db.session.delete(item)
        db.session.commit()
        
    flash('You have successfully removed this pet from your list!','success')

    return redirect(f"/dogs/{dog_id}")


@app.route('/cats/<int:cat_id>/like',methods=['POST'])
def catlike(cat_id):
    if "username" not in session:
        flash("You need to log in first to add this pet to your list", "danger")
        return redirect(f"/cats/{cat_id}")
    try:
        userprofile = User.query.get(session['username'])
    
        like = Likes(user_username=userprofile.username,
                    pet_id = cat_id)
        
        db.session.add(like)
        db.session.commit()
        flash('You have successfully added this pet to your list!','success')
        return redirect(f"/cats/{cat_id}")
    except:
        flash('You have already added this pet to your list.','danger')
        return redirect(f"/cats/{cat_id}")

@app.route('/cats/<int:cat_id>/dislike',methods=['POST'])
def catdislike(cat_id):
    if "username" not in session:
        flash("You need to log in first to remove this pet from your list.", "danger")
        return redirect(f"/cats/{cat_id}")
    usersession = session['username']

    like = (Likes
                .query
                .filter(Likes.user_username == usersession,
                        Likes.pet_id == cat_id)
                .all()
            )
    for item in like:
        db.session.delete(item)
        db.session.commit()
        
    flash('You have successfully removed this pet from your list!','success')

    return redirect(f"/cats/{cat_id}")
    

# api testing part#

@app.route('/apitest')
def apitest():
    
    token_url = 'https://api.petfinder.com/v2/oauth2/token'
    #dog_url = 'https://api.petfinder.com/v2/animals?type=dog&location=10044&distance=10&page=2'
    #dog_url = 'https://api.petfinder.com/v2/animals?distance=1&limit=10&location=10044&page=2&type=dog'
    # /v2/animals?distance=1&limit=25&location=10044&page=2&type=dog
    dog_url = 'https://api.petfinder.com/v2/animals?distance=1&limit=25&location=10044&page=2&type=dog'

    
    data = {'grant_type': 'client_credentials'}
    
    token_response = requests.post(token_url,data = data,verify = False,
                         allow_redirects=False,auth=(API_KEY,API_SECRET))
    
    token = json.loads(token_response.text)
    
    api_call_headers = {'Authorization': 'Bearer ' + token['access_token']}

    api_resp = requests.get(dog_url, headers=api_call_headers)

    pet_data = api_resp.json()
    
    return jsonify(pet_data)