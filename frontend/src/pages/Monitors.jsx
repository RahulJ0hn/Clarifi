import React, { useState, useEffect } from 'react';
import { Eye, Plus, Settings, Trash2, Play, Pause, RefreshCw, AlertCircle, Clock } from 'lucide-react';
import apiService from '../services/api';

const Monitors = () => {
  const [monitors, setMonitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [monitorTypes, setMonitorTypes] = useState([]);
  const [itemTypes, setItemTypes] = useState([]);
  const [stats, setStats] = useState({});
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    monitor_type: 'content',
    css_selector: '',
    item_name: '',
    item_type: 'auto',
    check_interval: 300,
    notification_enabled: true
  });

  useEffect(() => {
    loadMonitors();
    loadMonitorTypes();
    loadStats();
  }, []);

  const loadMonitors = async () => {
    try {
      setLoading(true);
      const response = await apiService.getMonitors();
      setMonitors(response.monitors || []);
    } catch (error) {
      console.error('Error loading monitors:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMonitorTypes = async () => {
    try {
      const response = await apiService.getMonitorTypes();
      setMonitorTypes(response.types || []);
      setItemTypes(response.item_types || []);
    } catch (error) {
      console.error('Error loading monitor types:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiService.getMonitorStats();
      setStats(response);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleCreateMonitor = async (e) => {
    e.preventDefault();
    try {
      await apiService.createMonitor(formData);
      setShowCreateForm(false);
      setFormData({
        name: '',
        url: '',
        monitor_type: 'content',
        css_selector: '',
        item_name: '',
        item_type: 'auto',
        check_interval: 300,
        notification_enabled: true
      });
      loadMonitors();
      loadStats();
    } catch (error) {
      console.error('Error creating monitor:', error);
      alert('Error creating monitor: ' + error.message);
    }
  };

  const handleToggleMonitor = async (monitorId) => {
    try {
      await apiService.toggleMonitor(monitorId);
      loadMonitors();
      loadStats();
    } catch (error) {
      console.error('Error toggling monitor:', error);
    }
  };

  const handleDeleteMonitor = async (monitorId) => {
    if (!window.confirm('Are you sure you want to delete this monitor?')) return;
    
    try {
      await apiService.deleteMonitor(monitorId);
      loadMonitors();
      loadStats();
    } catch (error) {
      console.error('Error deleting monitor:', error);
    }
  };

  const handleCheckMonitor = async (monitorId) => {
    try {
      await apiService.checkMonitor(monitorId);
      loadMonitors();
    } catch (error) {
      console.error('Error checking monitor:', error);
    }
  };

  const handleCheckAllMonitors = async () => {
    try {
      const activeMonitors = monitors.filter(m => m.is_active);
      if (activeMonitors.length === 0) {
        alert('No active monitors to check');
        return;
      }
      
      if (!window.confirm(`Check all ${activeMonitors.length} active monitors?`)) {
        return;
      }
      
      // Check each monitor
      for (const monitor of activeMonitors) {
        try {
          await apiService.checkMonitor(monitor.id);
        } catch (error) {
          console.error(`Error checking monitor ${monitor.name}:`, error);
        }
      }
      
      // Reload monitors after all checks
      loadMonitors();
      loadStats();
    } catch (error) {
      console.error('Error checking all monitors:', error);
    }
  };

  const formatInterval = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    
    try {
      // Parse the date string and treat it as UTC
      const date = new Date(dateString + 'Z'); // Add 'Z' to indicate UTC
      
      // Check if the date is valid
      if (isNaN(date.getTime())) {
        return 'Invalid date';
      }
      
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

  const formatCurrentValue = (monitor) => {
    if (!monitor.current_value) return 'No data yet';
    
    const value = monitor.current_value;
    
    // For item search monitors, show item-specific information
    if (monitor.monitor_type === 'item_search' && monitor.item_name) {
      return `${monitor.item_name}: ${value}`;
    }
    
    // For price monitors, try to extract numeric values
    if (monitor.monitor_type === 'price') {
      // Look for currency patterns
      const priceMatch = value.match(/[\$€£¥]?\s*[\d,]+\.?\d*/);
      if (priceMatch) {
        return priceMatch[0];
      }
      // Look for numbers that might be prices
      const numberMatch = value.match(/[\d,]+\.?\d*/);
      if (numberMatch) {
        return numberMatch[0];
      }
    }
    
    // For content monitors, show first meaningful text
    if (monitor.monitor_type === 'content') {
      // Remove HTML tags and get first 100 characters of clean text
      const cleanText = value.replace(/<[^>]*>/g, '').trim();
      if (cleanText.length > 0) {
        return cleanText.length > 100 ? cleanText.substring(0, 100) + '...' : cleanText;
      }
    }
    
    // For selector monitors, show the extracted content
    if (monitor.monitor_type === 'selector') {
      const cleanText = value.replace(/<[^>]*>/g, '').trim();
      if (cleanText.length > 0) {
        return cleanText.length > 100 ? cleanText.substring(0, 100) + '...' : cleanText;
      }
    }
    
    // Default: show first 100 characters
    return value.length > 100 ? value.substring(0, 100) + '...' : value;
  };

  const getMonitorTypeLabel = (type) => {
    const typeObj = monitorTypes.find(t => t.value === type);
    return typeObj ? typeObj.label : type;
  };

  const getItemTypeLabel = (type) => {
    const typeObj = itemTypes.find(t => t.value === type);
    return typeObj ? typeObj.label : type;
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Monitors</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Monitor
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Eye className="w-5 h-5 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total Monitors</p>
              <p className="text-lg font-semibold text-gray-900">{stats.total_monitors || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Play className="w-5 h-5 text-green-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Active Monitors</p>
              <p className="text-lg font-semibold text-gray-900">{stats.active_monitors || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Recent Changes</p>
              <p className="text-lg font-semibold text-gray-900">{stats.recent_changes || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <Clock className="w-5 h-5 text-red-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Stale Monitors</p>
              <p className="text-lg font-semibold text-gray-900">{stats.stale_monitors || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-2 mb-4 sm:mb-6">
        <button
          onClick={loadMonitors}
          className="bg-gray-100 text-gray-700 px-3 py-2 sm:px-4 sm:py-2 rounded-lg hover:bg-gray-200 flex items-center gap-2 text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          <span className="hidden sm:inline">Refresh</span>
          <span className="sm:hidden">Refresh</span>
        </button>
        <button
          onClick={handleCheckAllMonitors}
          className="bg-yellow-500 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-lg hover:bg-yellow-600 flex items-center gap-2 text-sm"
        >
          <Play className="w-4 h-4" />
          <span className="hidden sm:inline">Check All</span>
          <span className="sm:hidden">Check All</span>
        </button>
      </div>

      {/* Warning for blocked sites */}
      {stats.stale_monitors > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 sm:p-4 mb-4 sm:mb-6">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="min-w-0">
              <h3 className="text-sm font-medium text-red-800">Some monitors are being blocked by websites</h3>
              <p className="text-xs sm:text-sm text-red-700 mt-1">
                CoinMarketCap and some other sites block automated requests. Try these alternatives:
              </p>
              <ul className="text-xs sm:text-sm text-red-700 mt-2 list-disc list-inside space-y-1">
                <li>Cryptocurrency prices: <a href="https://cryptonews.com/" target="_blank" rel="noopener noreferrer" className="underline">https://cryptonews.com/</a> or <a href="https://coingecko.com/" target="_blank" rel="noopener noreferrer" className="underline">https://coingecko.com/</a></li>
                <li>Stock prices: <a href="https://finance.yahoo.com/" target="_blank" rel="noopener noreferrer" className="underline">https://finance.yahoo.com/</a> or <a href="https://marketwatch.com/" target="_blank" rel="noopener noreferrer" className="underline">https://marketwatch.com/</a></li>
                <li>General content: <a href="https://en.wikipedia.org/" target="_blank" rel="noopener noreferrer" className="underline">https://en.wikipedia.org/</a> or <a href="https://github.com/" target="_blank" rel="noopener noreferrer" className="underline">https://github.com/</a></li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Monitors List */}
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-2 text-sm sm:text-base">Loading monitors...</p>
        </div>
      ) : monitors.length === 0 ? (
        <div className="text-center py-8">
          <Eye className="w-10 h-10 sm:w-12 sm:h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-2">No monitors yet</h3>
          <p className="text-sm sm:text-base text-gray-600 mb-4">Create your first monitor to start tracking websites</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm sm:text-base"
          >
            Create Monitor
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {monitors.map((monitor) => (
            <div key={monitor.id} className="bg-white rounded-lg shadow p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">{monitor.name}</h3>
                  <p className="text-xs sm:text-sm text-gray-600 truncate">{monitor.url}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    monitor.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {monitor.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {getMonitorTypeLabel(monitor.monitor_type)}
                  </span>
                  {monitor.item_type && monitor.item_type !== 'auto' && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      {getItemTypeLabel(monitor.item_type)}
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-xs sm:text-sm font-medium text-gray-600 mb-1">Type</p>
                  <p className="text-xs sm:text-sm text-gray-900">{getMonitorTypeLabel(monitor.monitor_type)}</p>
                  {monitor.item_name && (
                    <p className="text-xs sm:text-sm text-gray-900 mt-1">
                      <span className="font-medium">Item:</span> {monitor.item_name}
                    </p>
                  )}
                  {monitor.css_selector && (
                    <p className="text-xs sm:text-sm text-gray-900 mt-1">
                      <span className="font-medium">Selector:</span> {monitor.css_selector}
                    </p>
                  )}
                </div>
                
                <div>
                  <p className="text-xs sm:text-sm font-medium text-gray-600 mb-1">Interval</p>
                  <p className="text-xs sm:text-sm text-gray-900">{formatInterval(monitor.check_interval)}</p>
                  <p className="text-xs sm:text-sm text-gray-600 mt-1">
                    Last checked: {formatDate(monitor.last_checked)}
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <p className="text-xs sm:text-sm font-medium text-gray-600 mb-1">Current Value</p>
                <p className="text-xs sm:text-sm text-gray-900 bg-gray-50 p-2 rounded break-words">
                  {formatCurrentValue(monitor)}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                <div className="flex gap-2">
                  <button
                    onClick={() => handleCheckMonitor(monitor.id)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-xs sm:text-sm hover:bg-blue-700"
                  >
                    <span className="hidden sm:inline">Check Now</span>
                    <span className="sm:hidden">Check</span>
                  </button>
                  <button
                    onClick={() => handleToggleMonitor(monitor.id)}
                    className={`px-3 py-1 rounded text-xs sm:text-sm ${
                      monitor.is_active
                        ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                        : 'bg-green-600 text-white hover:bg-green-700'
                    }`}
                  >
                    {monitor.is_active ? 'Pause' : 'Start'}
                  </button>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDeleteMonitor(monitor.id)}
                    className="text-red-600 hover:text-red-800 p-1"
                    title="Delete monitor"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Monitor Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create New Monitor</h2>
            
            <form onSubmit={handleCreateMonitor}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Monitor Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    URL to Monitor
                  </label>
                  <input
                    type="url"
                    value={formData.url}
                    onChange={(e) => setFormData({...formData, url: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Monitor Type
                  </label>
                  <select
                    value={formData.monitor_type}
                    onChange={(e) => setFormData({...formData, monitor_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {monitorTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {formData.monitor_type === 'item_search' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Item Name
                      </label>
                      <input
                        type="text"
                        value={formData.item_name}
                        onChange={(e) => setFormData({...formData, item_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., Bitcoin, AAPL, iPhone 15"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Item Type
                      </label>
                      <select
                        value={formData.item_type}
                        onChange={(e) => setFormData({...formData, item_type: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {itemTypes.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </>
                )}

                {formData.monitor_type === 'selector' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      CSS Selector (Optional)
                    </label>
                    <input
                      type="text"
                      value={formData.css_selector}
                      onChange={(e) => setFormData({...formData, css_selector: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder=".price, #content, etc."
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Check Interval (seconds)
                  </label>
                  <input
                    type="number"
                    value={formData.check_interval}
                    onChange={(e) => setFormData({...formData, check_interval: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="60"
                    max="86400"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="notification_enabled"
                    checked={formData.notification_enabled}
                    onChange={(e) => setFormData({...formData, notification_enabled: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="notification_enabled" className="ml-2 block text-sm text-gray-900">
                    Enable notifications
                  </label>
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                >
                  Create Monitor
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Monitors; 