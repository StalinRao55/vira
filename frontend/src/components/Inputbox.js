import React, { useState } from 'react';
import { Send, Mic, Upload, Brain, Zap, Volume2, Eye, EyeOff } from 'lucide-react';

const Inputbox = ({ 
  onSendMessage, 
  onFileUpload, 
  onVoiceInput,
  ragEnabled,
  setRagEnabled,
  agentsEnabled,
  setAgentsEnabled,
  voiceEnabled,
  setVoiceEnabled
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setIsUploading(true);
      await onFileUpload(e);
      setIsUploading(false);
      // Clear the file input
      e.target.value = null;
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {/* Feature Toggle Bar */}
      <div className="flex items-center justify-between mb-3 px-2">
        <div className="flex items-center space-x-4 text-sm">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={ragEnabled}
              onChange={(e) => setRagEnabled(e.target.checked)}
              className="form-checkbox h-4 w-4 text-blue-600"
            />
            <Brain className="w-4 h-4 text-blue-600" />
            <span className="text-gray-700">RAG</span>
          </label>
          
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={agentsEnabled}
              onChange={(e) => setAgentsEnabled(e.target.checked)}
              className="form-checkbox h-4 w-4 text-yellow-600"
            />
            <Zap className="w-4 h-4 text-yellow-600" />
            <span className="text-gray-700">Agents</span>
          </label>
          
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={voiceEnabled}
              onChange={(e) => setVoiceEnabled(e.target.checked)}
              className="form-checkbox h-4 w-4 text-green-600"
            />
            <Volume2 className="w-4 h-4 text-green-600" />
            <span className="text-gray-700">Voice</span>
          </label>
        </div>
        
        <div className="text-xs text-gray-500">
          {ragEnabled && "RAG: ON"} {agentsEnabled && " | Agents: ON"} {voiceEnabled && " | Voice: ON"}
        </div>
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="flex items-end space-x-3">
        {/* File Upload Button */}
        <div className="relative">
          <input
            type="file"
            id="file-upload"
            className="hidden"
            onChange={handleFileChange}
            accept=".pdf,.docx,.html,.txt"
          />
          <label
            htmlFor="file-upload"
            className="p-2 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors border border-gray-200"
            title="Upload Document"
          >
            <Upload className="w-5 h-5 text-gray-600" />
          </label>
          {isUploading && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
          )}
        </div>

        {/* Voice Input Button */}
        <button
          type="button"
          onClick={onVoiceInput}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
          title="Voice Input"
        >
          <Mic className="w-5 h-5 text-gray-600" />
        </button>

        {/* Text Input */}
        <div className="flex-1 relative">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none max-h-32"
            rows="1"
          />
          <div className="absolute right-3 bottom-3 text-xs text-gray-400">
            {inputValue.length}
          </div>
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!inputValue.trim()}
          className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3 rounded-lg hover:from-blue-600 hover:to-purple-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>

      {/* Feature Descriptions */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
        <div className="flex space-x-4">
          <span>💡 RAG: Use uploaded documents for context</span>
          <span>⚡ Agents: Execute automated tasks</span>
          <span>🔊 Voice: Enable text-to-speech</span>
        </div>
        <div>
          Tip: Upload documents first for better RAG responses
        </div>
      </div>
    </div>
  );
};

export default Inputbox;