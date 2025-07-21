import React, { useState, useEffect } from 'react';
import { Globe, Eye, Bell, BarChart3, RefreshCw, Plus, ExternalLink } from 'lucide-react';
import apiService from '../services/api';
import { useAppStore } from '../store/appStore';

const Dashboard = () => {
  const {
    ui,
    summaries,
    monitors,
    notifications,
    stats,
    setSummariesLoading,
    setSummariesError,
    setSummaries,
    setMonitorsLoading,
    setMonitorsError,
    setMonitors,
    setNotificationsLoading,
    setNotificationsError,
    setNotifications,
    setStatsLoading,
    setStatsError,
    setSummaryStats,
    setMonitorStats,
    setNotificationStats,
    showToast,
  } = useAppStore();

  const [summarizeForm, setSummarizeForm] = useState({
    url: '',
    question: ''
  });
  const [summarizing, setSummarizing] = useState(false);
  const [lastSummary, setLastSummary] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setStatsLoading(true);
      
      console.log('📊 Loading dashboard data...');
      
      // Load all data in parallel with proper error handling
      const [summaryStats, monitorStats, notificationStats, summaries, notifications] = await Promise.allSettled([
        apiService.getSummaryStats(),
        apiService.getMonitorStats(),
        apiService.getNotificationStats(),
        apiService.getSummaries(1, 5),
        apiService.getRecentNotifications(5)
      ]);

      // Handle summary stats
      if (summaryStats.status === 'fulfilled') {
        console.log('✅ Summary stats loaded:', summaryStats.value);
        setSummaryStats(summaryStats.value);
      } else {
        console.error('❌ Summary stats failed:', summaryStats.reason);
        setStatsError('Failed to load summary stats');
      }

      // Handle monitor stats
      if (monitorStats.status === 'fulfilled') {
        console.log('✅ Monitor stats loaded:', monitorStats.value);
        setMonitorStats(monitorStats.value);
      } else {
        console.error('❌ Monitor stats failed:', monitorStats.reason);
        setStatsError('Failed to load monitor stats');
      }

      // Handle notification stats
      if (notificationStats.status === 'fulfilled') {
        console.log('✅ Notification stats loaded:', notificationStats.value);
        setNotificationStats(notificationStats.value);
      } else {
        console.error('❌ Notification stats failed:', notificationStats.reason);
        setStatsError('Failed to load notification stats');
      }

      // Handle recent summaries
      if (summaries.status === 'fulfilled') {
        console.log('✅ Recent summaries loaded:', summaries.value);
        setSummaries(summaries.value.summaries || []);
      } else {
        console.error('❌ Recent summaries failed:', summaries.reason);
        setSummariesError('Failed to load recent summaries');
      }

      // Handle recent notifications
      if (notifications.status === 'fulfilled') {
        console.log('✅ Recent notifications loaded:', notifications.value);
        setNotifications(notifications.value || []);
      } else {
        console.error('❌ Recent notifications failed:', notifications.reason);
        setNotificationsError('Failed to load recent notifications');
      }
      
    } catch (error) {
      console.error('❌ Error loading dashboard data:', error);
      setStatsError('Failed to load dashboard data');
    } finally {
      setStatsLoading(false);
    }
  };

  const handleSummarize = async (e) => {
    e.preventDefault();
    if (!summarizeForm.url.trim()) return;

    try {
      setSummarizing(true);
      console.log('🎯 Starting summarization for:', summarizeForm.url);
      
      const result = await apiService.summarizeUrl(summarizeForm.url, summarizeForm.question);
      console.log('✅ Summarization completed:', result);
      
      setLastSummary(result);
      setSummarizeForm({ url: '', question: '' });
      
      // Show success toast
      showToast({
        type: 'success',
        title: 'Summarization Complete',
        message: `Successfully summarized ${result.url}`,
      });
      
      // Refresh dashboard data after successful summarization
      setTimeout(() => {
        loadDashboardData();
      }, 1000);
      
    } catch (error) {
      console.error('❌ Error summarizing:', error);
      
      // Create a more helpful error message
      let errorMessage = error.message;
      
      // If it's a 403 error, format the suggestions nicely
      if (errorMessage.includes('Access forbidden')) {
        errorMessage = errorMessage.replace(/\n\n/g, '\n');
        errorMessage = errorMessage.replace(/• /g, '\n• ');
      }
      
      showToast({
        type: 'error',
        title: 'Summarization Failed',
        message: errorMessage,
      });
    } finally {
      setSummarizing(false);
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

  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-secondary-900">Dashboard</h1>
          <p className="text-secondary-600 mt-1">
            Welcome to your AI-powered browser assistant.
          </p>
        </div>
        <button
          onClick={loadDashboardData}
          className="btn btn-refresh w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 sm:px-6 sm:py-3 text-sm sm:text-base font-medium"
          disabled={stats.loading}
        >
          <RefreshCw className={`h-4 w-4 sm:h-5 sm:w-5 ${stats.loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
            <div className="card-body">
            <div className="flex items-center">
              <Globe className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Total Summaries</p>
                  <p className="text-xl sm:text-2xl font-bold text-secondary-900">
                  {stats.loading ? '...' : (stats.summaries?.total_summaries || 0)}
                  </p>
                </div>
            </div>
          </div>
                </div>
        
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <Eye className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Active Monitors</p>
                <p className="text-xl sm:text-2xl font-bold text-secondary-900">
                  {stats.loading ? '...' : (stats.monitors?.active_monitors || 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <Bell className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Unread Notifications</p>
                <p className="text-xl sm:text-2xl font-bold text-secondary-900">
                  {stats.loading ? '...' : (stats.notifications?.unread_notifications || 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <BarChart3 className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Recent Activity</p>
                <p className="text-xl sm:text-2xl font-bold text-secondary-900">
                  {stats.loading ? '...' : (stats.summaries?.recent_summaries || 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Summarize Form */}
      <div className="card">
        <div className="card-body">
          <h2 className="text-lg sm:text-xl font-semibold text-secondary-900 mb-4">Summarize Web Content</h2>
          <form onSubmit={handleSummarize} className="space-y-4">
            <div>
              <label htmlFor="url" className="block text-sm font-medium text-secondary-700 mb-2">
                Website URL
              </label>
              <input
                type="url"
                id="url"
                value={summarizeForm.url}
                onChange={(e) => setSummarizeForm({ ...summarizeForm, url: e.target.value })}
                placeholder="https://example.com"
                className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label htmlFor="question" className="block text-sm font-medium text-secondary-700 mb-2">
                Specific Question (Optional)
              </label>
              <input
                type="text"
                id="question"
                value={summarizeForm.question}
                onChange={(e) => setSummarizeForm({ ...summarizeForm, question: e.target.value })}
                placeholder="What specific information are you looking for?"
                className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            
            <button
              type="submit"
              disabled={summarizing || !summarizeForm.url.trim()}
              className="w-full sm:w-auto btn btn-primary flex items-center justify-center gap-2 px-6 py-3 text-sm sm:text-base font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {summarizing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Summarizing...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Summarize
                </>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Recent Summaries */}
        <div className="card">
          <div className="card-body">
            <h3 className="text-base sm:text-lg font-semibold text-secondary-900 mb-4">Recent Summaries</h3>
            {summaries.loading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
                <span className="ml-2 text-secondary-600 text-sm sm:text-base">Loading summaries...</span>
              </div>
            ) : summaries.error ? (
              <div className="text-center py-8 text-red-600">
                <p className="text-sm sm:text-base">Error loading summaries</p>
                <button 
                  onClick={() => loadDashboardData()}
                  className="mt-2 text-sm text-primary-600 hover:underline"
                >
                  Try again
                </button>
              </div>
            ) : summaries.items.length === 0 ? (
              <div className="text-center py-8 text-secondary-500">
                <Globe className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-4 text-secondary-400" />
                <p className="text-sm sm:text-base">No summaries yet</p>
                <p className="text-xs sm:text-sm">Start by summarizing a webpage above</p>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4">
                {summaries.items.slice(0, 5).map((summary) => (
                  <div key={summary.id} className="border border-secondary-200 rounded-lg p-3 sm:p-4 hover:bg-secondary-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-secondary-900 truncate text-sm sm:text-base">
                          {summary.title || 'Untitled'}
                        </h4>
                        <p className="text-xs sm:text-sm text-secondary-600 mt-1 line-clamp-2">
                          {truncateText(summary.summary, 120)}
                        </p>
                        <div className="flex items-center mt-2 text-xs text-secondary-500">
                          <span>{formatDate(summary.created_at)}</span>
                          <span className="mx-2">•</span>
                          <span className="truncate">{summary.url}</span>
                        </div>
                      </div>
                      <a
                        href={summary.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 flex-shrink-0 text-primary-600 hover:text-primary-700"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Notifications */}
        <div className="card">
          <div className="card-body">
            <h3 className="text-base sm:text-lg font-semibold text-secondary-900 mb-4">Recent Notifications</h3>
            {notifications.loading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
                <span className="ml-2 text-secondary-600 text-sm sm:text-base">Loading notifications...</span>
              </div>
            ) : notifications.error ? (
              <div className="text-center py-8 text-red-600">
                <p className="text-sm sm:text-base">Error loading notifications</p>
                <button 
                  onClick={() => loadDashboardData()}
                  className="mt-2 text-sm text-primary-600 hover:underline"
                >
                  Try again
                </button>
              </div>
            ) : notifications.items.length === 0 ? (
              <div className="text-center py-8 text-secondary-500">
                <Bell className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-4 text-secondary-400" />
                <p className="text-sm sm:text-base">No notifications yet</p>
                <p className="text-xs sm:text-sm">You'll see notifications here when monitors detect changes</p>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4">
                {notifications.items.slice(0, 5).map((notification) => (
                  <div key={notification.id} className={`border rounded-lg p-3 sm:p-4 ${
                    notification.is_read 
                      ? 'border-secondary-200 bg-secondary-50' 
                      : 'border-primary-200 bg-primary-50'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-secondary-900 text-sm sm:text-base truncate">
                          {notification.title}
                        </h4>
                        <p className="text-xs sm:text-sm text-secondary-600 mt-1 line-clamp-2">
                          {truncateText(notification.message, 100)}
                        </p>
                        <div className="flex items-center mt-2 text-xs text-secondary-500">
                          <span>{formatDate(notification.created_at)}</span>
                          {!notification.is_read && (
                            <>
                              <span className="mx-2">•</span>
                              <span className="text-primary-600 font-medium">New</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 