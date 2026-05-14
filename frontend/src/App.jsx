import ReactMarkdown from 'react-markdown';
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, Send, FileText, CheckCircle2, Loader2, Bot, User, Sun, Moon } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hello! I am your Autonomous Financial Auditor. Upload a loan agreement and ask me to calculate EMIs, penalties, or summarize terms.' }
  ]);
  const [input, setInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeDocument, setActiveDocument] = useState(null);
  
  // NEW: Dark mode state
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setActiveDocument(file.name);
      setMessages(prev => [...prev, { role: 'system', text: `Successfully indexed ${file.name}.` }]);
    } catch (error) {
      console.error("Upload error:", error);
      setMessages(prev => [...prev, { role: 'system', text: `Failed to upload ${file.name}. Is the backend running?`, isError: true }]);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userQuery = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.get(`${API_BASE_URL}/search`, {
        params: { query: userQuery }
      });
      
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: response.data.answer,
        sources: response.data.sources_used 
      }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { role: 'system', text: "Error communicating with the auditor agent.", isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  // We wrap the entire app in a div that conditionally gets the 'dark' class
  return (
    <div className={`${isDarkMode ? 'dark' : ''} font-sans`}>
      {/* Main Container */}
      <div className="flex h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300">
        
        {/* LEFT SIDEBAR */}
        <div className="w-80 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col transition-colors duration-300">
          
          {/* Header Area (Where the green box was) */}
          <div className="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-start transition-colors duration-300">
            <div>
              <h1 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2 transition-colors duration-300">
                <FileText className="text-blue-600 dark:text-blue-400" />
                FinAudit AI
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 transition-colors duration-300">Enterprise RAG Engine</p>
            </div>
            
            {/* THE DARK MODE TOGGLE BUTTON */}
            <button 
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 transition-colors duration-200"
              aria-label="Toggle Dark Mode"
            >
              {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>

          <div className="p-6 grow">
            <h2 className="text-sm font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-4 transition-colors duration-300">Knowledge Base</h2>
            
            {/* Upload Button */}
            <button 
              onClick={() => fileInputRef.current.click()}
              disabled={isUploading}
              className="w-full flex items-center justify-center gap-2 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800/50 rounded-lg py-3 px-4 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors duration-200 disabled:opacity-50"
            >
              {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <UploadCloud className="w-5 h-5" />}
              <span className="font-medium">{isUploading ? 'Indexing Document...' : 'Upload Agreement'}</span>
            </button>
            <input type="file" accept=".pdf, .docx, .txt" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />

            {/* Active Document Indicator */}
            {activeDocument && (
              <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800/50 rounded-lg flex items-start gap-3 transition-colors duration-300">
                <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-900 dark:text-green-300">Active Document</p>
                  <p className="text-xs text-green-700 dark:text-green-400 truncate mt-1" title={activeDocument}>{activeDocument}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT MAIN AREA - Chat Interface */}
        <div className="flex-1 flex flex-col bg-slate-50/50 dark:bg-slate-900/50 relative transition-colors duration-300">
          
          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-8 space-y-6">
            {messages.map((msg, index) => (
              <div key={index} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                
                {/* AI Avatar */}
                {msg.role === 'ai' && (
                  <div className="w-10 h-10 rounded-full bg-blue-600 dark:bg-blue-500 flex items-center justify-center shrink-0 shadow-sm">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}

                {/* Message Bubble */}
<div className={`max-w-[70%] p-5 rounded-2xl shadow-sm text-sm leading-relaxed transition-colors duration-300 ${
  msg.role === 'user' 
    ? 'bg-blue-600 dark:bg-blue-500 text-white rounded-tr-none' 
    : msg.role === 'system'
      ? msg.isError 
        ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800/50 w-full text-center' 
        : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 w-full text-center text-xs'
      : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-tl-none'
}`}>
  
  {/* NEW: Markdown Renderer */}
  {msg.role === 'ai' ? (
    <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-800 prose-pre:text-slate-100">
      <ReactMarkdown>
        {msg.text}
      </ReactMarkdown>
    </div>
  ) : (
    msg.text
  )}

</div>

                {/* User Avatar */}
                {msg.role === 'user' && (
                  <div className="w-10 h-10 rounded-full bg-slate-300 dark:bg-slate-600 flex items-center justify-center shrink-0">
                    <User className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                  </div>
                )}
              </div>
            ))}
            
            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex gap-4 justify-start">
                 <div className="w-10 h-10 rounded-full bg-blue-600 dark:bg-blue-500 flex items-center justify-center shrink-0 shadow-sm">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-none p-5 flex items-center gap-2 shadow-sm transition-colors duration-300">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600 dark:text-blue-400" />
                  <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">Auditing documents & calculating...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-6 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 transition-colors duration-300">
            <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={activeDocument ? "Ask a question about the document..." : "Please upload a document first..."}
                disabled={isLoading || !activeDocument}
                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-6 pr-14 py-4 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-300 disabled:opacity-60 disabled:bg-slate-100 dark:disabled:bg-slate-800"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim() || !activeDocument}
                className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:hover:bg-blue-600 dark:disabled:hover:bg-blue-500"
              >
                <Send className="w-5 h-5 ml-1" />
              </button>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;