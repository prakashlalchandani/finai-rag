import ReactMarkdown from 'react-markdown';
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, Send, FileText, CheckCircle2, Loader2, Bot, User, Sun, Moon, LogOut, Trash2, ChevronDown, BookOpen } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  // --- Auth States ---
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token')); 
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authUsername, setAuthUsername] = useState('');

  // --- App States ---
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hello! I am your Autonomous Financial Auditor. Upload an agreement or choose an existing one to ask questions.' }
  ]);
  const [input, setInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  // --- Multi-Document States ---
  const [userDocuments, setUserDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState('all'); // 'all' means global context
  const [isDropdownOpen, setIsDropdownOpen] = useState(false); // Naya state custom dropdown ke liye
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchUserDocuments();
    }
  }, [isAuthenticated]);

  // ==========================================
  // API FUNCTIONS
  // ==========================================
  const fetchUserDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`, {
        params: { session_id: localStorage.getItem('session_id') || 'default_user' },
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setUserDocuments(response.data.documents || []);
    } catch (error) {
      console.error("Failed to fetch documents", error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      if (isLoginMode) {
        const response = await axios.post(`${API_BASE_URL}/login`, {
          email: authEmail,
          password: authPassword
        });
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('session_id', response.data.user_id);
        setIsAuthenticated(true);
      } else {
        await axios.post(`${API_BASE_URL}/register`, {
          username: authUsername,
          email: authEmail,
          password: authPassword
        });
        alert("Registration Successful! Please log in.");
        setIsLoginMode(true);
      }
    } catch (error) {
      alert("Auth Error: " + (error.response?.data?.detail || "Something went wrong"));
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('session_id');
    setIsAuthenticated(false);
    setUserDocuments([]);
    setSelectedDocument('all');
    setMessages([{ role: 'ai', text: 'Hello! I am your Autonomous Financial Auditor. Upload an agreement to begin.' }]);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', localStorage.getItem('session_id') || 'default_user');

    try {
      await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      await fetchUserDocuments();
      setSelectedDocument(file.name);
      setMessages(prev => [...prev, { role: 'system', text: `Successfully indexed ${file.name}.` }]);
    } catch (error) {
      console.error("Upload error:", error);
      setMessages(prev => [...prev, { role: 'system', text: `Failed to upload ${file.name}.`, isError: true }]);
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
        params: { 
          query: userQuery,
          session_id: localStorage.getItem('session_id') || 'default_user',
          document_selector: selectedDocument 
        },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
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

  // NAYA DELETE FUNCTION
  const handleDeleteDocument = async (filename, e) => {
    e.stopPropagation(); // Yeh dropdown ko band hone se rokega jab hum trash icon click karenge
    if (!window.confirm(`Are you sure you want to permanently delete "${filename}"?`)) return;

    try {
      await axios.delete(`${API_BASE_URL}/documents/${filename}`, {
        params: { session_id: localStorage.getItem('session_id') || 'default_user' },
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      // Update UI state
      const updatedDocs = userDocuments.filter(doc => doc !== filename);
      setUserDocuments(updatedDocs);
      
      // Agar delete kiya hua document hi active tha, toh wapas 'all' par jao
      if (selectedDocument === filename) {
        setSelectedDocument('all');
      }
      
      setMessages(prev => [...prev, { role: 'system', text: `Successfully deleted ${filename} from database.` }]);
    } catch (error) {
      console.error("Delete error:", error);
      alert("Failed to delete document.");
    }
  };

  // ==========================================
  // UI RENDERING
  // ==========================================

  if (!isAuthenticated) {
    return (
      <div className={`flex h-screen items-center justify-center transition-colors duration-300 ${isDarkMode ? 'dark bg-slate-900' : 'bg-slate-50'}`}>
        <div className="absolute top-4 right-4">
          <button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-white">
            {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>
        <div className="w-full max-w-md p-8 bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700">
          <h2 className="text-2xl font-bold mb-6 text-center text-slate-800 dark:text-white">
            {isLoginMode ? 'Welcome to FinAudit AI' : 'Create an Account'}
          </h2>
          <form onSubmit={handleAuth} className="space-y-4">
            {!isLoginMode && (
              <input type="text" placeholder="Username" value={authUsername} onChange={(e) => setAuthUsername(e.target.value)} className="w-full p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-white" required />
            )}
            <input type="email" placeholder="Email Address" value={authEmail} onChange={(e) => setAuthEmail(e.target.value)} className="w-full p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-white" required />
            <input type="password" placeholder="Password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} className="w-full p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-white" required />
            <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
              {isLoginMode ? 'Sign In' : 'Register'}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            {isLoginMode ? "Don't have an account? " : "Already have an account? "}
            <button onClick={() => setIsLoginMode(!isLoginMode)} className="text-blue-600 dark:text-blue-400 hover:underline">
              {isLoginMode ? 'Sign up' : 'Log in'}
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${isDarkMode ? 'dark' : ''} font-sans`}>
      <div className="flex h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300">
        
        {/* LEFT SIDEBAR */}
        <div className="w-80 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col transition-colors duration-300">
          
          <div className="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-start transition-colors duration-300">
            <div>
              <h1 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2 transition-colors duration-300">
                <FileText className="text-blue-600 dark:text-blue-400" />
                FinAudit AI
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 transition-colors duration-300">Enterprise RAG Engine</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 transition-colors duration-200">
                {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button onClick={handleLogout} className="p-2 rounded-lg bg-red-50 hover:bg-red-100 dark:bg-red-900/30 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 transition-colors duration-200" title="Logout">
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="p-6 grow">
            <h2 className="text-sm font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-4 transition-colors duration-300">Knowledge Base</h2>
            
            <button onClick={() => fileInputRef.current.click()} disabled={isUploading} className="w-full flex items-center justify-center gap-2 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800/50 rounded-lg py-3 px-4 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors duration-200 disabled:opacity-50">
              {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <UploadCloud className="w-5 h-5" />}
              <span className="font-medium">{isUploading ? 'Indexing Document...' : 'Upload Agreement'}</span>
            </button>
            <input type="file" accept=".pdf, .docx, .txt" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />

            {/* BEAUTIFUL CUSTOM DROPDOWN WITH DELETE BUTTON */}
            {userDocuments.length > 0 && (
              <div className="mt-8 relative">
                <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-3 block">
                  Active Context
                </label>
                
                {/* Dropdown Trigger Button */}
                <button 
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="w-full flex items-center justify-between bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <span className="flex items-center gap-2 truncate">
                    {selectedDocument === 'all' ? <BookOpen className="w-4 h-4 text-blue-500" /> : <FileText className="w-4 h-4 text-blue-500" />}
                    <span className="truncate">{selectedDocument === 'all' ? 'All Documents (Global)' : selectedDocument}</span>
                  </span>
                  <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown Menu Items */}
                {isDropdownOpen && (
                  <div className="absolute z-20 w-full mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                    
                    {/* All Documents Option */}
                    <div 
                      onClick={() => { setSelectedDocument('all'); setIsDropdownOpen(false); }}
                      className={`flex items-center gap-3 p-3 cursor-pointer border-b border-slate-100 dark:border-slate-700 transition-colors ${selectedDocument === 'all' ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'}`}
                    >
                      <BookOpen className="w-4 h-4" />
                      <span className="text-sm">All Documents (Global)</span>
                    </div>

                    {/* Individual Documents Loop */}
                    <div className="max-h-60 overflow-y-auto custom-scrollbar">
                      {userDocuments.map((doc, idx) => (
                        <div 
                          key={idx}
                          onClick={() => { setSelectedDocument(doc); setIsDropdownOpen(false); }}
                          className={`flex items-center justify-between p-3 cursor-pointer transition-colors group ${selectedDocument === doc ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'}`}
                        >
                          <div className="flex items-center gap-3 overflow-hidden pr-2">
                            <FileText className="w-4 h-4 shrink-0" />
                            <span className="text-sm truncate">{doc}</span>
                          </div>
                          
                          {/* Delete Button */}
                          <button 
                            onClick={(e) => handleDeleteDocument(doc, e)}
                            className="p-1.5 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 opacity-0 group-hover:opacity-100 transition-all"
                            title="Delete Document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Click outside to close dropdown logic (Optional but good UX) */}
            {isDropdownOpen && (
              <div className="fixed inset-0 z-10" onClick={() => setIsDropdownOpen(false)}></div>
            )}

          </div>
        </div>

        {/* RIGHT MAIN AREA - Chat Interface */}
        <div className="flex-1 flex flex-col bg-slate-50/50 dark:bg-slate-900/50 relative transition-colors duration-300">
          <div className="flex-1 overflow-y-auto p-8 space-y-6">
            {messages.map((msg, index) => (
              <div key={index} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'ai' && (
                  <div className="w-10 h-10 rounded-full bg-blue-600 dark:bg-blue-500 flex items-center justify-center shrink-0 shadow-sm">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                <div className={`max-w-[70%] p-5 rounded-2xl shadow-sm text-sm leading-relaxed transition-colors duration-300 ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 dark:bg-blue-500 text-white rounded-tr-none' 
                    : msg.role === 'system'
                      ? msg.isError 
                        ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800/50 w-full text-center' 
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 w-full text-center text-xs'
                      : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-tl-none'
                }`}>
                  {msg.role === 'ai' ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-800 prose-pre:text-slate-100">
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.text
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-10 h-10 rounded-full bg-slate-300 dark:bg-slate-600 flex items-center justify-center shrink-0">
                    <User className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                  </div>
                )}
              </div>
            ))}
            
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

          <div className="p-6 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 transition-colors duration-300">
            <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={userDocuments.length > 0 ? `Ask a question about ${selectedDocument === 'all' ? 'all documents' : selectedDocument}...` : "Please upload a document first..."}
                disabled={isLoading || userDocuments.length === 0}
                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-6 pr-14 py-4 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-300 disabled:opacity-60 disabled:bg-slate-100 dark:disabled:bg-slate-800"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim() || userDocuments.length === 0}
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