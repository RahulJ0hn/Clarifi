import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../store/appStore';
import toast from 'react-hot-toast';
import { AlertCircle, Check, Info, X, VolumeX } from 'lucide-react';

export const useWebSocket = (url = 'ws://localhost:8000/ws') => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const { addNotification, updateMonitor } = useAppStore();

  const connect = () => {
    try {
      setConnectionStatus('connecting');
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        console.log('WebSocket connected');
        
        // Clear any existing reconnection timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        console.log('WebSocket disconnected');
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setConnectionStatus('disconnected');
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setConnectionStatus('disconnected');
    }
  };

  const handleMessage = (message) => {
    switch (message.type) {
      case 'notification':
        const notification = message.data;
        addNotification(notification);
        
        // Show modern toast notification with better styling and controls
        const showNotificationToast = () => {
          const toastId = toast.custom(
            (t) => (
              <div className={`${t.visible ? 'animate-enter' : 'animate-leave'} max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}>
                <div className="flex-1 w-0 p-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      {notification.notification_type === 'error' && <AlertCircle className="h-5 w-5 text-red-500" />}
                      {notification.notification_type === 'warning' && <AlertCircle className="h-5 w-5 text-yellow-500" />}
                      {notification.notification_type === 'success' && <Check className="h-5 w-5 text-green-500" />}
                      {notification.notification_type === 'info' && <Info className="h-5 w-5 text-blue-500" />}
                    </div>
                    <div className="ml-3 flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {notification.title}
                      </p>
                      <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                        {notification.message.length > 120 
                          ? notification.message.substring(0, 120) + '...' 
                          : notification.message
                        }
                      </p>
                      {notification.message.length > 120 && (
                        <button
                          onClick={() => {
                            toast.dismiss(t.id);
                            // Show detailed view in a modal or expand the notification
                            showDetailedNotification(notification);
                          }}
                          className="mt-2 text-xs text-blue-600 hover:text-blue-800 font-medium"
                        >
                          View Details
                        </button>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex flex-col border-l border-gray-200">
                  <button
                    onClick={() => toast.dismiss(t.id)}
                    className="w-full border border-transparent rounded-none rounded-tr-lg p-4 flex items-center justify-center text-sm font-medium text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      toast.dismiss(t.id);
                      // Add mute functionality here
                      console.log('Muted notification from monitor:', notification.source);
                    }}
                    className="w-full border border-transparent rounded-none rounded-br-lg p-4 flex items-center justify-center text-sm font-medium text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <VolumeX className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ),
            {
              duration: 10000,
              position: 'top-right',
            }
          );
        };
        
        // Function to show detailed notification
        const showDetailedNotification = (notification) => {
          toast.custom(
            (t) => (
              <div className={`${t.visible ? 'animate-enter' : 'animate-leave'} max-w-lg w-full bg-white shadow-xl rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5`}>
                <div className="p-6">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      {notification.notification_type === 'error' && <AlertCircle className="h-6 w-6 text-red-500" />}
                      {notification.notification_type === 'warning' && <AlertCircle className="h-6 w-6 text-yellow-500" />}
                      {notification.notification_type === 'success' && <Check className="h-6 w-6 text-green-500" />}
                      {notification.notification_type === 'info' && <Info className="h-6 w-6 text-blue-500" />}
                    </div>
                    <div className="ml-3 flex-1">
                      <p className="text-lg font-semibold text-gray-900 mb-2">
                        {notification.title}
                      </p>
                      <div className="text-sm text-gray-600 space-y-2 max-h-64 overflow-y-auto">
                        {notification.message.split('\n').map((line, index) => (
                          <p key={index} className="whitespace-pre-wrap">{line}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end space-x-2">
                    <button
                      onClick={() => toast.dismiss(t.id)}
                      className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800"
                    >
                      Close
                    </button>
                    <button
                      onClick={() => {
                        toast.dismiss(t.id);
                        // Mark as read functionality
                        console.log('Marked as read:', notification.id);
                      }}
                      className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800"
                    >
                      Mark as Read
                    </button>
                  </div>
                </div>
              </div>
            ),
            {
              duration: 15000,
              position: 'top-right',
            }
          );
        };
        
        // Show different types of notifications
        switch (notification.notification_type) {
          case 'success':
            toast.success(
              `${notification.title}: ${notification.message.substring(0, 80)}${notification.message.length > 80 ? '...' : ''}`,
              { duration: 6000 }
            );
            break;
          case 'error':
            toast.error(
              `${notification.title}: ${notification.message.substring(0, 80)}${notification.message.length > 80 ? '...' : ''}`,
              { duration: 8000 }
            );
            break;
          case 'warning':
            toast(
              `${notification.title}: ${notification.message.substring(0, 80)}${notification.message.length > 80 ? '...' : ''}`,
              { 
                icon: '⚠️',
                duration: 7000,
                style: {
                  borderLeft: '4px solid #f59e0b',
                }
              }
            );
            break;
          default:
            // For monitor alerts, show a more detailed but compact notification
            if (notification.title.includes('Monitor Alert')) {
              showNotificationToast();
            } else {
              toast(
                `${notification.title}: ${notification.message.substring(0, 80)}${notification.message.length > 80 ? '...' : ''}`,
                { duration: 6000 }
              );
            }
        }
        break;
        
      case 'monitor_update':
        const monitorUpdate = message.data;
        updateMonitor(monitorUpdate.monitor_id, {
          current_value: monitorUpdate.current_value,
          last_checked: monitorUpdate.last_checked,
          ...(monitorUpdate.has_changed && { last_changed: monitorUpdate.last_checked })
        });
        break;
        
      case 'system_status':
        // Handle system status updates
        console.log('System status update:', message.data);
        break;
        
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [url]);

  return {
    isConnected,
    connectionStatus,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}; 