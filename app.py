from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

from config import Config
from models import db, User, Student, Company, PlacementOfficer, Job, Application, PlacementDrive, Notification
from forms import *

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(email='admin@placementsystem.com').first():
        admin = User(username='admin', email='admin@placementsystem.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        # Check if user exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form, role='student')
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='student'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        
        # Create student profile
        student = Student(
            user_id=user.id,
            full_name=form.full_name.data,
            roll_number=form.roll_number.data,
            department=form.department.data,
            semester=form.semester.data,
            cgpa=form.cgpa.data,
            phone=form.phone.data,
            tenth_percentage=form.tenth_percentage.data,
            twelfth_percentage=form.twelfth_percentage.data
        )
        db.session.add(student)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form, role='student')

@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        # Check if user exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form, role='company')
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='company'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        
        # Create company profile
        company = Company(
            user_id=user.id,
            company_name=form.company_name.data,
            industry=form.industry.data,
            website=form.website.data,
            description=form.description.data,
            location=form.location.data,
            contact_person=form.contact_person.data,
            contact_email=form.email.data,
            contact_phone=form.contact_phone.data
        )
        db.session.add(company)
        db.session.commit()
        
        flash('Registration successful! Please wait for admin verification.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form, role='company')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        recent_jobs = Job.query.filter_by(status='active').order_by(Job.posted_date.desc()).limit(5).all()
        applications = Application.query.filter_by(student_id=student.id).all()
        
        # Check for upcoming interviews
        upcoming_interviews = Application.query.filter_by(
            student_id=student.id, 
            interview_scheduled=True
        ).filter(Application.status.in_(['shortlisted', 'pending'])).all()
        
        return render_template('student/dashboard.html', 
                             student=student, 
                             jobs=recent_jobs, 
                             applications=applications,
                             upcoming_interviews=upcoming_interviews)
    
    elif current_user.role == 'company':
        company = Company.query.filter_by(user_id=current_user.id).first()
        jobs = Job.query.filter_by(company_id=company.id).order_by(Job.posted_date.desc()).all()
        total_applications = Application.query.join(Job).filter(Job.company_id == company.id).count()
        
        # Get counts for different statuses
        shortlisted_count = Application.query.join(Job).filter(
            Job.company_id == company.id, 
            Application.status == 'shortlisted'
        ).count()
        
        selected_count = Application.query.join(Job).filter(
            Job.company_id == company.id, 
            Application.status == 'selected'
        ).count()
        
        return render_template('company/dashboard.html', 
                             company=company, 
                             jobs=jobs, 
                             total_applications=total_applications,
                             shortlisted_count=shortlisted_count,
                             selected_count=selected_count)
    
    elif current_user.role == 'placement':
        officer = PlacementOfficer.query.filter_by(user_id=current_user.id).first()
        drives = PlacementDrive.query.filter_by(coordinator_id=officer.id).all()
        total_students = Student.query.count()
        total_companies = Company.query.count()
        return render_template('placement/dashboard.html', officer=officer, drives=drives, 
                             total_students=total_students, total_companies=total_companies)
    
    elif current_user.role == 'admin':
        total_students = Student.query.count()
        total_companies = Company.query.count()
        total_jobs = Job.query.count()
        total_placements = Student.query.filter_by(placement_status='placed').count()
        pending_companies = Company.query.filter_by(verified=False).count()
        return render_template('admin/dashboard.html', 
                             total_students=total_students,
                             total_companies=total_companies,
                             total_jobs=total_jobs,
                             total_placements=total_placements,
                             pending_companies=pending_companies)

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_jobs = Job.query.count()
    total_placements = Student.query.filter_by(placement_status='placed').count()
    pending_companies = Company.query.filter_by(verified=False).count()
    
    return render_template('admin/dashboard.html', 
                         total_students=total_students,
                         total_companies=total_companies,
                         total_jobs=total_jobs,
                         total_placements=total_placements,
                         pending_companies=pending_companies)

@app.route('/admin/manage-students')
@login_required
def manage_students():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    students = Student.query.all()
    return render_template('admin/manage_students.html', students=students)

@app.route('/admin/manage-companies')
@login_required
def manage_companies():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    companies = Company.query.all()
    return render_template('admin/manage_companies.html', companies=companies)

@app.route('/admin/company/<int:company_id>/verify', methods=['POST'])
@login_required
def verify_company(company_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    company = Company.query.get_or_404(company_id)
    company.verified = True
    db.session.commit()
    
    # Notify company
    company_user = User.query.get(company.user_id)
    notification = Notification(
        user_id=company_user.id,
        message='Your company has been verified! You can now post jobs.',
        type='verification'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Basic statistics
    total_students = Student.query.count()
    placed_students = Student.query.filter_by(placement_status='placed').count()
    placement_rate = (placed_students / total_students * 100) if total_students > 0 else 0
    
    # Department wise statistics
    departments = []
    dept_list = db.session.query(Student.department).distinct().all()
    
    for dept in dept_list:
        dept_name = dept[0]
        if dept_name:
            total = Student.query.filter_by(department=dept_name).count()
            placed = Student.query.filter_by(department=dept_name, placement_status='placed').count()
            
            departments.append({
                'department': dept_name,
                'total': total,
                'placed': placed
            })
    
    departments.sort(key=lambda x: x['department'])
    
    return render_template('admin/reports.html', 
                         placement_rate=round(placement_rate, 2),
                         placed_students=placed_students,
                         total_students=total_students,
                         departments=departments)

# ==================== LOGOUT ROUTE ====================

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ==================== STUDENT ROUTES ====================

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    form = StudentProfileForm(obj=student)
    
    if form.validate_on_submit():
        student.full_name = form.full_name.data
        student.phone = form.phone.data
        student.address = form.address.data
        student.skills = form.skills.data
        student.tenth_percentage = form.tenth_percentage.data
        student.twelfth_percentage = form.twelfth_percentage.data
        student.graduation_percentage = form.graduation_percentage.data
        student.backlogs = form.backlogs.data
        
        # Handle resume upload
        if form.resume.data:
            filename = secure_filename(f"{student.roll_number}_{form.resume.data.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.resume.data.save(filepath)
            student.resume_path = filepath
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))
    
    return render_template('student/profile.html', form=form, student=student)

@app.route('/student/jobs')
@login_required
def student_jobs():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    jobs = Job.query.filter_by(status='active').order_by(Job.posted_date.desc()).all()
    
    # Get applied job IDs
    applied_jobs = [app.job_id for app in Application.query.filter_by(student_id=student.id).all()]
    
    return render_template('student/jobs.html', jobs=jobs, applied_jobs=applied_jobs, student=student)

@app.route('/student/job/<int:job_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    # Check eligibility
    if student.cgpa < job.min_cgpa:
        flash('You do not meet the minimum CGPA requirement', 'danger')
        return redirect(url_for('student_jobs'))
    
    # Check if already applied
    existing = Application.query.filter_by(job_id=job_id, student_id=student.id).first()
    if existing:
        flash('You have already applied for this job', 'warning')
        return redirect(url_for('student_jobs'))
    
    if request.method == 'POST':
        application = Application(
            job_id=job_id,
            student_id=student.id,
            status='pending'
        )
        db.session.add(application)
        db.session.commit()
        
        # Create notification for company
        company = Company.query.get(job.company_id)
        company_user = User.query.get(company.user_id)
        notification = Notification(
            user_id=company_user.id,
            message=f'New application received for {job.title} from {student.full_name}',
            type='application'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('student_jobs'))
    
    return render_template('student/apply_job.html', job=job, student=student)

@app.route('/student/applications')
@login_required
def student_applications():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    applications = Application.query.filter_by(student_id=student.id).order_by(Application.applied_date.desc()).all()
    
    return render_template('student/applications.html', applications=applications)

@app.route('/student/interviews')
@login_required
def student_interviews():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    interviews = Application.query.filter_by(
        student_id=student.id, 
        interview_scheduled=True
    ).all()
    
    return render_template('student/interviews.html', interviews=interviews)

@app.route('/student/offer/<int:app_id>')
@login_required
def view_offer(app_id):
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(app_id)
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if application.student_id != student.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('student/offer_view.html', application=application)

@app.route('/student/offer/<int:app_id>/accept', methods=['POST'])
@login_required
def accept_offer(app_id):
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(app_id)
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if application.student_id != student.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    application.offer_accepted = True
    application.offer_acceptance_date = datetime.utcnow()
    student.placement_status = 'placed'
    student.placed_company = application.job.company.company_name
    
    db.session.commit()
    
    flash('Congratulations! You have accepted the offer.', 'success')
    return redirect(url_for('student_applications'))

# ==================== COMPANY ROUTES ====================

@app.route('/company/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company.verified:
        flash('Your company is not verified yet. Please wait for admin verification.', 'warning')
        return redirect(url_for('dashboard'))
    
    form = JobPostForm()
    if form.validate_on_submit():
        job = Job(
            company_id=company.id,
            title=form.title.data,
            description=form.description.data,
            requirements=form.requirements.data,
            location=form.location.data,
            salary=form.salary.data,
            job_type=form.job_type.data,
            experience_required=form.experience_required.data,
            min_cgpa=form.min_cgpa.data,
            eligible_branches=form.eligible_branches.data,
            last_date=form.last_date.data
        )
        db.session.add(job)
        db.session.commit()
        
        # Notify all students
        students = Student.query.all()
        for student in students:
            student_user = User.query.get(student.user_id)
            notification = Notification(
                user_id=student_user.id,
                message=f'New job posted: {job.title} at {company.company_name}',
                type='job'
            )
            db.session.add(notification)
        db.session.commit()
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('company_dashboard'))
    
    return render_template('company/post_job.html', form=form, company=company)

@app.route('/company/jobs')
@login_required
def company_jobs():
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    company = Company.query.filter_by(user_id=current_user.id).first()
    jobs = Job.query.filter_by(company_id=company.id).order_by(Job.posted_date.desc()).all()
    
    return render_template('company/manage_jobs.html', jobs=jobs, company=company)

@app.route('/company/job/<int:job_id>/applications')
@login_required
def job_applications(job_id):
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if job.company_id != company.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    applications = Application.query.filter_by(job_id=job_id).order_by(Application.applied_date.desc()).all()
    
    return render_template('company/view_applications.html', job=job, applications=applications)

@app.route('/company/application/<int:app_id>/update', methods=['POST'])
@login_required
def update_application(app_id):
    if current_user.role != 'company':
        return jsonify({'error': 'Access denied'}), 403
    
    application = Application.query.get_or_404(app_id)
    job = Job.query.get(application.job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if job.company_id != company.id:
        return jsonify({'error': 'Access denied'}), 403
    
    status = request.json.get('status')
    if status in ['shortlisted', 'rejected', 'selected']:
        application.status = status
        db.session.commit()
        
        # Notify student
        student = Student.query.get(application.student_id)
        student_user = User.query.get(student.user_id)
        notification = Notification(
            user_id=student_user.id,
            message=f'Your application for {job.title} has been {status}',
            type='application'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid status'}), 400

@app.route('/company/dashboard')
@login_required
def company_dashboard():
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    company = Company.query.filter_by(user_id=current_user.id).first()
    jobs = Job.query.filter_by(company_id=company.id).order_by(Job.posted_date.desc()).limit(5).all()
    total_applications = Application.query.join(Job).filter(Job.company_id == company.id).count()
    
    # Get counts for different statuses
    shortlisted_count = Application.query.join(Job).filter(
        Job.company_id == company.id, 
        Application.status == 'shortlisted'
    ).count()
    
    selected_count = Application.query.join(Job).filter(
        Job.company_id == company.id, 
        Application.status == 'selected'
    ).count()
    
    return render_template('company/dashboard.html', 
                         company=company, 
                         jobs=jobs, 
                         total_applications=total_applications,
                         shortlisted_count=shortlisted_count,
                         selected_count=selected_count)

# ==================== NEW INTERVIEW & OFFER LETTER ROUTES ====================

@app.route('/company/job/<int:job_id>/schedule-interview', methods=['GET', 'POST'])
@login_required
def schedule_interview(job_id):
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if job.company_id != company.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all shortlisted applications
    applications = Application.query.filter_by(job_id=job_id, status='shortlisted').all()
    
    if request.method == 'POST':
        interview_date = request.form.get('interview_date')
        interview_time = request.form.get('interview_time')
        interview_mode = request.form.get('interview_mode')
        interview_location = request.form.get('interview_location')
        
        # Save interview details to each application
        for app in applications:
            app.interview_date = interview_date
            app.interview_time = interview_time
            app.interview_mode = interview_mode
            app.interview_location = interview_location
            app.interview_scheduled = True
            
            # Notify student
            student = Student.query.get(app.student_id)
            student_user = User.query.get(student.user_id)
            notification = Notification(
                user_id=student_user.id,
                message=f'Interview scheduled for {job.title} on {interview_date} at {interview_time}',
                type='interview'
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Interview scheduled successfully! Students have been notified.', 'success')
        return redirect(url_for('job_applications', job_id=job_id))
    
    return render_template('company/schedule_interview.html', job=job, applications=applications)

@app.route('/company/job/<int:job_id>/conduct-interview/<int:app_id>', methods=['GET', 'POST'])
@login_required
def conduct_interview(job_id, app_id):
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    application = Application.query.get_or_404(app_id)
    
    if job.company_id != company.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Update interview results
        application.interview_round1_status = request.form.get('round1_status')
        application.interview_round1_remarks = request.form.get('round1_remarks')
        application.interview_round2_status = request.form.get('round2_status')
        application.interview_round2_remarks = request.form.get('round2_remarks')
        application.interview_round3_status = request.form.get('round3_status')
        application.interview_round3_remarks = request.form.get('round3_remarks')
        
        application.technical_score = request.form.get('technical_score')
        application.communication_score = request.form.get('communication_score')
        application.overall_score = request.form.get('overall_score')
        
        db.session.commit()
        flash('Interview results saved successfully!', 'success')
        return redirect(url_for('job_applications', job_id=job_id))
    
    return render_template('company/conduct_interview.html', job=job, application=application)

@app.route('/company/job/<int:job_id>/final-selection', methods=['GET', 'POST'])
@login_required
def final_selection(job_id):
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if job.company_id != company.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all interviewed applications
    applications = Application.query.filter_by(job_id=job_id, interview_scheduled=True).all()
    
    if request.method == 'POST':
        selected_ids = request.form.getlist('selected_students')
        
        for app in applications:
            if str(app.id) in selected_ids:
                app.status = 'selected'
                app.final_result = 'selected'
                
                # Update student placement status
                student = Student.query.get(app.student_id)
                student.placement_status = 'placed'
                student.placed_company = company.company_name
                
                # Notify student
                student_user = User.query.get(student.user_id)
                notification = Notification(
                    user_id=student_user.id,
                    message=f'Congratulations! You have been selected for {job.title} at {company.company_name}!',
                    type='selection'
                )
                db.session.add(notification)
            else:
                app.status = 'rejected'
                app.final_result = 'rejected'
        
        db.session.commit()
        flash('Final selection completed! Selected students have been notified.', 'success')
        return redirect(url_for('generate_offer_letters', job_id=job_id))
    
    return render_template('company/final_selection.html', job=job, applications=applications)

@app.route('/company/job/<int:job_id>/offer-letters', methods=['GET'])
@login_required
def generate_offer_letters(job_id):
    if current_user.role != 'company':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if job.company_id != company.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get selected applications
    applications = Application.query.filter_by(job_id=job_id, status='selected').all()
    
    return render_template('company/offer_letters.html', job=job, company=company, applications=applications)

@app.route('/company/offer-letter/<int:app_id>/generate')
@login_required
def download_offer_letter(app_id):
    application = Application.query.get_or_404(app_id)
    job = Job.query.get(application.job_id)
    
    # Check if user is either company OR the student who got selected
    if current_user.role == 'company':
        company = Company.query.filter_by(user_id=current_user.id).first()
        if job.company_id != company.id:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
    elif current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if application.student_id != student.id:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get details for offer letter
    company = Company.query.get(job.company_id)
    student = Student.query.get(application.student_id)
    
    # Generate offer letter HTML
    from datetime import datetime
    import random
    
    offer_no = f"OFF/{company.company_name[:3].upper()}/{datetime.now().year}/{random.randint(100, 999)}"
    
    # Mark offer as generated (if not already)
    if not application.offer_letter_generated:
        application.offer_letter_generated = True
        application.offer_letter_sent_date = datetime.utcnow()
        db.session.commit()
    
    return render_template('company/offer_letter_template.html',
                         offer_no=offer_no,
                         company=company,
                         job=job,
                         student=student,
                         date=datetime.now().strftime('%d-%m-%Y'))

@app.route('/company/offer-letter/<int:app_id>/send-to-placement', methods=['POST'])
@login_required
def send_offer_to_placement(app_id):
    if current_user.role != 'company':
        return jsonify({'error': 'Access denied'}), 403
    
    application = Application.query.get_or_404(app_id)
    job = Job.query.get(application.job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if job.company_id != company.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Here you would typically send an email to placement cell
    # For now, we'll just mark it as sent
    
    flash('Offer letter sent to placement cell successfully!', 'success')
    return jsonify({'success': True})

# ==================== PLACEMENT OFFICER ROUTES ====================

@app.route('/placement/create-drive', methods=['GET', 'POST'])
@login_required
def create_drive():
    if current_user.role != 'placement':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    officer = PlacementOfficer.query.filter_by(user_id=current_user.id).first()
    form = PlacementDriveForm()
    
    if form.validate_on_submit():
        drive = PlacementDrive(
            drive_name=form.drive_name.data,
            coordinator_id=officer.id,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(drive)
        db.session.commit()
        
        flash('Placement drive created successfully!', 'success')
        return redirect(url_for('placement_dashboard'))
    
    return render_template('placement/create_drive.html', form=form)

@app.route('/placement/drives')
@login_required
def placement_drives():
    if current_user.role != 'placement':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    officer = PlacementOfficer.query.filter_by(user_id=current_user.id).first()
    drives = PlacementDrive.query.filter_by(coordinator_id=officer.id).order_by(PlacementDrive.start_date.desc()).all()
    
    return render_template('placement/manage_drives.html', drives=drives)

@app.route('/placement/stats')
@login_required
def placement_stats():
    if current_user.role != 'placement':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get placement statistics
    total_students = Student.query.count()
    placed_students = Student.query.filter_by(placement_status='placed').count()
    
    # Company wise placements
    company_stats = db.session.query(
        Company.company_name,
        db.func.count(Student.id).label('students_placed')
    ).join(Job, Job.company_id == Company.id)\
     .join(Application, Application.job_id == Job.id)\
     .join(Student, Student.id == Application.student_id)\
     .filter(Application.status == 'selected')\
     .group_by(Company.id).all()
    
    return render_template('placement/view_stats.html',
                         total_students=total_students,
                         placed_students=placed_students,
                         company_stats=company_stats)

@app.route('/placement/dashboard')
@login_required
def placement_dashboard():
    if current_user.role != 'placement':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    officer = PlacementOfficer.query.filter_by(user_id=current_user.id).first()
    drives = PlacementDrive.query.filter_by(coordinator_id=officer.id).all()
    total_students = Student.query.count()
    total_companies = Company.query.count()
    
    # Get pending offers
    pending_offers = Application.query.filter_by(
        offer_letter_generated=True,
        offer_accepted=False
    ).count()
    
    return render_template('placement/dashboard.html', 
                         officer=officer, 
                         drives=drives, 
                         total_students=total_students, 
                         total_companies=total_companies,
                         pending_offers=pending_offers)

if __name__ == '__main__':
    app.run(debug=True)