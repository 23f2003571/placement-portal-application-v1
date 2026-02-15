from flask import Flask
from application.database import db

app=None

def create_app():
   app=Flask(__name__)
   app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///placement.sqlite3"
   db.init_app(app)
   return app

app=create_app()

from application.models import *    
from application.controllers import *

if __name__=="__main__":
   with app.app_context():
      db.create_all()
      existing_admin = User.query.filter_by(username='admin').first()

      if not existing_admin:
         admin_db = User(username='admin',
                         email='admin@gmail.com',
                         password='admin123',
                         role='admin')
         db.session.add(admin_db)
         db.session.commit()
   app.run(debug=True)