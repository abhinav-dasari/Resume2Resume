/**
 * ResumeForge AI — Main JavaScript
 *
 * Handles:
 * - Template selection gallery
 * - Drag-and-drop file upload (PDF only)
 * - AJAX file upload with template_id
 * - Processing animation controller
 * - Raw text toggle
 */

document.addEventListener('DOMContentLoaded', () => {
    initTemplateGallery();
    initUploadZone();
    initRawTextToggle();
});


// ─── Template Gallery ───────────────────────────────
function initTemplateGallery() {
    const gallery = document.getElementById('template-gallery');
    if (!gallery) return;

    const cards = gallery.querySelectorAll('.template-card');
    const templateInput = document.getElementById('template-id-input');
    const uploadZone = document.getElementById('upload-zone');
    const uploadInstruction = document.getElementById('upload-instruction');

    cards.forEach(card => {
        card.addEventListener('click', () => {
            // Remove selected from all cards
            cards.forEach(c => c.classList.remove('selected'));

            // Mark this card as selected
            card.classList.add('selected');

            // Set template_id in hidden input
            const templateId = card.getAttribute('data-template-id');
            if (templateInput) {
                templateInput.value = templateId;
            }

            // Enable upload zone
            if (uploadZone) {
                uploadZone.classList.remove('disabled');
                uploadZone.classList.add('enabled');
            }

            // Update instruction text
            if (uploadInstruction) {
                uploadInstruction.textContent = `Template "${card.querySelector('.template-card-name').textContent}" selected! Now upload your PDF resume.`;
                uploadInstruction.style.color = '#6ee7b7';
            }

            // Smooth scroll to upload zone
            const wrapper = document.getElementById('upload-zone-wrapper');
            if (wrapper) {
                wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    });
}


// ─── Upload Zone ────────────────────────────────────
function initUploadZone() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadForm = document.getElementById('upload-form');

    if (!uploadZone || !fileInput) return;

    // Click to browse
    uploadZone.addEventListener('click', (e) => {
        if (e.target.closest('.file-preview') || e.target.closest('.remove-file')) return;
        if (uploadZone.classList.contains('disabled')) return;
        if (!window.IS_LOGGED_IN) {
            window.location.href = '/login';
            return;
        }
        fileInput.click();
    });

    // Drag events
    ['dragenter', 'dragover'].forEach(event => {
        uploadZone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!uploadZone.classList.contains('disabled')) {
                uploadZone.classList.add('drag-over');
            }
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        uploadZone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadZone.classList.remove('drag-over');
        });
    });

    // Drop handler
    uploadZone.addEventListener('drop', (e) => {
        if (uploadZone.classList.contains('disabled')) return;
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            if (!window.IS_LOGGED_IN) {
                window.location.href = '/login';
                return;
            }
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });

    // File input change
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            if (!window.IS_LOGGED_IN) {
                window.location.href = '/login';
                return;
            }
            handleFileSelect(fileInput.files[0]);
        }
    });

    // Upload button
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            if (fileInput.files.length > 0) {
                if (!window.IS_LOGGED_IN) {
                    window.location.href = '/login';
                    return;
                }
                submitUpload();
            }
        });
    }

    // Form submit
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (fileInput.files.length > 0) {
                if (!window.IS_LOGGED_IN) {
                    window.location.href = '/login';
                    return;
                }
                submitUpload();
            }
        });
    }
}


