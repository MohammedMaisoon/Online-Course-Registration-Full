# app.py - Main Flask Application
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import re
import secrets
import MySQLdb.cursors

# Initialize Flask app
app = Flask(__name__)
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Configuration
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Change to your MySQL username
app.config['MYSQL_PASSWORD'] = ''  # Change to your MySQL password
app.config['MYSQL_DB'] = 'course_registration'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mohammedmaisooninfo@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'
app.config['MAIL_DEFAULT_SENDER'] = 'mohammedmaisooninfo@gmail.com'
mail = Mail(app)

@app.context_processor
def utility_processor():
    def get_course_image(course):
        # Check if course has an image attribute
        if course and 'image' in course and course['image']:
            return url_for('static', filename=f'img/courses/{course["image"]}')
        # Return default placeholder if no image exists
        return url_for('static', filename='img/course-placeholder.jpg')
    
    return dict(get_course_image=get_course_image)

# Helper Functions
def is_logged_in(f):
    """Decorator to check if user is logged in"""
    def wrapped(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login'))
    wrapped.__name__ = f.__name__
    return wrapped

def is_admin(f):
    """Decorator to check if user is an admin"""
    def wrapped(*args, **kwargs):
        if 'logged_in' in session and session['user_role'] == 'admin':
            return f(*args, **kwargs)
        else:
            flash('You are not authorized to access this page', 'danger')
            return redirect(url_for('dashboard'))
    wrapped.__name__ = f.__name__
    return wrapped

# Routes
@app.route('/')
def index():
    """Home page route"""
    # Get featured courses
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM courses WHERE is_featured = 1 LIMIT 3")
    featured_courses = cur.fetchall()
    cur.close()
    
    return render_template('index.html', featured_courses=featured_courses)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        
        # Use Flask-MySQLdb connection
        cur = mysql.connection.cursor()
        
        # Check if email already exists
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        if cur.fetchone():
            flash('Email already registered', 'error')
            cur.close()
            return render_template('register.html')
        
        # Create new user
        cur.execute('''
            INSERT INTO users (first_name, last_name, email, password, role, created_at) 
            VALUES (%s, %s, %s, %s, 'student', NOW())
        ''', (first_name, last_name, email, password))
        mysql.connection.commit()
        
        # Log user in
        user_id = cur.lastrowid
        cur.close()
        
        session['user_id'] = user_id
        session['user_name'] = f"{first_name} {last_name}"
        session['logged_in'] = True
        
        flash('Registration successful!', 'success')
        
        # Check for pending enrollment
        if 'pending_enrollment' in session:
            course_id = session.pop('pending_enrollment')
            return redirect(url_for('enroll', course_id=course_id))
        
        return redirect(url_for('index'))
    
    # GET request - return the registration form
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Use Flask-MySQLdb connection
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        
        # Simple password verification (in production, use password hashing)
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            session['user_role'] = user['role']
            session['logged_in'] = True
            
            # Check for pending enrollment
            if 'pending_enrollment' in session:
                course_id = session.pop('pending_enrollment')
                return redirect(url_for('enroll', course_id=course_id))
            
            return redirect(url_for('dashboard'))
        else:
            # Try a different flash message category that might be recognized by your template
            flash('Invalid email or password', 'danger')
            # Force a render of the login template - don't rely on redirect
            return render_template('login.html')
    
    # GET request
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout route"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    """User dashboard route"""
    cur = mysql.connection.cursor()
    
    # Get enrolled courses
    cur.execute("""
        SELECT c.*, e.progress, e.enrolled_date 
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.user_id = %s
        ORDER BY e.enrolled_date DESC
    """, [session['user_id']])
    enrolled_courses = cur.fetchall()
    
    # Get completed courses count
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM enrollments 
        WHERE user_id = %s AND progress = 100
    """, [session['user_id']])
    completed_count = cur.fetchone()['count']
    
    # Get in-progress courses count
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM enrollments 
        WHERE user_id = %s AND progress > 0 AND progress < 100
    """, [session['user_id']])
    in_progress_count = cur.fetchone()['count']
    
    # Get upcoming assignments/exams
    cur.execute("""
        SELECT a.*, c.title as course_title
        FROM assignments a
        JOIN courses c ON a.course_id = c.id
        JOIN enrollments e ON e.course_id = c.id AND e.user_id = %s
        WHERE a.due_date > NOW()
        ORDER BY a.due_date ASC
        LIMIT 5
    """, [session['user_id']])
    upcoming_assignments = cur.fetchall()
    
    cur.close()
    
    return render_template('dashboard.html', 
                          enrolled_courses=enrolled_courses,
                          completed_count=completed_count,
                          in_progress_count=in_progress_count,
                          upcoming_assignments=upcoming_assignments)

@app.route('/courses')
def courses():
    """Courses listing route"""
    # Get filter parameters
    category = request.args.get('category', '')
    level = request.args.get('level', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 6
    offset = (page - 1) * per_page
    
    # Build query
    query = "SELECT * FROM courses WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = %s"
        params.append(category)
    
    if level:
        query += " AND level = %s"
        params.append(level)
    
    if search:
        query += " AND (title LIKE %s OR description LIKE %s)"
        search_param = f"%{search}%"
        params.append(search_param)
        params.append(search_param)
    
    # Count total courses for pagination
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    total_courses = len(cur.fetchall())
    
    # Get paginated courses
    query += " LIMIT %s OFFSET %s"
    params.append(per_page)
    params.append(offset)
    
    cur.execute(query, params)
    courses = cur.fetchall()
    
    # Get categories for filter
    cur.execute("SELECT DISTINCT category FROM courses")
    categories = [row['category'] for row in cur.fetchall()]
    
    # Get levels for filter
    cur.execute("SELECT DISTINCT level FROM courses")
    levels = [row['level'] for row in cur.fetchall()]
    
    cur.close()
    
    # Calculate pagination info
    total_pages = (total_courses + per_page - 1) // per_page
    
    return render_template('courses.html', 
                          courses=courses,
                          categories=categories,
                          levels=levels,
                          current_page=page,
                          total_pages=total_pages,
                          total_courses=total_courses,
                          category=category,
                          level=level,
                          search=search)


@app.route('/course/<int:course_id>')
def course_detail(course_id):
    # Get course details
    cur = mysql.connection.cursor()
    
    # Get course
    cur.execute('SELECT * FROM courses WHERE id = %s', (course_id,))
    course = cur.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('courses'))
    
    # Fix for the SQL error - get modules without using module_order
    try:
        cur.execute('''
            SELECT * FROM modules 
            WHERE course_id = %s
        ''', (course_id,))
        modules = cur.fetchall()
    except Exception as e:
        print(f"Error fetching modules: {e}")
        modules = []
    
    # Get instructor
    instructor_id = course.get('instructor_id', 1)
    cur.execute('SELECT * FROM users WHERE id = %s', (instructor_id,))
    instructor = cur.fetchone()
    
    # Get reviews
    cur.execute('''
        SELECT r.*, u.first_name, u.last_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.course_id = %s
    ''', (course_id,))
    reviews = cur.fetchall()
    
    # Calculate average rating
    avg_rating = 0
    if reviews:
        total = sum(review['rating'] for review in reviews)
        avg_rating = total / len(reviews)
    
    # Check if user is enrolled
    is_enrolled = False
    if 'user_id' in session:
        cur.execute('''
            SELECT * FROM enrollments 
            WHERE user_id = %s AND course_id = %s
        ''', (session['user_id'], course_id))
        if cur.fetchone():
            is_enrolled = True
    
    cur.close()
    
    return render_template('course_detail.html', 
                          course=course,
                          instructor=instructor,
                          modules=modules,
                          reviews=reviews,
                          avg_rating=avg_rating,
                          is_enrolled=is_enrolled)

@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    # Check if user is logged in
    if 'user_id' not in session:
        # Store the course ID in session to redirect after login
        session['pending_enrollment'] = course_id
        flash('Please log in to enroll in this course', 'info')
        return redirect(url_for('login'))
    
    # User is logged in, proceed with enrollment
    user_id = session['user_id']
    
    # Check if already enrolled
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM enrollments WHERE user_id = %s AND course_id = %s', 
                (user_id, course_id))
    existing_enrollment = cur.fetchone()
    
    if not existing_enrollment:
        # Get course information for the email
        cur.execute('SELECT * FROM courses WHERE id = %s', (course_id,))
        course = cur.fetchone()
        
        # Create new enrollment
        cur.execute('''
            INSERT INTO enrollments (user_id, course_id, enrolled_date, progress) 
            VALUES (%s, %s, NOW(), 0)
        ''', (user_id, course_id))
        mysql.connection.commit()
        
        # Send enrollment email
        send_enrollment_email(user_id, course)
        
        flash('Successfully enrolled in the course!', 'success')
    else:
        flash('You are already enrolled in this course', 'info')
    
    cur.close()
    
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/learn/<int:course_id>')
@is_logged_in
def learn(course_id):
    """Course learning interface route"""
    cur = mysql.connection.cursor()
    
    # Check if enrolled
    cur.execute("SELECT * FROM enrollments WHERE user_id = %s AND course_id = %s",
                [session['user_id'], course_id])
    enrollment = cur.fetchone()
    
    if not enrollment:
        flash('You need to enroll in this course first', 'danger')
        return redirect(url_for('course_detail', course_id=course_id))
    
    # Get course details
    cur.execute("SELECT * FROM courses WHERE id = %s", [course_id])
    course = cur.fetchone()
    
    if not course:
        flash('Course not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get course content/modules
    try:
        cur.execute("SELECT * FROM modules WHERE course_id = %s ORDER BY id", [course_id])
        modules = cur.fetchall()
    except Exception as e:
        print(f"Error fetching modules: {e}")
        modules = []
    
    # Get user progress (change this based on your progress tracking system)
    progress = enrollment.get('progress', 0)
    
    cur.close()
    
    return render_template('learn.html', 
                          course=course, 
                          modules=modules, 
                          progress=progress)
    
def send_enrollment_email(user_id, course):
    # Get user email
    cur = mysql.connection.cursor()
    cur.execute('SELECT email, first_name FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    
    if not user:
        return
    
    # Create email content
    subject = f"Enrollment Confirmation: {course['title']}"
    
    body = f"""
    Dear {user['first_name']},
    
    Thank you for enrolling in "{course['title']}".
    
    Course Details:
    - Duration: {course['duration']} hours
    - Level: {course['level']}
    - Price: {"Free" if course['price'] == 0 else f"₹{course['price']}"}
    
    You can start learning right away by visiting your dashboard.
    
    Best regards,
    Skills On Demand Team
    """
    
    # Send email (implementation depends on your email service)
    try:
        # Using Flask-Mail example
        msg = Message(subject, recipients=[user['email']])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")    

@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page route"""
    return render_template('contact.html')    

if __name__ == '__main__':
    app.run(debug=True)