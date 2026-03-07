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
         if not user.is_approved:
            return render_template('login.html',error3="You are blocked by admin")
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
@app.route('/studentdash')
def studentdash():
   if 'user_id' not in session:
      return redirect(url_for('login'))
   
   student = Studentprofile.query.filter_by(user_id=session['user_id']).first()
   if not student:
      return redirect(url_for('student_profile'))
   
   companies=Companyprofile.query.join(User).filter(User.is_approved==True).all()
   apps=Application.query.filter_by(student_id=student.id).all()

   search = request.args.get('search')

   if search:
      company = Companyprofile.query.filter(
            Companyprofile.company_name.ilike(f"%{search}%")
        ).first()

      if company:
            return redirect(url_for('stu_com_overview', company_id=company.id))

      drives = Placementdrive.query.filter(
         Placementdrive.job_title.ilike(f"%{search}%")
      ).all()

      if drives:
         if len(drives) == 1:
            return redirect(url_for('stu_com_view', drive_id=drives.id))

         elif len(drives) > 1:
            return render_template(
               "studentdash.html",
               student=student,
               companies=companies,
                apps=apps,
               drives=drives
            )
      
      return render_template('studentdash.html',
                          student=student,
                          companies=companies,
                          apps=apps,
                          error3="Incorrect info..! Please write valid Companny Name or Job Title"
                          )
      
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

   drives = Placementdrive.query.filter_by(company_id=company_id,is_approved=True,is_closed=False).all()
   return render_template('stu_com_overview.html',
                          drives=drives,
                          company=company)
