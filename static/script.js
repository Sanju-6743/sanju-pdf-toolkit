// PDF Toolkit JavaScript

// Initialize Socket.IO connection
let socket;

// Connect to Socket.IO server
function connectSocket() {
    socket = io();

    // Socket.IO Connection Events
    socket.on('connect', () => {
        const connectionIndicator = document.getElementById('connection-indicator');
        const connectionText = document.getElementById('connection-text');
        
        if (connectionIndicator && connectionText) {
            connectionIndicator.classList.remove('disconnected');
            connectionIndicator.classList.add('connected');
            connectionText.textContent = 'Connected';
            showNotification('Connected to server', 'success');
        }
    });

    socket.on('disconnect', () => {
        const connectionIndicator = document.getElementById('connection-indicator');
        const connectionText = document.getElementById('connection-text');
        
        if (connectionIndicator && connectionText) {
            connectionIndicator.classList.remove('connected');
            connectionIndicator.classList.add('disconnected');
            connectionText.textContent = 'Disconnected';
            showNotification('Disconnected from server', 'error');
        }
    });

    // Socket.IO Status Updates
    socket.on('status_update', (data) => {
        const { status, message, progress, tool, downloads, filename, original_size, compressed_size, reduction_percent, preview_text, log_entry, detail } = data;
        
        // Play notification sounds for status changes
        if (status === 'success') {
            playNotificationSound('success');
        } else if (status === 'error') {
            playNotificationSound('error');
        }
        
        // Update progress bar if provided
        if (progress !== undefined) {
            const progressBar = document.getElementById(`${tool}-progress-bar`);
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
        }
        
        // Update status message
        const statusElement = document.getElementById(`${tool}-status`);
        if (statusElement) {
            statusElement.textContent = message;
        }
        
        // Show/hide progress container
        const progressContainer = document.getElementById(`${tool}-progress-container`);
        if (progressContainer) {
            if (status === 'processing') {
                progressContainer.classList.remove('hidden');
                
                // Progress handling (entertainment features removed)
            } else if (status === 'success' || status === 'error') {
                // Hide progress after a delay
                setTimeout(() => {
                    progressContainer.classList.add('hidden');
                    
                    // Entertainment features removed
                }, 1000);
            }
        }
        
        // Show notification for important status updates
        if (status === 'success') {
            showNotification(message, 'success');
            
            // Second notification removed
        } else if (status === 'error' || status === 'warning') {
            showNotification(message, status);
        } else if (status === 'processing') {
            // Processing notifications removed
        }
        
        // Helper function to generate a title for the card based on the log message
        function getCardTitle(logText, status) {
            if (status === 'success') return 'Success';
            if (status === 'error') return 'Error';
            if (status === 'warning') return 'Warning';
            
            if (logText.includes('Initializing') || logText.includes('Starting')) {
                return 'Process Started';
            } else if (logText.includes('Processing file')) {
                return 'Processing File';
            } else if (logText.includes('Processing page')) {
                return 'Processing Page';
            } else if (logText.includes('Added page')) {
                return 'Page Added';
            } else if (logText.includes('Writing')) {
                return 'Writing Output';
            } else if (logText.includes('Created')) {
                return 'File Created';
            } else if (logText.includes('PDF has')) {
                return 'File Analysis';
            } else if (logText.includes('Reordering')) {
                return 'Reordering Files';
            } else if (logText.includes('Extracting')) {
                return 'Extracting Pages';
            } else if (logText.includes('compression')) {
                return 'Setting Compression';
            } else if (logText.includes('Original file size')) {
                return 'File Size Analysis';
            } else if (logText.includes('Compressed file size')) {
                return 'Compression Results';
            } else {
                return 'Processing';
            }
        }
        
        // Function to update the processing timer
        function updateProcessingTimer(tool) {
            const timerElement = document.getElementById(`${tool}-timer`);
            if (!timerElement) return;
            
            // If we don't have a start time stored, set it now
            if (!window[`${tool}StartTime`]) {
                window[`${tool}StartTime`] = new Date();
                
                // Clear any existing interval
                if (window[`${tool}TimerInterval`]) {
                    clearInterval(window[`${tool}TimerInterval`]);
                }
                
                // Set up interval to update the timer every second
                window[`${tool}TimerInterval`] = setInterval(() => {
                    if (!window[`${tool}StartTime`]) return;
                    
                    const elapsedMs = new Date() - window[`${tool}StartTime`];
                    const seconds = Math.floor((elapsedMs / 1000) % 60);
                    const minutes = Math.floor((elapsedMs / (1000 * 60)) % 60);
                    
                    timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                }, 1000);
            }
        }
        
        // Function to update the timeline progress
        function updateTimelineProgress(tool, status, progress) {
            const timelineProgress = document.getElementById(`${tool}-timeline-progress`);
            if (!timelineProgress) return;
            
            // Update progress bar width
            if (progress !== undefined) {
                timelineProgress.style.width = `${progress}%`;
            }
            
            // Update timeline markers based on progress
            const statusLogContainer = document.getElementById(`${tool}-status-log`);
            if (!statusLogContainer) return;
            
            const timelineMarkers = statusLogContainer.querySelectorAll('.timeline-marker');
            
            // Determine which markers should be active based on progress
            if (progress <= 20) {
                // Only start is active
                activateMarker(timelineMarkers, 'start');
            } else if (progress > 20 && progress <= 80) {
                // Start and processing are active
                activateMarker(timelineMarkers, 'start');
                activateMarker(timelineMarkers, 'processing');
            } else if (progress > 80 && progress < 100) {
                // Start, processing, and finalizing are active
                activateMarker(timelineMarkers, 'start');
                activateMarker(timelineMarkers, 'processing');
                activateMarker(timelineMarkers, 'finalizing');
            } else if (progress >= 100 || status === 'success' || status === 'error') {
                // All markers are active
                timelineMarkers.forEach(marker => {
                    const dot = marker.querySelector('.marker-dot');
                    if (dot) {
                        dot.classList.add('active');
                    }
                    marker.classList.add('active');
                });
            }
        }
        
        // Helper function to activate a specific marker
        function activateMarker(markers, stage) {
            markers.forEach(marker => {
                if (marker.getAttribute('data-stage') === stage) {
                    const dot = marker.querySelector('.marker-dot');
                    if (dot) {
                        dot.classList.add('active');
                    }
                    marker.classList.add('active');
                }
            });
        }
        
        // Show compression info if provided
        if (original_size && compressed_size && reduction_percent) {
            const infoContainer = document.getElementById('compress-info');
            const originalSizeElement = document.getElementById('original-size');
            const compressedSizeElement = document.getElementById('compressed-size');
            const reductionElement = document.getElementById('size-reduction');
            
            if (infoContainer && originalSizeElement && compressedSizeElement && reductionElement) {
                originalSizeElement.textContent = original_size;
                compressedSizeElement.textContent = compressed_size;
                reductionElement.textContent = reduction_percent;
                infoContainer.classList.remove('hidden');
            }
        }
        
        // Show text preview if provided
        if (preview_text) {
            const previewContainer = document.getElementById(`${tool}-preview`);
            const previewContent = document.getElementById(`${tool}-content`);
            
            if (previewContainer && previewContent) {
                previewContent.textContent = preview_text;
                previewContainer.classList.remove('hidden');
            }
        }
        
        // Show downloads if provided
        if (downloads && status === 'success') {
            const resultsContainer = document.getElementById(`${tool}-results`);
            if (resultsContainer) {
                // Get a random success message
                const successMessages = [
                    "Your PDF is Ready! 🎉",
                    "Mission Accomplished! 🚀",
                    "PDF Magic Complete! ✨",
                    "Success! Your PDF is Ready! 🌟",
                    "PDF Transformation Complete! 🔄"
                ];
                
                const randomSuccessMessage = successMessages[Math.floor(Math.random() * successMessages.length)];
                
                // Get a random completion message
                const completionMessages = [
                    "Tom & Jerry have finished processing your files!",
                    "Your documents have been expertly processed!",
                    "Your PDF has been transformed with care!",
                    "All done! Your document is ready to download.",
                    "Processing complete with flying colors!"
                ];
                
                const randomCompletionMessage = completionMessages[Math.floor(Math.random() * completionMessages.length)];
                
                resultsContainer.innerHTML = `
                    <div class="download-options">
                        <h3>${randomSuccessMessage}</h3>
                        <p style="text-align: center; margin-bottom: 20px;">${randomCompletionMessage}</p>
                        ${downloads.map(download => `
                            <div class="download-item">
                                <a href="${download.url}" class="download-button" download>
                                    <i class="fas fa-download"></i> ${download.label || 'Download Your PDF'}
                                </a>
                                <button class="email-button" data-filename="${download.filename}" title="Email this file">
                                    <i class="fas fa-envelope"></i>
                                </button>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                // Show the results container without animation
                resultsContainer.classList.remove('hidden');
                
                // Add event listeners to email buttons
                const emailButtons = resultsContainer.querySelectorAll('.email-button');
                emailButtons.forEach(button => {
                    button.addEventListener('click', () => {
                        const filename = button.getAttribute('data-filename');
                        showEmailModal(filename);
                    });
                });
            }
        }
        
        // Show notification based on status
        if (status === 'success') {
            showNotification(message, 'success');
        } else if (status === 'error') {
            showNotification(message, 'error');
        }
    });

    // Email Status Updates
    socket.on('email_status', (data) => {
        const { status, message } = data;
        
        // Update email sending status
        const sendingStatus = document.getElementById('sending-status');
        if (sendingStatus) {
            sendingStatus.textContent = message;
            sendingStatus.className = 'sending-status';
            sendingStatus.classList.add(status);
        }
        
        // Show notification
        showNotification(message, status);
        
        // Close modal on success after delay
        if (status === 'success') {
            setTimeout(() => {
                const modalOverlay = document.querySelector('.modal-overlay');
                if (modalOverlay) {
                    document.body.removeChild(modalOverlay);
                }
            }, 2000);
        }
    });
}

