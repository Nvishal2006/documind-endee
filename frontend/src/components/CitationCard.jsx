import React from 'react';
import { Bookmark } from 'lucide-react';

export default function CitationCard({ citationText }) {
  const parts = citationText.replace('[', '').replace(']', '').split(', ');
  const doc = parts[0]?.replace('Doc: ', '') || 'Unknown';
  const page = parts[1]?.replace('Page: ', '') || '?';
  
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-md text-xs font-medium cursor-help hover:bg-indigo-100 transition-colors" title={citationText}>
      <Bookmark className="w-3 h-3" />
      <span>{doc}</span>
      <span className="opacity-50">|</span>
      <span>p.{page}</span>
    </div>
  );
}
