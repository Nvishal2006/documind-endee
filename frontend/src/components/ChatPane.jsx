import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import CitationCard from './CitationCard';
import { fetchSSE } from '../hooks/useSSE';

export default function ChatPane() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! I am DocuMind. Upload some documents on the left, then ask me anything about them.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setIsLoading(true);

    const botMessageIndex = messages.length + 1;
    setMessages(prev => [...prev, { role: 'assistant', text: '', citations: '' }]);

    try {
      await fetchSSE('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage })
      }, (data) => {
        if (data.citations) {
            setMessages(prev => {
                const newMsg = [...prev];
                newMsg[botMessageIndex].citations = data.citations;
                return newMsg;
            });
        }
        if (data.content) {
            setMessages(prev => {
                const newMsg = [...prev];
                newMsg[botMessageIndex].text += data.content;
                return newMsg;
            });
        }
        if (data.done) {
            setIsLoading(false);
        }
      });
    } catch (error) {
      console.error(error);
      setIsLoading(false);
      setMessages(prev => {
          const newMsg = [...prev];
          newMsg[botMessageIndex].text += "\n\n**Error connecting to server.**";
          return newMsg;
      });
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 shadow-inner overflow-hidden">
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 p-4 sticky top-0 z-20 shadow-sm flex items-center">
        <Bot className="w-6 h-6 text-indigo-600 mr-2" />
        <h1 className="text-lg font-semibold text-slate-800">DocuMind Chat</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-indigo-600 ml-3' : 'bg-white border border-slate-200 shadow-sm mr-3'}`}>
                {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-indigo-600" />}
              </div>

              <div className={`px-5 py-3.5 rounded-2xl shadow-sm text-sm leading-relaxed whitespace-pre-wrap
                ${msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-tr-none' 
                  : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none relative'}`}>
                
                {msg.text}
                
                {msg.role === 'assistant' && msg.text === '' && isLoading && i === messages.length - 1 && (
                  <div className="flex items-center gap-2 h-5 mt-1">
                    <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                    <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                  </div>
                )}

                {msg.citations && (
                  <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
                    {msg.citations.split(' | ').filter(Boolean).map((cit, cidx) => (
                      <CitationCard key={cidx} citationText={cit} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white/90 backdrop-blur-md border-t border-slate-200">
        <form onSubmit={handleSubmit} className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask a question about your documents..."
            className="w-full pl-5 pr-14 py-4 rounded-full border border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all shadow-sm disabled:bg-slate-50 disabled:cursor-not-allowed"
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="absolute right-2 p-2.5 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:bg-slate-300 disabled:text-slate-500 transition-all shadow-md"
          >
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5 ml-[2px]" />}
          </button>
        </form>
        <p className="text-center text-xs text-slate-400 mt-2">DocuMind AI responses are generated based on exact retrieved excerpts.</p>
      </div>
    </div>
  );
}
