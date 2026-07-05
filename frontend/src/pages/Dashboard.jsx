import React, { useState, useEffect } from "react";
import { Menu } from "lucide-react";
import { useSwipeable } from "react-swipeable"; // 👈 NEW IMPORT

import Sidebar from "../components/sidebar/Sidebar";
import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";
import { documentAPI, chatAPI } from "../api/api";

const Dashboard = () => {
  const [messages, setMessages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [userDocuments, setUserDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState("all");

  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    setUserDocuments([]);
    setSelectedDocument("all");
    fetchUserDocuments();
  }, []);

  const fetchUserDocuments = async () => {
    try {
      const sessionId = localStorage.getItem("session_id") || "default_user";
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
    formData.append("file", file);
    formData.append("session_id", localStorage.getItem("session_id") || "default_user");

    try {
      await documentAPI.uploadDocument(formData);
      await fetchUserDocuments();
      setSelectedDocument(file.name);

      setMessages((prev) => [
        ...prev,
        { role: "system", text: `Successfully indexed ${file.name}.` },
      ]);
      
      setSidebarOpen(false);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "system", text: `Failed to upload ${file.name}.`, isError: true },
      ]);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async (userQuery) => {
    setMessages((prev) => [...prev, { role: "user", text: userQuery }]);
    setIsLoading(true);

    try {
      const sessionId = localStorage.getItem("session_id") || "default_user";
      const response = await chatAPI.search(userQuery, sessionId, selectedDocument);
      setMessages((prev) => [...prev, { role: "ai", text: response.data.answer }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "system", text: "Error communicating with the auditor agent.", isError: true },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (filename) => {
    try {
      const sessionId = localStorage.getItem("session_id") || "default_user";
      await documentAPI.deleteDocument(filename, sessionId);

      setUserDocuments((prev) => prev.filter((doc) => doc !== filename));
      
      if (selectedDocument === filename) {
        setSelectedDocument("all");
      }

      setMessages((prev) => [
        ...prev,
        { role: "system", text: `Successfully deleted ${filename}.` },
      ]);

      // 📱 HAPTIC FEEDBACK (SUCCESS)
      // Single 50ms vibration for a satisfying click feel
      if ('vibrate' in navigator) {
        navigator.vibrate(50);
      }

    } catch (error) {
      // 📱 HAPTIC FEEDBACK (ERROR)
      // Three quick vibrations to alert the user of failure
      if ('vibrate' in navigator) {
        navigator.vibrate([50, 50, 50, 50, 50]);
      }
      alert("Failed to delete document.");
    }
  };

  // 👈 NEW: Swipe Handler Logic
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => {
      if (sidebarOpen) {
        setSidebarOpen(false); // Close sidebar on left swipe
      }
    },
    onSwipedRight: () => {
      if (!sidebarOpen) {
        setSidebarOpen(true); // Optional: Open sidebar on right swipe!
      }
    },
    trackMouse: false, // Set to true if you want to test swiping with a mouse on desktop
    delta: 40, // Minimum swipe distance in pixels to trigger the action
  });

  return (
    // 👈 NEW: Spread the swipeHandlers onto the main wrapper div
    <div {...swipeHandlers} className="relative flex h-screen overflow-hidden bg-white dark:bg-[#09090b] transition-colors duration-300">
      
      <Sidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        isUploading={isUploading}
        handleFileUpload={handleFileUpload}
        userDocuments={userDocuments}
        selectedDocument={selectedDocument}
        setSelectedDocument={setSelectedDocument}
        handleDeleteDocument={handleDeleteDocument}
      />

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex flex-1 flex-col bg-slate-50/50 dark:bg-slate-900/50 min-w-0">
        
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-zinc-200 bg-white/90 px-4 py-3 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/90 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="text-lg font-semibold text-zinc-800 dark:text-zinc-100">FinAI</h1>
        </header>

        <div className="flex min-h-0 flex-1 flex-col">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
          />
          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            userDocuments={userDocuments}
            selectedDocument={selectedDocument}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;