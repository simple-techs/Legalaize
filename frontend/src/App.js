import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ChatProvider } from '@/contexts/ChatContext';
import Header from '@/components/layout/Header';
import ChatPage from '@/pages/ChatPage';
import AnalyzePage from '@/pages/AnalyzePage';
import BriefPage from '@/pages/BriefPage';
import LawyersPage from '@/pages/LawyersPage';
import TemplatesPage from '@/pages/TemplatesPage';

export default function App() {
  return (
    <ChatProvider>
      <Router>
        <div className="h-screen flex flex-col bg-white max-w-4xl mx-auto sm:border-x sm:border-gray-100">
          <Header />
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/brief" element={<BriefPage />} />
            <Route path="/lawyers" element={<LawyersPage />} />
            <Route path="/templates" element={<TemplatesPage />} />
          </Routes>
          <div className="px-4 py-3 text-center flex-shrink-0">
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
      </Router>
    </ChatProvider>
  );
}
