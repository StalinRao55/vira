# VIRA AI - Advanced Chatbot System

A comprehensive AI chatbot system built with FastAPI, React, and OpenAI's GPT-4o-mini. Features include RAG (Retrieval-Augmented Generation), agent automation, voice processing, and document AI.

## 🚀 Features

### Core AI Capabilities
- **Conversational AI**: Natural language processing with GPT-4o-mini
- **Memory System**: Context-aware conversations with short and long-term memory
- **Multi-modal Input**: Support for text, voice, and document inputs

### Advanced Systems
- **RAG System**: Document upload and context-aware responses using Sentence Transformers
- **Agent System**: Automated task execution (web search, file operations, system commands)
- **Voice Processing**: Text-to-speech with pyttsx3 integration
- **Document AI**: Process PDF, DOCX, and HTML files

### Professional UI
- **React Frontend**: Modern, responsive interface with Tailwind CSS
- **Real-time Chat**: Streaming responses with typing indicators
- **Sidebar Controls**: System status, document management, and agent tasks
- **Markdown Support**: Rich text formatting with syntax highlighting

### Infrastructure
- **FastAPI Backend**: High-performance API with automatic documentation
- **MongoDB Integration**: User sessions and interaction logging
- **CORS Support**: Cross-origin resource sharing for frontend-backend communication
- **Error Handling**: Comprehensive error handling and logging

## 📋 System Requirements

### Backend Requirements
- Python 3.8+
- OpenAI API key
- MongoDB (optional, system works without it)

### Frontend Requirements
- Modern browser with JavaScript support
- No additional dependencies required

## 🛠️ Installation

### 1. Clone and Setup
```bash
git clone <repository-url>
cd vira-ai
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment
echo "OPENAI_API_KEY=your_openai_api_key_here" > backend/.env
```

### 3. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies (optional, using http-server)
npm install -g http-server
```

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
# Run the complete system
.\start_system.bat
```

This will:
- Start the FastAPI backend on http://127.0.0.1:8001
- Start the React frontend on http://127.0.0.1:3001
- Open the application in your browser

### Option 2: Manual Startup
```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload

# Terminal 2: Start frontend
cd frontend
python -m http.server 3001

# Open browser to http://127.0.0.1:3001
```

## 📖 Usage Guide

### Basic Chat
1. Open http://127.0.0.1:3001 in your browser
2. Type your message in the input box
3. Press Enter or click Send

### RAG System (Document Processing)
1. Click the upload button (📄) in the input area
2. Select a PDF, DOCX, or HTML file
3. The system will process the document and use it for context
4. Ask questions related to the document content

### Agent System
1. Open the sidebar (⚙️ button)
2. Enter agent tasks in the "Agent Tasks" section
3. Examples:
   - "Search for information about AI"
   - "Open browser to https://example.com"
   - "List files in C:\Users"

### Voice Features
1. Enable voice in the input area toggle
2. The system will speak responses using text-to-speech
3. (Future: Voice input support)

### System Controls
- **RAG Toggle**: Enable/disable document context
- **Agents Toggle**: Enable/disable agent execution
- **Voice Toggle**: Enable/disable text-to-speech
- **Reset Chat**: Clear all history and documents

## 🔧 API Endpoints

### Chat API
```http
POST /chat
Content-Type: application/json

{
  "message": "Your message here",
  "use_rag": true,
  "use_agents": false,
  "speak": false
}
```

### Document Upload
```http
POST /upload
Content-Type: multipart/form-data

file: [PDF/DOCX/HTML file]
```

### Agent Tasks
```http
POST /agent
Content-Type: application/json

{
  "task": "Task description here"
}
```

### Voice Processing
```http
POST /voice
Content-Type: application/json

{
  "text": "Text to speak",
  "action": "speak"  // or "recognize"
}
```

### System Status
```http
GET /status
```

## 📁 Project Structure

```
vira-ai/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── llm.py              # LLM integration
│   ├── rag.py              # RAG system
│   ├── agents.py           # Agent system
│   ├── voice.py            # Voice processing
│   ├── memory.py           # Memory management
│   ├── database.py         # MongoDB integration
│   ├── config.py           # Configuration
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── package.json        # Frontend dependencies
│   ├── index.html          # HTML entry point
│   ├── tailwind.config.js  # Tailwind CSS config
│   └── src/
│       ├── App.js          # Main React component
│       ├── index.js        # React entry point
│       ├── index.css       # Global styles
│       └── components/     # React components
│           ├── ChatWindow.js
│           ├── Inputbox.js
│           ├── Message.js
│           └── Sidebar.js
├── start_system.bat        # Automated startup script
└── README.md              # This file
```

## 🎯 Advanced Features

### RAG System
- **Document Processing**: Extracts text from PDF, DOCX, and HTML files
- **Embedding Generation**: Uses Sentence Transformers for semantic search
- **Context Injection**: Automatically includes relevant document context in responses
- **Similarity Search**: Finds most relevant document sections for queries

### Agent System
- **Web Search**: Placeholder for search API integration
- **File Operations**: Read, write, and list files
- **System Commands**: Execute shell commands
- **Browser Control**: Open URLs and search queries
- **Task History**: Track and display agent task results

### Voice System
- **Text-to-Speech**: Convert AI responses to speech
- **Voice Properties**: Configurable rate, volume, and voice selection
- **Placeholder for STT**: Framework ready for speech-to-text integration

### Memory Management
- **Conversation History**: Maintains context across multiple exchanges
- **Session Storage**: Optional MongoDB integration for persistent sessions
- **Context Window**: Intelligent context management for long conversations

## 🔒 Security Features

- **Environment Variables**: API keys stored securely
- **Input Validation**: Comprehensive input sanitization
- **CORS Protection**: Controlled cross-origin access
- **Error Handling**: Graceful error responses without exposing internals

## 📊 Performance Features

- **Streaming Responses**: Real-time response streaming
- **Caching**: Intelligent caching for document embeddings
- **Async Processing**: Non-blocking I/O operations
- **Memory Management**: Efficient context window management

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check Python version (3.8+ required)
   - Verify OpenAI API key in `.env`
   - Check port 8001 is not in use

2. **Frontend won't load**
   - Check port 3001 is not in use
   - Verify frontend files are in correct location
   - Check browser console for errors

3. **Document upload fails**
   - Check file size limits
   - Verify file format (PDF, DOCX, HTML)
   - Check uploads directory permissions

4. **RAG not working**
   - Verify document was uploaded successfully
   - Check RAG toggle is enabled
   - Ensure query is related to document content

### Logs and Debugging
- Backend logs: Check terminal output for FastAPI
- Frontend logs: Use browser developer tools
- Error responses: Check API response for error details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models and API
- FastAPI team for excellent web framework
- React team for powerful UI library
- Sentence Transformers for embedding models
- All open-source contributors

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

---

**VIRA AI** - Your advanced AI assistant for professional use cases.#   v i r a  
 