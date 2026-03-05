from flask import Flask, abort,render_template,redirect,request,url_for,session
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from .models import *
from app import app

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registeration',methods=['GET','POST'])
def registeration():
   if request.method == 'POST':
      name = request.form['name']
      email = request.form['email']
      password = request.form['password']
      role = request.form['role']

      user = User.query.filter_by(username=name,email=email,role=role).first()
      if user:
         return render_template('registeration.html', error="Email already registered. Go to login page.")

      new_user = User(username=name,email=email,password=password,role=role, is_approved=False if role=="company" else True)
      db.session.add(new_user)
      db.session.commit()
      return redirect(url_for('login'))
   return render_template('registeration.html')

@app.route('/login',methods=['GET','POST'])
def login():
   if request.method == 'POST':
      name = request.form['name']
      password = request.form['password']

      user = User.query.filter_by(username=name,password=password).first()
      if user and user.role == 'student':
         session['name'] = user.username
         session['user_id'] = user.id
         session['role'] = user.role
         return redirect(url_for('studentdash'))
      
      elif user and user.role == 'company':
         if not user.is_approved:
            return render_template('login.html',error1="Waiting for admin approval")
         session['name'] = user.username
         session['user_id'] = user.id
         session['role'] = user.role
         return redirect(url_for('companydash'))
      
      elif user and user.role == 'admin':
         session['name'] = user.username
         session['user_id'] = user.id
         session['role'] = user.role
         return redirect(url_for('admindash'))
      return render_template('login.html',error2='Invalid username or password! or registeration not done.')
   return render_template('login.html')

@app.route('/logout')
def logout():
   session.clear()
   return redirect(url_for('index'))

# Student----------------------------------------------------------------------------------------------------
@app.route('/studentdash',methods=['GET','POST'])
def studentdash():
   if 'user_id' not in session:
      return redirect(url_for('login'))
   
   student = Studentprofile.query.filter_by(user_id=session['user_id']).first()
   if not student:
      return redirect(url_for('student_profile'))
   
   companies=Companyprofile.query.join(User).filter(User.is_approved==True).all()
   apps=Application.query.filter_by(student_id=student.id).all()
   return render_template('studentdash.html',
                          student=student,
                          companies=companies,
                          apps=apps,
                          )

@app.route('/student_profile', methods=["GET","POST"])
def student_profile():
   user_id = session.get("user_id")

   if not user_id:
      return redirect("/login")
   
   student = Studentprofile.query.filter_by(user_id=user_id).first()

   if request.method == 'POST':
      if student:
         if request.form.get('student_name'):
            student.student_name = request.form.get('student_name')
         if request.form.get('department'):
            student.departmentt = request.form.get('department')
         if request.form.get('cgpa'):
            student.cgpa = request.form.get('cgpa')

         if request.form.get('resume'):
            student.resume = request.form.get('resume')
      else:
         student = Studentprofile(
            user_id=user_id, 
            student_name=request.form["student_name"], 
            department=request.form["department"], 
            cgpa=request.form['cgpa'], 
            resume=request.form['resume'])
      db.session.add(student)
      db.session.commit()
      return redirect(url_for('studentdash'))
   return render_template('student_profile.html')

@app.route('/stu_com_overview/<int:company_id>',methods=['GET','POST'])
def stu_com_overview(company_id):
   company = Companyprofile.query.get(company_id)
   if company is None:
      abort(404)

   drives = Placementdrive.query.filter_by(company_id=company_id,is_closed=False).all()
   return render_template('stu_com_overview.html',
                          drives=drives,
                          company=company)

@app.route('/stu_com_view/<int:drive_id>')
def stu_com_view(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)


   app = Application.query.filter_by(drive_id=drive_id).first()
   return render_template('stu_com_view.html', 
                          app=app,
                          drive=drive)

@app.route('/student_history')
def student_history():
   user_id = session.get("user_id")

   if not user_id:
      return redirect("/login")
   
   student = Studentprofile.query.filter_by(user_id=session['user_id']).first()
   if not student:
      return redirect(url_for('student_profile'))
   
   apps=Application.query.filter_by(student_id=student.id).all()
   return render_template('student_history.html',
                          student=student,
                          apps=apps)

@app.route('/apply_job/<int:drive_id>')
def apply_job(drive_id):
   if 'user_id' not in session:
      return redirect(url_for('login'))
   
   student=Studentprofile.query.filter_by(user_id=session["user_id"]).first()
   if not student:
      return render_template('studentdash.html', error2="Please complete your student profile first.")
   
   existing = Application.query.filter_by(drive_id=drive_id, student_id=student.id).first()
   drive=Placementdrive.query.get(drive_id)
   if existing:
      return render_template('stu_com_view.html',drive=drive, error3="Already applied!")
   
   app = Application(drive_id=drive_id, student_id=student.id)
   db.session.add(app)
   db.session.commit()
   return redirect(url_for('stu_com_view', drive_id=drive_id))

