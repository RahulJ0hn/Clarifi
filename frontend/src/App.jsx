import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import Dashboard from './pages/Dashboard';
import Summaries from './pages/Summaries';
import Monitors from './pages/Monitors';
import Notifications from './pages/Notifications';
import AuthGuard from './components/auth/AuthGuard';
import Toast from './components/ui/Toast';
import './index.css';

function App() {
  return (
      <Router>
        <div className="min-h-screen bg-secondary-50">
          <AuthGuard>
            <Header />
            <main className="flex-1 pt-20 sm:pt-20 lg:pt-20 px-4 sm:px-6 lg:px-8 pb-4 sm:pb-6 lg:pb-8">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/summaries" element={<Summaries />} />
                  <Route path="/monitors" element={<Monitors />} />
                  <Route path="/notifications" element={<Notifications />} />
                </Routes>
              </main>
            <Toast />
          </AuthGuard>
        </div>
      </Router>
  );
}

export default App; 