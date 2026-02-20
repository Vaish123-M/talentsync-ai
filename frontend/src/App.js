import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import UploadResumes from './pages/UploadResumes';
import CandidateSearch from './pages/CandidateSearch';
import Automation from './pages/Automation';

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <Sidebar />
        
        <main className="pt-16 min-h-screen md:ml-64">
          <div className="p-4 sm:p-6 lg:p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<UploadResumes />} />
              <Route path="/search" element={<CandidateSearch />} />
              <Route path="/automation" element={<Automation />} />
            </Routes>
          </div>
          <Footer />
        </main>
      </div>
    </Router>
  );
}

export default App;

