import React, { useState } from 'react';
import { 
  Settings, 
  FileText, 
  Database, 
  RefreshCw, 
  Zap, 
  Eye, 
  EyeOff, 
  AlertTriangle,
  CheckCircle,
  Clock,
  File,
  Upload
} from 'lucide-react';

const Sidebar = ({ 
  isOpen, 
  onClose, 
  uploadedFiles, 
  systemStatus, 
  onResetChat, 
  onAgentTask 
}) => {
  const [agentInput, setAgentInput] = useState('');
  const [agentHistory, setAgentHistory] = useState([]);

  const executeAgentTask = async () => {
    if (!agentInput.trim()) return;

    const task = agentInput;
    setAgentInput('');
    
    // Add to history
    const newTask = {
      id: Date.now(),
      task,
      status: 'running',
      timestamp: new Date().toLocaleTimeString()
    };
    setAgentHistory(prev => [...prev, newTask]);

    try {
      const response = await fetch('http://127.0.0.1:8001/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task })
      });

      const data = await response.json();
      
      // Update history with result
      setAgentHistory(prev => prev.map(item => 
        item.id === newTask.id 
          ? { ...item, status: 'completed', result: data.result }
          : item
      ));
    } catch (error) {
      setAgentHistory(prev => prev.map(item => 
        item.id === newTask.id 
          ? { ...item, status: 'error', result: 'Error executing task' }
          : item
      ));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="w-96 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">System Control</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg"
          >
            <EyeOff className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        
        {/* System Status */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center">
            <Database className="w-4 h-4 mr-2" />
            System Status
          </h3>
          {systemStatus ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className={`flex items-center ${systemStatus.status === 'operational' ? 'text-green-600' : 'text-red-600'}`}>
                  <div className={`w-2 h-2 rounded-full mr-2 ${systemStatus.status === 'operational' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  {systemStatus.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Memory:</span>
                <span className="text-blue-600">{systemStatus.memory_entries} entries</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Documents:</span>
                <span className="text-purple-600">{systemStatus.rag_documents} files</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Features:</span>
                <div className="flex space-x-2">
                  {systemStatus.features?.rag && <span className="text-blue-600">RAG</span>}
                  {systemStatus.features?.agents && <span className="text-yellow-600">Agents</span>}
                  {systemStatus.features?.voice && <span className="text-green-600">Voice</span>}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-sm">Loading system status...</div>
          )}
        </div>

        {/* Document Management */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center">
            <FileText className="w-4 h-4 mr-2" />
            Documents ({uploadedFiles.length})
          </h3>
          {uploadedFiles.length > 0 ? (
            <div className="space-y-2">
              {uploadedFiles.map((file, index) => (
                <div key={index} className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <File className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium">{file.name}</span>
                    </div>
                    <span className="text-xs text-gray-500">{file.uploaded}</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {(file.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-sm text-center py-4">
              <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              No documents uploaded yet
            </div>
          )}
        </div>

        {/* Agent System */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center">
            <Zap className="w-4 h-4 mr-2" />
            Agent Tasks
          </h3>
          
          {/* Task Input */}
          <div className="space-y-2 mb-4">
            <input
              type="text"
              value={agentInput}
              onChange={(e) => setAgentInput(e.target.value)}
              placeholder="Enter agent task..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && executeAgentTask()}
            />
            <button
              onClick={executeAgentTask}
              disabled={!agentInput.trim()}
              className="w-full bg-yellow-500 text-white py-2 px-4 rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Execute Task
            </button>
          </div>

          {/* Task History */}
          {agentHistory.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs text-gray-600 uppercase tracking-wider">Recent Tasks</h4>
              {agentHistory.slice(-5).map((task) => (
                <div key={task.id} className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-500">{task.timestamp}</span>
                    {task.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                    {task.status === 'running' && <Clock className="w-4 h-4 text-blue-500 animate-spin" />}
                    {task.status === 'error' && <AlertTriangle className="w-4 h-4 text-red-500" />}
                  </div>
                  <div className="text-sm text-gray-900 mb-1">{task.task}</div>
                  {task.result && (
                    <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">{task.result}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={onResetChat}
            className="w-full bg-red-500 text-white py-3 px-4 rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reset Chat & Clear Documents</span>
          </button>
          
          <div className="text-xs text-gray-500 text-center">
            Reset clears all chat history and uploaded documents
          </div>
        </div>

      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-500 text-center">
          VIRA AI v2.0.0
          <br />
          Advanced AI Assistant System
        </div>
      </div>
    </div>
  );
};

export default Sidebar;