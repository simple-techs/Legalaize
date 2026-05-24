import React, { useState } from 'react';
import { FileText, Download, Search, Eye, Loader2 } from 'lucide-react';
import axios from 'axios';

const TEMPLATES = [
  {
    id: 'nda',
    name: 'Non-Disclosure Agreement',
    category: 'Business',
    description: 'Protect confidential information shared between parties.',
  },
  {
    id: 'employment',
    name: 'Employment Agreement',
    category: 'Employment',
    description: 'Standard employment contract covering terms, compensation, and responsibilities.',
  },
  {
    id: 'lease',
    name: 'Lease Agreement',
    category: 'Real Estate',
    description: 'Residential or commercial lease agreement between landlord and tenant.',
  },
  {
    id: 'demand',
    name: 'Demand Letter',
    category: 'General',
    description: 'Formal letter requesting payment, action, or resolution of a dispute.',
  },
  {
    id: 'cease',
    name: 'Cease & Desist',
    category: 'General',
    description: 'Letter demanding the recipient stop a specific activity.',
  },
  {
    id: 'contractor',
    name: 'Contractor Agreement',
    category: 'Business',
    description: 'Independent contractor agreement covering scope of work and payment terms.',
  },
  {
    id: 'service',
    name: 'Service Agreement',
    category: 'Business',
    description: 'Agreement between a service provider and client outlining terms of service.',
  },
  {
    id: 'partnership',
    name: 'Partnership Agreement',
    category: 'Business',
    description: 'Agreement defining the terms and obligations of business partners.',
  },
];

export default function TemplatesPage() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [generating, setGenerating] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewContent, setPreviewContent] = useState('');

  const categories = ['All', ...new Set(TEMPLATES.map(t => t.category))];

  const filtered = TEMPLATES.filter(t => {
    const matchesSearch = t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === 'All' || t.category === category;
    return matchesSearch && matchesCategory;
  });

  const handleGenerate = async (template) => {
    setGenerating(template.id);
    try {
      const response = await axios.post('/api/template', {
        template_id: template.id,
        template_name: template.name,
      });
      const content = response.data.content;
      const blob = new Blob([content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${template.name.replace(/\s+/g, '_')}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to generate template:', error);
    }
    setGenerating(null);
  };

  const handlePreview = async (template) => {
    if (preview === template.id) {
      setPreview(null);
      return;
    }
    setPreview(template.id);
    setPreviewContent('Loading preview...');
    try {
      const response = await axios.post('/api/template', {
        template_id: template.id,
        template_name: template.name,
      });
      setPreviewContent(response.data.content);
    } catch {
      setPreviewContent('Failed to load preview. Please try again.');
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <h1 className="font-heading text-2xl text-primary mb-1">Legal Templates</h1>
      <p className="text-sm text-gray-500 mb-6">Pre-built templates you can customize and download</p>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search templates..."
          className="w-full bg-gray-100 rounded-xl pl-9 pr-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      {/* Category filter */}
      <div className="flex gap-2 overflow-x-auto pb-3 scrollbar-hide mb-4">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`whitespace-nowrap text-xs font-medium rounded-full px-3 py-1.5 transition-colors ${
              category === cat
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Templates grid */}
      <div className="space-y-3">
        {filtered.map(template => (
          <div key={template.id}>
            <div className="bg-gray-50 rounded-2xl p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0">
                  <FileText size={18} className="text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm text-primary">{template.name}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">{template.description}</p>
                  <span className="inline-block text-[10px] font-medium bg-gray-200 text-gray-600 rounded-full px-2 py-0.5 mt-2">
                    {template.category}
                  </span>
                </div>
              </div>
              <div className="flex gap-2 mt-3 pl-[52px]">
                <button
                  onClick={() => handlePreview(template)}
                  className="flex items-center gap-1 bg-gray-200 text-gray-700 text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-gray-300 transition-colors"
                >
                  <Eye size={12} />
                  Preview
                </button>
                <button
                  onClick={() => handleGenerate(template)}
                  disabled={generating === template.id}
                  className="flex items-center gap-1 bg-accent text-white text-xs font-medium rounded-lg px-3 py-1.5 hover:bg-accent/90 transition-colors disabled:opacity-50"
                >
                  {generating === template.id ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Download size={12} />
                  )}
                  Generate
                </button>
              </div>
            </div>
            {preview === template.id && (
              <div className="mt-2 bg-white border border-gray-100 rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-y-auto">
                  {previewContent}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
