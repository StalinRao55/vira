import React from 'react';
import { Bot, User, FileText, Zap, Brain, AlertCircle } from 'lucide-react';
import Message from './Message';

const ChatWindow = ({ messages, isTyping, chatEndRef }) => {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-4 rounded-full mb-4">
            <Bot className="w-12 h-12 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to VIRA AI</h2>
          <p className="text-gray-600 mb-6 max-w-md">
            Your advanced AI assistant with RAG, agent capabilities, and document processing.
            Upload documents, enable agents, and start chatting!
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-2xl">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <Brain className="w-6 h-6 text-blue-600 mb-2" />
              <h3 className="font-semibold mb-1">RAG System</h3>
              <p className="text-sm text-gray-600">Upload documents for context-aware responses</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <Zap className="w-6 h-6 text-yellow-600 mb-2" />
              <h3 className="font-semibold mb-1">Agent System</h3>
              <p className="text-sm text-gray-600">Execute tasks and automate workflows</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <FileText className="w-6 h-6 text-green-600 mb-2" />
              <h3 className="font-semibold mb-1">Document AI</h3>
              <p className="text-sm text-gray-600">Process PDFs, DOCX, and HTML files</p>
            </div>
          </div>
        </div>
      ) : (
        messages.map((message) => (
          <Message key={message.id} message={message} />
        ))
      )}
      
      {isTyping && (
        <div className="flex justify-start">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 max-w-md">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-full">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div ref={chatEndRef} />
    </div>
  );
};

export default ChatWindow;