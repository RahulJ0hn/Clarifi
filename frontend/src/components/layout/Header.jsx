import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bell, Brain, Menu, X } from 'lucide-react';
import { UserButton } from '@clerk/clerk-react';
import { useAppStore } from '../../store/appStore';
import apiService from '../../services/api';

const Header = () => {
  const location = useLocation();
  const { notifications } = useAppStore();
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Fetch unread count from API
  useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        const stats = await apiService.getNotificationStats();
        setUnreadCount(stats.unread_notifications || 0);
      } catch (error) {
        console.error('Error fetching notification stats:', error);
        // Fallback to global store
        setUnreadCount(notifications.filter(n => !n.is_read).length);
      }
    };
    
    fetchUnreadCount();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [notifications]);

  // Listen for notification read events
  useEffect(() => {
    const handleNotificationRead = () => {
      // Immediately fetch updated count when notifications are marked as read
      const fetchUnreadCount = async () => {
        try {
          const stats = await apiService.getNotificationStats();
          setUnreadCount(stats.unread_notifications || 0);
        } catch (error) {
          console.error('Error fetching notification stats:', error);
        }
      };
      fetchUnreadCount();
    };

    // Listen for custom events when notifications are marked as read
    window.addEventListener('notification-read', handleNotificationRead);
    
    return () => {
      window.removeEventListener('notification-read', handleNotificationRead);
    };
  }, []);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: '📊' },
    { name: 'Summaries', href: '/summaries', icon: '📝' },
    { name: 'Monitors', href: '/monitors', icon: '👀' },
    { name: 'Notifications', href: '/notifications', icon: '🔔' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-secondary-200 shadow-sm h-16">
      <div className="px-4 sm:px-6 lg:px-8 h-full">
        <div className="flex items-center justify-between h-full">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <Brain className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-secondary-900">
                Clarifi
              </span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                  location.pathname === item.href
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.name}
              </Link>
            ))}
          </nav>

          {/* Right side actions */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <Link
              to="/notifications"
              className="relative p-2 text-secondary-400 hover:text-secondary-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 rounded-md"
            >
              <Bell className="h-6 w-6" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 h-5 w-5 bg-danger-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>
            
            {/* User Authentication */}
            <UserButton afterSignOutUrl="/" />

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-secondary-400 hover:text-secondary-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 rounded-md"
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Overlay */}
      {mobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setMobileMenuOpen(false)}
          />
          
          {/* Mobile Menu */}
          <div className="md:hidden fixed top-16 left-0 right-0 bg-white border-t border-secondary-200 shadow-lg z-50 transform transition-transform duration-300 ease-in-out">
            <div className="px-4 py-2 space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-3 py-3 rounded-md text-base font-medium transition-colors ${
                    location.pathname === item.href
                      ? 'bg-primary-50 text-primary-600 border-l-4 border-primary-500'
                      : 'text-secondary-500 hover:text-secondary-700 hover:bg-secondary-50'
                  }`}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        </>
      )}
    </header>
  );
};

export default Header; 