// DOM Ready Event
document.addEventListener('DOMContentLoaded', () => {
    // Connect to Socket.IO
    connectSocket();
    
    // Initialize Theme
    initTheme();
    
    // Initialize background music
    initBackgroundMusic();
    
    // Initialize Tool Navigation
    initToolNavigation();
    
    // Initialize File Uploads
    initFileUploads();
    
    // Initialize Forms
    initForms();
    
    // Initialize Form Controls
    initFormControls();
});

// Initialize Theme
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    // Set theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update icon
    const icon = themeToggle.querySelector('i');
    if (savedTheme === 'dark') {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
    
    // Theme Toggle Event
    themeToggle.addEventListener('click', () => {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update icon
        const icon = themeToggle.querySelector('i');
        if (newTheme === 'dark') {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        } else {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        }
    });
}

// Initialize Background Music
function initBackgroundMusic() {
    const musicToggle = document.getElementById('music-toggle');
    const backgroundMusic = document.getElementById('background-music');
    
    if (!musicToggle || !backgroundMusic) return;
    
    // Set initial volume
    backgroundMusic.volume = 0.3;
    
    // Check for saved music preference
    const musicEnabled = localStorage.getItem('musicEnabled') === 'true';
    
    if (musicEnabled) {
        musicToggle.classList.add('active');
        // Try to play music (may be blocked by browser autoplay policy)
        const playPromise = backgroundMusic.play();
        
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.log('Autoplay prevented by browser policy:', error);
            });
        }
    }
    
    // Add event listener to music toggle
    musicToggle.addEventListener('click', () => {
        if (backgroundMusic.paused) {
            // Play music
            backgroundMusic.play()
                .then(() => {
                    musicToggle.classList.add('active');
                    localStorage.setItem('musicEnabled', 'true');
                })
                .catch(error => {
                    console.error('Error playing background music:', error);
                    showNotification('Please interact with the page first to enable music', 'info');
                });
        } else {
            // Pause music
            backgroundMusic.pause();
            musicToggle.classList.remove('active');
            localStorage.setItem('musicEnabled', 'false');
        }
    });
}

