import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export const useAppStore = create()(
  devtools(
    persist(
      (set, get) => ({
        // Initial State
        ui: {
          sidebarOpen: false,
          currentUrl: '',
          loading: false,
          error: null,
          toast: null,
        },
        
        // Data with pagination and loading states
        summaries: {
          items: [],
          loading: false,
          error: null,
          pagination: {
            page: 1,
            per_page: 20,
            total: 0,
            has_more: false,
          },
        },
        
        monitors: {
          items: [],
          loading: false,
          error: null,
          pagination: {
            page: 1,
            per_page: 20,
            total: 0,
            has_more: false,
          },
        },
        
        notifications: {
          items: [],
          loading: false,
          error: null,
          pagination: {
            page: 1,
            per_page: 20,
            total: 0,
            has_more: false,
          },
        },
        
        currentSummary: null,
        
        stats: {
          summaries: null,
          monitors: null,
          notifications: null,
          loading: false,
          error: null,
        },
        
        // UI Actions
        toggleSidebar: () => {
          set((state) => ({
            ui: {
              ...state.ui,
              sidebarOpen: !state.ui.sidebarOpen,
            },
          }));
        },
        
        setSidebarOpen: (open) => {
          set((state) => ({
            ui: {
              ...state.ui,
              sidebarOpen: open,
            },
          }));
        },
        
        setCurrentUrl: (url) => {
          set((state) => ({
            ui: {
              ...state.ui,
              currentUrl: url,
            },
          }));
        },
        
        setLoading: (loading) => {
          set((state) => ({
            ui: {
              ...state.ui,
              loading,
            },
          }));
        },
        
        setError: (error) => {
          set((state) => ({
            ui: {
              ...state.ui,
              error,
            },
          }));
        },
        
        showToast: (toast) => {
          set((state) => ({
            ui: {
              ...state.ui,
              toast,
            },
          }));
        },
        
        clearToast: () => {
          set((state) => ({
            ui: {
              ...state.ui,
              toast: null,
            },
          }));
        },
        
        // Summary Actions
        setSummariesLoading: (loading) => {
          set((state) => ({
            summaries: {
              ...state.summaries,
              loading,
            },
          }));
        },
        
        setSummariesError: (error) => {
          set((state) => ({
            summaries: {
              ...state.summaries,
              error,
              loading: false,
            },
          }));
        },
        
        setSummaries: (summaries, pagination = null) => {
          set((state) => ({
            summaries: {
              ...state.summaries,
              items: summaries,
              loading: false,
              error: null,
              pagination: pagination || state.summaries.pagination,
            },
          }));
        },
        
        addSummary: (summary) => {
          set((state) => ({
            summaries: {
              ...state.summaries,
              items: [summary, ...state.summaries.items],
              pagination: {
                ...state.summaries.pagination,
                total: state.summaries.pagination.total + 1,
              },
            },
          }));
        },
        
        updateSummary: (id, updates) => {
          set((state) => ({
            summaries: {
              ...state.summaries,
              items: state.summaries.items.map((summary) =>
                summary.id === id ? { ...summary, ...updates } : summary
              ),
            },
          }));
        },
        
        removeSummary: (id) => {
          set((state) => ({
            summaries: {
              ...state.summaries,
              items: state.summaries.items.filter((summary) => summary.id !== id),
              pagination: {
                ...state.summaries.pagination,
                total: Math.max(0, state.summaries.pagination.total - 1),
              },
            },
          }));
        },
        
        setCurrentSummary: (summary) => {
          set({ currentSummary: summary });
        },
        
        // Monitor Actions
        setMonitorsLoading: (loading) => {
          set((state) => ({
            monitors: {
              ...state.monitors,
              loading,
            },
          }));
        },
        
        setMonitorsError: (error) => {
          set((state) => ({
            monitors: {
              ...state.monitors,
              error,
              loading: false,
            },
          }));
        },
        
        setMonitors: (monitors, pagination = null) => {
          set((state) => ({
            monitors: {
              ...state.monitors,
              items: monitors,
              loading: false,
              error: null,
              pagination: pagination || state.monitors.pagination,
            },
          }));
        },
        
        addMonitor: (monitor) => {
          set((state) => ({
            monitors: {
              ...state.monitors,
              items: [monitor, ...state.monitors.items],
              pagination: {
                ...state.monitors.pagination,
                total: state.monitors.pagination.total + 1,
              },
            },
          }));
        },
        
        updateMonitor: (id, updates) => {
          set((state) => ({
            monitors: {
              ...state.monitors,
              items: state.monitors.items.map((monitor) =>
                monitor.id === id ? { ...monitor, ...updates } : monitor
              ),
            },
          }));
        },
        
        removeMonitor: (id) => {
          set((state) => ({
            monitors: {
              ...state.monitors,
              items: state.monitors.items.filter((monitor) => monitor.id !== id),
              pagination: {
                ...state.monitors.pagination,
                total: Math.max(0, state.monitors.pagination.total - 1),
              },
            },
          }));
        },
        
        // Notification Actions
        setNotificationsLoading: (loading) => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              loading,
            },
          }));
        },
        
        setNotificationsError: (error) => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              error,
              loading: false,
            },
          }));
        },
        
        setNotifications: (notifications, pagination = null) => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              items: notifications,
              loading: false,
              error: null,
              pagination: pagination || state.notifications.pagination,
            },
          }));
        },
        
        addNotification: (notification) => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              items: [notification, ...state.notifications.items],
              pagination: {
                ...state.notifications.pagination,
                total: state.notifications.pagination.total + 1,
              },
            },
          }));
        },
        
        markNotificationRead: (id) => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              items: state.notifications.items.map((notification) =>
                notification.id === id
                  ? { ...notification, is_read: true, read_at: new Date().toISOString() }
                  : notification
              ),
            },
          }));
        },
        
        markAllNotificationsRead: () => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              items: state.notifications.items.map((notification) => ({
                ...notification,
                is_read: true,
                read_at: new Date().toISOString(),
              })),
            },
          }));
        },
        
        removeNotification: (id) => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              items: state.notifications.items.filter(
                (notification) => notification.id !== id
              ),
              pagination: {
                ...state.notifications.pagination,
                total: Math.max(0, state.notifications.pagination.total - 1),
              },
            },
          }));
        },
        
        // Stats Actions
        setStatsLoading: (loading) => {
          set((state) => ({
            stats: {
              ...state.stats,
              loading,
            },
          }));
        },
        
        setStatsError: (error) => {
          set((state) => ({
            stats: {
              ...state.stats,
              error,
              loading: false,
            },
          }));
        },
        
        setSummaryStats: (stats) => {
          set((state) => ({
            stats: {
              ...state.stats,
              summaries: stats,
              loading: false,
              error: null,
            },
          }));
        },
        
        setMonitorStats: (stats) => {
          set((state) => ({
            stats: {
              ...state.stats,
              monitors: stats,
              loading: false,
              error: null,
            },
          }));
        },
        
        setNotificationStats: (stats) => {
          set((state) => ({
            stats: {
              ...state.stats,
              notifications: stats,
              loading: false,
              error: null,
            },
          }));
        },
        
        // WebSocket Actions for real-time updates
        handleWebSocketMessage: (message) => {
          const { type, data } = message;
          
          switch (type) {
            case 'notification':
              get().addNotification(data);
              get().showToast({
                type: 'info',
                title: 'New Notification',
                message: data.title,
              });
              break;
              
            case 'monitor_update':
              get().updateMonitor(data.id, data);
              get().showToast({
                type: 'info',
                title: 'Monitor Update',
                message: `Monitor "${data.name}" has been updated`,
              });
              break;
              
            case 'system_status':
              // Handle system status updates
              break;
              
            default:
              console.log('Unknown WebSocket message type:', type);
          }
        },
        
        // Utility actions
        resetStore: () => {
          set({
            ui: {
              sidebarOpen: false,
              currentUrl: '',
              loading: false,
              error: null,
              toast: null,
            },
            summaries: {
              items: [],
              loading: false,
              error: null,
              pagination: { page: 1, per_page: 20, total: 0, has_more: false },
            },
            monitors: {
              items: [],
              loading: false,
              error: null,
              pagination: { page: 1, per_page: 20, total: 0, has_more: false },
            },
            notifications: {
              items: [],
              loading: false,
              error: null,
              pagination: { page: 1, per_page: 20, total: 0, has_more: false },
            },
            currentSummary: null,
            stats: {
              summaries: null,
              monitors: null,
              notifications: null,
              loading: false,
              error: null,
            },
          });
        },
      }),
      {
        name: 'clarifi-store',
        partialize: (state) => ({
          ui: {
            sidebarOpen: state.ui.sidebarOpen,
            currentUrl: state.ui.currentUrl,
          },
          summaries: {
            items: state.summaries.items.slice(0, 10),
            pagination: state.summaries.pagination,
          },
          monitors: {
            items: state.monitors.items,
            pagination: state.monitors.pagination,
          },
          notifications: {
            items: state.notifications.items.slice(0, 50),
            pagination: state.notifications.pagination,
          },
          stats: state.stats,
        }),
      }
    ),
    {
      name: 'clarifi-store',
    }
  )
); 