@app.route('/student_search')
def student_search():
    return render_template("studentdash.html")
# Company-----------------------------------------------------------------------------------------------------
@app.route('/companydash',methods=['GET','POST'])
def companydash():
   if 'user_id' not in session:
      return redirect(url_for('login'))
   
   company = Companyprofile.query.filter_by(user_id=session['user_id']).first()
   if not company:
      return redirect(url_for('company_profile'))
   
   drives = Placementdrive.query.filter_by(company_id=company.id, is_closed=False).all()
   closed_drives = Placementdrive.query.filter_by(company_id=company.id,is_closed=True).all()

   drive_data=[]

   for drive in drives:
      total_apps = Application.query.filter_by(drive_id=drive.id).count()

      shortlisted= Application.query.filter_by(drive_id=drive.id, status='Shortlist').all()

      drive_data.append({
         "job": drive,
         "total_apps": total_apps,
         "shortlisted": shortlisted
      })
   
   return render_template('companydash.html',
                          company=company,
                          drives=drive_data,
                          closed_drives=closed_drives)

@app.route('/company_profile', methods=["GET","POST"])
def company_profile():
   user_id = session.get("user_id")

   if not user_id:
      return redirect("/login")
   
   company = Companyprofile.query.filter_by(user_id=user_id).first()

   if request.method == 'POST':
      if company:
         if request.form.get('company_name'):
            company.company_name = request.form.get('company_name')
         if request.form.get('hr_contact'):
            company.hr_contact = request.form.get('hr_contact')
         if request.form.get('website'):
            company.website = request.form.get('website')

         if request.form.get('location'):
            company.location = request.form.get('location')
      else:
         company = Companyprofile(
            user_id=user_id, 
            company_name=request.form["company_name"], 
            hr_contact=request.form["hr_contact"], 
            website=request.form['website'], 
            location=request.form['location'])
      db.session.add(company)
      db.session.commit()
      return redirect(url_for('companydash'))
   return render_template('company_profile.html')

@app.route('/create_drive',methods=['GET','POST'])
def create_drive():
   user_id = session.get("user_id")

   if not user_id:
      return redirect("/login")
   
   company = Companyprofile.query.filter_by(user_id=user_id).first()
   
   if not company:
      return render_template('companydash.html', error1="Please complete your company profile first.")
   
   if request.method == "POST":
      drive=Placementdrive(
         company_id=company.id,
         job_title=request.form["jobtitle"],
         job_description=request.form["jobdescription"],
         salary=request.form["salary"]
      )
      db.session.add(drive)
      db.session.commit()
      return redirect(url_for('companydash'))
   return render_template('com_create_drive.html')

@app.route('/view_drives/<int:drive_id>')
def view_drives(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)

   applications = Application.query.filter_by(drive_id=drive_id).all()
   return render_template('com_drive_update.html', drive=drive, applications=applications)

@app.route('/review-application/<int:app_id>', methods=['GET', 'POST'])
def review_application(app_id):
   app = Application.query.get(app_id)
   if app is None:
      abort(404)

   if request.method=="POST":
      status=request.form.get('status')

      app.status=status
      db.session.commit()
      return redirect(url_for('view_drives', drive_id=app.drive_id))
   return render_template('com_stu_app.html', app=app)

@app.route('/company_close/<int:drive_id>')
def company_close(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)
   
   drive.is_closed=True
   db.session.commit()
   return redirect(url_for('companydash'))

@app.route('/company_open/<int:drive_id>')
def company_open(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)
   
   drive.is_closed=False
   db.session.commit()
   return redirect(url_for('companydash'))

@app.route('/company_edit/<int:drive_id>', methods=['GET','POST'])
def company_edit(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)
   
   if request.method == 'POST':
      drive.job_title=request.form["jobtitle"]
      drive.job_description=request.form["jobdescription"]
      drive.salary=request.form["salary"]

      db.session.commit()
      return redirect(url_for('companydash'))
   return render_template('com_edit_drive.html', drive = drive)

@app.route("/company_delete/<int:drive_id>")
def company_delete(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)

   db.session.delete(drive)
   db.session.commit()
   return redirect(url_for("companydash"))
# Admin-------------------------------------------------------------------------------------------------------
@app.route('/admindash',methods=['GET','POST'])
def admindash():
   
   return render_template('admindash.html')

@app.route('/admin_view_stu',methods=['GET','POST'])
def admin_view_stu():
   
   return render_template('admin_view_stu.html')

@app.route('/admin_view_com',methods=['GET','POST'])
def admin_view_com():
   
   return render_template('admin_view_com.html')
