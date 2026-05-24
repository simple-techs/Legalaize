import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Lightbulb, FileText, Users, Info } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';
import ChatMessage from '@/components/chat/ChatMessage';
import TypingIndicator from '@/components/chat/TypingIndicator';
import ChatInput from '@/components/chat/ChatInput';

const capabilities = [
  { label: 'Search laws', icon: Search },
  { label: 'Give legal suggestions', icon: Lightbulb },
  { label: 'Generate legal docs', icon: FileText },
  { label: 'Suggest lawyers', icon: Users },
];

export default function ChatPage() {
  const { messages, isLoading, sendMessage, generateBrief } = useChat();
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const isInitial = messages.length <= 1;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleCapabilityClick = (label) => {
    const prompts = {
      'Search laws': 'What laws apply to my situation?',
      'Give legal suggestions': 'I need legal advice about a situation I\'m facing.',
      'Generate legal docs': 'I need help generating a legal document.',
      'Suggest lawyers': 'Can you help me find a lawyer?',
    };
    sendMessage(prompts[label] || label);
  };

  const handleGenerateBrief = async () => {
    const brief = await generateBrief();
    if (brief) navigate('/brief');
  };

  const handleMatchLawyers = async () => {
    navigate('/lawyers');
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Chat messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-hide">
        {isInitial && (
          <div className="mb-6">
            {/* Capabilities card */}
            <div className="bg-gray-50 rounded-2xl p-5 mb-4">
              <div className="flex flex-wrap items-center gap-3">
                <p className="text-sm text-gray-500 font-medium mr-auto">Some things I can do</p>
                <div className="flex flex-wrap gap-2 w-full">
                  {capabilities.map((cap) => (
                    <button
                      key={cap.label}
                      onClick={() => handleCapabilityClick(cap.label)}
                      className="flex-1 min-w-[140px] bg-gray-200/70 hover:bg-gray-300/70 text-gray-700 text-xs font-medium rounded-lg px-3 py-2.5 transition-colors text-center"
                    >
                      {cap.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom action buttons */}
      <div className="px-4 pb-1 flex items-center gap-2">
        <button
          onClick={handleMatchLawyers}
          className="flex items-center gap-1.5 bg-accent text-white text-xs font-semibold rounded-full px-4 py-2 hover:bg-accent/90 transition-colors"
        >
          Match
          <Info size={12} className="opacity-70" />
        </button>
        <button
          onClick={handleGenerateBrief}
          className="flex items-center gap-1.5 bg-accent text-white text-xs font-semibold rounded-full px-4 py-2 hover:bg-accent/90 transition-colors"
        >
          Generate
          <Info size={12} className="opacity-70" />
        </button>
      </div>

      <ChatInput />

      {/* Legal disclaimer */}
      <div className="px-4 py-3 text-center">
        <p className="text-[10px] text-gray-400 leading-relaxed">
          Always discuss Legalaize output with an attorney. Legalaize is an AI lawyer, not a licensed lawyer, does not practice law.
          Legalaize is the first AI Lawyer working with human Lawyers licensed to practice law in your preferred area. By using
          Legalaize, you agree to our{' '}
          <button className="underline hover:text-gray-600">Terms of Service</button>
          {' '}&{' '}
          <button className="underline hover:text-gray-600">Privacy Policy</button>.
        </p>
      </div>
    </div>
  );
}
