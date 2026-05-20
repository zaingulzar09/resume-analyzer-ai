document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const setupForm = document.getElementById('setupForm');
    const interviewJobRole = document.getElementById('interviewJobRole');
    const interviewSetup = document.getElementById('interviewSetup');
    const interviewSession = document.getElementById('interviewSession');
    const currentQuestionNum = document.getElementById('currentQuestionNum');
    const totalQuestions = document.getElementById('totalQuestions');
    const currentQuestion = document.getElementById('currentQuestion');
    const answerInput = document.getElementById('answerInput');
    const submitAnswer = document.getElementById('submitAnswer');
    const loadingEvaluation = document.getElementById('loadingEvaluation');
    const answerFeedback = document.getElementById('answerFeedback');
    const answerScore = document.getElementById('answerScore');
    const feedbackContent = document.getElementById('feedbackContent');
    const nextQuestion = document.getElementById('nextQuestion');
    const finishInterview = document.getElementById('finishInterview');
    const interviewComplete = document.getElementById('interviewComplete');
    const averageScore = document.getElementById('averageScore');
    const startNewInterview = document.getElementById('startNewInterview');

    // Interview state
    let interviewState = {
        jobRole: '',
        questions: [],
        currentQuestionIndex: 0,
        scores: []
    };

    // Handle interview setup form submission
    setupForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const jobRole = interviewJobRole.value;
        
        // Show loading state
        interviewSetup.classList.add('hidden');
        
        // Fetch interview questions
        fetch('/api/get-interview-questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ job_role: jobRole })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Initialize interview state
            interviewState = {
                jobRole: jobRole,
                questions: data.questions,
                currentQuestionIndex: 0,
                scores: []
            };
            
            // Start the interview
            startInterview();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while setting up the interview. Please try again.');
            interviewSetup.classList.remove('hidden');
        });
    });
    
    // Submit answer button handler
    submitAnswer.addEventListener('click', function() {
        const answer = answerInput.value.trim();
        
        if (answer.length < 10) {
            alert('Please provide a more detailed answer');
            return;
        }
        
        // Show loading indicator
        submitAnswer.disabled = true;
        loadingEvaluation.classList.remove('hidden');
        
        // Get current question
        const question = interviewState.questions[interviewState.currentQuestionIndex];
        
        // Submit answer for evaluation
        fetch('/api/evaluate-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                answer: answer,
                job_role: interviewState.jobRole
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Display feedback
            displayFeedback(data);
            
            // Store score
            interviewState.scores.push(data.score);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while evaluating your answer. Please try again.');
        })
        .finally(() => {
            loadingEvaluation.classList.add('hidden');
            submitAnswer.disabled = false;
        });
    });
    
    // Next question button handler
    nextQuestion.addEventListener('click', function() {
        // Move to next question
        interviewState.currentQuestionIndex++;
        
        // Reset UI
        answerInput.value = '';
        answerFeedback.classList.add('hidden');
        
        // Check if interview is complete
        if (interviewState.currentQuestionIndex >= interviewState.questions.length) {
            completeInterview();
        } else {
            // Update question display
            updateQuestionDisplay();
        }
    });
    
    // Finish interview button handler
    finishInterview.addEventListener('click', function() {
        completeInterview();
    });
    
    // Start new interview button handler
    startNewInterview.addEventListener('click', function() {
        // Reset UI to setup state
        interviewComplete.classList.add('hidden');
        interviewSetup.classList.remove('hidden');
    });
    
    // Function to start the interview
    function startInterview() {
        // Update UI
        interviewSession.classList.remove('hidden');
        
        // Set total questions
        totalQuestions.textContent = interviewState.questions.length;
        
        // Display first question
        updateQuestionDisplay();
    }
    
    // Function to update question display
    function updateQuestionDisplay() {
        const questionIndex = interviewState.currentQuestionIndex;
        const question = interviewState.questions[questionIndex];
        
        // Update question number
        currentQuestionNum.textContent = questionIndex + 1;
        
        // Update question text
        currentQuestion.textContent = question;
        
        // Show/hide finish button based on question number
        if (questionIndex === interviewState.questions.length - 1) {
            nextQuestion.classList.add('hidden');
            finishInterview.classList.remove('hidden');
        } else {
            nextQuestion.classList.remove('hidden');
            finishInterview.classList.add('hidden');
        }
    }
    
    // Function to display feedback
    function displayFeedback(data) {
        // Update score
        answerScore.textContent = data.score;
        
        // Update feedback content - since we're now returning HTML, use innerHTML
        feedbackContent.innerHTML = data.feedback;
        
        // Show feedback section
        answerFeedback.classList.remove('hidden');
        
        // Scroll to feedback
        answerFeedback.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Function to complete the interview
    function completeInterview() {
        // Calculate average score
        const totalScore = interviewState.scores.reduce((sum, score) => sum + score, 0);
        const avgScore = Math.round(totalScore / interviewState.scores.length);
        
        // Update UI
        interviewSession.classList.add('hidden');
        interviewComplete.classList.remove('hidden');
        averageScore.textContent = avgScore;
    }
});