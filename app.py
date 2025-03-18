from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
import random
from datetime import datetime

# بارگذاری متغیرهای محیطی
load_dotenv()

# تعریف اپلیکیشن Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# تعریف مدل User
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    appointments = db.relationship('Appointment', backref='user', lazy=True)

# تعریف مدل Appointment
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    education = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(15), nullable=False)
    consultant = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    appointment_number = db.Column(db.String(4), nullable=False)

# لود کردن کاربر برای Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# روت برای صفحه اصلی
@app.route('/')
def index():
    return render_template('home.html')

# روت برای نوبت‌های امروز
@app.route('/today_appointments')
def today_appointments():
    today = datetime.now().strftime('%Y/%m/%d')
    appointments = Appointment.query.filter_by(date=today).all()
    return render_template('today_appointments.html', appointments=appointments, today=today)

# روت برای رزرو نوبت
@app.route('/book', methods=['GET', 'POST'])
def book():
    consultants = ['مشاور 1', 'مشاور 2', 'مشاور 3']
    if request.method == 'POST':
        appointment_number = str(random.randint(1000, 9999))
        appointment = Appointment(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=request.form['name'],
            phone_number=request.form['phone_number'],
            age=request.form['age'],
            education=request.form['education'],
            national_id=request.form['national_id'],
            consultant=request.form['consultant'],
            date=request.form['date'],
            appointment_number=appointment_number
        )
        db.session.add(appointment)
        db.session.commit()
        flash('نوبت با موفقیت ثبت شد!')
        return render_template('book.html', consultants=consultants, appointment_number=appointment_number)
    return render_template('book.html', consultants=consultants)

# روت برای ورود
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('نام کاربری یا رمز عبور اشتباه است!')
    return render_template('login.html')

# روت برای ثبت‌نام
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        flash('ثبت‌نام با موفقیت انجام شد!')
        return redirect(url_for('login'))
    return render_template('register.html')

# روت برای خروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# روت برای پنل مدیریت
@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز!')
        return redirect(url_for('index'))
    appointments = Appointment.query.all()
    return render_template('admin_panel.html', appointments=appointments)

# روت برای تأیید نوبت
@app.route('/confirm_appointment/<int:appointment_id>')
@login_required
def confirm_appointment(appointment_id):
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز!')
        return redirect(url_for('index'))
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.confirmed = True
    db.session.commit()
    flash('نوبت با موفقیت تأیید شد!')
    return redirect(url_for('admin_panel'))

# روت برای لغو نوبت
@app.route('/cancel_appointment/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز!')
        return redirect(url_for('index'))
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash('نوبت با موفقیت لغو شد!')
    return redirect(url_for('admin_panel'))

# روت برای صفحه پروفایل
@app.route('/profile')
@login_required
def profile():
    if not current_user.is_authenticated:
        flash('لطفاً ابتدا وارد شوید!')
        return redirect(url_for('login'))
    appointments = Appointment.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', appointments=appointments)

# اجرای اپلیکیشن
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)