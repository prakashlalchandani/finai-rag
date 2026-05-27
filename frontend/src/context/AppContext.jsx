import React, { createContext, useState, useContext, useEffect } from 'react';
import { documentAPI } from '../api/api'; // NAYA: API import karna hoga

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const [isDarkMode, setIsDarkMode] = useState(true);

  const login = (token, userId, username) => {
    localStorage.setItem('token', token);
    const uniqueSessionId = `${userId}_${Date.now()}`;
    localStorage.setItem('session_id', uniqueSessionId);
    localStorage.setItem('username', username);
    setIsAuthenticated(true);
  };

  // NAYA: Logout ko async banaya aur API call add ki
  const logout = async () => {
    try {
      const sessionId = localStorage.getItem('session_id');
      if (sessionId) {
        // Backend API call to delete all files, SQL, and vectors
        await documentAPI.cleanupData(sessionId);
      }
    } catch (error) {
      console.error("Backend cleanup failed, but proceeding with local logout", error);
    } finally {
      // API fail ho ya pass, browser se session hamesha clear hona chahiye
      localStorage.removeItem('token');
      localStorage.removeItem('session_id');
      localStorage.removeItem('username'); 
      setIsAuthenticated(false);
    }
  };

  const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

  return (
    <AppContext.Provider value={{ isAuthenticated, isDarkMode, login, logout, toggleDarkMode }}>
      <div className={`${isDarkMode ? 'dark' : ''} font-sans h-screen`}>
        {children}
      </div>
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);