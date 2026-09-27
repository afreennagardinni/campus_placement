from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, company, placement, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False)
    company_profile = db.relationship('Company', backref='user', uselist=False)
    placement_profile = db.relationship('PlacementOfficer', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    resume_path = db.Column(db.String(200))
    skills = db.Column(db.Text)  # Comma separated skills
    tenth_percentage = db.Column(db.Float)
    twelfth_percentage = db.Column(db.Float)
    graduation_percentage = db.Column(db.Float)
    backlogs = db.Column(db.Integer, default=0)
    placement_status = db.Column(db.String(20), default='not_placed')  # not_placed, placed
    placed_company = db.Column(db.String(100))
    
    # Relationships
    applications = db.relationship('Application', backref='student', lazy=True)
    
    def get_skills_list(self):
        return self.skills.split(',') if self.skills else []

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    company_name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(15))
    verified = db.Column(db.Boolean, default=False)
    
    # Relationships
    jobs = db.relationship('Job', backref='company', lazy=True)

class PlacementOfficer(db.Model):
    __tablename__ = 'placement_officers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(50))
    phone = db.Column(db.String(15))
    designation = db.Column(db.String(100))
    
    # Relationships
    drives = db.relationship('PlacementDrive', backref='coordinator', lazy=True)

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    salary = db.Column(db.String(50))
    job_type = db.Column(db.String(50))  # full-time, internship
    experience_required = db.Column(db.String(50))
    min_cgpa = db.Column(db.Float)
    eligible_branches = db.Column(db.Text)  # Comma separated branches
    last_date = db.Column(db.DateTime, nullable=False)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, closed
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=True)
    
    # Relationships
    applications = db.relationship('Application', backref='job', lazy=True)

# ==================== UPDATED APPLICATION CLASS WITH NEW FIELDS ====================
class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, shortlisted, rejected, selected
    remarks = db.Column(db.Text)
    round_1_status = db.Column(db.String(20))  # pending, passed, failed
    round_2_status = db.Column(db.String(20))
    round_3_status = db.Column(db.String(20))
    final_result = db.Column(db.String(20))
    
    # ===== NEW FIELDS FOR INTERVIEW & OFFER LETTER =====
    interview_date = db.Column(db.String(20), nullable=True)
    interview_time = db.Column(db.String(20), nullable=True)
    interview_mode = db.Column(db.String(50), nullable=True)  # Online/Offline
    interview_location = db.Column(db.String(200), nullable=True)  # Address or meeting link
    interview_scheduled = db.Column(db.Boolean, default=False)
    
    interview_round1_status = db.Column(db.String(20), default='pending')  # pending/passed/failed
    interview_round1_remarks = db.Column(db.Text, nullable=True)
    interview_round2_status = db.Column(db.String(20), default='pending')
    interview_round2_remarks = db.Column(db.Text, nullable=True)
    interview_round3_status = db.Column(db.String(20), default='pending')
    interview_round3_remarks = db.Column(db.Text, nullable=True)
    
    technical_score = db.Column(db.Integer, nullable=True)  # Out of 100
    communication_score = db.Column(db.Integer, nullable=True)  # Out of 100
    overall_score = db.Column(db.Integer, nullable=True)  # Out of 100
    
    offer_letter_generated = db.Column(db.Boolean, default=False)
    offer_letter_path = db.Column(db.String(200), nullable=True)
    offer_letter_sent_date = db.Column(db.DateTime, nullable=True)
    offer_accepted = db.Column(db.Boolean, default=False)
    offer_acceptance_date = db.Column(db.DateTime, nullable=True)
    
    joining_date = db.Column(db.String(20), nullable=True)
    joining_confirmed = db.Column(db.Boolean, default=False)
    
    # Unique constraint to prevent duplicate applications
    __table_args__ = (db.UniqueConstraint('job_id', 'student_id', name='unique_application'),)
    
    def __repr__(self):
        return f'<Application {self.id}: {self.student_id} for {self.job_id}>'

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    
    id = db.Column(db.Integer, primary_key=True)
    drive_name = db.Column(db.String(100), nullable=False)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('placement_officers.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, ongoing, completed
    
    # Relationships
    jobs = db.relationship('Job', backref='drive', lazy=True)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # job, application, drive, interview, offer
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.message[:20]}>'