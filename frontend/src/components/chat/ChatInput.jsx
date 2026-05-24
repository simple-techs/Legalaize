import React, { useState, useRef } from 'react';
import { Send, Plus, X } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';

export default function ChatInput() {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState([]);
  const fileInputRef = useRef(null);
  const { sendMessage, analyzeDocument, isLoading } = useChat();

  const handleSubmit = (e) => {
    e.preventDefault();
    if ((!input.trim() && attachments.length === 0) || isLoading) return;

    if (attachments.length > 0 && !input.trim()) {
      attachments.forEach(file => analyzeDocument(file));
    } else {
      sendMessage(input.trim(), attachments);
    }
    setInput('');
    setAttachments([]);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setAttachments(prev => [...prev, ...files]);
    e.target.value = '';
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t border-gray-100 bg-white px-4 py-3">
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {attachments.map((file, i) => (
            <div key={i} className="flex items-center gap-1.5 bg-gray-100 rounded-lg px-2.5 py-1.5 text-xs text-gray-700">
              <span className="max-w-[120px] truncate">{file.name}</span>
              <button onClick={() => removeAttachment(i)} className="hover:text-red-500">
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
          aria-label="Upload document"
        >
          <Plus size={20} className="text-gray-600" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
          multiple
          onChange={handleFileSelect}
        />
        <div className="flex-1 relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Chat with Legalaize"
            className="w-full bg-gray-100 rounded-full px-4 py-2.5 text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
            disabled={isLoading}
          />
        </div>
        <button
          type="submit"
          disabled={(!input.trim() && attachments.length === 0) || isLoading}
          className="flex-shrink-0 w-10 h-10 rounded-full bg-primary hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          aria-label="Send message"
        >
          <Send size={16} className="text-white" />
        </button>
      </form>
    </div>
  );
}
