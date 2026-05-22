import React, { useState } from 'react';
import { FileText, ChevronDown, BookOpen, Trash2 } from 'lucide-react';

const DocumentSelector = ({ userDocuments, selectedDocument, setSelectedDocument, handleDeleteDocument }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  if (userDocuments.length === 0) return null;

  return (
    <div className="relative">
      <label className="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest mb-3 block">
        Active Context
      </label>
      
      <button 
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="w-full flex items-center justify-between bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 text-zinc-800 dark:text-zinc-200 rounded-xl px-4 py-3 text-sm transition-all shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-zinc-200 dark:focus:ring-zinc-700"
      >
        <span className="flex items-center gap-2.5 overflow-hidden">
          {selectedDocument === 'all' ? <BookOpen className="w-4 h-4 shrink-0 text-zinc-400" /> : <FileText className="w-4 h-4 shrink-0 text-zinc-400" />}
          <span className="truncate font-medium">{selectedDocument === 'all' ? 'All Documents (Global)' : selectedDocument}</span>
        </span>
        <ChevronDown className={`w-4 h-4 shrink-0 text-zinc-400 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`} />
      </button>

      {isDropdownOpen && (
        <div className="absolute z-50 w-full mt-2 bg-white/95 dark:bg-zinc-800/95 backdrop-blur-md border border-zinc-200 dark:border-zinc-700/80 rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          <div 
            onClick={() => { setSelectedDocument('all'); setIsDropdownOpen(false); }}
            className={`flex items-center gap-3 p-3.5 cursor-pointer border-b border-zinc-100 dark:border-zinc-700/50 transition-colors ${selectedDocument === 'all' ? 'bg-zinc-50 dark:bg-zinc-700/50 font-medium' : 'hover:bg-zinc-50 dark:hover:bg-zinc-700/30 text-zinc-600 dark:text-zinc-300'}`}
          >
            <BookOpen className="w-4 h-4 text-zinc-400" />
            <span className="text-sm">All Documents (Global)</span>
          </div>

          <div className="max-h-60 overflow-y-auto custom-scrollbar">
            {userDocuments.map((doc, idx) => (
              <div 
                key={idx}
                onClick={() => { setSelectedDocument(doc); setIsDropdownOpen(false); }}
                className={`flex items-start justify-between p-3.5 cursor-pointer transition-colors group ${selectedDocument === doc ? 'bg-zinc-50 dark:bg-zinc-700/50 font-medium' : 'hover:bg-zinc-50 dark:hover:bg-zinc-700/30 text-zinc-600 dark:text-zinc-300'}`}
              >
                <div className="flex items-start gap-3 overflow-hidden pr-2">
                  <FileText className="w-4 h-4 shrink-0 mt-0.5 text-zinc-400" />
                  <span className="text-sm wrap-break-word leading-tight">{doc}</span>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); handleDeleteDocument(doc); setIsDropdownOpen(false); }}
                  className="p-1.5 rounded-md text-zinc-400 hover:text-red-600 hover:bg-red-50 dark:hover:text-red-400 dark:hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all"
                  title="Delete Document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {isDropdownOpen && <div className="fixed inset-0 z-40" onClick={() => setIsDropdownOpen(false)}></div>}
    </div>
  );
};

export default DocumentSelector;