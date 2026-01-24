/**
 * Reactive Authentication Module for MahaInsight
 * Handles 401 errors by attempting token refresh
 * No timers, no client-side JWT decoding
 */

let isRefreshing = false;
let failedQueue = [];

/**
 * Add request to queue to be retried after refresh
 */
const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });

    failedQueue = [];
};

/**
 * Refresh access token
 * Handles concurrent calls by returning same promise or queuing
 */
async function refreshToken() {
    if (isRefreshing) {
        return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
        });
    }

    isRefreshing = true;

    try {
        console.log('Refreshing access token...');
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            console.log('Token refreshed successfully');
            processQueue(null, true);
            return true;
        } else {
            const errorData = await response.json().catch(() => ({}));
            console.error('Token refresh failed:', response.status, errorData);

            // If refresh fails (especially 401), session is dead
            if (response.status === 401) {
                console.log('Refresh token invalid or expired, redirecting to login');
                processQueue(new Error('Session expired'), null);

                // Only redirect if not already on login/register pages
                if (!window.location.pathname.startsWith('/login') &&
                    !window.location.pathname.startsWith('/register')) {
                    window.location.href = '/login?expired=1';
                }
            } else {
                processQueue(new Error('Refresh failed'), null);
            }

            return false;
        }
    } catch (error) {
        console.error('Token refresh network error:', error);
        processQueue(error, null);
        return false;
    } finally {
        isRefreshing = false;
    }
}

/**
 * Enhanced fetch wrapper that handles 401 errors
 */
async function authenticatedFetch(url, options = {}) {
    // Ensure credentials are included
    options.credentials = 'include';
    options.headers = options.headers || {};
    options.headers['X-Requested-With'] = 'XMLHttpRequest'; // Mark as AJAX

    try {
        let response = await fetch(url, options);

        // If 401, attempt token refresh and retry
        if (response.status === 401) {
            // Check if it's a "real" auth error or just lack of permission
            const data = await response.clone().json().catch(() => null);

            // Should retry only if error indicates expired/missing token, not standard forbidden
            if (data && (data.code === 'INVALID_TOKEN' || data.code === 'NO_TOKEN' || data.reason === 'access_token_expired')) {
                console.log('Received 401 (Token Expired), attempting refresh...');

                const success = await refreshToken();

                if (success) {
                    // Retry original request
                    console.log('Retrying original request...');
                    return await fetch(url, options);
                } else {
                    // Refresh failed, error will be handled by UI or redirect
                    throw new Error('Session expired');
                }
            }
        }

        return response;
    } catch (error) {
        console.error('Authenticated fetch error:', error);
        throw error;
    }
}

/**
 * Check authentication status without timers
 * Called on page load to set UI state
 */
async function checkAndRefreshToken() {
    try {
        const response = await fetch('/api/auth/status', {
            method: 'GET',
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            if (data.authenticated) {
                console.log('User authenticated');
                return true;
            }
        } else if (response.status === 401) {
            // If we get 401 on status check, we might be able to refresh immediately
            // This handles case where user comes back after tab sleep > 15 mins
            const data = await response.json();
            if (data.can_refresh) {
                console.log('Session stale, refreshing...');
                return await refreshToken();
            }
        }

        return false;
    } catch (error) {
        console.error('Auth check error:', error);
        return false;
    }
}

// Global available functions
window.authenticatedFetch = authenticatedFetch;
window.checkAndRefreshToken = checkAndRefreshToken;
window.refreshToken = refreshToken;

// Init on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        checkAndRefreshToken(); // Just check status once, no timers
    });
} else {
    checkAndRefreshToken();
}
