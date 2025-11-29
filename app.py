from flask import Flask, render_template, request, redirect, flash, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

db = SQLAlchemy(app)

class ToDo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"{self.sno} - {self.title}"

@app.route('/', methods=['GET', 'POST'])
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
            todo = ToDo(title=title, desc=desc)
            db.session.add(todo)
            db.session.commit()
            flash('Todo added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the todo.', 'error')
            print(f"Error: {e}")
        
        return redirect(url_for('hello_world'))

    allTodo = ToDo.query.order_by(ToDo.date_created.desc()).all()
    return render_template('index.html', allTodo=allTodo)

@app.route("/update/<int:sno>", methods=['GET', 'POST'])
def update(sno):
    todo = ToDo.query.filter_by(sno=sno).first()
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
def delete(sno):
    todo = ToDo.query.filter_by(sno=sno).first()
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
