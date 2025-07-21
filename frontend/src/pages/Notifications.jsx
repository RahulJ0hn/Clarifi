import React, { useState, useEffect } from 'react';
import { Bell, Check, Trash2, RefreshCw, Eye, Clock, AlertCircle, Info } from 'lucide-react';
import apiService from '../services/api';

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [selectedNotifications, setSelectedNotifications] = useState([]);
  const [filter, setFilter] = useState('all'); // all, unread, read
  
  useEffect(() => {
    loadNotifications();
    loadStats();
  }, [filter]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await apiService.getNotifications(
        1, 
        50, 
        filter === 'unread',
        null
      );
      setNotifications(response.notifications || []);
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiService.getNotificationStats();
      setStats(response);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleMarkAsRead = async (notificationIds) => {
    try {
      await apiService.markNotificationsRead(notificationIds);
      loadNotifications();
      loadStats();
      setSelectedNotifications([]);
      
      // Dispatch event to update header bell count
      window.dispatchEvent(new Event('notification-read'));
    } catch (error) {
      console.error('Error marking notifications as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await apiService.markAllNotificationsRead();
      loadNotifications();
      loadStats();
      setSelectedNotifications([]);
      
      // Dispatch event to update header bell count
      window.dispatchEvent(new Event('notification-read'));
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    if (!window.confirm('Are you sure you want to delete this notification?')) return;
    
    try {
      await apiService.deleteNotification(notificationId);
      loadNotifications();
      loadStats();
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const handleDeleteSelected = async () => {
    if (!window.confirm(`Are you sure you want to delete ${selectedNotifications.length} notifications?`)) return;
    
    try {
      await Promise.all(selectedNotifications.map(id => apiService.deleteNotification(id)));
      loadNotifications();
      loadStats();
      setSelectedNotifications([]);
    } catch (error) {
      console.error('Error deleting selected notifications:', error);
    }
  };

  const handleSelectNotification = (notificationId) => {
    setSelectedNotifications(prev => 
      prev.includes(notificationId)
        ? prev.filter(id => id !== notificationId)
        : [...prev, notificationId]
    );
  };

  const handleSelectAll = () => {
    if (selectedNotifications.length === notifications.length) {
      setSelectedNotifications([]);
    } else {
      setSelectedNotifications(notifications.map(n => n.id));
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'success':
        return <Check className="h-5 w-5 text-green-500" />;
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
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

  const isRecentNotification = (dateString) => {
    if (!dateString) return false;
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / 3600000);
    
    // Show "New" tag only for notifications created within the last hour
    return diffHours < 1;
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-secondary-900">Notifications</h1>
        <div className="flex items-center space-x-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="input text-sm"
          >
            <option value="all">All Notifications</option>
            <option value="unread">Unread Only</option>
            <option value="read">Read Only</option>
          </select>
          <button
            onClick={loadNotifications}
            className="btn btn-secondary btn-sm"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-body p-4">
            <div className="flex items-center">
              <Bell className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Total Notifications</p>
                <p className="text-xl sm:text-2xl font-bold text-secondary-900">{stats.total_notifications || 0}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body p-4">
            <div className="flex items-center">
              <Eye className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Unread</p>
                <p className="text-xl sm:text-2xl font-bold text-secondary-900">{stats.unread_notifications || 0}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body p-4">
            <div className="flex items-center">
              <Check className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Read</p>
                <p className="text-xl sm:text-2xl font-bold text-secondary-900">{(stats.total_notifications || 0) - (stats.unread_notifications || 0)}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body p-4">
            <div className="flex items-center">
              <Clock className="h-6 w-6 sm:h-8 sm:w-8 text-orange-600" />
              <div className="ml-3">
                <p className="text-xs sm:text-sm font-medium text-secondary-600">Today</p>
                <p className="text-xl sm:text-2xl font-bold text-secondary-900">{stats.recent_notifications || 0}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      {notifications.length > 0 && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-secondary-50 p-3 sm:p-4 rounded-lg gap-3">
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={selectedNotifications.length === notifications.length}
                onChange={handleSelectAll}
                className="checkbox"
              />
              <span className="ml-2 text-xs sm:text-sm text-secondary-700">
                Select All ({selectedNotifications.length}/{notifications.length})
              </span>
            </label>
          </div>
          
          <div className="flex items-center space-x-2">
            {selectedNotifications.length > 0 && (
              <>
                <button
                  onClick={() => handleMarkAsRead(selectedNotifications)}
                  className="btn btn-sm btn-secondary text-xs"
                >
                  <Check className="h-3 w-3 mr-1" />
                  <span className="hidden sm:inline">Mark as Read</span>
                  <span className="sm:hidden">Read</span>
                </button>
                <button
                  onClick={handleDeleteSelected}
                  className="btn btn-sm btn-danger text-xs"
                >
                  <Trash2 className="h-3 w-3 mr-1" />
                  <span className="hidden sm:inline">Delete Selected</span>
                  <span className="sm:hidden">Delete</span>
                </button>
              </>
            )}
            <button
              onClick={handleMarkAllAsRead}
              className="btn btn-sm btn-primary text-xs"
            >
              <Check className="h-3 w-3 mr-1" />
              <span className="hidden sm:inline">Mark All as Read</span>
              <span className="sm:hidden">Read All</span>
            </button>
          </div>
        </div>
      )}

      {/* Notifications List */}
      {loading ? (
        <div className="card">
          <div className="card-body text-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-secondary-600 text-sm sm:text-base">Loading notifications...</p>
          </div>
        </div>
      ) : notifications.length === 0 ? (
        <div className="card">
          <div className="card-body text-center py-12 sm:py-16">
            <Bell className="h-12 w-12 sm:h-16 sm:w-16 text-secondary-400 mx-auto mb-4" />
            <h3 className="text-base sm:text-lg font-semibold text-secondary-900 mb-2">
              No Notifications Yet
            </h3>
            <p className="text-sm sm:text-base text-secondary-600">
              You'll receive notifications when monitored content changes
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {notifications.map((notification) => (
            <div 
              key={notification.id} 
              className={`card ${!notification.is_read ? 'border-l-4 border-l-primary-500 bg-primary-50' : ''}`}
            >
              <div className="card-body p-3 sm:p-4">
                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    checked={selectedNotifications.includes(notification.id)}
                    onChange={() => handleSelectNotification(notification.id)}
                    className="checkbox mt-1"
                  />
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        {getNotificationIcon(notification.notification_type)}
                        <h3 className="text-sm sm:text-base font-semibold text-secondary-900 truncate">
                          {notification.title}
                        </h3>
                        {!notification.is_read && isRecentNotification(notification.created_at) && (
                          <span className="px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded-full flex-shrink-0">
                            New
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 flex-shrink-0">
                        <span className="text-xs text-secondary-500">
                          {formatDate(notification.created_at)}
                        </span>
                        <button
                          onClick={() => handleDeleteNotification(notification.id)}
                          className="btn btn-sm btn-danger p-1"
                          title="Delete"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                    
                    {/* Compact preview - only show first 80 characters */}
                    <p className="text-xs sm:text-sm text-secondary-600 mt-1 line-clamp-2">
                      {notification.message.length > 80 
                        ? `${notification.message.substring(0, 80)}...` 
                        : notification.message}
                    </p>
                    
                    {/* Source info - only show if available */}
                    {notification.source_type && (
                      <div className="mt-2 text-xs text-secondary-500 flex items-center">
                        <span className="mr-2">Source:</span>
                        <span className="truncate">{notification.source_type}</span>
                        {notification.source && (
                          <span className="ml-1 truncate">- {notification.source}</span>
                        )}
                      </div>
                    )}
                    
                    {/* Action link - only show if URL exists */}
                    {notification.data && notification.data.url && (
                      <div className="mt-2">
                        <a
                          href={notification.data.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-800 text-xs sm:text-sm inline-flex items-center"
                        >
                          <span className="hidden sm:inline">View monitored page</span>
                          <span className="sm:hidden">View page</span>
                          <span className="ml-1">→</span>
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Notifications; 