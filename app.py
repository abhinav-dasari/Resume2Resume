"""
Resume Template Builder — Flask Application with User Authentication & History

Routes:
    /                   - Home page with template selection & upload area
    /register           - User Registration (Signup)
    /login              - User Login
    /logout             - User Logout
    /history            - Document Extraction History (User Dashboard)
    /history/view/<id>  - View historical extraction result
    /upload             - POST: Accept PDF resume, run extraction, save history
    /result             - GET: Show extracted data in selected template layout
    /templates          - GET: Return available templates as JSON
    /export/json        - GET: Download extracted data as JSON
    /export/csv         - GET: Download extracted data as CSV
"""

import os
import json
from functools import wraps
from flask import (
    Flask, render_template, request, session,
    redirect, url_for, flash, jsonify
)
from flask import Flask

from models import db, User, DocumentHistory
from ocr.ocr import extract_text
from dotenv import load_dotenv
from extractor.parser import extract_info
from exports.export import export_json, export_csv, export_pdf
from utils.helpers import allowed_file, secure_save, cleanup_old_files
from resume_templates import get_template, get_all_templates

from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# ─── App Configuration ───────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Database Configuration (Supports PostgreSQL & SQLite fallback)
DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'autofill.db')
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Fix Heroku/Supabase postgres:// scheme to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DEFAULT_SQLITE_PATH}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db.init_app(app)

# Upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
EXTRACTED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# Ensure directories exist and database tables are created
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

with app.app_context():
    db.create_all()


# ─── Auth Decorator ─────────────────────────────────

def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            if request.path == '/upload' or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Please log in to upload documents.', 'redirect': url_for('login')}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ─── Auth Routes ─────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration Route with duplicate username & email check."""
    if session.get('user_id'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic validations
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')

        # Check for duplicate Username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Username is already taken. Please choose another.', 'error')
            return render_template('register.html')

        # Check for duplicate Email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email address is already registered. Please log in instead.', 'error')
            return render_template('register.html')

        # Create new user with hashed password
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()

            # Auto-login after registration
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            flash('Account created successfully! Welcome to ResumeForge AI.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login Route with hashed password verification."""
    if session.get('user_id'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        login_input = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not login_input or not password:
            flash('Please enter both username/email and password.', 'error')
            return render_template('login.html')

        # Allow login by username or email
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input.lower())
        ).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('home'))
        else:
            flash('Invalid username/email or password.', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User Logout Route."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ─── Main & Document History Routes ────────────────

@app.route('/')
def home():
    """Home page with template selection and upload area."""
    templates = get_all_templates()
    return render_template('home.html', templates=templates)


@app.route('/templates')
def templates_api():
    """Return available resume templates as JSON."""
    templates = get_all_templates()
    return jsonify({'templates': templates})


@app.route('/history')
@login_required
def history():
    """User Dashboard / Extraction History."""
    user_id = session.get('user_id')
    documents = DocumentHistory.query.filter_by(user_id=user_id).order_by(DocumentHistory.created_at.desc()).all()
    return render_template('history.html', documents=documents)


@app.route('/history/view/<int:doc_id>')
@login_required
def view_history(doc_id):
    """Load historical extraction into session and show result page."""
    user_id = session.get('user_id')
    doc = DocumentHistory.query.filter_by(id=doc_id, user_id=user_id).first_or_404()

    try:
        fields = json.loads(doc.extracted_json)
    except Exception:
        fields = {}

    session['raw_text'] = doc.raw_text or ''
    session['doc_type'] = doc.document_type
    session['fields'] = fields
    session['original_filename'] = doc.original_filename
    session['ocr_method'] = 'database_history'
    # Default template for historical records
    if 'template_id' not in session:
        session['template_id'] = 'modern-minimal'

    return redirect(url_for('result'))


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    """
    Accept a PDF resume upload, run text extraction, parse resume fields,
    and store results in session and SQLite database.
    Returns JSON response for AJAX handling.
    """
    # Clean up old files for privacy
    cleanup_old_files(UPLOAD_FOLDER, max_age_hours=1)

    # Get template_id from the form
    template_id = request.form.get('template_id', 'modern-minimal')
    template = get_template(template_id)
    if not template:
        template_id = 'modern-minimal'

    # Check if file was submitted
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file was uploaded.'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file was selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload a PDF file.'
        }), 400

    # Save the file securely
    filepath, original_filename = secure_save(file, UPLOAD_FOLDER)

    if filepath is None:
        return jsonify({
            'success': False,
            'error': 'File could not be saved. It may exceed the 10 MB size limit.'
        }), 400

    try:
        # Step 1: Run Text Extraction from PDF
        ocr_result = extract_text(filepath)

        if not ocr_result['success']:
            return jsonify({
                'success': False,
                'error': f"Failed to read document: {ocr_result['error']}"
            }), 500

        raw_text = ocr_result['text']

        if not raw_text.strip():
            return jsonify({
                'success': False,
                'error': 'No text could be extracted from the PDF. '
                         'The document may be empty or a scanned image.'
            }), 400

        # Step 2: Extract structured resume information
        extraction_result = extract_info(raw_text)

        # Step 3: Store in session
        session['raw_text'] = raw_text
        session['doc_type'] = 'resume'
        session['fields'] = extraction_result['fields']
        session['original_filename'] = original_filename
        session['ocr_method'] = ocr_result['method']
        session['template_id'] = template_id

        # Step 4: Save to Database History if user is logged in
        user_id = session.get('user_id')
        if user_id:
            try:
                doc_record = DocumentHistory(
                    user_id=user_id,
                    original_filename=original_filename,
                    document_type='resume',
                    extracted_json=json.dumps(extraction_result['fields'], ensure_ascii=False),
                    raw_text=raw_text
                )
                db.session.add(doc_record)
                db.session.commit()
            except Exception as db_err:
                db.session.rollback()
                print(f"Failed to save document history to database: {db_err}")

        # Also save extracted data to a local JSON file as backup
        output_path = os.path.join(EXTRACTED_FOLDER, 'last_extraction.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'document_type': 'resume',
                'template_id': template_id,
                'fields': extraction_result['fields'],
                'raw_text': raw_text,
                'source_file': original_filename,
                'ocr_method': ocr_result['method'],
            }, f, indent=2, ensure_ascii=False)

        # Clean up the uploaded file for privacy
        try:
            os.remove(filepath)
        except OSError:
            pass

        return jsonify({'success': True})

    except Exception as e:
        # Clean up on error
        try:
            os.remove(filepath)
        except OSError:
            pass
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@app.route('/result')
@login_required
def result():
    """Display the extracted resume data in the selected template layout."""
    # Check if we have data in session
    if 'fields' not in session:
        flash('No resume has been processed yet. Please upload a resume first.', 'warning')
        return redirect(url_for('home'))

    template_id = session.get('template_id', 'modern-minimal')
    template = get_template(template_id) or get_template('modern-minimal')

    return render_template(
        'result.html',
        doc_type='resume',
        fields=session.get('fields', {}),
        raw_text=session.get('raw_text', ''),
        original_filename=session.get('original_filename', ''),
        ocr_method=session.get('ocr_method', ''),
        template=template,
        template_id=template_id,
    )


