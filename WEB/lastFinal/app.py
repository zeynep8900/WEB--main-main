from flask import Flask, flash, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import JSON
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime  
import os
import secrets
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from random import choice
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_wtf import FlaskForm
from wtforms import TextAreaField, FileField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from flask import abort
from sqlalchemy.orm import contains_eager
import requests  # Bu satır eklenmeli




app = Flask(__name__)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure SECRET_KEY is set
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(24)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Serializer for token generation (password reset, etc.)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    is_admin = db.Column(db.Boolean, default=False)  

    # Additional user information
    address = db.Column(db.String(1000))
    phone_number = db.Column(db.String(20))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    birthdate = db.Column(db.Date)
    gender = db.Column(db.String(10))
    comments = db.relationship('Comment', backref='user', lazy=True)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(100))
    city_description = db.Column(db.Text)
    cultural_places = db.Column(db.Text)
    tourist_attractions = db.Column(db.Text)
    restaurants = db.Column(db.Text)
    bars = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    places_of_interest = db.Column(db.Text)  
    accommodation = db.Column(db.Text)  # Konaklayacak yerler için ek alan
    trivago_link = db.Column(db.String(255))  # Trivago linki için ek alan
    transportation = db.Column(db.Text)  # Ulaşım bilgileri için ek alan





    

    # Define a one-to-many relationship with comments
    comments = db.relationship('Comment', backref='city', lazy=True)
    def average_rating(self):
        if self.comments:
            return round(sum(comment.rating for comment in self.comments) / len(self.comments), 1)
        return None

    

# Update the Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    photo_url = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=False)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

    user = db.relationship('User', backref='notebooks')
    city = db.relationship('City', backref='notebooks')


    

# Create all tables
with app.app_context():
    db.create_all()

# Flask-Admin setup
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
# Add models to admin panel
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(City, db.session))
admin.add_view(ModelView(Comment, db.session))
admin.add_view(ModelView(ContactMessage, db.session ))
admin.add_view(ModelView(Notebook, db.session))


