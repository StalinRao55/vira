import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Upload, Bot, User, Settings, FileText, Brain, Zap, Volume2, Eye, EyeOff } from 'lucide-react';
import ChatWindow from './components/ChatWindow';
import Inputbox from './components/Inputbox';
import Sidebar from './components/Sidebar';
import './index.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [ragEnabled, setRagEnabled] = useState(true);
  const [agentsEnabled, setAgentsEnabled] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);

  const chatEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch system status
  useEffect(() => {
    fetchSystemStatus();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8001/status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const handleSendMessage = async (message) => {
    if (!message.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: message,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await fetch('http://127.0.0.1:8001/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          use_rag: ragEnabled,
          use_agents: agentsEnabled,
          speak: voiceEnabled
        })
      });

      const data = await response.json();
      
      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: data.response,
        agent_response: data.agent_response,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8001/upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (data.message) {
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          size: file.size,
          uploaded: new Date().toLocaleString()
        }]);
        
        // Add upload confirmation message
        const uploadMessage = {
          id: Date.now(),
          type: 'system',
          content: `Document "${file.name}" uploaded successfully. VIRA can now use this document for context.`,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, uploadMessage]);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleVoiceInput = () => {
    // Placeholder for voice input implementation
    alert('Voice input feature coming soon! Requires microphone access and speech recognition.');
  };

  const handleResetChat = async () => {
    try {
      await fetch('http://127.0.0.1:8001/reset', {
        method: 'POST'
      });
      setMessages([]);
      setUploadedFiles([]);
      await fetchSystemStatus();
    } catch (error) {
      console.error('Error resetting chat:', error);
    }
  };

  const handleAgentTask = async (task) => {
    try {
      const response = await fetch('http://127.0.0.1:8001/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ task })
      });

      const data = await response.json();
      
      const agentMessage = {
        id: Date.now(),
        type: 'agent',
        content: data.result,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error executing agent task:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        uploadedFiles={uploadedFiles}
        systemStatus={systemStatus}
        onResetChat={handleResetChat}
        onAgentTask={handleAgentTask}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Settings className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">VIRA AI</h1>
                <p className="text-sm text-gray-500">Advanced AI Assistant</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1 text-sm text-gray-600">
                <div className={`w-2 h-2 rounded-full ${systemStatus?.status === 'operational' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span>{systemStatus?.status || 'Checking...'}</span>
              </div>
              {systemStatus && (
                <span className="text-xs text-gray-500 ml-2">
                  Memory: {systemStatus.memory_entries} | Docs: {systemStatus.rag_documents}
                </span>
              )}
            </div>
          </div>
        </header>

        {/* Chat Window */}
        <ChatWindow 
          messages={messages}
          isTyping={isTyping}
          chatEndRef={chatEndRef}
        />

        {/* Input Area */}
        <Inputbox 
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          onVoiceInput={handleVoiceInput}
          ragEnabled={ragEnabled}
          setRagEnabled={setRagEnabled}
          agentsEnabled={agentsEnabled}
          setAgentsEnabled={setAgentsEnabled}
          voiceEnabled={voiceEnabled}
          setVoiceEnabled={setVoiceEnabled}
        />
      </div>
    </div>
  );
}

export default App;