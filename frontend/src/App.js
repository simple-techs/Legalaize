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
        </div>
      </Router>
    </ChatProvider>
  );
}
