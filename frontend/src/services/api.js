const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api';

class ApiService {
  async getClerkToken() {
    try {
      // Check if Clerk is available in window object
      if (typeof window !== 'undefined' && window.Clerk && window.Clerk.session) {
        const token = await window.Clerk.session.getToken();
        console.log('🔑 Clerk token debug:', {
          hasToken: !!token,
          tokenLength: token ? token.length : 0,
          tokenPreview: token ? token.substring(0, 50) + '...' : 'No token'
        });
        return token;
      } else {
        console.log('❌ Clerk not available in window object');
        return null;
      }
    } catch (error) {
      console.error('❌ Clerk token retrieval error:', error);
      return null;
    }
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Get Clerk token
    const token = await this.getClerkToken();
    let authHeader = {};
    
    if (token) {
      authHeader = { 'Authorization': `Bearer ${token}` };
      console.log('✅ Auth header created with token');
    } else {
      console.log('❌ No Clerk token available');
    }
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...authHeader,
        ...options.headers,
      },
      ...options,
    };

    console.log('🚀 Making API request:', {
      url,
      method: config.method || 'GET',
      hasAuthHeader: !!authHeader.Authorization,
      body: config.body || 'No body'
    });

    try {
      const response = await fetch(url, config);
      
      console.log('📥 API response:', {
        status: response.status,
        statusText: response.statusText,
        url: response.url
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      console.log('✅ API success:', data);
      return data;
    } catch (error) {
      console.error('💥 API request failed:', {
        message: error.message,
        endpoint,
        url,
        error
      });
      throw error;
    }
  }

  // Summarization API
  async summarizeUrl(url, question = '') {
    return this.request('/summarize', {
      method: 'POST',
      body: JSON.stringify({ url, question }),
    });
  }

  async getSummaries(page = 1, perPage = 20, urlFilter = null) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    if (urlFilter) {
      params.append('url_filter', urlFilter);
    }
    
    return this.request(`/summaries?${params}`);
  }

  async getSummary(summaryId) {
    return this.request(`/summaries/${summaryId}`);
  }

  async deleteSummary(summaryId) {
    return this.request(`/summaries/${summaryId}`, {
      method: 'DELETE',
    });
  }

  async getSummaryStats() {
    return this.request('/stats');
  }

  // Monitor API
  async createMonitor(monitorData) {
    return this.request('/monitors', {
      method: 'POST',
      body: JSON.stringify(monitorData),
    });
  }

  async getMonitors(page = 1, perPage = 20, activeOnly = false, monitorType = null) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      active_only: activeOnly.toString(),
    });
    
    if (monitorType) {
      params.append('monitor_type', monitorType);
    }
    
    return this.request(`/monitors?${params}`);
  }

  async getMonitor(monitorId) {
    return this.request(`/monitors/${monitorId}`);
  }

  async updateMonitor(monitorId, updates) {
    return this.request(`/monitors/${monitorId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteMonitor(monitorId) {
    return this.request(`/monitors/${monitorId}`, {
      method: 'DELETE',
    });
  }

  async checkMonitor(monitorId) {
    return this.request(`/monitors/${monitorId}/check`, {
      method: 'POST',
    });
  }

  async getMonitorStatus(monitorId) {
    return this.request(`/monitors/${monitorId}/status`);
  }

  async toggleMonitor(monitorId) {
    return this.request(`/monitors/${monitorId}/toggle`, {
      method: 'POST',
    });
  }

  async getMonitorTypes() {
    return this.request('/monitors/types');
  }

  async getMonitorStats() {
    return this.request('/monitors/stats');
  }

  // Notification API
  async getNotifications(page = 1, perPage = 20, unreadOnly = false, notificationType = null) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      unread_only: unreadOnly.toString(),
    });
    
    if (notificationType) {
      params.append('notification_type', notificationType);
    }
    
    return this.request(`/notifications?${params}`);
  }

  async getNotification(notificationId) {
    return this.request(`/notifications/${notificationId}`);
  }

  async markNotificationsRead(notificationIds) {
    return this.request('/notifications/mark-read', {
      method: 'POST',
      body: JSON.stringify({ notification_ids: notificationIds }),
    });
  }

  async markAllNotificationsRead() {
    return this.request('/notifications/mark-all-read', {
      method: 'POST',
    });
  }

  async deleteNotification(notificationId) {
    return this.request(`/notifications/${notificationId}`, {
      method: 'DELETE',
    });
  }

  async createNotification(notificationData) {
    return this.request('/notifications', {
      method: 'POST',
      body: JSON.stringify(notificationData),
    });
  }

  async getNotificationStats() {
    return this.request('/notifications/stats');
  }

  async getUnreadCount() {
    return this.request('/notifications/unread/count');
  }

  async getRecentNotifications(limit = 5) {
    try {
      const response = await this.request(`/notifications/recent?limit=${limit}`);
      // Handle both response formats for backward compatibility
      if (response.notifications) {
        return response.notifications; // New format
      } else if (Array.isArray(response)) {
        return response; // Old format
      } else {
        console.warn('Unexpected response format for recent notifications:', response);
        return [];
      }
    } catch (error) {
      console.error('Error fetching recent notifications:', error);
      // Return empty array on error to prevent UI crashes
      return [];
    }
  }

  // Health Check
  async healthCheck() {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${baseUrl}/health`);
    return response.json();
  }
}

export const apiService = new ApiService();
export default apiService; 