function handleFileSelect(file) {
    if (!window.IS_LOGGED_IN) {
        window.location.href = '/login';
        return;
    }

    // PDF only
    const allowedTypes = ['application/pdf'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    // Validate type
    if (!allowedTypes.includes(file.type)) {
        showAlert('Please upload a PDF file only.', 'error');
        return;
    }

    // Validate size
    if (file.size > maxSize) {
        showAlert('File size must be less than 10 MB.', 'error');
        return;
    }

    // Check template is selected
    const templateInput = document.getElementById('template-id-input');
    if (templateInput && !templateInput.value) {
        showAlert('Please select a resume template first.', 'warning');
        return;
    }

    // Show file preview
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadPrompt = document.getElementById('upload-prompt');

    if (filePreview) {
        filePreview.classList.add('active');
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = formatFileSize(file.size);
    }

    if (uploadBtn) {
        uploadBtn.disabled = false;
        uploadBtn.style.display = 'inline-flex';
    }

    if (uploadPrompt) {
        uploadPrompt.style.display = 'none';
    }
}


function submitUpload() {
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadZone = document.getElementById('upload-zone');
    const processingSection = document.getElementById('processing-section');
    const uploadSection = document.getElementById('upload-section');
    const templateInput = document.getElementById('template-id-input');

    if (!fileInput.files.length) return;

    if (!window.IS_LOGGED_IN) {
        window.location.href = '/login';
        return;
    }

    // Validate template selection
    if (templateInput && !templateInput.value) {
        showAlert('Please select a resume template first.', 'warning');
        return;
    }

    // Show processing UI
    if (uploadSection) uploadSection.style.display = 'none';
    if (processingSection) {
        processingSection.style.display = 'block';
        startProcessingAnimation();
    }

    // Create FormData and send via AJAX
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    if (templateInput) {
        formData.append('template_id', templateInput.value);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.status === 401) {
            window.location.href = '/login';
            return null;
        }
        return response.json();
    })
    .then(data => {
        if (!data) return;
        if (data.redirect) {
            window.location.href = data.redirect;
            return;
        }
        if (data.success) {
            // Complete processing animation then redirect
            completeProcessingAnimation(() => {
                window.location.href = '/result';
            });
        } else {
            showAlert(data.error || 'An error occurred during processing.', 'error');
            if (uploadSection) uploadSection.style.display = 'block';
            if (processingSection) processingSection.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showAlert('An error occurred. Please try again.', 'error');
        if (uploadSection) uploadSection.style.display = 'block';
        if (processingSection) processingSection.style.display = 'none';
    });
}


// ─── Processing Animation ───────────────────────────
function startProcessingAnimation() {
    const steps = document.querySelectorAll('.step');
    if (!steps.length) return;

    let currentStep = 0;

    function activateStep() {
        if (currentStep >= steps.length) return;

        // Mark previous steps as completed
        for (let i = 0; i < currentStep; i++) {
            steps[i].classList.remove('active');
            steps[i].classList.add('completed');
            const icon = steps[i].querySelector('.step-icon');
            if (icon) icon.textContent = '✓';
        }

        // Activate current step
        steps[currentStep].classList.add('active');
        currentStep++;

        // Auto-advance (the real completion happens via AJAX callback)
        if (currentStep < steps.length) {
            setTimeout(activateStep, 1500);
        }
    }

    activateStep();
}


function completeProcessingAnimation(callback) {
    const steps = document.querySelectorAll('.step');

    // Mark all steps as completed
    steps.forEach(step => {
        step.classList.remove('active');
        step.classList.add('completed');
        const icon = step.querySelector('.step-icon');
        if (icon) icon.textContent = '✓';
    });

    // Brief pause before redirect
    setTimeout(() => {
        if (callback) callback();
    }, 800);
}


// ─── Raw Text Toggle ────────────────────────────────
function initRawTextToggle() {
    const toggleBtn = document.getElementById('raw-text-toggle');
    const rawContent = document.getElementById('raw-text-content');

    if (!toggleBtn || !rawContent) return;

    toggleBtn.addEventListener('click', () => {
        toggleBtn.classList.toggle('open');
        rawContent.classList.toggle('open');
    });
}


// ─── PDF Export Helper ──────────────────────────────
function downloadPDF() {
    const resultForm = document.getElementById('result-form');

    if (resultForm) {
        // Create a temporary hidden form to POST form fields to /export/pdf
        const tempForm = document.createElement('form');
        tempForm.method = 'POST';
        tempForm.action = '/export/pdf';
        tempForm.style.display = 'none';

        // Collect all input and textarea fields from the form
        const elements = resultForm.querySelectorAll('input, textarea');
        elements.forEach(el => {
            if (el.name) {
                const hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = el.name;
                hidden.value = el.value;
                tempForm.appendChild(hidden);
            }
        });

        document.body.appendChild(tempForm);
        tempForm.submit();
        setTimeout(() => tempForm.remove(), 1000);
    } else {
        window.location.href = '/export/pdf';
    }
}


// ─── Remove File ────────────────────────────────────
function removeFile() {
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadPrompt = document.getElementById('upload-prompt');

    if (fileInput) fileInput.value = '';
    if (filePreview) filePreview.classList.remove('active');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.style.display = 'none';
    }
    if (uploadPrompt) uploadPrompt.style.display = 'block';
}


// ─── Utilities ──────────────────────────────────────
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}


function showAlert(message, type = 'error') {
    // Remove existing alerts
    const existing = document.querySelectorAll('.alert');
    existing.forEach(el => el.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;

    const icons = {
        error: '⚠️',
        success: '✅',
        warning: '⚡'
    };

    alertDiv.innerHTML = `<span>${icons[type] || '📌'}</span> ${message}`;

    // Insert at top of main container
    const container = document.querySelector('.main-container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.style.opacity = '0';
            alertDiv.style.transform = 'translateY(-10px)';
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }
}
