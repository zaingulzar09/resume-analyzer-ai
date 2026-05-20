document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const resumeForm = document.getElementById('resumeForm');
    const resumeFile = document.getElementById('resumeFile');
    const fileNameDisplay = document.querySelector('.file-name');
    const loadingIndicator = document.getElementById('loadingAnalysis');
    const analysisResults = document.getElementById('analysisResults');
    const errorMessage = document.getElementById('errorMessage') || createErrorElement();
    const resumeScore = document.getElementById('resumeScore');
    const structureFeedback = document.getElementById('structureFeedback');
    const contentFeedback = document.getElementById('contentFeedback');
    const improvementsFeedback = document.getElementById('improvementsFeedback');
    const keywordsFound = document.getElementById('keywordsFound');
    const keywordsMissing = document.getElementById('keywordsMissing');
    const summaryFeedback = document.getElementById('summaryFeedback');
    const downloadUpdatedResumeBtn = document.getElementById('downloadUpdatedResumeBtn');

    // Create error message element if it doesn't exist
    function createErrorElement() {
        const errorDiv = document.createElement('div');
        errorDiv.id = 'errorMessage';
        errorDiv.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4 hidden';
        errorDiv.setAttribute('role', 'alert');
        
        const strongEl = document.createElement('strong');
        strongEl.className = 'font-bold';
        strongEl.textContent = 'Error! ';
        
        const messageSpan = document.createElement('span');
        messageSpan.className = 'block sm:inline error-text';
        
        errorDiv.appendChild(strongEl);
        errorDiv.appendChild(messageSpan);
        
        // Insert before the form
        resumeForm.parentNode.insertBefore(errorDiv, resumeForm);
        
        return errorDiv;
    }

    // Show error message
    function showError(message) {
        const errorText = errorMessage.querySelector('.error-text') || errorMessage;
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
        
        // Scroll to error
        errorMessage.scrollIntoView({ behavior: 'smooth' });
        
        // Hide after 10 seconds
        setTimeout(() => {
            errorMessage.classList.add('hidden');
        }, 10000);
    }

    // Update file name display when file is selected
    resumeFile.addEventListener('change', function() {
        downloadUpdatedResumeBtn.classList.add('hidden');
        downloadUpdatedResumeBtn.disabled = true;

        if (this.files.length > 0) {
            const file = this.files[0];
            fileNameDisplay.textContent = file.name;
            
            // Validate file type
            const fileExt = file.name.split('.').pop().toLowerCase();
            if (fileExt !== 'pdf' && fileExt !== 'docx') {
                showError('Please upload a PDF or DOCX file only.');
                resumeFile.value = '';
                fileNameDisplay.textContent = 'No file chosen';
            }
            
            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                showError('File size exceeds 5MB limit. Please upload a smaller file.');
                resumeFile.value = '';
                fileNameDisplay.textContent = 'No file chosen';
            }
        } else {
            fileNameDisplay.textContent = 'No file chosen';
        }
    });

    // Handle form submission
    resumeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Hide any previous errors
        errorMessage.classList.add('hidden');
        
        // Validation
        if (!resumeFile.files.length) {
            showError('Please select a resume file to upload');
            return;
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('resume', resumeFile.files[0]);
        formData.append('job_role', document.getElementById('jobRole').value);
        
        // Hide download button until analysis completes
        downloadUpdatedResumeBtn.classList.add('hidden');
        downloadUpdatedResumeBtn.disabled = true;

        // Show loading indicator
        loadingIndicator.classList.remove('hidden');
        analysisResults.classList.add('hidden');
        
        // Submit to API
        fetch('/api/analyze-resume', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.message || errorData.error || 'Server error: ' + response.status);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.message || data.error);
            }
            displayAnalysisResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            showError(error.message || 'An error occurred while analyzing your resume. Please try again.');
        })
        .finally(() => {
            loadingIndicator.classList.add('hidden');
        });
    });

    // Display analysis results
    function displayAnalysisResults(data) {
        // Check if we have valid data
        if (!data || (data.ai_error && !data.feedback)) {
            showError('Analysis completed but with errors. Using basic analysis results.');
        }
        
        // Update score with animation
        const score = data.score || 0;
        animateScore(0, score);
        
        // Update feedback sections with formatted text
        if (data.feedback) {
            structureFeedback.innerHTML = formatFeedback(data.feedback.structure || 'No feedback available');
            contentFeedback.innerHTML = formatFeedback(data.feedback.content || 'No feedback available');
            improvementsFeedback.innerHTML = formatFeedback(data.feedback.improvements || 'No feedback available');
            summaryFeedback.innerHTML = formatFeedback(data.feedback.summary || 'No feedback available');
        }
        
        // Update keywords lists
        displayKeywordsList(keywordsFound, data.keywords_found, 'No relevant keywords found', 'success');
        displayKeywordsList(keywordsMissing, data.keywords_missing, 'No missing keywords!', 'warning');
        
        // Show results
        analysisResults.classList.remove('hidden');
        downloadUpdatedResumeBtn.classList.remove('hidden');
        downloadUpdatedResumeBtn.disabled = false;
        
        // Scroll to results
        analysisResults.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Download an updated copy of the resume
    downloadUpdatedResumeBtn.addEventListener('click', function() {
        if (!resumeFile.files.length) {
            showError('Please select the resume file again to download the updated version.');
            return;
        }

        downloadUpdatedResumeBtn.disabled = true;
        downloadUpdatedResumeBtn.textContent = 'Generating updated resume...';

        const formData = new FormData();
        formData.append('resume', resumeFile.files[0]);
        formData.append('job_role', document.getElementById('jobRole').value);

        fetch('/api/update-resume', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.message || errorData.error || 'Server error: ' + response.status);
                });
            }
            const disposition = response.headers.get('Content-Disposition');
            let filename = 'updated_resume';
            if (disposition && disposition.includes('filename=')) {
                filename = disposition.split('filename=')[1].trim().replace(/['"]+/g, '');
            }
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            const downloadUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl);
        })
        .catch(error => {
            console.error('Error:', error);
            showError(error.message || 'An error occurred while generating the updated resume. Please try again.');
        })
        .finally(() => {
            downloadUpdatedResumeBtn.disabled = false;
            downloadUpdatedResumeBtn.textContent = 'Download Updated Resume';
        });
    });
    
    // Helper function to display keywords lists
    function displayKeywordsList(container, keywords, emptyMessage, type) {
        container.innerHTML = '';
        if (keywords && keywords.length > 0) {
            keywords.forEach(keyword => {
                const li = document.createElement('li');
                li.textContent = keyword;
                li.className = type;
                container.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = emptyMessage;
            li.className = 'empty';
            container.appendChild(li);
        }
    }
    
    // Helper function to format feedback text
    function formatFeedback(text) {
        if (!text) return '';
        
        // Convert bullet points (- Item) to HTML lists
        if (text.includes('- ')) {
            const lines = text.split('\n');
            let inList = false;
            let formattedText = '';
            
            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('- ')) {
                    if (!inList) {
                        formattedText += '<ul>';
                        inList = true;
                    }
                    formattedText += `<li>${trimmed.substring(2)}</li>`;
                } else {
                    if (inList) {
                        formattedText += '</ul>';
                        inList = false;
                    }
                    if (trimmed) {
                        formattedText += `<p>${trimmed}</p>`;
                    }
                }
            }
            
            if (inList) {
                formattedText += '</ul>';
            }
            
            return formattedText;
        }
        
        // Add paragraph tags and handle line breaks
        return '<p>' + text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
    }
    
    // Animate score counter
    function animateScore(start, end) {
        const duration = 1500;
        const frameDuration = 1000/60;
        const totalFrames = Math.round(duration/frameDuration);
        let frame = 0;
        
        const animate = () => {
            frame++;
            const progress = frame / totalFrames;
            const currentValue = Math.round(start + (end - start) * progress);
            
            resumeScore.textContent = currentValue;
            
            if (frame < totalFrames) {
                requestAnimationFrame(animate);
            } else {
                resumeScore.textContent = end;
            }
        };
        
        animate();
    }
});