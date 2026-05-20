from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file, after_this_request
import os
import shutil
from dotenv import load_dotenv, find_dotenv
import json
import uuid
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Load environment variables from project root or fallback to static/.env
env_loaded = load_dotenv(find_dotenv())
if not env_loaded:
    fallback_env = os.path.join(os.path.dirname(__file__), 'static', '.env')
    if os.path.exists(fallback_env):
        load_dotenv(fallback_env)

# Import from utils package after loading environment variables
from utils import analyze_resume, get_interview_questions, evaluate_answer, db, User, FeedbackHistory
from utils.resume_analyzer import create_updated_resume
from utils.api_config import validate_llm_provider

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview_coach.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
print(f"Upload directory set to: {app.config['UPLOAD_FOLDER']}")

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('landing.html')

@app.route('/home')
@login_required
def home():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('landing'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already in use')
            return redirect(url_for('landing'))
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        # Log in user
        login_user(new_user)
        
        return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        
        flash('Invalid username or password')
        return redirect(url_for('landing'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))

@app.route('/resume')
@login_required
def resume_page():
    return render_template('resume.html')

@app.route('/interview')
@login_required
def interview_page():
    return render_template('interview.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    # Get user's feedback history from database
    feedback_history = FeedbackHistory.query.filter_by(user_id=current_user.id).order_by(FeedbackHistory.created_at.desc()).all()
    
    # Prepare data for the dashboard
    resume_scores = [item.score for item in feedback_history if item.feedback_type == 'resume']
    interview_scores = [item.score for item in feedback_history if item.feedback_type == 'interview']
    
    data = {
        'resume_score': resume_scores[-1] if resume_scores else None,
        'interview_scores': interview_scores,
        'feedback_history': [
            {
                'type': item.feedback_type,
                'score': item.score,
                'question': item.question,
                'answer': item.answer,
                'feedback': item.get_feedback_data(),
                'date': item.created_at
            } for item in feedback_history
        ]
    }
    
    return render_template('dashboard.html', data=data)

@app.route('/api/analyze-resume', methods=['POST'])
@login_required
def api_analyze_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload PDF or DOCX files only.'}), 400
    
    # Save the file temporarily
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # Make sure the uploads directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        file.save(filepath)
        print(f"File saved at: {filepath}")
        
        # Check if file was saved properly
        if not os.path.exists(filepath):
            return jsonify({'error': 'File could not be saved'}), 500
            
        if os.path.getsize(filepath) == 0:
            return jsonify({'error': 'Uploaded file is empty'}), 400
        
        # Analyze the resume
        job_role = request.form.get('job_role', 'General')
        print(f"Analyzing resume for job role: {job_role}")
        
        analysis_results = analyze_resume(filepath, job_role)
        
        # Store results in database
        try:
            feedback = FeedbackHistory(
                user_id=current_user.id,
                feedback_type='resume',
                score=analysis_results['score'],
                feedback_data=json.dumps(analysis_results)
            )
            db.session.add(feedback)
            db.session.commit()
            print("Resume analysis results saved to database")
        except Exception as db_error:
            print(f"Warning: Could not save feedback to database: {str(db_error)}")
            # Continue even if database saving fails
        
        # Clean up the file
        try:
            os.remove(filepath)
            print(f"Temporary file removed: {filepath}")
        except Exception as cleanup_error:
            print(f"Warning: Could not remove temporary file: {str(cleanup_error)}")
        
        return jsonify(analysis_results)
    except Exception as e:
        print(f"Error in resume analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Clean up the file in case of error
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Temporary file removed after error: {filepath}")
        except:
            pass
            
        return jsonify({
            'error': str(e),
            'message': 'An error occurred while analyzing your resume. Please try again or contact support.'
        }), 500

@app.route('/api/update-resume', methods=['POST'])
@login_required
def api_update_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload PDF or DOCX files only.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        print(f"File saved at: {filepath}")

        if not os.path.exists(filepath):
            return jsonify({'error': 'File could not be saved'}), 500

        if os.path.getsize(filepath) == 0:
            return jsonify({'error': 'Uploaded file is empty'}), 400

        job_role = request.form.get('job_role', 'General')
        print(f"Generating updated resume for job role: {job_role}")

        # Analyze the resume to drive update suggestions
        analysis_results = analyze_resume(filepath, job_role)

        updated_file_path, download_filename = create_updated_resume(filepath, job_role, analysis_results, filename)

        if not os.path.exists(updated_file_path):
            raise Exception('Unable to generate updated resume file')

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
            try:
                if os.path.exists(updated_file_path):
                    os.remove(updated_file_path)
            except Exception:
                pass
            return response

        return send_file(updated_file_path, as_attachment=True, download_name=download_filename)
    except Exception as e:
        print(f"Error updating resume: {str(e)}")
        import traceback
        traceback.print_exc()

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass

        return jsonify({
            'error': str(e),
            'message': 'An error occurred while generating the updated resume. Please try again.'
        }), 500

@app.route('/api/get-interview-questions', methods=['POST'])
@login_required
def api_get_interview_questions():
    data = request.get_json()
    job_role = data.get('job_role', 'General')
    
    try:
        questions = get_interview_questions(job_role)
        return jsonify({'questions': questions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate-answer', methods=['POST'])
@login_required
def api_evaluate_answer():
    data = request.get_json()
    question = data.get('question', '')
    answer = data.get('answer', '')
    job_role = data.get('job_role', 'General')
    
    try:
        evaluation = evaluate_answer(question, answer, job_role)
        
        # Store results in database
        feedback = FeedbackHistory(
            user_id=current_user.id,
            feedback_type='interview',
            question=question,
            answer=answer,
            score=evaluation['score'],
            feedback_data=json.dumps(evaluation)
        )
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify(evaluation)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api-status')
@login_required
def api_status():
    """Check the status of the LLM provider."""
    # Don't import again - use the already imported one from top
    status_key, message, provider = validate_llm_provider()
    
    # Debug print to terminal
    print(f"🔍 API Status Check: status_key={status_key}, message={message}")
    
    # Map status to what the template expects
    if status_key == "valid":
        status = "working"
    elif status_key == "warning":
        status = "warning"
    else:
        status = "error"
    
    return render_template('api_status.html', status=status, message=message)

@app.route('/api/optimize-resume', methods=['POST'])
@login_required
def api_optimize_resume():
    """Generate an optimized version of the resume using AI."""
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_role = data.get('job_role', 'General')
        
        if not resume_text:
            return jsonify({'error': 'No resume text provided'}), 400
        
        from utils.resume_analyzer import optimize_resume_with_ai
        
        optimized_text, error = optimize_resume_with_ai(resume_text, job_role)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'optimized_text': optimized_text,
            'message': 'Resume optimized successfully!'
        })
        
    except Exception as e:
        print(f"Error in optimize-resume: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-resume-text', methods=['POST'])
@login_required
def api_extract_resume_text():
    """Extract text from uploaded resume without full analysis."""
    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)
        from utils.resume_analyzer import extract_text_from_file
        text = extract_text_from_file(filepath)
        os.remove(filepath)
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)