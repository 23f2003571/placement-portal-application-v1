from .database import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin/company/student

    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student_profile = db.relationship('Studentprofile', back_populates='user',uselist=False, cascade="all, delete")
    company_profile = db.relationship('Companyprofile', back_populates='user',uselist=False, cascade="all, delete")

class Studentprofile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    department = db.Column(db.String(150), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    resume = db.Column(db.String(200))

    user = db.relationship('User', back_populates='student_profile')
    applications = db.relationship('Application', back_populates='student',cascade="all, delete")

class Companyprofile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(150), nullable=False)
    website = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    user = db.relationship('User', back_populates='company_profile')
    drives = db.relationship('Placementdrive', back_populates='company',cascade="all, delete")



class Placementdrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companyprofile.id'), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text(500), nullable=False)
    salary= db.Column(db.String(50), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)

    company = db.relationship('Companyprofile', back_populates='drives')
    applications = db.relationship('Application', back_populates='drive',cascade="all, delete")



class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('studentprofile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placementdrive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Applied')  #Applied/Shortlisted/Selected/Rejected

    student = db.relationship('Studentprofile', back_populates='applications')
    drive = db.relationship('Placementdrive', back_populates='applications')
