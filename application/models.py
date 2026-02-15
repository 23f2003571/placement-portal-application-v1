from .database import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin/company/student
    
    company_profile = db.relationship('Companyprofile', back_populates='user',uselist=False)
    applications = db.relationship('Application', back_populates='student')



class Companyprofile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(150))
    website = db.Column(db.String(150))
    approval_status = db.Column(db.String(50), default='Pending')  # Pending/Approved/ Rejected

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    user = db.relationship('User', back_populates='company_profile')
    drives = db.relationship('Placementdrive', back_populates='company')



class Placementdrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companyprofile.id'))
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text(500), nullable=False)
    eligibility_criteria = db.Column(db.String(250), nullable=False)
    application_deadline = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Pending')  #Pending/Approved/Closed

    company = db.relationship('Companyprofile', back_populates='drives')
    applications = db.relationship('Application', back_populates='drive')



class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('placementdrive.id'))
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Applied')  #Applied/Shortlisted/Selected/Rejected

    student = db.relationship('User', back_populates='applications')
    drive = db.relationship('Placementdrive', back_populates='applications')