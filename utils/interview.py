import os
import json
import random
from dotenv import load_dotenv, find_dotenv
from utils.api_config import get_llm_provider
from utils.openai_patch import patch_openai

# Load environment variables from project root or fallback to static/.env
env_loaded = load_dotenv(find_dotenv())
if not env_loaded:
    fallback_env = os.path.join(os.path.dirname(__file__), '..', 'static', '.env')
    fallback_env = os.path.normpath(fallback_env)
    if os.path.exists(fallback_env):
        load_dotenv(fallback_env)

# Apply the OpenAI patch
patch_openai()

# Get the LLM provider
provider = get_llm_provider()
if provider:
    provider_name = os.getenv("LLM_PROVIDER", "OpenAI").capitalize()
    print(f"Interview module: {provider_name} provider initialized successfully")
else:
    print("Interview module: Using basic evaluation (LLM provider not available)")

# Pre-defined interview questions by job role
INTERVIEW_QUESTIONS = {
    "Software Developer": [
        "Tell me about a challenging programming problem you solved recently.",
        "How do you stay updated with the latest programming technologies?",
        "Explain how you would design a scalable web application.",
        "How do you approach debugging a complex issue in your code?",
        "Describe your experience with agile development methodologies.",
        "How do you ensure your code is maintainable and readable for other developers?",
        "What strategies do you use for testing your code?",
        "Describe a situation where you had to optimize code for performance.",
        "How do you handle technical disagreements with team members?",
        "What's your approach to learning a new programming language or framework?"
    ],
    "Data Scientist": [
        "Explain a complex data analysis project you've worked on.",
        "How do you validate your machine learning models?",
        "What techniques do you use for handling missing data?",
        "Describe your approach to feature engineering.",
        "How do you communicate technical findings to non-technical stakeholders?",
        "What's your experience with big data technologies?",
        "How do you avoid overfitting in your models?",
        "Describe a situation where your data analysis led to a significant business decision.",
        "What statistical methods do you commonly use in your work?",
        "How do you stay current with advances in machine learning and data science?"
    ],
    "Project Manager": [
        "Describe how you handle scope changes in a project.",
        "How do you manage stakeholder expectations?",
        "Tell me about a time when you had to deal with a project that was behind schedule.",
        "How do you prioritize tasks within a project?",
        "Describe your approach to risk management.",
        "How do you ensure effective communication within your project team?",
        "Tell me about a conflict you resolved within a project team.",
        "How do you track and report project progress?",
        "Describe how you allocate resources in a project.",
        "How do you evaluate the success of a completed project?"
    ],
    "General": [
        "Tell me about yourself and your career goals.",
        "What are your greatest professional strengths?",
        "How do you handle stress and pressure?",
        "Describe a challenge you faced at work and how you overcame it.",
        "Where do you see yourself in five years?",
        "Why are you interested in this position?",
        "Describe your ideal work environment.",
        "How do you prioritize your work when dealing with multiple deadlines?",
        "Tell me about a time you demonstrated leadership skills.",
        "How do you handle receiving constructive criticism?"
    ]
}

def get_interview_questions(job_role="General", count=5):
    """
    Get interview questions for a specific job role.
    
    Args:
        job_role: Target job role
        count: Number of questions to return
        
    Returns:
        List of interview questions
    """
    questions = INTERVIEW_QUESTIONS.get(job_role, INTERVIEW_QUESTIONS["General"])
    # Randomly select questions if more are available than requested
    if len(questions) > count:
        return random.sample(questions, count)
    return questions

def evaluate_answer(question, answer, job_role="General"):
    """
    Evaluate an interview answer using LLM provider.
    
    Args:
        question: The interview question
        answer: The user's answer
        job_role: Target job role
        
    Returns:
        Dictionary with evaluation results
    """
    if not answer or len(answer.strip()) < 10:
        return {
            "score": 0,
            "feedback": "Your answer was too short to evaluate. Please provide a more detailed response."
        }
    
    if provider:
        try:
            return get_ai_answer_evaluation(question, answer, job_role)
        except Exception as e:
            print(f"AI evaluation failed: {e}")
            # Fallback evaluation if AI fails
            return get_basic_evaluation(question, answer, job_role)
    else:
        # Fallback evaluation if LLM provider is not available
        return get_basic_evaluation(question, answer, job_role)

