import React, { useState, useEffect } from 'react';
import Sidebar from '../components/sidebar/Sidebar';
import ChatWindow from '../components/chat/ChatWindow';
import ChatInput from '../components/chat/ChatInput';
import { documentAPI, chatAPI } from '../api/api';

const Dashboard = () => {
  const [messages, setMessages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [userDocuments, setUserDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState('all');

  useEffect(() => {
    setUserDocuments([]); 
    setSelectedDocument('all');
  }, []);

  const fetchUserDocuments = async () => {
    try {
      const sessionId = localStorage.getItem('session_id') || 'default_user';
      const response = await documentAPI.fetchDocuments(sessionId);
      setUserDocuments(response.data.documents || []);
    } catch (error) {
      console.error("Failed to fetch documents", error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', localStorage.getItem('session_id') || 'default_user');

    try {
      await documentAPI.uploadDocument(formData);
      await fetchUserDocuments();
      setSelectedDocument(file.name);
      setMessages(prev => [...prev, { role: 'system', text: `Successfully indexed ${file.name}.` }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'system', text: `Failed to upload ${file.name}.`, isError: true }]);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async (userQuery) => {
    setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
    setIsLoading(true);

    try {
      const sessionId = localStorage.getItem('session_id') || 'default_user';
      const response = await chatAPI.search(userQuery, sessionId, selectedDocument);
      setMessages(prev => [...prev, { role: 'ai', text: response.data.answer }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'system', text: "Error communicating with the auditor agent.", isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (filename) => {
    if (!window.confirm(`Are you sure you want to permanently delete "${filename}"?`)) return;
    try {
      const sessionId = localStorage.getItem('session_id') || 'default_user';
      await documentAPI.deleteDocument(filename, sessionId);
      setUserDocuments(prev => prev.filter(doc => doc !== filename));
      if (selectedDocument === filename) setSelectedDocument('all');
      setMessages(prev => [...prev, { role: 'system', text: `Successfully deleted ${filename}.` }]);
    } catch (error) {
      alert("Failed to delete document.");
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-[#09090b] transition-colors duration-300">
      <Sidebar 
        isUploading={isUploading} 
        handleFileUpload={handleFileUpload} 
        userDocuments={userDocuments} 
        selectedDocument={selectedDocument} 
        setSelectedDocument={setSelectedDocument} 
        handleDeleteDocument={handleDeleteDocument} 
      />
      <div className="flex-1 flex flex-col bg-slate-50/50 dark:bg-slate-900/50 relative">
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} userDocuments={userDocuments} selectedDocument={selectedDocument} />
      </div>
    </div>
  );
};

export default Dashboard;