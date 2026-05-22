import React, { createContext, useState, useContext, useEffect } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const [isDarkMode, setIsDarkMode] = useState(true);

  // src/context/AppContext.jsx mein login function ko isse replace kar:
  const login = (token, userId, username) => {
    localStorage.setItem('token', token);
    const uniqueSessionId = `${userId}_${Date.now()}`;
    localStorage.setItem('session_id', uniqueSessionId);
    localStorage.setItem('username', username); // NAYA: Username save kar rahe hain
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('session_id');
    setIsAuthenticated(false);
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