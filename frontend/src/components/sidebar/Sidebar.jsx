import React, { useRef } from 'react';
import { FileText, Sun, Moon, LogOut, UploadCloud, Loader2 } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import DocumentSelector from './DocumentSelector';

const Sidebar = ({ isUploading, handleFileUpload, userDocuments, selectedDocument, setSelectedDocument, handleDeleteDocument }) => {
  const { isDarkMode, toggleDarkMode, logout } = useAppContext();
  const fileInputRef = useRef(null);

  return (
    <div className="w-72 md:w-80 bg-zinc-50 dark:bg-[#18181b] border-r border-zinc-200 dark:border-zinc-800/50 flex flex-col transition-colors duration-300">
      
      {/* Header */}
      <div className="p-5 flex justify-between items-center">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-zinc-900 dark:bg-white rounded-lg flex items-center justify-center shadow-sm">
            <FileText className="w-4 h-4 text-white dark:text-zinc-900" />
          </div>
          <h1 className="text-[17px] font-semibold text-zinc-800 dark:text-zinc-100 tracking-tight">
            FinAudit AI<span className="text-zinc-400 dark:text-zinc-500 font-normal"></span>
          </h1>
        </div>
        
        <div className="flex gap-1">
          <button onClick={toggleDarkMode} className="p-2 rounded-md hover:bg-zinc-200/50 dark:hover:bg-zinc-800 text-zinc-500 transition-colors">
            {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button onClick={logout} className="p-2 rounded-md hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 text-zinc-500 transition-colors" title="Logout">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Area */}
      <div className="px-5 py-4 flex-1 overflow-y-auto custom-scrollbar">
        <h2 className="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest mb-4">Workspace</h2>
        
        <button 
          onClick={() => fileInputRef.current.click()} 
          disabled={isUploading} 
          className="w-full flex items-center justify-center gap-2 bg-white dark:bg-zinc-800/50 text-zinc-700 dark:text-zinc-300 border border-dashed border-zinc-300 dark:border-zinc-700 rounded-xl py-3 px-4 hover:bg-zinc-100 hover:border-zinc-400 dark:hover:bg-zinc-800 dark:hover:border-zinc-500 disabled:opacity-50 transition-all duration-200"
        >
          {isUploading ? <Loader2 className="w-4 h-4 animate-spin text-zinc-500" /> : <UploadCloud className="w-4 h-4 text-zinc-500" />}
          <span className="text-sm font-medium">{isUploading ? 'Indexing...' : 'Upload Document'}</span>
        </button>
        <input type="file" accept=".pdf, .docx, .txt" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />

        <div className="mt-8">
          <DocumentSelector 
            userDocuments={userDocuments} 
            selectedDocument={selectedDocument} 
            setSelectedDocument={setSelectedDocument} 
            handleDeleteDocument={handleDeleteDocument} 
          />
        </div>
      </div>
    </div>
  );
};

export default Sidebar;