import React, { useState } from 'react';
import { Sun, Moon, FileText } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { authAPI } from '../api/api';

const Login = () => {
  const { isDarkMode, toggleDarkMode, login } = useAppContext();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authUsername, setAuthUsername] = useState('');

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      if (isLoginMode) {
        const response = await authAPI.login({ email: authEmail, password: authPassword });
        login(response.data.access_token, response.data.user_id, response.data.username); 
      } else {
        await authAPI.register({ username: authUsername, email: authEmail, password: authPassword });
        alert("Registration Successful! Please log in.");
        setIsLoginMode(true);
      }
    } catch (error) {
      alert("Auth Error: " + (error.response?.data?.detail || "Something went wrong"));
    }
  };

  return (
    <div className="flex h-screen items-center justify-center transition-colors duration-300 bg-white dark:bg-[#09090b]">
      <div className="absolute top-6 right-6">
        <button onClick={toggleDarkMode} className="p-2.5 rounded-full bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 transition-all">
          {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>

      <div className="w-full max-w-md px-8 py-10 bg-transparent sm:bg-white sm:dark:bg-zinc-900/50 sm:border border-zinc-200 dark:border-zinc-800 rounded-3xl sm:shadow-2xl sm:shadow-zinc-200/20 sm:dark:shadow-black/40 backdrop-blur-xl">
        
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-zinc-900 dark:bg-white rounded-xl flex items-center justify-center shadow-md mb-4">
            <FileText className="w-6 h-6 text-white dark:text-zinc-900" />
          </div>
          <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50 tracking-tight">
            {isLoginMode ? 'Welcome back' : 'Create your account'}
          </h2>
        </div>

        <form onSubmit={handleAuth} className="space-y-4">
          {!isLoginMode && (
            <input type="text" placeholder="Username" value={authUsername} onChange={(e) => setAuthUsername(e.target.value)} className="w-full px-4 py-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all" required />
          )}
          <input type="email" placeholder="Email Address" value={authEmail} onChange={(e) => setAuthEmail(e.target.value)} className="w-full px-4 py-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all" required />
          <input type="password" placeholder="Password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} className="w-full px-4 py-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all" required />
          
          <button type="submit" className="w-full py-3.5 mt-2 bg-zinc-900 hover:bg-zinc-800 dark:bg-white dark:hover:bg-zinc-200 text-white dark:text-zinc-900 rounded-xl font-medium transition-all active:scale-[0.98]">
            {isLoginMode ? 'Continue' : 'Sign Up'}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-zinc-500 dark:text-zinc-400">
          {isLoginMode ? "Don't have an account? " : "Already have an account? "}
          <button onClick={() => setIsLoginMode(!isLoginMode)} className="text-zinc-900 dark:text-white font-medium hover:underline">
            {isLoginMode ? 'Sign up' : 'Log in'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;