// Initialize Tool Navigation
function initToolNavigation() {
    const toolSearch = document.getElementById('tool-search');
    const categoryLinks = document.querySelectorAll('.nav-link');
    const toolCards = document.querySelectorAll('.tool-card');
    
    if (!toolSearch || !categoryLinks.length || !toolCards.length) return;
    
    // Tool Search
    toolSearch.addEventListener('input', () => {
        const searchTerm = toolSearch.value.toLowerCase();
        
        toolCards.forEach(card => {
            const title = card.querySelector('h2').textContent.toLowerCase();
            const description = card.querySelector('.tool-description').textContent.toLowerCase();
            
            if (title.includes(searchTerm) || description.includes(searchTerm)) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    });
    
    // Category Navigation
    categoryLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links
            categoryLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            link.classList.add('active');
            
            // Get category
            const category = link.getAttribute('data-category');
            
            // Show/hide cards based on category
            toolCards.forEach(card => {
                if (category === 'all' || card.getAttribute('data-category') === category) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
}

// Initialize File Uploads
function initFileUploads() {
    const fileInputs = document.querySelectorAll('.file-upload-input');
    
    if (!fileInputs.length) return;
    
    fileInputs.forEach(input => {
        const label = input.previousElementSibling;
        const formId = input.closest('form').id;
        const selectedFiles = document.getElementById(`${formId.split('-')[0]}-selected-files`);
        
        if (!label || !selectedFiles) return;
        
        // Handle file selection
        input.addEventListener('change', () => {
            if (input.files.length > 0) {
                // Always just show the count of files selected
                selectedFiles.textContent = `${input.files.length} file${input.files.length > 1 ? 's' : ''} selected`;
                // Add title attribute to show all filenames on hover
                const fileNames = Array.from(input.files).map(file => file.name);
                selectedFiles.title = fileNames.join('\n');
                
                // Make sure form-actions is visible
                const form = input.closest('form');
                if (form) {
                    const formActions = form.querySelector('.form-actions');
                    if (formActions) {
                        formActions.style.display = 'flex';
                    }
                }
                
                // We're not showing the file order list anymore as per user request
            } else {
                selectedFiles.textContent = 'No files selected';
            }
        });
        
        // Handle drag and drop
        label.addEventListener('dragover', (e) => {
            e.preventDefault();
            label.classList.add('highlight');
        });
        
        label.addEventListener('dragleave', () => {
            label.classList.remove('highlight');
        });
        
        label.addEventListener('drop', (e) => {
            e.preventDefault();
            label.classList.remove('highlight');
            
            if (e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                
                // Trigger change event
                const event = new Event('change');
                input.dispatchEvent(event);
            }
        });
    });
}

// Initialize Forms
function initForms() {
    const forms = document.querySelectorAll('.ajax-form');
    
    if (!forms.length) return;
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get form ID
            const formId = form.id;
            const tool = formId.split('-')[0];
            
            // Show progress container
            const progressContainer = document.getElementById(`${tool}-progress-container`);
            if (progressContainer) {
                progressContainer.classList.remove('hidden');
            }
            
            // Update status
            const statusElement = document.getElementById(`${tool}-status`);
            if (statusElement) {
                statusElement.textContent = 'Processing...';
            }
            
            // Hide results container
            const resultsContainer = document.getElementById(`${tool}-results`);
            if (resultsContainer) {
                resultsContainer.classList.add('hidden');
            }
            
            // Hide preview container if exists
            const previewContainer = document.getElementById(`${tool}-preview`);
            if (previewContainer) {
                previewContainer.classList.add('hidden');
            }
            
            // Hide info container if exists
            const infoContainer = document.getElementById(`${tool}-info`);
            if (infoContainer) {
                infoContainer.classList.add('hidden');
            }
            
            // Reset and show status log container
            const statusLogContainer = document.getElementById(`${tool}-status-log`);
            if (statusLogContainer) {
                // Clear status cards
                const statusCards = document.getElementById(`${tool}-status-cards`);
                if (statusCards) {
                    statusCards.innerHTML = '';
                }
                
                // Reset timeline progress
                const timelineProgress = document.getElementById(`${tool}-timeline-progress`);
                if (timelineProgress) {
                    timelineProgress.style.width = '0%';
                }
                
                // Reset timeline markers
                const timelineMarkers = statusLogContainer.querySelectorAll('.timeline-marker');
                timelineMarkers.forEach(marker => {
                    const dot = marker.querySelector('.marker-dot');
                    if (dot) {
                        if (marker.getAttribute('data-stage') === 'start') {
                            dot.classList.add('active');
                            marker.classList.add('active');
                        } else {
                            dot.classList.remove('active');
                            marker.classList.remove('active');
                        }
                    }
                });
                
                // Reset timer
                const timerElement = document.getElementById(`${tool}-timer`);
                if (timerElement) {
                    timerElement.textContent = '00:00';
                }
                
                // Reset start time
                window[`${tool}StartTime`] = null;
                
                // Clear any existing timer interval
                if (window[`${tool}TimerInterval`]) {
                    clearInterval(window[`${tool}TimerInterval`]);
                    window[`${tool}TimerInterval`] = null;
                }
                
                // Reset spinner icon
                const spinnerIcon = statusLogContainer.querySelector('.status-title i');
                if (spinnerIcon) {
                    spinnerIcon.className = 'fas fa-sync-alt fa-spin';
                }
                
                // Show the container
                statusLogContainer.classList.remove('hidden');
                
                // Add initial status card
                const timestamp = new Date().toLocaleTimeString();
                const initialCard = document.createElement('div');
                initialCard.className = 'status-card info';
                initialCard.innerHTML = `
                    <div class="status-card-icon">
                        <i class="fas fa-play-circle"></i>
                    </div>
                    <div class="status-card-content">
                        <div class="status-card-title">Process Started</div>
                        <div class="status-card-message">Starting ${tool} process...</div>
                        <div class="status-card-time">${timestamp}</div>
                    </div>
                `;
                statusCards.appendChild(initialCard);
            }
            
            // Submit form with AJAX
            const formData = new FormData(form);
            
            fetch(form.action, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                // Check if the response is valid JSON
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned non-JSON response');
                }
                
                return response.json();
            })
            .then(data => {
                if (data.status === 'error') {
                    showNotification(data.message, 'error');
                    
                    // Update status
                    if (statusElement) {
                        statusElement.textContent = data.message;
                    }
                    
                    // Hide progress container
                    if (progressContainer) {
                        progressContainer.classList.add('hidden');
                    }
                }
            })
            .catch(error => {
                showNotification('Error submitting form: ' + error.message, 'error');
                
                // Update status
                if (statusElement) {
                    statusElement.textContent = 'Error: ' + error.message;
                }
                
                // Hide progress container
                if (progressContainer) {
                    progressContainer.classList.add('hidden');
                }
            });
        });
    });
}

