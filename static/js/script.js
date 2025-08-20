let currentFile = null;
        
        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        
        // Drag and drop functionality
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });
        
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
        
        // Handle file upload
        function handleFileUpload(file) {
            const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            
            if (!allowedTypes.includes(file.type)) {
                showAlert('error', 'Only PDF and DOCX files are supported!');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            showAlert('info', 'Uploading and processing file...');
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentFile = data.filename;
                    document.getElementById('fileName').textContent = currentFile;
                    document.getElementById('currentFile').style.display = 'block';
                    chatInput.disabled = false; // Enable chat even without file
                    sendBtn.disabled = false;
                    chatInput.placeholder = 'Chat with AI or upload a document...';
                    showAlert('success', data.message);
                    
                    // Hide upload area
                    uploadArea.style.display = 'none';
                    
                    // Clear welcome message
                    const welcomeMsg = document.querySelector('.welcome-message');
                    if (welcomeMsg) {
                        welcomeMsg.style.display = 'none';
                    }
                } else {
                    showAlert('error', data.message);
                }
            })
            .catch(error => {
                showAlert('error', 'Error uploading file: ' + error.message);
            });
        }
        
        // Send message
        function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            chatInput.value = '';
            
            // Show loading
            showLoading();
            
            // Send to backend
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    addMessage(data.response, 'bot');
                    loadConversations(); // Refresh conversations list
                } else {
                    showAlert('error', data.message);
                }
            })
            .catch(error => {
                hideLoading();
                showAlert('error', 'Error sending message: ' + error.message);
            });
        }
        
        // Add message to chat
        function addMessage(content, type) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            
            const now = new Date();
            const timestamp = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
            
            messageDiv.innerHTML = `
                <div class="message-avatar ${type}-avatar">
                    ${type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>'}
                </div>
                <div class="message-content">
                    ${content.replace(/\n/g, '<br>')}
                    <div class="timestamp">${timestamp}</div>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Show loading animation
        function showLoading() {
            const chatMessages = document.getElementById('chatMessages');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.id = 'loadingIndicator';
            loadingDiv.innerHTML = '<div class="spinner"></div><span class="ms-2">Thinking...</span>';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Hide loading animation
        function hideLoading() {
            const loadingIndicator = document.getElementById('loadingIndicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        }
        
        // Show alert
        function showAlert(type, message) {
            const alertContainer = document.getElementById('alertContainer');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            alertContainer.appendChild(alertDiv);
            
            // Auto dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
        
        // Load conversations list
        function loadConversations() {
            fetch('/conversations')
            .then(response => response.json())
            .then(data => {
                const historyContainer = document.getElementById('chatHistory');
                historyContainer.innerHTML = '';
                
                data.conversations.forEach((conversation) => {
                    const historyItem = document.createElement('button');
                    historyItem.className = 'history-item';
                    historyItem.setAttribute('data-conversation-id', conversation.id);
                    
                    if (conversation.id === data.current_conversation_id) {
                        historyItem.classList.add('active');
                    }
                    
                    historyItem.innerHTML = `
                        <div style="font-weight: 500; display: flex; align-items: center;">
                            ${conversation.document_file ? '<i class="fas fa-file-alt me-2"></i>' : '<i class="fas fa-comment me-2"></i>'}
                            ${conversation.title}
                        </div>
                        <div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">
                            ${new Date(conversation.created_at).toLocaleDateString('vi-VN')} • ${conversation.message_count} tin nhắn
                        </div>
                        <button class="delete-conversation" onclick="deleteConversation(event, '${conversation.id}')" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: #9ca3af; font-size: 12px; opacity: 0; transition: opacity 0.2s;">
                            <i class="fas fa-trash"></i>
                        </button>
                    `;
                    
                    // Add click handler for switching conversation
                    historyItem.addEventListener('click', () => switchConversation(conversation.id));
                    
                    // Show delete button on hover
                    historyItem.addEventListener('mouseenter', () => {
                        const deleteBtn = historyItem.querySelector('.delete-conversation');
                        if (deleteBtn) deleteBtn.style.opacity = '1';
                    });
                    
                    historyItem.addEventListener('mouseleave', () => {
                        const deleteBtn = historyItem.querySelector('.delete-conversation');
                        if (deleteBtn) deleteBtn.style.opacity = '0';
                    });
                    
                    historyContainer.appendChild(historyItem);
                });
            });
        }
        
        // Switch to a conversation
        function switchConversation(conversationId) {
            fetch(`/conversation/${conversationId}/switch`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear current messages
                    const chatMessages = document.getElementById('chatMessages');
                    chatMessages.innerHTML = '';
                    
                    // Load messages from this conversation
                    data.messages.forEach(message => {
                        addMessage(message.message, 'user');
                        addMessage(message.response, 'bot');
                    });
                    
                    // Update UI based on document
                    if (data.document_file) {
                        currentFile = data.document_file;
                        document.getElementById('fileName').textContent = currentFile;
                        document.getElementById('currentFile').style.display = 'block';
                        document.getElementById('uploadArea').style.display = 'none';
                        chatInput.disabled = false;
                        sendBtn.disabled = false;
                        chatInput.placeholder = 'Ask a question about your document...';
                        
                        // Hide welcome message
                        const welcomeMsg = document.querySelector('.welcome-message');
                        if (welcomeMsg) welcomeMsg.style.display = 'none';
                    } else {
                        // No document in this conversation
                        currentFile = null;
                        document.getElementById('currentFile').style.display = 'none';
                        document.getElementById('uploadArea').style.display = 'block';
                        chatInput.disabled = false;
                        sendBtn.disabled = false;
                        chatInput.placeholder = 'Chat with AI or upload a document...';
                        
                        // Show welcome message if no messages
                        if (data.messages.length === 0) {
                            const welcomeMsg = document.querySelector('.welcome-message');
                            if (!welcomeMsg) {
                                chatMessages.innerHTML = `
                                    <div class="welcome-message">
                                        <h3>Welcome to AI Document Assistant</h3>
                                        <p>Upload a PDF or DOCX document to start chatting about its contents, or just chat normally.</p>
                                    </div>
                                `;
                            } else {
                                welcomeMsg.style.display = 'block';
                            }
                        }
                    }
                    
                    // Update sidebar to show active conversation
                    loadConversations();
                }
            });
        }
        
        // Delete conversation
        function deleteConversation(event, conversationId) {
            event.stopPropagation(); // Prevent switching to conversation
            
            if (confirm('Are you sure you want to delete this conversation?')) {
                fetch(`/conversation/${conversationId}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadConversations();
                        
                        // If deleted current conversation, reload page
                        const currentActive = document.querySelector('.history-item.active');
                        if (currentActive && currentActive.getAttribute('data-conversation-id') === conversationId) {
                            location.reload();
                        }
                    }
                });
            }
        }
        
        // Load current conversation messages
        function loadCurrentMessages() {
            fetch('/current_messages')
            .then(response => response.json())
            .then(data => {
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.innerHTML = '';
                
                if (data.messages.length === 0) {
                    chatMessages.innerHTML = `
                        <div class="welcome-message">
                            <h3>Welcome to AI Document Assistant</h3>
                            <p>Upload a PDF or DOCX document to start chatting about its contents, or just chat normally.</p>
                        </div>
                    `;
                } else {
                    data.messages.forEach(message => {
                        addMessage(message.message, 'user');
                        addMessage(message.response, 'bot');
                    });
                }
            });
        }
        
        // Start new chat
        function startNewChat() {
            fetch('/new_chat', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear current chat
                    document.getElementById('chatMessages').innerHTML = `
                        <div class="welcome-message">
                            <h3>Welcome to AI Document Assistant</h3>
                            <p>Upload a PDF or DOCX document to start chatting about its contents, or just chat normally.</p>
                        </div>
                    `;
                    
                    // Reset file upload UI
                    currentFile = null;
                    document.getElementById('currentFile').style.display = 'none';
                    document.getElementById('uploadArea').style.display = 'block';
                    chatInput.disabled = false; // Enable chat even without document
                    sendBtn.disabled = false;
                    chatInput.placeholder = 'Chat with AI or upload a document...';
                    
                    // Clear alerts
                    document.getElementById('alertContainer').innerHTML = '';
                    
                    // Reload conversations list
                    loadConversations();
                }
            });
        }
        
        // Clear all conversations (for testing)
        function clearAllHistory() {
            if (confirm('Are you sure you want to delete ALL conversations? This cannot be undone.')) {
                // You can implement this endpoint if needed
                showAlert('info', 'This feature is not implemented yet.');
            }
        }
        
        // Toggle sidebar (mobile)
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('show');
        }
        
        // Enter key to send message
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Auto-resize textarea
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Load conversations and current messages on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadConversations();
            loadCurrentMessages();
            
            // Check document status
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.has_document && data.current_file) {
                    currentFile = data.current_file;
                    document.getElementById('fileName').textContent = currentFile;
                    document.getElementById('currentFile').style.display = 'block';
                    document.getElementById('uploadArea').style.display = 'none';
                    chatInput.placeholder = 'Ask a question about your document...';
                }
            });
        });