def get_basic_evaluation(question, answer, job_role):
    """Provide basic evaluation when AI is not available."""
    word_count = len(answer.split())
    
    # Basic scoring based on length and content
    score = min(40 + (word_count * 2), 85)  # Base score with length bonus, capped at 85
    
    feedback = f"""
    <h4>Score: {score}/100</h4>
    
    <h4>Basic Analysis:</h4>
    <p>Your answer contains {word_count} words.</p>
    
    <h4>Strengths:</h4>
    <ul>
        <li>You provided a response to the question</li>
        <li>Answer length {"is appropriate" if word_count > 20 else "could be longer"}</li>
    </ul>
    
    <h4>Suggestions for Improvement:</h4>
    <ul>
        <li>Use specific examples from your experience</li>
        <li>Structure your answer with clear points</li>
        <li>Relate your response directly to the {job_role} role</li>
        <li>Consider using the STAR method (Situation, Task, Action, Result) for behavioral questions</li>
    </ul>
    
    <p><strong>Note:</strong> This is a basic evaluation. For detailed AI-powered feedback, ensure your OpenAI API key is properly configured.</p>
    """
    
    return {
        "score": score,
        "feedback": feedback.strip()
    }

def get_ai_answer_evaluation(question, answer, job_role):
    """
    Use OpenAI to evaluate interview answer.
    """
    if not client:
        raise Exception("OpenAI client not available")
    
    prompt = f"""
    Evaluate this interview answer for a {job_role} position:
    
    Question: {question}
    
    Answer: {answer}
    
    Please provide:
    1. A score from 0-100
    2. Detailed feedback on the strengths of the answer
    3. Specific suggestions for improvement
    4. How well the answer addresses the question
    
    Format your response as JSON with these keys: score, strengths, improvements, relevance
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert interview coach with HR experience."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )
    
    try:
        evaluation_text = response.choices[0].message.content
        # Extract JSON from response
        evaluation_text = evaluation_text.strip()
        if evaluation_text.startswith("```json"):
            evaluation_text = evaluation_text[7:-3]  # Remove ```json and ``` markers
        elif evaluation_text.startswith("```"):
            evaluation_text = evaluation_text[3:-3]  # Remove ``` markers
            
        evaluation = json.loads(evaluation_text)
        
        # Convert strengths and improvements to HTML lists if they're in array format
        strengths_html = evaluation.get('strengths', 'Good attempt at answering the question.')
        if isinstance(strengths_html, list):
            strengths_html = "<ul>" + "".join([f"<li>{item}</li>" for item in strengths_html]) + "</ul>"
        
        improvements_html = evaluation.get('improvements', 'Try to be more specific and provide concrete examples.')
        if isinstance(improvements_html, list):
            improvements_html = "<ul>" + "".join([f"<li>{item}</li>" for item in improvements_html]) + "</ul>"
        
        # Construct feedback message with HTML formatting
        feedback = f"""
        <h4>Score: {evaluation.get('score', 50)}/100</h4>
        
        <h4>Strengths:</h4>
        <div>{strengths_html}</div>
        
        <h4>Areas for Improvement:</h4>
        <div>{improvements_html}</div>
        
        <h4>Relevance to Question:</h4>
        <p>{evaluation.get('relevance', 'Ensure your answer directly addresses all aspects of the question.')}</p>
        """
        
        return {
            "score": evaluation.get("score", 50),
            "feedback": feedback.strip(),
            "detailed": evaluation
        }
    except Exception as e:
        # If JSON parsing fails, fall back to basic evaluation
        return get_basic_evaluation(question, answer, job_role)