// Initialize Form Controls
function initFormControls() {
    // Split PDF Form Handling
    const splitMethodRadios = document.querySelectorAll('input[name="split_method"]');
    const pageRangeGroup = document.getElementById('page-range-group');
    const oddEvenGroup = document.getElementById('odd-even-group');
    
    if (splitMethodRadios.length && pageRangeGroup && oddEvenGroup) {
        splitMethodRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.value === 'range') {
                    pageRangeGroup.classList.remove('hidden');
                    oddEvenGroup.classList.add('hidden');
                } else if (radio.value === 'odd_even') {
                    pageRangeGroup.classList.add('hidden');
                    oddEvenGroup.classList.remove('hidden');
                } else {
                    pageRangeGroup.classList.add('hidden');
                    oddEvenGroup.classList.add('hidden');
                }
            });
        });
    }
    
    // Rotate PDF Form Handling
    const rotatePageRadios = document.querySelectorAll('input[name="pages"]');
    const rotateRangeGroup = document.getElementById('rotate-range-group');
    
    if (rotatePageRadios.length && rotateRangeGroup) {
        rotatePageRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.value === 'custom') {
                    rotateRangeGroup.classList.remove('hidden');
                } else {
                    rotateRangeGroup.classList.add('hidden');
                }
            });
        });
    }
    
    // Watermark Form Handling
    const watermarkTypeRadios = document.querySelectorAll('input[name="watermark_type"]');
    const textWatermarkGroup = document.getElementById('text-watermark-group');
    const imageWatermarkGroup = document.getElementById('image-watermark-group');
    
    if (watermarkTypeRadios.length && textWatermarkGroup && imageWatermarkGroup) {
        watermarkTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.value === 'text') {
                    textWatermarkGroup.classList.remove('hidden');
                    imageWatermarkGroup.classList.add('hidden');
                } else {
                    textWatermarkGroup.classList.add('hidden');
                    imageWatermarkGroup.classList.remove('hidden');
                }
            });
        });
    }
    
    // Opacity Range Handling
    const opacityRange = document.getElementById('opacity');
    const opacityValue = document.getElementById('opacity-value');
    
    if (opacityRange && opacityValue) {
        opacityRange.addEventListener('input', () => {
            opacityValue.textContent = opacityRange.value + '%';
        });
    }
    
    // Password Toggle Handling
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    if (passwordToggles.length) {
        passwordToggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const input = toggle.previousElementSibling;
                const icon = toggle.querySelector('i');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
        });
    }
}

