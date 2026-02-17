from flask import Flask,render_template,redirect,request,url_for,session

from .models import *
from app import app

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registeration',methods=['GET','POST'])
def registeration():
   if request.method == 'POST':
      name = request.form['username']
      email = request.form['email']
      password = request.form['password']
      role = request.form['role']

      user = User.query.filter_by(username=name,email=email,role=role).first()
      if user:
         return redirect(url_for('login'))

      new_user = User(username=name,email=email,password=password,role=role)
      db.session.add(new_user)
      db.session.commit()
      return redirect(url_for('login'))
   return render_template('registeration.html')

@app.route('/login',methods=['GET','POST'])
def login():
   if request.method == 'POST':
      name = request.form['username']
      password = request.form['password']

      user = User.query.filter_by(username=name,password=password).first()
      if user and user.role == 'student':
         return redirect(url_for('studentdash'))
      
      elif user and user.role == 'company':
         companyprofile = Companyprofile.query.filter_by(user_id=user.id).first()
         if companyprofile is None or companyprofile.approval_status != "Approved":
                    return render_template('login.html',error="Waiting for admin approval")
         return redirect(url_for('companydash'))
      
      elif user and user.role == 'admin':
         return redirect(url_for('admindash'))
      return render_template('login.html',error_msg='Invalid username or password!')
   return render_template('login.html')

@app.route('/logout')
def logout():
   return redirect(url_for('index'))

@app.route('/studentdash',methods=['GET','POST'])
def studentdash():
   
   return render_template('studentdash.html')

@app.route('/companydash',methods=['GET','POST'])
def companydash():
   
   return render_template('companydash.html')

@app.route('/admindash',methods=['GET','POST'])
def admindash():
   
   return render_template('admindash.html')
