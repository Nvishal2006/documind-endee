import React, { useCallback, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { UploadCloud, FileText, Trash2, CheckCircle, Clock, AlertCircle } from 'lucide-react';

export default function DocLibrary() {
  const queryClient = useQueryClient();
  const [isDragActive, setIsDragActive] = useState(false);

  // Queries
  const { data: docs = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await fetch('/api/documents');
      return res.json();
    },
    refetchInterval: 3000
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/api/health');
      return res.json();
    },
    refetchInterval: 10000
  });

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries(['documents'])
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      await fetch(`/api/document/${id}`, { method: 'DELETE' });
    },
    onSuccess: () => queryClient.invalidateQueries(['documents'])
  });

  // Handlers
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadMutation.mutate(e.dataTransfer.files[0]);
    }
  }, [uploadMutation]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadMutation.mutate(e.target.files[0]);
    }
  };

  return (
    <div className="flex flex-col h-full h-full p-4 gap-4">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">DocuMind Library</h2>
      </div>

      {health?.endee?.status !== 'ok' && (
        <div className="text-xs p-2 bg-red-50 text-red-600 rounded-md border border-red-100 flex items-center gap-2">
          <AlertCircle size={14} /> Endee Vector DB is offline or unreachable
        </div>
      )}

      {/* Upload Area */}
      <div 
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center transition-colors cursor-pointer
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:bg-slate-100'}`}
        onClick={() => document.getElementById('fileUpload').click()}
      >
        <UploadCloud className={`w-8 h-8 mb-2 ${isDragActive ? 'text-blue-500' : 'text-slate-400'}`} />
        <p className="text-sm font-medium text-slate-600">Drag & drop files here</p>
        <p className="text-xs text-slate-400 mt-1">PDF, DOCX, TXT up to 50MB</p>
        <input 
          id="fileUpload" 
          type="file" 
          className="hidden" 
          onChange={handleFileInput} 
          accept=".pdf,.docx,.txt"
        />
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto pr-1">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-2">Your Documents</h3>
        <div className="space-y-2">
          {docs.length === 0 && (
            <p className="text-sm text-slate-400 text-center py-4">No documents uploaded yet.</p>
          )}
          {docs.map(doc => (
            <div key={doc.id} className="flex items-center p-3 bg-white border border-slate-200 rounded-lg shadow-sm hover:shadow transition-shadow group">
              <FileText className="w-8 h-8 p-1.5 bg-blue-50 text-blue-600 rounded-md shrink-0" />
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-700 truncate">{doc.filename}</p>
                <div className="flex items-center mt-1">
                  {doc.status === 'ready' ? (
                    <span className="flex items-center text-[10px] uppercase font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full">
                      <CheckCircle className="w-3 h-3 mr-1" /> Ready
                    </span>
                  ) : doc.status === 'processing' ? (
                    <span className="flex items-center text-[10px] uppercase font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full">
                      <Clock className="w-3 h-3 mr-1 animate-spin" /> Processing
                    </span>
                  ) : (
                    <span className="flex items-center text-[10px] uppercase font-bold text-red-600 bg-red-50 px-1.5 py-0.5 rounded-full">
                      <AlertCircle className="w-3 h-3 mr-1" /> Error
                    </span>
                  )}
                </div>
              </div>
              <button 
                onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(doc.id); }}
                className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-md opacity-0 group-hover:opacity-100 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