// Drag and Drop for File Order
function initDragAndDrop(list, orderInput) {
    let draggedItem = null;
    
    // Add event listeners to list items
    const items = list.querySelectorAll('.file-order-item');
    
    items.forEach(item => {
        // Drag start
        item.addEventListener('dragstart', () => {
            draggedItem = item;
            setTimeout(() => {
                item.classList.add('dragging');
            }, 0);
        });
        
        // Drag end
        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
            draggedItem = null;
            
            // Update order input
            updateOrderInput(list, orderInput);
        });
        
        // Make items draggable
        item.setAttribute('draggable', 'true');
    });
    
    // Add event listeners to list
    list.addEventListener('dragover', (e) => {
        e.preventDefault();
        
        if (!draggedItem) return;
        
        // Get item below cursor
        const afterElement = getDragAfterElement(list, e.clientY);
        
        if (afterElement === null) {
            list.appendChild(draggedItem);
        } else {
            list.insertBefore(draggedItem, afterElement);
        }
    });
    
    // Update order input initially
    updateOrderInput(list, orderInput);
}

// Get element below cursor
function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.file-order-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// Update order input
function updateOrderInput(list, orderInput) {
    const items = list.querySelectorAll('.file-order-item');
    const order = Array.from(items).map(item => item.getAttribute('data-index'));
    
    if (orderInput) {
        orderInput.value = order.join(',');
    }
}

