import React from 'react';
import { Bot, User, FileText, Zap, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const Message = ({ message }) => {
  const renderContent = (content) => {
    return (
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={atomDark}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  const getMessageType = () => {
    switch (message.type) {
      case 'user':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-900',
          icon: <User className="w-5 h-5 text-blue-600" />
        };
      case 'assistant':
        return {
          bg: 'bg-purple-50',
          border: 'border-purple-200',
          text: 'text-purple-900',
          icon: <Bot className="w-5 h-5 text-purple-600" />
        };
      case 'agent':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-900',
          icon: <Zap className="w-5 h-5 text-yellow-600" />
        };
      case 'system':
        return {
          bg: 'bg-green-50',
          border: 'border-green-200',
          text: 'text-green-900',
          icon: <FileText className="w-5 h-5 text-green-600" />
        };
      case 'error':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-900',
          icon: <AlertCircle className="w-5 h-5 text-red-600" />
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-900',
          icon: <Bot className="w-5 h-5 text-gray-600" />
        };
    }
  };

  const type = getMessageType();

  return (
    <div className={`animate-in slide-in-from-bottom-2 duration-300`}>
      <div className={`max-w-4xl mx-auto`}>
        <div className={`rounded-2xl p-4 border-l-4 ${type.bg} ${type.border} ${type.text}`}>
          <div className="flex items-start space-x-3">
            {/* Avatar/Icon */}
            <div className="flex-shrink-0 mt-0.5">
              <div className="bg-white p-2 rounded-full shadow-sm border border-gray-200">
                {type.icon}
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-sm capitalize">
                    {message.type === 'user' ? 'You' : 
                     message.type === 'assistant' ? 'VIRA AI' :
                     message.type === 'agent' ? 'Agent System' :
                     message.type === 'system' ? 'System' :
                     message.type === 'error' ? 'Error' : 'AI'}
                  </span>
                  {message.type === 'assistant' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      AI Assistant
                    </span>
                  )}
                  {message.type === 'agent' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Agent
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500">
                  {message.timestamp}
                </div>
              </div>

              {/* Main Content */}
              <div className="text-sm leading-relaxed">
                {renderContent(message.content)}
              </div>

              {/* Agent Response (if present) */}
              {message.agent_response && (
                <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center space-x-2 mb-1">
                    <Zap className="w-4 h-4 text-yellow-600" />
                    <span className="text-xs font-medium text-yellow-800">Agent Response</span>
                  </div>
                  <div className="text-xs text-yellow-900">
                    {message.agent_response}
                  </div>
                </div>
              )}

              {/* Status Indicators */}
              {message.type === 'agent' && (
                <div className="mt-2 flex items-center space-x-2 text-xs">
                  {message.status === 'running' && (
                    <>
                      <Clock className="w-4 h-4 text-blue-500 animate-spin" />
                      <span className="text-blue-600">Running...</span>
                    </>
                  )}
                  {message.status === 'completed' && (
                    <>
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-green-600">Completed</span>
                    </>
                  )}
                  {message.status === 'error' && (
                    <>
                      <AlertCircle className="w-4 h-4 text-red-500" />
                      <span className="text-red-600">Error</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Message;