from app import app, db, User, bcrypt

with app.app_context():
    # حذف کاربر قبلی اگه باشه
    db.session.query(User).filter_by(username='karo').delete()
    db.session.commit()

    # ساخت کاربر جدید
    hashed_password = bcrypt.generate_password_hash('00000').decode('utf-8')
    admin_user = User(username='karo', password=hashed_password, is_admin=True)
    db.session.add(admin_user)
    db.session.commit()
    print("کاربر ادمین با نام karo و رمز 00000 ساخته شد!")
    # چک کردن ذخیره شدن
    user = User.query.filter_by(username='karo').first()
    print(f"کاربر یافت شد: {user.username}, رمز: {user.password}")