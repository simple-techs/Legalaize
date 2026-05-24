import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'assistant',
      content: 'Hey, How are you? How can I help?',
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [legalBrief, setLegalBrief] = useState(null);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);

  const sendMessage = useCallback(async (content, attachments = []) => {
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      attachments,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('message', content);

      const history = [...messages, userMessage].map(m => ({
        role: m.role,
        content: m.content,
      }));
      formData.append('history', JSON.stringify(history));

      if (attachments.length > 0) {
        attachments.forEach(file => {
          formData.append('files', file);
        });
      }

      const response = await axios.post('/api/chat', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (response.data.legal_brief) {
        setLegalBrief(response.data.legal_brief);
      }
    } catch (error) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error.response?.status === 429
          ? "I'm currently experiencing high demand. Please try again in a moment."
          : "I apologize, but I'm having trouble processing your request. Please try again.",
        timestamp: new Date(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [messages]);

  const analyzeDocument = useCallback(async (file) => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setUploadedDocuments(prev => [...prev, {
        name: file.name,
        analysis: response.data.analysis,
        timestamp: new Date(),
      }]);

      const assistantMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.data.analysis,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: "I had trouble analyzing that document. Please ensure it's a supported format (PDF, DOCX, JPG, PNG) and try again.",
        timestamp: new Date(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const generateBrief = useCallback(async () => {
    setIsLoading(true);
    try {
      const history = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));

      const response = await axios.post('/api/brief', { history });
      setLegalBrief(response.data.brief);
      return response.data.brief;
    } catch (error) {
      console.error('Failed to generate brief:', error);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [messages]);

  const matchLawyers = useCallback(async (userLocation = '') => {
    try {
      const history = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));

      const payload = { history };
      if (userLocation) {
        payload.location = userLocation;
      }

      const response = await axios.post('/api/match', payload);
      return {
        lawyers: response.data.lawyers || [],
        legal_category: response.data.legal_category || '',
        jurisdiction: response.data.jurisdiction || '',
        search_location: response.data.search_location || '',
        source: response.data.source || '',
      };
    } catch (error) {
      console.error('Failed to match lawyers:', error);
      return { lawyers: [], source: 'error' };
    }
  }, [messages]);

  const clearChat = useCallback(() => {
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: 'Hey, How are you? How can I help?',
        timestamp: new Date(),
      },
    ]);
    setLegalBrief(null);
    setUploadedDocuments([]);
  }, []);

  return (
    <ChatContext.Provider value={{
      messages,
      isLoading,
      legalBrief,
      uploadedDocuments,
      sendMessage,
      analyzeDocument,
      generateBrief,
      matchLawyers,
      clearChat,
      setLegalBrief,
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
