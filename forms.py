from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, IntegerField, SelectField, DateField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class StudentRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    roll_number = StringField('Roll Number', validators=[DataRequired(), Length(max=20)])
    department = SelectField('Department', choices=[
        ('CSE', 'Computer Science'),
        ('ECE', 'Electronics'),
        ('EEE', 'Electrical'),
        ('MECH', 'Mechanical'),
        ('CIVIL', 'Civil')
    ], validators=[DataRequired()])
    semester = IntegerField('Semester', validators=[DataRequired(), NumberRange(min=1, max=8)])
    cgpa = FloatField('CGPA', validators=[DataRequired(), NumberRange(min=0, max=10)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=15)])
    tenth_percentage = FloatField('10th Percentage', validators=[NumberRange(min=0, max=100)])
    twelfth_percentage = FloatField('12th/Diploma Percentage', validators=[NumberRange(min=0, max=100)])

class CompanyRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    industry = StringField('Industry', validators=[DataRequired()])
    website = StringField('Website')
    description = TextAreaField('Company Description')
    location = StringField('Location', validators=[DataRequired()])
    contact_person = StringField('Contact Person', validators=[DataRequired()])
    contact_phone = StringField('Contact Phone', validators=[DataRequired()])

class JobPostForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    requirements = TextAreaField('Requirements', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    salary = StringField('Salary Package')
    job_type = SelectField('Job Type', choices=[
        ('full-time', 'Full Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract')
    ], validators=[DataRequired()])
    experience_required = StringField('Experience Required')
    min_cgpa = FloatField('Minimum CGPA Required', validators=[NumberRange(min=0, max=10)])
    eligible_branches = StringField('Eligible Branches (comma separated)')
    last_date = DateField('Last Date to Apply', validators=[DataRequired()], format='%Y-%m-%d')

class StudentProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address')
    skills = StringField('Skills (comma separated)')
    resume = FileField('Upload Resume', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents allowed!')])
    tenth_percentage = FloatField('10th Percentage', validators=[NumberRange(min=0, max=100)])
    twelfth_percentage = FloatField('12th/Diploma Percentage', validators=[NumberRange(min=0, max=100)])
    graduation_percentage = FloatField('Graduation Percentage', validators=[NumberRange(min=0, max=100)])
    backlogs = IntegerField('Number of Backlogs', default=0)

class PlacementDriveForm(FlaskForm):
    drive_name = StringField('Drive Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('End Date', validators=[DataRequired()], format='%Y-%m-%d')