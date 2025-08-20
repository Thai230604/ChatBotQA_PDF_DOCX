from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import json

# Import your existing modules
from creat_vector import setup_vector_store, get_current_file, clear_vector_store
from chat import get_chat_response

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
CHAT_HISTORY_FILE = 'chat_histories.json'

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Chat histories structure:
# {
#   "user_sessions": {
#     "user_id": {
#       "conversations": {
#         "conversation_id": {
#           "title": "Generated title from first message",
#           "created_at": "timestamp",
#           "messages": [
#             {
#               "timestamp": "HH:MM",
#               "message": "user message",
#               "response": "bot response",
#               "has_document": true/false
#             }
#           ],
#           "document_file": "filename.pdf" or null
#         }
#       },
#       "current_conversation": "conversation_id"
#     }
#   }
# }

def load_chat_histories():
    """Load chat histories from file"""
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"user_sessions": {}}

def save_chat_histories(histories):
    """Save chat histories to file"""
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(histories, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving chat histories: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_id():
    """Get or create user ID"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def get_current_conversation_id():
    """Get current conversation ID"""
    return session.get('current_conversation_id')

def set_current_conversation_id(conversation_id):
    """Set current conversation ID"""
    session['current_conversation_id'] = conversation_id

def create_new_conversation(user_id):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    histories = load_chat_histories()
    
    if user_id not in histories["user_sessions"]:
        histories["user_sessions"][user_id] = {
            "conversations": {},
            "current_conversation": conversation_id
        }
    
    histories["user_sessions"][user_id]["conversations"][conversation_id] = {
        "title": "New Chat",
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "document_file": None
    }
    
    histories["user_sessions"][user_id]["current_conversation"] = conversation_id
    save_chat_histories(histories)
    set_current_conversation_id(conversation_id)
    
    return conversation_id

def get_or_create_conversation():
    """Get current conversation or create new one"""
    user_id = get_user_id()
    conversation_id = get_current_conversation_id()
    histories = load_chat_histories()
    
    # Check if user exists and has current conversation
    if (user_id in histories["user_sessions"] and 
        conversation_id and 
        conversation_id in histories["user_sessions"][user_id]["conversations"]):
        return conversation_id
    else:
        # Create new conversation
        return create_new_conversation(user_id)

def generate_title_from_message(message):
    """Generate conversation title from first message"""
    # Simple title generation - take first 30 chars
    title = message.strip()
    if len(title) > 30:
        title = title[:30] + "..."
    return title

def add_message_to_conversation(message, response, has_document=False):
    """Add message to current conversation"""
    user_id = get_user_id()
    conversation_id = get_or_create_conversation()
    histories = load_chat_histories()
    
    if user_id in histories["user_sessions"] and conversation_id in histories["user_sessions"][user_id]["conversations"]:
        conversation = histories["user_sessions"][user_id]["conversations"][conversation_id]
        
        # If this is the first message, update title
        if not conversation["messages"]:
            conversation["title"] = generate_title_from_message(message)
        
        # Add message
        conversation["messages"].append({
            "timestamp": datetime.now().strftime('%H:%M'),
            "message": message,
            "response": response,
            "has_document": has_document
        })
        
        # Update document file if has document
        if has_document:
            conversation["document_file"] = get_current_file()
        
        save_chat_histories(histories)

def get_conversation_messages(conversation_id=None):
    """Get messages from specific conversation or current one"""
    user_id = get_user_id()
    if not conversation_id:
        conversation_id = get_current_conversation_id()
    
    histories = load_chat_histories()
    
    if (user_id in histories["user_sessions"] and 
        conversation_id and 
        conversation_id in histories["user_sessions"][user_id]["conversations"]):
        return histories["user_sessions"][user_id]["conversations"][conversation_id]["messages"]
    
    return []

def get_user_conversations():
    """Get all conversations for current user"""
    user_id = get_user_id()
    histories = load_chat_histories()
    
    if user_id in histories["user_sessions"]:
        conversations = histories["user_sessions"][user_id]["conversations"]
        # Sort by created_at desc
        sorted_conversations = sorted(
            conversations.items(), 
            key=lambda x: x[1]["created_at"], 
            reverse=True
        )
        return [
            {
                "id": conv_id,
                "title": conv_data["title"],
                "created_at": conv_data["created_at"],
                "message_count": len(conv_data["messages"]),
                "document_file": conv_data.get("document_file")
            }
            for conv_id, conv_data in sorted_conversations
        ]
    
    return []

@app.route('/')
def index():
    # Ensure user has a current conversation
    get_or_create_conversation()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Không có file được chọn'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Không có file được chọn'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Setup vector store using your existing function
        if setup_vector_store(file_path):
            # Update current conversation with document info
            user_id = get_user_id()
            conversation_id = get_current_conversation_id()
            histories = load_chat_histories()
            
            if (user_id in histories["user_sessions"] and 
                conversation_id in histories["user_sessions"][user_id]["conversations"]):
                histories["user_sessions"][user_id]["conversations"][conversation_id]["document_file"] = filename
                save_chat_histories(histories)
            
            return jsonify({
                'success': True, 
                'message': f'File {filename} đã được tải lên và xử lý thành công!',
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'message': 'Lỗi khi xử lý file'})
    else:
        return jsonify({'success': False, 'message': 'Chỉ hỗ trợ file PDF và DOCX'})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    question = data.get('message', '')
    
    if not question.strip():
        return jsonify({'success': False, 'message': 'Vui lòng nhập câu hỏi'})
    
    try:
        # Use your existing chat function
        result = get_chat_response(question)
        
        if result['success']:
            # Add to current conversation
            add_message_to_conversation(
                question, 
                result['response'], 
                result['has_document']
            )
            
            return jsonify({
                'success': True, 
                'response': result['response'],
                'has_document': result['has_document'],
                'current_file': result['current_file']
            })
        else:
            return jsonify({'success': False, 'message': result['response']})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/conversations')
def get_conversations():
    """Get all conversations for sidebar"""
    conversations = get_user_conversations()
    current_conversation_id = get_current_conversation_id()
    
    return jsonify({
        'conversations': conversations,
        'current_conversation_id': current_conversation_id
    })

@app.route('/conversation/<conversation_id>')
def get_conversation(conversation_id):
    """Get specific conversation messages"""
    messages = get_conversation_messages(conversation_id)
    return jsonify({'messages': messages})

@app.route('/conversation/<conversation_id>/switch', methods=['POST'])
def switch_conversation(conversation_id):
    """Switch to a different conversation"""
    user_id = get_user_id()
    histories = load_chat_histories()
    
    # Verify conversation exists
    if (user_id in histories["user_sessions"] and 
        conversation_id in histories["user_sessions"][user_id]["conversations"]):
        
        set_current_conversation_id(conversation_id)
        
        # Update current conversation in storage
        histories["user_sessions"][user_id]["current_conversation"] = conversation_id
        save_chat_histories(histories)
        
        # Load document if conversation has one
        conversation = histories["user_sessions"][user_id]["conversations"][conversation_id]
        document_file = conversation.get("document_file")
        
        if document_file and os.path.exists(os.path.join(UPLOAD_FOLDER, document_file)):
            setup_vector_store(os.path.join(UPLOAD_FOLDER, document_file))
        else:
            clear_vector_store()
        
        return jsonify({
            'success': True,
            'messages': conversation["messages"],
            'document_file': document_file
        })
    else:
        return jsonify({'success': False, 'message': 'Conversation not found'})

@app.route('/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    user_id = get_user_id()
    histories = load_chat_histories()
    
    if (user_id in histories["user_sessions"] and 
        conversation_id in histories["user_sessions"][user_id]["conversations"]):
        
        # Delete conversation
        del histories["user_sessions"][user_id]["conversations"][conversation_id]
        
        # If this was current conversation, create new one
        if histories["user_sessions"][user_id]["current_conversation"] == conversation_id:
            new_conversation_id = create_new_conversation(user_id)
            clear_vector_store()  # Clear any loaded documents
        
        save_chat_histories(histories)
        
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Conversation not found'})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    """Create a new conversation"""
    user_id = get_user_id()
    new_conversation_id = create_new_conversation(user_id)
    
    # Clear vector store
    clear_vector_store()
    
    return jsonify({
        'success': True,
        'conversation_id': new_conversation_id
    })

@app.route('/current_messages')
def get_current_messages():
    """Get messages from current conversation"""
    messages = get_conversation_messages()
    return jsonify({'messages': messages})

@app.route('/status')
def get_status():
    """Get current status - if document is loaded"""
    current_file = get_current_file()
    return jsonify({
        'has_document': current_file is not None,
        'current_file': current_file
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)