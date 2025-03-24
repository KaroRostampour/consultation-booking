from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
import random  # برای شماره نوبت تصادفی
import bcrypt  # برای رمزنگاری پسورد
from dotenv import load_dotenv  # برای لود متغیرهای محیطی

from models import db, User, Appointment, Consultant


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:12345*@localhost/consultation_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# مقداردهی اولیه db و migrate
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# نمایش نوبت‌های امروز
@app.route('/today_appointments')
def today_appointments():
    today = datetime.now().strftime('%Y/%m/%d')
    appointments = Appointment.query.filter_by(date=today).all()
    return render_template('today_appointments.html', appointments=appointments, today=today)

# فرم رزرو نوبت (داینامیک شده)
@app.route('/book', methods=['GET', 'POST'])
def book():
    consultants = Consultant.query.all()  # لود داینامیک مشاورها از دیتابیس
    if request.method == 'POST':
        appointment_number = str(random.randint(1000, 9999))
        appointment = Appointment(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=request.form['name'],
            phone_number=request.form['phone_number'],
            age=request.form['age'],
            education=request.form['education'],
            national_id=request.form['national_id'],
            consultant=request.form['consultant'],  # نام مشاور از فرم
            date=request.form['date'],
            appointment_number=appointment_number
        )
        db.session.add(appointment)
        db.session.commit()
        flash('نوبت شما با موفقیت ثبت شد! لطفاً شماره نوبت خود را یادداشت کنید.', 'success')
        return render_template('book.html', consultants=consultants, appointment_number=appointment_number)
    return render_template('book.html', consultants=consultants)

# ورود کاربر
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.hashpw(password.encode('utf-8'), user.password.encode('utf-8')) == user.password.encode('utf-8'):
            login_user(user)
            return redirect(url_for('index'))
        flash('نام کاربری یا رمز عبور اشتباه است!')
    return render_template('login.html')

# ثبت‌نام کاربر
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        new_user = User(username=username, password=hashed_password, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        flash('ثبت‌نام با موفقیت انجام شد!')
        return redirect(url_for('login'))
    return render_template('register.html')

# ساخت کاربر ادمین (موقت)
@app.route('/create_admin')
def create_admin():
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw('123456*'.encode('utf-8'), salt).decode('utf-8')
        admin_user = User(username='karo', password=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        return "کاربر ادمین با موفقیت ساخته شد! username: karo, password: 123456*"
    return "کاربر ادمین قبلاً وجود دارد!"

# خروج کاربر
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# پنل ادمین
@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('فقط ادمین‌ها به این صفحه دسترسی دارند!')
        return redirect(url_for('index'))
    appointments = Appointment.query.all()
    return render_template('admin_panel.html', appointments=appointments)

# تأیید نوبت
@app.route('/confirm_appointment/<int:appointment_id>')
@login_required
def confirm_appointment(appointment_id):
    if not current_user.is_admin:
        flash('فقط ادمین‌ها می‌توانند این کار را انجام دهند!')
        return redirect(url_for('index'))
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.confirmed = True
    db.session.commit()
    flash('نوبت با موفقیت تأیید شد!')
    return redirect(url_for('admin_panel'))

# لغو نوبت
@app.route('/cancel_appointment/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    if not current_user.is_admin:
        flash('فقط ادمین‌ها می‌توانند این کار را انجام دهند!')
        return redirect(url_for('index'))
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash('نوبت با موفقیت لغو شد!')
    return redirect(url_for('admin_panel'))

# پروفایل کاربر
@app.route('/profile')
@login_required
def profile():
    if not current_user.is_authenticated:
        flash('لطفاً ابتدا وارد شوید!')
        return redirect(url_for('login'))
    appointments = Appointment.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', appointments=appointments)

# صفحه اصلی
@app.route('/')
def index():
    return render_template('home.html')

# نمایش لیست مشاورها
@app.route('/admin/consultants')
@login_required
def list_consultants():
    if not current_user.is_admin:
        flash('فقط ادمین‌ها به این صفحه دسترسی دارند!')
        return redirect(url_for('index'))
    consultants = Consultant.query.all()  # لود همه مشاورها
    return render_template('admin_consultants.html', consultants=consultants)

# اضافه کردن مشاور
@app.route('/admin/add_consultant', methods=['GET', 'POST'])
@login_required
def add_consultant():
    if not current_user.is_admin:
        flash('فقط ادمین‌ها به این صفحه دسترسی دارند!')
        return redirect(url_for('admin_panel'))
    if request.method == 'POST':
        name = request.form['name']
        specialty = request.form['specialty']
        time_start = request.form['time_start']
        time_end = request.form['time_end']
        days = ','.join(request.form.getlist('days'))

        new_consultant = Consultant(name=name, specialty=specialty, time_start=time_start, time_end=time_end, days=days)
        db.session.add(new_consultant)
        db.session.commit()
        flash('مشاور با موفقیت ثبت شد!')
        return redirect(url_for('list_consultants'))  # به لیست مشاورها برمی‌گرده
    return render_template('admin_add_consultant.html')

# ویرایش مشاور
@app.route('/admin/edit_consultant/<int:consultant_id>', methods=['GET', 'POST'])
@login_required
def edit_consultant(consultant_id):
    if not current_user.is_admin:
        flash('فقط ادمین‌ها به این صفحه دسترسی دارند!')
        return redirect(url_for('index'))
    consultant = Consultant.query.get_or_404(consultant_id)
    if request.method == 'POST':
        consultant.name = request.form['name']
        consultant.specialty = request.form['specialty']
        consultant.time_start = request.form['time_start']
        consultant.time_end = request.form['time_end']
        consultant.days = ','.join(request.form.getlist('days'))
        db.session.commit()
        flash('مشاور با موفقیت ویرایش شد!')
        return redirect(url_for('list_consultants'))
    return render_template('admin_edit_consultant.html', consultant=consultant)

# حذف مشاور
@app.route('/admin/delete_consultant/<int:consultant_id>')
@login_required
def delete_consultant(consultant_id):
    if not current_user.is_admin:
        flash('فقط ادمین‌ها به این صفحه دسترسی دارند!')
        return redirect(url_for('index'))
    consultant = Consultant.query.get_or_404(consultant_id)
    db.session.delete(consultant)
    db.session.commit()
    flash('مشاور با موفقیت حذف شد!')
    return redirect(url_for('list_consultants'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)