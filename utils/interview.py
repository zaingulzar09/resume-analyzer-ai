import os
import json
import random
import re
from dotenv import load_dotenv, find_dotenv
from utils.api_config import get_llm_provider
from utils.openai_patch import patch_openai

# Load environment variables
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

# Pre-defined interview questions by job role (fallback)
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
    Uses AI if available, falls back to pre-defined questions.
    """
    # Try to generate AI questions if provider is available
    if provider:
        try:
            ai_questions = generate_ai_questions(job_role, count)
            if ai_questions and len(ai_questions) > 0:
                return ai_questions
        except Exception as e:
            print(f"AI question generation failed: {e}")
    
    # Fallback to pre-defined questions
    questions = INTERVIEW_QUESTIONS.get(job_role, INTERVIEW_QUESTIONS["General"])
    if len(questions) > count:
        return random.sample(questions, count)
    return questions

def generate_ai_questions(job_role, count):
    """Generate interview questions using AI."""
    prompt = f"""Generate {count} interview questions for a {job_role} position.

The questions should:
1. Be relevant to the {job_role} role
2. Mix behavioral and technical questions
3. Be challenging but fair

Return ONLY a JSON array of strings, like this:
["Question 1", "Question 2", "Question 3"]

No explanations, just the JSON array."""

    try:
        print(f"🤖 Generating {count} AI questions for {job_role}...")
        
        response = provider.chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert interviewer. Generate relevant questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        # Clean response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Parse JSON array
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            questions = json.loads(json_match.group())
            if isinstance(questions, list) and len(questions) > 0:
                print(f"✅ Generated {len(questions)} AI questions")
                return questions[:count]
        
        return None
        
    except Exception as e:
        print(f"❌ AI question generation failed: {e}")
        return None

def evaluate_answer(question, answer, job_role="General"):
    """
    Evaluate an interview answer using LLM provider.
    """
    if not answer or len(answer.strip()) < 10:
        return {
            "score": 0,
            "feedback": "Your answer was too short to evaluate. Please provide a more detailed response.",
            "feedback_html": "<h4>Score: 0/100</h4><p>Your answer was too short to evaluate. Please provide a more detailed response.</p>"
        }
    
    if provider:
        try:
            return get_ai_answer_evaluation(question, answer, job_role)
        except Exception as e:
            print(f"AI evaluation failed: {e}")
            return get_basic_evaluation(question, answer, job_role)
    else:
        return get_basic_evaluation(question, answer, job_role)

def get_basic_evaluation(question, answer, job_role):
    """Provide basic evaluation when AI is not available."""
    word_count = len(answer.split())
    score = min(40 + (word_count * 2), 85)
    
    feedback_html = f"""
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
        <li>Consider using the STAR method (Situation, Task, Action, Result)</li>
    </ul>
    """
    
    return {
        "score": score,
        "feedback": feedback_html.strip()
    }

def get_ai_answer_evaluation(question, answer, job_role):
    """Use AI to evaluate interview answer."""
    prompt = f"""Evaluate this interview answer for a {job_role} position:

Question: {question}

Answer: {answer}

Provide evaluation as JSON with these exact keys:
- score (integer 0-100)
- strengths (string with HTML bullet points)
- improvements (string with HTML bullet points)
- relevance (string with feedback)

Return ONLY the JSON object, no other text."""

    try:
        print(f"🤖 Evaluating answer for {job_role} position...")
        
        response = provider.chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert interviewer. Provide constructive, honest feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        # Clean response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            evaluation = json.loads(json_match.group())
            
            # Build HTML feedback
            strengths_html = evaluation.get('strengths', 'Good attempt at answering the question.')
            improvements_html = evaluation.get('improvements', 'Try to be more specific.')
            
            feedback_html = f"""
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
                "feedback": feedback_html.strip(),
                "detailed": evaluation
            }
        
        return get_basic_evaluation(question, answer, job_role)
        
    except Exception as e:
        print(f"❌ AI evaluation failed: {e}")
        return get_basic_evaluation(question, answer, job_role)