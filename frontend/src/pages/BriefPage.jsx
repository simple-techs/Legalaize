import React, { useState, useEffect } from 'react';
import { Download, Share2, Send, Loader2, Edit3, Save } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';
import ReactMarkdown from 'react-markdown';

export default function BriefPage() {
  const { legalBrief, generateBrief, isLoading, setLegalBrief } = useChat();
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [shared, setShared] = useState(false);

  useEffect(() => {
    if (!legalBrief) {
      generateBrief();
    }
  }, [legalBrief, generateBrief]);

  const handleEdit = () => {
    setEditContent(legalBrief || '');
    setIsEditing(true);
  };

  const handleSave = () => {
    setLegalBrief(editContent);
    setIsEditing(false);
  };

  const handleDownload = () => {
    if (!legalBrief) return;
    const blob = new Blob([legalBrief], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'legal-brief.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    if (!legalBrief) return;
    try {
      await navigator.clipboard.writeText(legalBrief);
      setShared(true);
      setTimeout(() => setShared(false), 2000);
    } catch {
      const textArea = document.createElement('textarea');
      textArea.value = legalBrief;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setShared(true);
      setTimeout(() => setShared(false), 2000);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-heading text-2xl text-primary mb-1">Legal Brief</h1>
          <p className="text-sm text-gray-500">AI-generated summary of your legal situation</p>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={isEditing ? handleSave : handleEdit}
          className="flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg px-3 py-2 transition-colors"
        >
          {isEditing ? <Save size={14} /> : <Edit3 size={14} />}
          {isEditing ? 'Save' : 'Edit'}
        </button>
        <button
          onClick={handleDownload}
          disabled={!legalBrief}
          className="flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg px-3 py-2 transition-colors disabled:opacity-40"
        >
          <Download size={14} />
          Download
        </button>
        <button
          onClick={handleShare}
          disabled={!legalBrief}
          className="flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg px-3 py-2 transition-colors disabled:opacity-40"
        >
          <Share2 size={14} />
          {shared ? 'Copied!' : 'Share'}
        </button>
        <button
          disabled={!legalBrief}
          className="flex items-center gap-1.5 bg-accent hover:bg-accent/90 text-white text-xs font-medium rounded-lg px-3 py-2 transition-colors disabled:opacity-40"
        >
          <Send size={14} />
          Send to Lawyer
        </button>
      </div>

      {/* Brief content */}
      <div className="bg-gray-50 rounded-2xl p-6 min-h-[300px]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3">
            <Loader2 size={28} className="text-accent animate-spin" />
            <p className="text-sm text-gray-500">Generating your legal brief...</p>
          </div>
        ) : isEditing ? (
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full h-96 bg-white rounded-xl p-4 text-sm text-gray-700 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-accent/20 resize-none font-mono"
          />
        ) : legalBrief ? (
          <div className="chat-markdown text-sm text-gray-700 leading-relaxed">
            <ReactMarkdown>{legalBrief}</ReactMarkdown>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <p className="text-sm text-gray-500 mb-2">No legal brief generated yet.</p>
            <p className="text-xs text-gray-400">
              Start a conversation in the chat to generate your legal brief.
            </p>
            <button
              onClick={generateBrief}
              className="mt-4 bg-accent text-white text-xs font-medium rounded-lg px-4 py-2 hover:bg-accent/90 transition-colors"
            >
              Generate Brief
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
