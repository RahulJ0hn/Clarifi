// JSDoc type definitions for the frontend application

/**
 * @typedef {Object} ApiResponse
 * @property {*} [data]
 * @property {string} [message]
 * @property {string} [error]
 */

/**
 * @typedef {Object} Summary
 * @property {string} id
 * @property {string} url
 * @property {string|null} title
 * @property {string} summary_text
 * @property {string|null} question
 * @property {string|null} response
 * @property {string} ai_provider
 * @property {number|null} processing_time
 * @property {string} created_at
 */

/**
 * @typedef {Object} SummaryRequest
 * @property {string} url
 * @property {string} [question]
 * @property {boolean} [include_content]
 * @property {string} [ai_provider]
 */

/**
 * @typedef {Object} Monitor
 * @property {string} id
 * @property {string} name
 * @property {string} url
 * @property {'content'|'price'|'selector'} monitor_type
 * @property {string|null} css_selector
 * @property {string|null} xpath_selector
 * @property {string|null} current_value
 * @property {string|null} previous_value
 * @property {number} check_interval
 * @property {boolean} is_active
 * @property {boolean} notification_enabled
 * @property {string|null} last_checked
 * @property {string|null} last_changed
 * @property {string} created_at
 * @property {string|null} updated_at
 * @property {Object|null} metadata
 */

/**
 * @typedef {Object} Notification
 * @property {string} id
 * @property {string} title
 * @property {string} message
 * @property {'info'|'warning'|'error'|'success'} notification_type
 * @property {string|null} source
 * @property {string|null} source_type
 * @property {boolean} is_read
 * @property {boolean} is_sent
 * @property {'low'|'normal'|'high'|'urgent'} priority
 * @property {string} created_at
 * @property {string|null} read_at
 * @property {string|null} sent_at
 * @property {Object|null} data
 */

/**
 * @typedef {Object} UIState
 * @property {boolean} sidebarOpen
 * @property {string} currentUrl
 * @property {boolean} loading
 * @property {string|null} error
 */

// Export empty object to make this a module
export {}; 