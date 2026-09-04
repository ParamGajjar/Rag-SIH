import React, { useState } from 'react';
import { Search, Mic, ArrowUp, ChevronDown, HelpCircle, User, FileText, CheckCircle, FlaskConical, Building2, Shield, Info, ExternalLink } from 'lucide-react';

function App() {
  const [query, setQuery] = useState('');
  const [isChatActive, setIsChatActive] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    // Switch to chat view
    setIsChatActive(true);
    
    // Add user message
    const userMsg = { type: 'user', text: query };
    
    // Add fake AI response
    const aiMsg = { 
      type: 'ai', 
      text: 'Based on your query, Indian Standard IS 14489:2018 is applicable. It covers the code of practice on occupational safety and health audit. To proceed with certification, you will need to register on the e-BIS portal and submit the required documentation along with the test reports from a BIS-recognized laboratory.',
      references: [
        { title: 'IS 14489:2018 - Code of Practice on Occupational Safety', link: '#' },
        { title: 'e-BIS Portal - Certification Guidelines', link: '#' }
      ]
    };
    
    setMessages([...messages, userMsg, aiMsg]);
    setQuery('');
  };

  const handleCardClick = (text) => {
    setQuery(text);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Navbar */}
      <nav className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 text-white p-2 rounded-lg">
            <Shield size={24} />
          </div>
          <h1 className="text-xl font-bold text-slate-800">StandardAssist IN</h1>
        </div>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
          <a href="#" className="hover:text-blue-600 transition-colors">Home</a>
          <a href="#" className="hover:text-blue-600 transition-colors">Find Standards</a>
          <a href="#" className="hover:text-blue-600 transition-colors">Certificates</a>
          <a href="#" className="hover:text-blue-600 transition-colors">Labs</a>
        </div>
        
        <div className="flex items-center gap-4">
          <button className="text-slate-500 hover:text-slate-700">
            <HelpCircle size={20} />
          </button>
          <div className="h-8 w-8 bg-slate-200 rounded-full flex items-center justify-center text-slate-600">
            <User size={18} />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 pt-12 pb-24">
        
        {!isChatActive ? (
          // Initial Screen
          <div className="flex flex-col items-center animate-fade-in text-center mt-10">
            <div className="bg-blue-100 text-blue-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-6 inline-flex items-center gap-2">
              <Info size={16} /> AI-Powered Indian Standards Guide
            </div>
            <h2 className="text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">How can I assist you with standards?</h2>
            <p className="text-lg text-slate-600 mb-10 max-w-2xl">
              Get intelligent guidance on Indian Standards, product certification, testing requirements, and regulatory compliance.
            </p>
            
            {/* Search Bar - Initial */}
            <form onSubmit={handleSearch} className="w-full max-w-2xl relative mb-16 shadow-lg shadow-slate-200 rounded-2xl group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500" size={20} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Describe your product or ask about a standard..."
                className="w-full pl-12 pr-16 py-4 rounded-2xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-lg shadow-sm transition-all"
              />
              <button 
                type="submit"
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-md disabled:opacity-50"
                disabled={!query.trim()}
              >
                <ArrowUp size={20} />
              </button>
            </form>

            {/* Quick Actions Grid */}
            <div className="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-left">
              <button onClick={() => handleCardClick("Find standards for electronic toys")} className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all group text-left">
                <FileText className="text-blue-500 mb-3 group-hover:scale-110 transition-transform" size={24} />
                <h3 className="font-semibold text-slate-800 mb-1">Find Standards</h3>
                <p className="text-sm text-slate-500">Discover applicable standards for your specific product category.</p>
              </button>
              
              <button onClick={() => handleCardClick("What is the certification process for ISI mark?")} className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all group text-left">
                <CheckCircle className="text-green-500 mb-3 group-hover:scale-110 transition-transform" size={24} />
                <h3 className="font-semibold text-slate-800 mb-1">Certification Scheme</h3>
                <p className="text-sm text-slate-500">Learn about mandatory and voluntary certification procedures.</p>
              </button>
              
              <button onClick={() => handleCardClick("Where can I test drinking water samples?")} className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all group text-left">
                <FlaskConical className="text-purple-500 mb-3 group-hover:scale-110 transition-transform" size={24} />
                <h3 className="font-semibold text-slate-800 mb-1">Testing & Labs</h3>
                <p className="text-sm text-slate-500">Find recognized laboratories and testing parameters.</p>
              </button>
            </div>
          </div>
        ) : (
          // Chat View
          <div className="flex flex-col h-full animate-fade-in-up">
            <div className="flex-1 overflow-y-auto pb-32 space-y-8">
              {messages.map((msg, index) => (
                <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.type === 'ai' && (
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mr-3 flex-shrink-0">
                      <Shield size={16} />
                    </div>
                  )}
                  
                  <div className={`max-w-[85%] rounded-2xl p-5 ${
                    msg.type === 'user' 
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'bg-white border border-slate-200 shadow-sm text-slate-700'
                  }`}>
                    <p className="leading-relaxed">{msg.text}</p>
                    
                    {msg.references && (
                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <button 
                          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                          className="flex items-center justify-between w-full text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                        >
                          <span className="flex items-center gap-2"><FileText size={16}/> Sources & References</span>
                          <ChevronDown size={16} className={`transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>
                        
                        {isDropdownOpen && (
                          <div className="mt-3 space-y-2 bg-slate-50 p-3 rounded-xl border border-slate-100">
                            {msg.references.map((ref, idx) => (
                              <a key={idx} href={ref.link} className="flex items-center justify-between p-2 hover:bg-white rounded-lg group text-sm text-slate-600 hover:text-blue-600 transition-colors">
                                <span className="truncate pr-4">{ref.title}</span>
                                <ExternalLink size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Sticky Input Area for Chat */}
            <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent pt-10 pb-6 px-4">
              <div className="max-w-3xl mx-auto">
                <form onSubmit={handleSearch} className="relative shadow-lg shadow-slate-200/50 rounded-2xl bg-white border border-slate-200 group">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask another question..."
                    className="w-full pl-5 pr-14 py-4 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  <button 
                    type="submit"
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50"
                    disabled={!query.trim()}
                  >
                    <ArrowUp size={18} />
                  </button>
                </form>
                <div className="text-center mt-3 text-xs text-slate-400">
                  Information is AI-generated and based on available public sources. Please verify with official authorities.
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
      
      {/* Custom Styles for animations */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fadeIn 0.4s ease-out; }
        .animate-fade-in-up { animation: fadeInUp 0.4s ease-out; }
      `}} />
    </div>
  );
}

export default App;
