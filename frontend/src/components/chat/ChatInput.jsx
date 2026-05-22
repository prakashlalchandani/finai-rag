import React, { useState } from 'react';
import { Send } from 'lucide-react';

const ChatInput = ({ onSendMessage, isLoading, userDocuments, selectedDocument }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput('');
  };

  const isDisabled = isLoading || userDocuments.length === 0;
  const placeholderText = userDocuments.length > 0 
    ? `Ask a question about ${selectedDocument === 'all' ? 'your documents' : selectedDocument}...` 
    : "Please upload a document first...";

  return (
    <div className="p-4 md:p-6 bg-transparent transition-colors duration-300 flex justify-center">
      <form 
        onSubmit={handleSubmit} 
        className={`w-full max-w-4xl relative flex items-end p-2 bg-white dark:bg-zinc-800 border transition-all duration-300 rounded-3xl shadow-sm
          ${isDisabled ? 'border-zinc-200 dark:border-zinc-700 opacity-70' : 'border-zinc-300 dark:border-zinc-600 focus-within:ring-2 focus-within:ring-zinc-200 dark:focus-within:ring-zinc-700 hover:shadow-md'}
        `}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder={placeholderText}
          disabled={isDisabled}
          rows={1}
          className="w-full max-h-32 bg-transparent text-zinc-800 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 px-4 py-3 focus:outline-none resize-none custom-scrollbar"
        />
        <button
          type="submit"
          disabled={isDisabled || !input.trim()}
          className="m-1 p-3 flex-shrink-0 flex items-center justify-center bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-full hover:bg-zinc-700 dark:hover:bg-white transition-all duration-200 disabled:opacity-30 disabled:hover:bg-zinc-900 dark:disabled:hover:bg-zinc-100 transform active:scale-95"
        >
          <Send className="w-5 h-5 ml-0.5" />
        </button>
      </form>
    </div>
  );
};

export default ChatInput;