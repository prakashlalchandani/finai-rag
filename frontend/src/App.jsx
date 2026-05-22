import React from 'react';
import { AppProvider, useAppContext } from './context/AppContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

const AppContent = () => {
  const { isAuthenticated } = useAppContext();
  return isAuthenticated ? <Dashboard /> : <Login />;
};

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;