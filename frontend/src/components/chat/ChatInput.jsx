import React, { useState, useRef } from 'react';
import { Send } from 'lucide-react';

const ChatInput = ({ onSendMessage, isLoading, userDocuments, selectedDocument }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  const handleInput = (e) => {
    setMessage(e.target.value);
    
    // Auto-Resize Magic
    const textarea = textareaRef.current;
    if (textarea) {
      // Pehle height 'auto' set karo taaki shrink ho sake agar user backspace dabaye
      textarea.style.height = 'auto';
      // Ab scrollHeight (actual text height) ke hisaab se nayi height do, max 120px (approx 4-5 lines)
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
      
      // Message send hone ke baad box ki height wapas default kar do
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    // Agar user Enter dabaye (aur Shift NAHI dabaya ho), toh message send karo
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Agar user ne koi document upload nahi kiya hai toh input disable kar do
  const isInputDisabled = isLoading || (userDocuments && userDocuments.length === 0);

  return (
    <div className="p-4 bg-white dark:bg-[#09090b] border-t border-zinc-200 dark:border-zinc-800/50 transition-colors duration-300">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-end">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={isInputDisabled ? "Please upload a document first..." : "Ask a question about your documents... (Shift+Enter for new line)"}
          disabled={isInputDisabled}
          className="w-full bg-zinc-100 dark:bg-zinc-800/50 text-zinc-900 dark:text-zinc-100 placeholder-zinc-500 dark:placeholder-zinc-400 rounded-2xl pl-5 pr-14 py-3.5 focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700 resize-none overflow-y-auto custom-scrollbar transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
          rows={1}
          style={{ 
            minHeight: '52px', 
            maxHeight: '120px' // Yahan par max height set hai 4-5 lines ke liye
          }}
        />
        
        <button
          type="submit"
          disabled={!message.trim() || isInputDisabled}
          className="absolute right-2 bottom-1.5 p-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-xl hover:bg-zinc-800 dark:hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};

export default ChatInput;