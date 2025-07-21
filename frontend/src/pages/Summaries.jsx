import React, { useState, useEffect } from 'react';
import { Globe, ExternalLink, Calendar, Clock, Eye, X } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import apiService from '../services/api';

const Summaries = () => {
  const { summaries: summariesState, setSummaries } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchSummaries();
  }, []);

  const fetchSummaries = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('📋 Fetching summaries from backend...');
      const response = await apiService.getSummaries();
      
      console.log('✅ Summaries fetched:', response);
      setSummaries(response.summaries || []);
    } catch (err) {
      console.error('❌ Error fetching summaries:', err);
      setError('Failed to load summaries. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    
    try {
      // Parse the date string and treat it as UTC
      const date = new Date(dateString + 'Z'); // Add 'Z' to indicate UTC
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      // If more than a week, show the actual date
      return date.toLocaleDateString();
    } catch (error) {
      console.error('Error parsing date:', dateString, error);
      return 'Invalid date';
    }
  };

  const truncateText = (text, maxLength = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const handleViewDetails = (summary) => {
    setSelectedSummary(summary);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedSummary(null);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-secondary-900">Summaries</h1>
        </div>
        
        <div className="card">
          <div className="card-body text-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-secondary-600">Loading summaries...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-secondary-900">Summaries</h1>
        </div>
        
        <div className="card">
          <div className="card-body text-center py-16">
            <div className="text-red-500 mb-4">
              <svg className="h-12 w-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-secondary-900 mb-2">
              Error Loading Summaries
            </h3>
            <p className="text-secondary-600 mb-4">{error}</p>
            <button
              onClick={fetchSummaries}
              className="btn btn-primary"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-secondary-900">Summaries</h1>
        <div className="text-sm text-secondary-600">
          {summariesState.items?.length || 0} summary{(summariesState.items?.length || 0) !== 1 ? 'ies' : ''}
        </div>
      </div>
      
      {!summariesState.items || summariesState.items.length === 0 ? (
        <div className="card">
          <div className="card-body text-center py-12 sm:py-16">
            <Globe className="h-12 w-12 sm:h-16 sm:w-16 text-secondary-400 mx-auto mb-4" />
            <h3 className="text-base sm:text-lg font-semibold text-secondary-900 mb-2">
              No Summaries Yet
            </h3>
            <p className="text-sm sm:text-base text-secondary-600">
              Start by analyzing a webpage using the sidebar
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {summariesState.items?.map((summary) => (
            <div key={summary.id} className="card hover:shadow-lg transition-shadow">
              <div className="card-body p-4 sm:p-6">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-secondary-900 line-clamp-2 text-sm sm:text-base flex-1 mr-2">
                    {summary.title}
                  </h3>
                  <a
                    href={summary.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:text-primary-700 flex-shrink-0"
                    title="Open original webpage"
                  >
                    <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4" />
                  </a>
                </div>
                
                <p className="text-secondary-600 text-xs sm:text-sm mb-3 line-clamp-1">
                  {summary.url}
                </p>
                
                <div className="prose prose-sm max-w-none mb-4">
                  <p className="text-secondary-900 line-clamp-3 text-xs sm:text-sm">
                    {truncateText(summary.summary_text)}
                  </p>
                </div>
                
                {summary.question && (
                  <div className="mb-4 p-2 sm:p-3 bg-secondary-50 rounded-lg">
                    <h4 className="font-medium text-secondary-900 text-xs sm:text-sm mb-1">
                      Question:
                    </h4>
                    <p className="text-secondary-700 text-xs sm:text-sm line-clamp-2">
                      {summary.question}
                    </p>
                    {summary.response && (
                      <>
                        <h4 className="font-medium text-secondary-900 text-xs sm:text-sm mb-1 mt-2">
                          Answer:
                        </h4>
                        <p className="text-secondary-900 text-xs sm:text-sm line-clamp-2">
                          {truncateText(summary.response, 100)}
                        </p>
                      </>
                    )}
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs text-secondary-500 mb-3">
                  <div className="flex items-center">
                    <Calendar className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">{formatDate(summary.created_at)}</span>
                    <span className="sm:hidden">{formatDate(summary.created_at).split(' ')[0]}</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">{summary.processing_time ? `${summary.processing_time}s` : 'N/A'}</span>
                    <span className="sm:hidden">{summary.processing_time ? `${summary.processing_time}s` : '-'}</span>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <button
                    onClick={() => handleViewDetails(summary)}
                    className="btn btn-primary btn-sm flex items-center justify-center w-full sm:w-auto"
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">View Details</span>
                    <span className="sm:hidden">Details</span>
                  </button>
                  <a
                    href={summary.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-secondary-600 hover:text-secondary-800 flex items-center justify-center sm:justify-start"
                  >
                    <span className="hidden sm:inline">Original Page</span>
                    <span className="sm:hidden">Original</span>
                    <ExternalLink className="h-3 w-3 ml-1" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Details Modal */}
      {showModal && selectedSummary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-2 sm:p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-4 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl sm:text-2xl font-bold text-secondary-900">
                  Summary Details
                </h2>
                <button
                  onClick={closeModal}
                  className="p-2 text-secondary-400 hover:text-secondary-600 rounded-md hover:bg-secondary-100"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-secondary-900 mb-2 text-base sm:text-lg">
                    {selectedSummary.title}
                  </h3>
                  <p className="text-secondary-600 text-sm">
                    {selectedSummary.url}
                  </p>
                </div>
                
                {selectedSummary.question && (
                  <div className="p-3 sm:p-4 bg-secondary-50 rounded-lg">
                    <h4 className="font-medium text-secondary-900 mb-2 text-sm sm:text-base">
                      Your Question:
                    </h4>
                    <p className="text-secondary-700 text-sm sm:text-base">
                      {selectedSummary.question}
                    </p>
                  </div>
                )}
                
                {selectedSummary.response && (
                  <div className="p-3 sm:p-4 bg-primary-50 rounded-lg border-l-4 border-primary-500">
                    <h4 className="font-medium text-secondary-900 mb-2 text-sm sm:text-base">
                      Answer to Your Question:
                    </h4>
                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-secondary-900 text-sm sm:text-base">
                        {selectedSummary.response}
                      </div>
                    </div>
                  </div>
                )}
                
                <div>
                  <h4 className="font-medium text-secondary-900 mb-2 text-sm sm:text-base">
                    Complete Summary:
                  </h4>
                  <div className="prose prose-sm max-w-none bg-secondary-50 p-3 sm:p-4 rounded-lg">
                    <div className="whitespace-pre-wrap text-secondary-900 text-sm sm:text-base">
                      {selectedSummary.summary_text}
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-sm text-secondary-500 pt-4 border-t border-secondary-200 gap-2">
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-2" />
                    {formatDate(selectedSummary.created_at)}
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2" />
                    {selectedSummary.processing_time ? `${selectedSummary.processing_time}s` : 'N/A'}
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pt-4 gap-2">
                  <a
                    href={selectedSummary.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary w-full sm:w-auto flex items-center justify-center"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Visit Original Page
                  </a>
                  <button
                    onClick={closeModal}
                    className="btn btn-primary w-full sm:w-auto"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Summaries; 