import React, { useState, useEffect } from 'react';
import { MapPin, Briefcase, ExternalLink, Send, Loader2, Star } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';

const SAMPLE_LAWYERS = [
  {
    id: 1,
    name: 'Sarah Mitchell',
    practice_area: 'Employment Law',
    jurisdiction: 'California',
    rating: 4.9,
    contact: 'sarah.mitchell@lawfirm.com',
    website: 'https://example.com',
    description: 'Specializing in wrongful termination, workplace discrimination, and employment contracts.',
  },
  {
    id: 2,
    name: 'James Rodriguez',
    practice_area: 'Tenant Rights',
    jurisdiction: 'New York',
    rating: 4.8,
    contact: 'j.rodriguez@lawfirm.com',
    website: 'https://example.com',
    description: 'Expert in landlord-tenant disputes, eviction defense, and housing rights.',
  },
  {
    id: 3,
    name: 'Emily Chen',
    practice_area: 'Contract Law',
    jurisdiction: 'Texas',
    rating: 4.7,
    contact: 'e.chen@lawfirm.com',
    website: 'https://example.com',
    description: 'Focused on contract review, NDA enforcement, and business agreements.',
  },
  {
    id: 4,
    name: 'Michael Thompson',
    practice_area: 'Immigration Law',
    jurisdiction: 'Florida',
    rating: 4.9,
    contact: 'm.thompson@lawfirm.com',
    website: 'https://example.com',
    description: 'Helping clients navigate visas, green cards, and immigration proceedings.',
  },
  {
    id: 5,
    name: 'Patricia Williams',
    practice_area: 'Family Law',
    jurisdiction: 'Illinois',
    rating: 4.6,
    contact: 'p.williams@lawfirm.com',
    website: 'https://example.com',
    description: 'Experienced in divorce, custody battles, and family mediation.',
  },
];

export default function LawyersPage() {
  const { matchLawyers } = useChat();
  const [lawyers, setLawyers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');

  useEffect(() => {
    async function fetchLawyers() {
      setLoading(true);
      try {
        const matched = await matchLawyers();
        setLawyers(matched && matched.length > 0 ? matched : SAMPLE_LAWYERS);
      } catch {
        setLawyers(SAMPLE_LAWYERS);
      }
      setLoading(false);
    }
    fetchLawyers();
  }, [matchLawyers]);

  const practiceAreas = ['All', ...new Set(lawyers.map(l => l.practice_area))];
  const filtered = filter === 'All' ? lawyers : lawyers.filter(l => l.practice_area === filter);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <h1 className="font-heading text-2xl text-primary mb-1">Find a Lawyer</h1>
      <p className="text-sm text-gray-500 mb-6">Matched attorneys based on your legal needs</p>

      {/* Filter chips */}
      <div className="flex gap-2 overflow-x-auto pb-3 scrollbar-hide mb-4">
        {practiceAreas.map(area => (
          <button
            key={area}
            onClick={() => setFilter(area)}
            className={`whitespace-nowrap text-xs font-medium rounded-full px-3 py-1.5 transition-colors ${
              filter === area
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {area}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-64 gap-3">
          <Loader2 size={28} className="text-accent animate-spin" />
          <p className="text-sm text-gray-500">Finding matching attorneys...</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(lawyer => (
            <div key={lawyer.id} className="bg-gray-50 rounded-2xl p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-medium text-sm text-primary">{lawyer.name}</h3>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Star size={12} className="text-amber-400 fill-amber-400" />
                    <span className="text-xs text-gray-500">{lawyer.rating}</span>
                  </div>
                </div>
                <span className="text-[10px] font-medium bg-accent/10 text-accent rounded-full px-2 py-0.5">
                  {lawyer.practice_area}
                </span>
              </div>
              <p className="text-xs text-gray-600 mb-3">{lawyer.description}</p>
              <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                <span className="flex items-center gap-1">
                  <MapPin size={12} />
                  {lawyer.jurisdiction}
                </span>
                <span className="flex items-center gap-1">
                  <Briefcase size={12} />
                  {lawyer.practice_area}
                </span>
              </div>
              <div className="flex gap-2">
                <a
                  href={`mailto:${lawyer.contact}`}
                  className="flex items-center gap-1 bg-accent text-white text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-accent/90 transition-colors"
                >
                  <Send size={12} />
                  Contact
                </a>
                {lawyer.website && (
                  <a
                    href={lawyer.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 bg-gray-200 text-gray-700 text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-gray-300 transition-colors"
                  >
                    <ExternalLink size={12} />
                    Website
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
