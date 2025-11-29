from flask import Flask, render_template, request, redirect, flash, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    todos = db.relationship('ToDo', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class ToDo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"{self.sno} - {self.title}"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('hello_world'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not username:
            flash('Username is required!', 'error')
            return redirect(url_for('register'))
        
        if not email:
            flash('Email is required!', 'error')
            return redirect(url_for('register'))
        
        if not password:
            flash('Password is required!', 'error')
            return redirect(url_for('register'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters!', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            print(f"Error: {e}")
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('hello_world'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username:
            flash('Username is required!', 'error')
            return redirect(url_for('login'))
        
        if not password:
            flash('Password is required!', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('hello_world'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def hello_world():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc = request.form.get('desc', '').strip()
        
        # Validation
        if not title:
            flash('Title is required!', 'error')
            return redirect(url_for('hello_world'))
        
        if not desc:
            flash('Description is required!', 'error')
            return redirect(url_for('hello_world'))
        
        if len(title) > 200:
            flash('Title must be 200 characters or less!', 'error')
            return redirect(url_for('hello_world'))
        
        if len(desc) > 500:
            flash('Description must be 500 characters or less!', 'error')
            return redirect(url_for('hello_world'))
        
        try:
            todo = ToDo(title=title, desc=desc, user_id=current_user.id)
            db.session.add(todo)
            db.session.commit()
            flash('Todo added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the todo.', 'error')
            print(f"Error: {e}")
        
        return redirect(url_for('hello_world'))

    allTodo = ToDo.query.filter_by(user_id=current_user.id).order_by(ToDo.date_created.desc()).all()
    return render_template('index.html', allTodo=allTodo)

@app.route("/update/<int:sno>", methods=['GET', 'POST'])
@login_required
def update(sno):
    todo = ToDo.query.filter_by(sno=sno, user_id=current_user.id).first()
    if not todo:
        abort(404)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc = request.form.get('desc', '').strip()
        
        # Validation
        if not title:
            flash('Title is required!', 'error')
            return redirect(url_for('update', sno=sno))
        
        if not desc:
            flash('Description is required!', 'error')
            return redirect(url_for('update', sno=sno))
        
        if len(title) > 200:
            flash('Title must be 200 characters or less!', 'error')
            return redirect(url_for('update', sno=sno))
        
        if len(desc) > 500:
            flash('Description must be 500 characters or less!', 'error')
            return redirect(url_for('update', sno=sno))
        
        try:
            todo.title = title
            todo.desc = desc
            db.session.commit()
            flash('Todo updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the todo.', 'error')
            print(f"Error: {e}")
        
        return redirect(url_for('hello_world'))
    
    return render_template('update.html', todo=todo)

@app.route("/delete/<int:sno>")
@login_required
def delete(sno):
    todo = ToDo.query.filter_by(sno=sno, user_id=current_user.id).first()
    if not todo:
        abort(404)
    
    try:
        db.session.delete(todo)
        db.session.commit()
        flash('Todo deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the todo.', 'error')
        print(f"Error: {e}")
    
    return redirect(url_for('hello_world'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("DATABASE CREATED")
    app.run(debug=True, port=7000)
