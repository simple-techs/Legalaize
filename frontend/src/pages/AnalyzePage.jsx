import React, { useRef, useState } from 'react';
import { Upload, FileText, AlertTriangle, CheckCircle, X, Loader2 } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';
import ReactMarkdown from 'react-markdown';

export default function AnalyzePage() {
  const { uploadedDocuments, analyzeDocument, isLoading } = useChat();
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => analyzeDocument(file));
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => analyzeDocument(file));
    e.target.value = '';
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <h1 className="font-heading text-2xl text-primary mb-1">Document Analysis</h1>
      <p className="text-sm text-gray-500 mb-6">Upload legal documents for AI-powered analysis</p>

      {/* Upload area */}
      <div
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors cursor-pointer mb-6 ${
          dragActive ? 'border-accent bg-accent/5' : 'border-gray-200 hover:border-gray-300'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        {isLoading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 size={32} className="text-accent animate-spin" />
            <p className="text-sm text-gray-500">Analyzing document...</p>
          </div>
        ) : (
          <>
            <Upload size={32} className="mx-auto mb-3 text-gray-400" />
            <p className="text-sm font-medium text-gray-700 mb-1">Drop files here or click to upload</p>
            <p className="text-xs text-gray-400">Supports PDF, DOCX, JPG, PNG</p>
          </>
        )}
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
          multiple
          onChange={handleFileSelect}
        />
      </div>

      {/* Analyzed documents list */}
      {uploadedDocuments.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-heading text-lg text-primary">Analyzed Documents</h2>
          {uploadedDocuments.map((doc, i) => (
            <div key={i}>
              <button
                onClick={() => setSelectedDoc(selectedDoc === i ? null : i)}
                className="w-full flex items-center gap-3 bg-gray-50 hover:bg-gray-100 rounded-xl p-4 transition-colors text-left"
              >
                <FileText size={20} className="text-accent flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{doc.name}</p>
                  <p className="text-xs text-gray-400">
                    {new Date(doc.timestamp).toLocaleDateString()}
                  </p>
                </div>
                <CheckCircle size={16} className="text-green-500 flex-shrink-0" />
              </button>
              {selectedDoc === i && (
                <div className="mt-2 bg-white border border-gray-100 rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-medium text-sm text-primary">Analysis Results</h3>
                    <button onClick={() => setSelectedDoc(null)} className="text-gray-400 hover:text-gray-600">
                      <X size={16} />
                    </button>
                  </div>
                  <div className="chat-markdown text-sm text-gray-700 leading-relaxed">
                    <ReactMarkdown>{doc.analysis}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Supported formats */}
      <div className="mt-8 bg-amber-50 border border-amber-200 rounded-xl p-4">
        <div className="flex gap-2">
          <AlertTriangle size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-amber-800 mb-1">Supported Document Types</p>
            <p className="text-xs text-amber-700">
              Lease agreements, employment contracts, NDAs, business contracts, legal notices, partnership agreements, and more.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