@app.route('/stu_com_view/<int:drive_id>')
def stu_com_view(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)

   student = Studentprofile.query.filter_by(user_id=session['user_id']).first()

   app = Application.query.filter_by(drive_id=drive_id, student_id=student.id).first()
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

      apps= Application.query.filter_by(drive_id=drive.id, status='Shortlist').all()

      shortlist = []

      for app in apps:
        if app.student.user.is_approved == True:
            shortlist.append(app)
            
      drive_data.append({
         "job": drive,
         "total_apps": total_apps,
         "shortlist": shortlist
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

      title=request.form['jobtitle']
      description=request.form['jobdescription']
      salary=request.form['salary']
      
      existing= Placementdrive.query.filter_by(company_id=company.id,
                                            job_title=title,
                                            job_description=description,
                                            salary=salary)
      if existing:
         return render_template('com_create_drive.html', error="This Drive(Job) is already created.")
   
      drive=Placementdrive(
         company_id=company.id,
         job_title=title,
         job_description=description,
         salary=salary
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

@app.route('/whole_companystudent_profile/<int:student_id>/<int:company_id>')
def whole_companystudent_profile(student_id, company_id):
   student = Studentprofile.query.get(student_id)
   if student is None:
      abort(404)

   apps = Application.query.join(Placementdrive).filter(
      Application.student_id==student.id,
      Placementdrive.company_id== company_id
   ).all()
   apps_count = Application.query.join(Placementdrive).filter(
      Application.student_id==student.id,
      Placementdrive.company_id == company_id
   ).count()
   return render_template('whole_companystudent_profile.html',
                           student=student,
                           company_id=company_id,
                           apps=apps,
                           apps_count=apps_count)

@app.route('/company_stu_history/<int:student_id>/<int:company_id>')
def company_stu_history(student_id, company_id):
   student = Studentprofile.query.get(student_id)
   if student is None:
      abort(404)
      
   apps = Application.query.join(Placementdrive).filter(
      Application.student_id==student.id,
      Placementdrive.company_id== company_id
   ).all()
   return render_template('company_stu_history.html',
                          student=student,
                          company_id=company_id,
                          apps=apps)
# Admin-------------------------------------------------------------------------------------------------------
@app.route('/admindash',methods=['GET','POST'])
def admindash():
   if 'user_id' not in session:
      return redirect(url_for('login'))
   
   registered_companies = Companyprofile.query.join(User).filter(User.is_approved==True).all()
   registered_students = Studentprofile.query.join(User).all()
   approval_companies = User.query.filter_by(role='company', is_approved=False).all()   
   job_drives = Placementdrive.query.filter_by(is_approved=False).all()
   ongoing_drives = Placementdrive.query.filter_by(is_approved=True).all()
   apps = Application.query.all()

   total_students = Studentprofile.query.join(User).filter(User.is_approved==True).count()
   total_companies = Companyprofile.query.join(User).filter(User.is_approved==True).count()
   total_drives = Placementdrive.query.count()
   total_apps = Application.query.count()

   search = request.args.get('search')

   if search:
      search=search.strip()
      if search.isdigit():
         student = Studentprofile.query.filter_by(id=int(search)).first()

         if student:
            return redirect(url_for('whole_student_profile', student_id=student.id))
         else:
            return render_template('admindash.html',
                           registered_companies=registered_companies,
                          registered_students=registered_students,
                          approval_companies=approval_companies,
                          job_drives=job_drives,
                          ongoing_drives=ongoing_drives,
                          apps=apps,
                          total_students=total_students,
                          total_companies=total_companies,
                          total_drives=total_drives,
                          total_apps=total_apps,
                          error4="Incorrect info..! Please write valid Student ID"
                          )
      
      else:
         student = Studentprofile.query.filter(
            Studentprofile.student_name.ilike(f"%{search}%")).first()
         company = Companyprofile.query.filter(
            Companyprofile.company_name.ilike(f"%{search}%")).first()
         
         if student:
            return redirect(url_for('whole_student_profile', student_id=student.id))
         
         elif company:
            return redirect(url_for('whole_company_profile', company_id=company.id))
         return render_template('admindash.html',
                           registered_companies=registered_companies,
                          registered_students=registered_students,
                          approval_companies=approval_companies,
                          job_drives=job_drives,
                          ongoing_drives=ongoing_drives,
                          apps=apps,
                          total_students=total_students,
                          total_companies=total_companies,
                          total_drives=total_drives,
                          total_apps=total_apps,
                          error4="Incorrect info..! Please write valid Student Name or Companny Name"
                          )
         
   return render_template('admindash.html',
                          registered_companies=registered_companies,
                          registered_students=registered_students,
                          approval_companies=approval_companies,
                          job_drives=job_drives,
                          ongoing_drives=ongoing_drives,
                          apps=apps,
                          total_students=total_students,
                          total_companies=total_companies,
                          total_drives=total_drives,
                          total_apps=total_apps)

@app.route('/admin_view_stu/<int:app_id>')
def admin_view_stu(app_id):
   app = Application.query.get(app_id)
   if app is None:
      abort(404)
   return render_template('admin_view_stu.html',
                          app=app)

@app.route('/admin_view_com/<int:drive_id>')
def admin_view_com(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)

   app = Application.query.filter_by(drive_id=drive_id).first()
   return render_template('admin_view_com.html',
                           app=app,
                          drive=drive)

@app.route('/company_approve/<int:company_id>')
def company_approve(company_id):
   user = User.query.get(company_id)
   if user is None:
      abort(404)

   user.is_approved=True
   db.session.commit()
   return redirect(url_for('admindash'))

@app.route('/company_blacklist/<int:company_id>')
def company_blacklist(company_id):
   user = User.query.get(company_id)
   if user is None:
      abort(404)

   user.is_approved=False
   db.session.commit()
   return redirect(url_for('admindash'))

@app.route('/student_approve/<int:student_id>')
def student_approve(student_id):
   user = User.query.get(student_id)
   if user is None:
      abort(404)

   user.is_approved=True
   db.session.commit()
   return redirect(url_for('admindash'))

@app.route('/student_blacklist/<int:student_id>')
def student_blacklist(student_id):
   user = User.query.get(student_id)
   if user is None:
      abort(404)

   user.is_approved=False
   db.session.commit()
   return redirect(url_for('admindash'))

@app.route('/drive_approve/<int:drive_id>')
def drive_approve(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)

   drive.is_approved=True
   db.session.commit()
   return redirect(url_for('admindash'))

@app.route('/drive_disapprove/<int:drive_id>')
def drive_disapprove(drive_id):
   drive = Placementdrive.query.get(drive_id)
   if drive is None:
      abort(404)

   drive.is_approved=False
   db.session.commit()
   return redirect(url_for('admindash'))

@app.route('/whole_student_profile/<int:student_id>')
def whole_student_profile(student_id):
   student = Studentprofile.query.get(student_id)
   if student is None:
      abort(404)

   apps = Application.query.filter_by(student_id=student.id).all()
   apps_count = Application.query.filter_by(student_id=student.id).count()
   return render_template('whole_student_profile.html',
                           student=student,
                           apps=apps,
                           apps_count=apps_count)

@app.route('/admin_stu_history/<int:student_id>')
def admin_stu_history(student_id):
   student = Studentprofile.query.get(student_id)
   if student is None:
      abort(404)
      
   apps=Application.query.filter_by(student_id=student.id).all()
   return render_template('admin_stu_history.html',
                          student=student,
                          apps=apps)

@app.route('/whole_company_profile/<int:company_id>')
def whole_company_profile(company_id):
   company = Companyprofile.query.get(company_id)
   if company is None:
      abort(404)

   drives = Placementdrive.query.filter_by(company_id=company.id).all()
   
   drives_count = Placementdrive.query.filter_by(company_id=company.id).count()

   drive_data = []

   for drive in drives:
    total_apps = Application.query.filter_by(drive_id=drive.id).count()

    drive_data.append({
        "drive": drive,
        "total_apps": total_apps
    })
   
   apps = Application.query.join(Placementdrive).filter(
       Placementdrive.company_id == company.id).all()
   apps_count = Application.query.join(Placementdrive).filter(
       Placementdrive.company_id == company.id).count()
   
   return render_template('whole_company_profile.html',
                           company=company,
                           drives=drives,
                           apps=apps,
                           drive_data=drive_data,
                           apps_count=apps_count,
                           drives_count=drives_count
                           )
#------------------------------------------------------------------------------
@app.route('/admin_indirectview_student/<int:app_id>')
def admin_indirectview_student(app_id):

    app = Application.query.get(app_id)

    return render_template(
        "admin_view_stu.html",
        app=app,
        back_url=url_for('whole_student_profile',
                         student_id=app.student_id)
    )

@app.route('/company_indirectview_student/<int:app_id>/<int:company_id>')
def company_indirectview_student(app_id,company_id):

    app = Application.query.get(app_id)

    return render_template(
        "admin_view_stu.html",
        app=app,
        back_url=url_for('whole_companystudent_profile',
                         student_id=app.student_id, 
                         company_id=company_id)
    )


@app.route('/admin_mainpageview_student/<int:app_id>')
def admin_mainpageview_student(app_id):

    app = Application.query.get(app_id)

    return render_template(
        "admin_view_stu.html",
        app=app,
        back_url=url_for('admindash')
    )