// Show Email Modal
function showEmailModal(filename) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>Send File by Email</h3>
                <button class="close-button">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="email">Email Address:</label>
                    <input type="email" id="email" required>
                </div>
                <div class="form-group">
                    <label for="subject">Subject:</label>
                    <input type="text" id="subject" value="Your PDF file from PDF Toolkit">
                </div>
                <div class="form-group">
                    <label for="message">Message:</label>
                    <textarea id="message" rows="4">Here is the PDF file you requested.</textarea>
                </div>
                <div id="sending-status" class="sending-status"></div>
            </div>
            <div class="modal-footer">
                <button class="cancel-button">Cancel</button>
                <button class="send-button">Send Email</button>
            </div>
        </div>
    `;
    
    // Add modal to body
    document.body.appendChild(modal);
    
    // Add event listeners
    const closeButton = modal.querySelector('.close-button');
    const cancelButton = modal.querySelector('.cancel-button');
    const sendButton = modal.querySelector('.send-button');
    
    closeButton.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    cancelButton.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    sendButton.addEventListener('click', () => {
        const email = modal.querySelector('#email').value;
        const subject = modal.querySelector('#subject').value;
        const message = modal.querySelector('#message').value;
        
        if (!email) {
            showNotification('Email address is required', 'error');
            return;
        }
        
        // Update sending status
        const sendingStatus = modal.querySelector('#sending-status');
        sendingStatus.textContent = 'Sending email...';
        sendingStatus.className = 'sending-status';
        
        // Disable send button
        sendButton.disabled = true;
        
        // Send email
        fetch('/send_email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename,
                email,
                subject,
                message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'error') {
                sendingStatus.textContent = data.message;
                sendingStatus.className = 'sending-status error';
                sendButton.disabled = false;
            }
        })
        .catch(error => {
            sendingStatus.textContent = 'Error sending email: ' + error.message;
            sendingStatus.className = 'sending-status error';
            sendButton.disabled = false;
        });
    });
}

// Play notification sound
function playNotificationSound(type) {
    let sound;
    switch (type) {
        case 'success':
            sound = document.getElementById('success-sound');
            break;
        case 'error':
            sound = document.getElementById('error-sound');
            break;
        case 'notification':
        case 'info':
            sound = document.getElementById('notification-sound');
            break;
        default:
            return;
    }
    
    if (sound) {
        // Reset the sound to the beginning
        sound.currentTime = 0;
        
        // Play the sound
        sound.play().catch(error => {
            console.error('Error playing notification sound:', error);
        });
    }
}

// Show Notification
function showNotification(message, type = 'info') {
    // Play notification sound
    playNotificationSound(type);
    
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) return;
    
    // Clear any existing notifications
    notificationContainer.innerHTML = '';
    
    // Get appropriate icon based on type
    let icon = 'fas fa-info-circle';
    if (type === 'success') {
        icon = 'fas fa-check-circle';
    } else if (type === 'error') {
        icon = 'fas fa-exclamation-circle';
    } else if (type === 'warning') {
        icon = 'fas fa-exclamation-triangle';
    } else if (type === 'processing') {
        icon = 'fas fa-cog fa-spin';
        type = 'processing'; // Set a specific class for processing
    }
    
    // Create fun emoji/character messages based on type
    let funMessage = '';
    if (type === 'processing') {
        const processingMessages = [
            "Tom & Jerry are working on it! 🐱🐭",
            "Our cartoon friends are processing your PDFs! 📄",
            "The PDF battle is underway! 💪",
            "Cartoon magic happening! ✨"
        ];
        funMessage = processingMessages[Math.floor(Math.random() * processingMessages.length)];
    } else if (type === 'success') {
        const successMessages = [
            "Victory! Your PDF is ready! 🏆",
            "Tom & Jerry finished the job! 🐱🐭",
            "Mission accomplished! 🎉",
            "PDF magic complete! ✨"
        ];
        funMessage = successMessages[Math.floor(Math.random() * successMessages.length)];
    } else if (type === 'error') {
        const errorMessages = [
            "Oops! Even Tom & Jerry make mistakes! 🐱🐭",
            "Our cartoon friends need another try! 🔄",
            "PDF battle lost this time! 😅",
            "Time for cartoon plan B! 🚨"
        ];
        funMessage = errorMessages[Math.floor(Math.random() * errorMessages.length)];
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="margin-top: 20px;"><i class="${icon}" style="font-size: 2.5rem; margin-bottom: 0.8rem;"></i></div>
        <div style="font-weight: 600; font-size: 1.2rem;">${funMessage}</div>
        <div style="margin: 10px 0;">${message}</div>
        <div class="notification-progress">
            <div class="notification-progress-bar"></div>
        </div>
    `;
    
    notificationContainer.appendChild(notification);
    
    // No animation for notifications
    
    // Remove notification after delay
    setTimeout(() => {
        notification.style.opacity = '0';
        
        setTimeout(() => {
            if (notification.parentNode === notificationContainer) {
                notificationContainer.removeChild(notification);
            }
        }, 400);
    }, 4000);
}