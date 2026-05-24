import React, { useState, useEffect } from 'react';
import { MapPin, Briefcase, ExternalLink, Phone, Star, Loader2, Image } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';

const SAMPLE_LAWYERS = [
  {
    id: 1,
    name: 'Sarah Mitchell',
    practice_area: 'Employment Law',
    jurisdiction: 'California',
    rating: 4.9,
    review_count: 0,
    phone: '',
    website: 'https://example.com',
    image_url: '',
    address: '',
    description: 'Specializing in wrongful termination, workplace discrimination, and employment contracts.',
  },
  {
    id: 2,
    name: 'James Rodriguez',
    practice_area: 'Tenant Rights',
    jurisdiction: 'New York',
    rating: 4.8,
    review_count: 0,
    phone: '',
    website: 'https://example.com',
    image_url: '',
    address: '',
    description: 'Expert in landlord-tenant disputes, eviction defense, and housing rights.',
  },
  {
    id: 3,
    name: 'Emily Chen',
    practice_area: 'Contract Law',
    jurisdiction: 'Texas',
    rating: 4.7,
    review_count: 0,
    phone: '',
    website: 'https://example.com',
    image_url: '',
    address: '',
    description: 'Focused on contract review, NDA enforcement, and business agreements.',
  },
  {
    id: 4,
    name: 'Michael Thompson',
    practice_area: 'Immigration Law',
    jurisdiction: 'Florida',
    rating: 4.9,
    review_count: 0,
    phone: '',
    website: 'https://example.com',
    image_url: '',
    address: '',
    description: 'Helping clients navigate visas, green cards, and immigration proceedings.',
  },
  {
    id: 5,
    name: 'Patricia Williams',
    practice_area: 'Family Law',
    jurisdiction: 'Illinois',
    rating: 4.6,
    review_count: 0,
    phone: '',
    website: 'https://example.com',
    image_url: '',
    address: '',
    description: 'Experienced in divorce, custody battles, and family mediation.',
  },
];

export default function LawyersPage() {
  const { matchLawyers } = useChat();
  const [lawyers, setLawyers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [source, setSource] = useState('');
  const [legalCategory, setLegalCategory] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');

  useEffect(() => {
    async function fetchLawyers() {
      setLoading(true);
      try {
        const result = await matchLawyers();
        if (result && result.lawyers && result.lawyers.length > 0) {
          setLawyers(result.lawyers);
          setSource(result.source || '');
          setLegalCategory(result.legal_category || '');
          setJurisdiction(result.jurisdiction || '');
        } else {
          setLawyers(SAMPLE_LAWYERS);
          setSource('sample');
        }
      } catch {
        setLawyers(SAMPLE_LAWYERS);
        setSource('sample');
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
      <p className="text-sm text-gray-500 mb-2">Matched attorneys based on your legal needs</p>

      {source === 'yelp' && (legalCategory || jurisdiction) && (
        <div className="bg-accent/5 border border-accent/20 rounded-xl px-3 py-2 mb-4">
          <p className="text-xs text-accent font-medium">
            Showing real attorneys
            {legalCategory ? ` for ${legalCategory}` : ''}
            {jurisdiction ? ` in ${jurisdiction}` : ''}
          </p>
          <p className="text-[10px] text-gray-400 mt-0.5">Powered by Yelp</p>
        </div>
      )}

      {source === 'sample' && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-3 py-2 mb-4">
          <p className="text-xs text-amber-700">
            Showing sample attorneys. Start a chat about your legal issue to get matched with real lawyers.
          </p>
        </div>
      )}

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
              <div className="flex gap-3">
                {lawyer.image_url ? (
                  <img
                    src={lawyer.image_url}
                    alt={lawyer.name}
                    className="w-14 h-14 rounded-xl object-cover flex-shrink-0"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-xl bg-gray-200 flex items-center justify-center flex-shrink-0">
                    <Image size={20} className="text-gray-400" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <h3 className="font-medium text-sm text-primary">{lawyer.name}</h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        <div className="flex items-center gap-0.5">
                          <Star size={12} className="text-amber-400 fill-amber-400" />
                          <span className="text-xs text-gray-500">{lawyer.rating}</span>
                        </div>
                        {lawyer.review_count > 0 && (
                          <span className="text-[10px] text-gray-400">({lawyer.review_count} reviews)</span>
                        )}
                      </div>
                    </div>
                    <span className="text-[10px] font-medium bg-accent/10 text-accent rounded-full px-2 py-0.5 flex-shrink-0">
                      {lawyer.practice_area.length > 30
                        ? lawyer.practice_area.split(',')[0]
                        : lawyer.practice_area}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mb-2 line-clamp-2">{lawyer.description}</p>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mb-2">
                    {lawyer.jurisdiction && (
                      <span className="flex items-center gap-1">
                        <MapPin size={12} />
                        {lawyer.jurisdiction}
                      </span>
                    )}
                    {lawyer.address && lawyer.address !== lawyer.jurisdiction && (
                      <span className="flex items-center gap-1 text-[10px] text-gray-400">
                        {lawyer.address}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {lawyer.phone && (
                      <a
                        href={`tel:${lawyer.phone}`}
                        className="flex items-center gap-1 bg-accent text-white text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-accent/90 transition-colors"
                      >
                        <Phone size={12} />
                        {lawyer.phone}
                      </a>
                    )}
                    {lawyer.website && (
                      <a
                        href={lawyer.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 bg-gray-200 text-gray-700 text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-gray-300 transition-colors"
                      >
                        <ExternalLink size={12} />
                        {lawyer.source === 'yelp' ? 'View on Yelp' : 'Website'}
                      </a>
                    )}
                    {!lawyer.phone && lawyer.contact && (
                      <a
                        href={`mailto:${lawyer.contact}`}
                        className="flex items-center gap-1 bg-accent text-white text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-accent/90 transition-colors"
                      >
                        <Briefcase size={12} />
                        Contact
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
