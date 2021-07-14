from flask import Flask, render_template, url_for, flash, redirect
from flask_bcrypt import Bcrypt
from forms import RegistrationForm, LoginForm
from flask_sqlalchemy import SQLAlchemy
from audio import printWAV
import time, random, threading
from turbo_flask import Turbo
import json


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = '58cb11e106953683a34325b53dfd9c30'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

interval=10
FILE_NAME = "siratt.wav"
turbo = Turbo(app)


class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(60), nullable=False)

  def __repr__(self):
    return f"User('{self.username}', '{self.email}', '{self.password}')"
  


@app.route("/")
@app.route("/home")
def home():
  return render_template('home.html', subtitle='Home Page', text='This is the home page')


@app.route("/second_page")
def second_page():
    return render_template('second_page.html', subtitle='Second Page', text='This is the second page')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():# checks if entries are valid
      try:
          pw_hash = bcrypt.generate_password_hash(form.password.data).encode('utf-8')
          user = User(username=form.username.data, email=form.email.data, password=pw_hash)
          db.session.add(user)
          db.session.commit()

      except Exception as e:
        flash(f'The following error occured {e} occured')
      else:
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('register.html', title='Register', form=form)
    
  

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit(): # checks if entries are valid
        user = User.query.filter_by(email=form.email.data).all()
        if not user:
          flash(f'User not found {form.email.data}!')
          return render_template('login.html', title='Login', form=form)
        pw_hash = bcrypt.generate_password_hash(form.password.data).encode('utf-8')
        if not bcrypt.check_password_hash(pw_hash, user[0].password):
          flash(f'Incorrect password for {form.email.data}!')
          return render_template('login.html', title='Login', form=form)
        flash(f'Logged In {form.email.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('login.html', title='Login', form=form)
    

  
@app.route("/captions")
def captions():
    TITLE = "Sir Att Narrates Hello"
    return render_template('captions.html', songName=TITLE, file=FILE_NAME)
  
@app.before_first_request
def before_first_request():
    #resetting time stamp file to 0
    file = open("pos.txt","w") 
    file.write(str(0))
    file.close()

    #starting thread that will time updates
    threading.Thread(target=update_captions).start()

@app.context_processor
def inject_load():
    # getting previous time stamp
    file = open("pos.txt","r")
    pos = int(file.read())
    file.close()

    # writing next time stamp
    file = open("pos.txt","w")
    file.write(str(pos+interval))
    file.close()

    #returning captions
    return {'caption':printWAV(FILE_NAME, pos=pos, clip=interval)}

def update_captions():
    with app.app_context():
        while True:
            # timing thread waiting for the interval
            time.sleep(interval)

            # forcefully updating captionsPane with caption
            turbo.push(turbo.replace(render_template('captionsPane.html'), 'load'))  
  

if __name__ == '__main__':
  app.run(debug=True, host="0.0.0.0")
