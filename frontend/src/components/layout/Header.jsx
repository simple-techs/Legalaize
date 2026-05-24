import React, { useState } from 'react';
import { Menu, X, MessageSquare, FileText, Scale, BookTemplate, Home } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: 'Chat', path: '/', icon: MessageSquare },
    { label: 'Document Analysis', path: '/analyze', icon: FileText },
    { label: 'Legal Brief', path: '/brief', icon: Scale },
    { label: 'Find a Lawyer', path: '/lawyers', icon: Home },
    { label: 'Templates', path: '/templates', icon: BookTemplate },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto flex items-center justify-between px-4 h-14">
          <button
            onClick={() => navigate('/')}
            className="font-heading text-2xl text-primary tracking-tight"
          >
            Legalaize
          </button>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Menu"
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </header>

      {/* Mobile menu overlay */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 bg-black/30" onClick={() => setMenuOpen(false)}>
          <div
            className="absolute right-0 top-0 h-full w-72 bg-white shadow-xl p-6 animate-in slide-in-from-right duration-300"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-8">
              <span className="font-heading text-xl text-primary">Menu</span>
              <button onClick={() => setMenuOpen(false)} className="p-1 rounded hover:bg-gray-100">
                <X size={20} />
              </button>
            </div>
            <nav className="space-y-1">
              {navItems.map(item => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <button
                    key={item.path}
                    onClick={() => { navigate(item.path); setMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors ${
                      isActive
                        ? 'bg-primary text-white'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon size={18} />
                    <span className="font-medium text-sm">{item.label}</span>
                  </button>
                );
              })}
            </nav>
            <div className="absolute bottom-6 left-6 right-6">
              <p className="text-xs text-gray-400 text-center">
                Legalaize is an AI lawyer, not a licensed lawyer.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
