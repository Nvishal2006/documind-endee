import React from 'react';
import DocLibrary from './components/DocLibrary';
import ChatPane from './components/ChatPane';

function App() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-800">
      {/* Left Pane: Document Library */}
      <div className="w-1/3 min-w-[320px] max-w-[450px] border-r border-slate-200 bg-white shadow-sm flex flex-col z-10">
        <DocLibrary />
      </div>

      {/* Right Pane: Chat Interface */}
      <div className="flex-1 flex flex-col bg-slate-50 relative">
        <ChatPane />
      </div>
    </div>
  );
}

export default App;