# Define routes and views
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message(subject='Password Reset Request',
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f'Please use the following link to reset your password: {reset_url}'
            mail.send(msg)
            flash('Password reset link has been sent to your email.', 'info')
        else:
            flash('Email address not found.', 'error')
        
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.', 'error')
        return redirect(url_for('forgot_password'))
    except BadTimeSignature:
        flash('Invalid password reset link.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash("Password and Confirm Password do not match.", 'error')
            return redirect(url_for('reset_password', token=token))
        
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=8)
        db.session.commit()
        flash('Your password has been reset successfully. Please login with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    admin_button_visible = False
    if current_user.is_authenticated and current_user.is_admin:
        admin_button_visible = True

    if request.method == 'POST':
        if request.form.get('recommendation_button') == 'yes':
            cities = City.query.all()
            recommended_city = choice(cities)
            flash(f"We recommend visiting {recommended_city.city_name}!", 'info')
            return redirect(url_for('index'))
        
        if request.form.get('selected_city'):
            selected_city_id = request.form.get('selected_city')
            return redirect(url_for('create_route', city_id=selected_city_id))

    search_term = request.form.get('destination_city')
    if search_term:
        cities = City.query.filter(City.city_name.ilike(f'%{search_term}%')).all()
    else:
        cities = City.query.all()

    return render_template('index.html', cities=cities, admin_button_visible=admin_button_visible)


@app.route('/create_route/<city_id>', methods=['GET', 'POST'])
@login_required  # Kullanıcının giriş yapmış olmasını sağlar
def create_route(city_id):
    if request.method == 'POST':
        activities = request.form.get('activities')
        city = City.query.get(city_id)
        if city:
            # Rotanın oluşturulacağı işlemleri yapabilirsiniz
            flash(f"Route created successfully for {city.city_name}!", 'success')
            flash(f"Activities: {activities}", 'info')

            # Create Notebook entry
            content = f"Route for {city.city_name}: {activities}"
            new_notebook = Notebook(user_id=current_user.id, city_id=city_id, content=content)
            db.session.add(new_notebook)
            db.session.commit()
            
        else:
            flash("City not found!", 'error')
        
        return redirect(url_for('index'))

    city = City.query.get(city_id)
    if city:
        # Kullanıcının kendi notlarını al
        user_notebooks = Notebook.query.join(City).filter(
            Notebook.user_id == current_user.id,
            Notebook.city_id == city_id
        ).all()
        return render_template('create_route.html', city=city, user_notebooks=user_notebooks)
    else:
        flash("City not found!", 'error')
        return redirect(url_for('index'))



@app.route('/notebook', methods=['GET', 'POST'])
@login_required
def notebook():
    if request.method == 'POST':
        # Kullanıcı bir not defteri oluşturduğunda
        content = request.form.get('content')

        if content:
            new_notebook = Notebook(user_id=current_user.id, content=content)
            db.session.add(new_notebook)
            db.session.commit()
            flash('Notebook created successfully!', 'success')
            return redirect(url_for('notebook'))

    # GET isteği geldiğinde, kullanıcının mevcut not defterlerini göster
    user_notebooks = current_user.notebooks
    return render_template('create_route.html', notebooks=user_notebooks)




# Define a function to handle file uploads
def save_photo(file):
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure that the upload folder exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file.save(file_path)
        return file_path
    
# Define a WTForms form for comments and ratings
class CommentForm(FlaskForm):
    comment_text = TextAreaField('Add a Comment:', validators=[DataRequired()])
    photo = FileField('Upload a Photo:')
    rating = IntegerField('Rate the City:', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit')

def get_weather(city_name):
    api_key = 'd936c54fa85a929c1fb472e8361f657d'
    base_url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric'
    }
    response = requests.get(base_url, params=params)
    return response.json() if response.status_code == 200 else None

@app.route('/city_detail/<int:city_id>', methods=['GET', 'POST'])
def city_detail(city_id):
    city = City.query.get_or_404(city_id)
    comments = Comment.query.filter_by(city_id=city_id).all()
    form = CommentForm()

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('You need to be logged in to post a comment.', 'error')
            return redirect(url_for('login'))

        if form.validate_on_submit():
            comment_text = form.comment_text.data
            photo = form.photo.data
            rating = form.rating.data
            photo_url = save_photo(photo) if photo else None

            new_comment = Comment(
                user_id=current_user.id, 
                city_id=city_id, 
                text=comment_text, 
                photo_url=photo_url,
                rating=rating
            )
            db.session.add(new_comment)
            db.session.commit()
            flash('Comment posted successfully.', 'success')
            return redirect(url_for('city_detail', city_id=city_id))
        else:
            flash('Please provide a rating between 1 and 5.', 'error')

    average_rating = city.average_rating()

    # Get weather data for the city
    weather_data = get_weather(city.city_name)

    return render_template('city_detail.html', city=city, comments=comments, form=form, average_rating=average_rating, weather=weather_data)




@app.route('/city_recommendation', methods=['POST'])
def city_recommendation():
    if request.method == 'POST' and request.form.get('recommendation_button') == 'yes':
        # Şehir listesini al
        cities = City.query.all()
        # Rasgele bir şehir seç
        recommended_city = choice(cities)
        # Seçilen şehrin ismini flash mesajı olarak göster
        flash(f"We recommend visiting {recommended_city.city_name}!", 'info')
        return redirect(url_for('index'))  # Kullanıcıyı ana sayfaya yönlendir
    return redirect(url_for('index'))
@app.route('/profile', methods=['GET', 'POST'])

@login_required
def profile():
    if request.method == 'POST':
        # Update profile info
        current_user.city = request.form['city']
        current_user.country = request.form['country']
        current_user.phone = request.form['phone']
        current_user.gender = request.form['gender']

        birthdate_str = request.form['birthdate']
        if birthdate_str:
            try:
                current_user.birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid birthdate format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('profile'))

        # Save changes to the database
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        # Update name and email
        current_user.name = request.form['name']
        current_user.email = request.form['email']

        # Check if new password is provided
        if request.form['new_password']:
            # Check if current password is correct
            if check_password_hash(current_user.password, request.form['current_password']):
                # Set new password
                current_user.password = generate_password_hash(request.form['new_password'], method='pbkdf2:sha256', salt_length=8)
            else:
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('profile'))

        # Save changes to the database
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('contact'))

        # Save the message to the database
        new_message = ContactMessage(name=name, email=email, message=message)
        db.session.add(new_message)
        db.session.commit()

        # E-posta gönderme işlemi
        msg = Message(subject='Contact Form Submission',
                      sender=email,
                      recipients=['your-email@example.com'])
        msg.body = f'Name: {name}\nEmail: {email}\nMessage: {message}'
        mail.send(msg)



    return render_template("contact.html", thank_you=False)



@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))

        flash('Invalid email or password. Please try again.')

    return render_template("login.html", logged_in=current_user.is_authenticated)

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Password and Confirm Password do not match.")
            return redirect(url_for('signup'))

        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalnum() and not char.isalpha() for char in password):
            flash("Password must be at least 8 characters long, contain at least 1 number, and 1 non-alphanumeric character.")
            return redirect(url_for('signup'))

        hash_and_salted_password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            email=email,
            password=hash_and_salted_password,
            name=request.form.get('name'),
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("login"))

    return render_template("signup.html", logged_in=current_user.is_authenticated)

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    else:
        flash("You are not logged in.")
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template("about_us.html")



# Flask-Mail setup
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'zeynepfb704@gmail.com'
app.config['MAIL_PASSWORD'] = 'Zeynep12345.'

mail = Mail(app)




if __name__ == '__main__':
    app.run(debug=True, port=5000)

           