@app.route('/export/pdf', methods=['GET', 'POST'])
@login_required
def export_pdf_route():
    """Download extracted & edited data as a formatted PDF matching selected template."""
    if 'fields' not in session:
        flash('No data to export. Please upload a resume first.', 'warning')
        return redirect(url_for('home'))

    # If POST request, update session with current form edits from user
    if request.method == 'POST':
        form_data = request.form.to_dict()
        # Merge edited form data into fields session
        current_fields = session.get('fields', {})
        for key, val in form_data.items():
            if val:
                current_fields[key] = val
        session['fields'] = current_fields

    data = session.get('fields', {})
    template_id = session.get('template_id', 'modern-minimal')

    filename = session.get('original_filename', 'resume')
    filename = filename.rsplit('.', 1)[0] if '.' in filename else filename
    return export_pdf(data, template_id=template_id, filename=f'{filename}_resume.pdf')


@app.route('/export/json')
@login_required
def export_json_route():
    """Download extracted data as JSON."""
    if 'fields' not in session:
        flash('No data to export. Please upload a resume first.', 'warning')
        return redirect(url_for('home'))

    data = {
        'document_type': 'resume',
        **session.get('fields', {})
    }

    filename = session.get('original_filename', 'extracted_data')
    filename = filename.rsplit('.', 1)[0] if '.' in filename else filename
    return export_json(data, filename=f'{filename}_extracted.json')


@app.route('/export/csv')
@login_required
def export_csv_route():
    """Download extracted data as CSV."""
    if 'fields' not in session:
        flash('No data to export. Please upload a resume first.', 'warning')
        return redirect(url_for('home'))

    data = {
        'document_type': 'resume',
        **session.get('fields', {})
    }

    filename = session.get('original_filename', 'extracted_data')
    filename = filename.rsplit('.', 1)[0] if '.' in filename else filename
    return export_csv(data, filename=f'{filename}_extracted.csv')


# ─── Error Handlers ──────────────────────────────────

@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors."""
    flash('File is too large. Maximum allowed size is 10 MB.', 'error')
    return redirect(url_for('home'))


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    flash('Page not found.', 'error')
    return redirect(url_for('home'))


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('home'))


# ─── Run ─────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=False, port=5000)