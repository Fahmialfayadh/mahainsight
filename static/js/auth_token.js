/**
 * JWT Token Auto-Refresh Module for MahaInsight
 * Automatically refreshes access token before expiry
 * Handles 401 errors by attempting token refresh
 */

// Configuration
const TOKEN_REFRESH_INTERVAL = 14 * 60 * 1000; // 14 minutes (refresh 1 min before 15 min expiry)
const RETRY_DELAY = 2000; // 2 seconds delay before retry after refresh

let refreshTimeout = null;
let isRefreshing = false;

/**
 * Decode JWT token to extract payload (client-side, for expiry check only)
 * Note: This doesn't verify the token, just reads the payload
 */
function decodeJWT(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error('Failed to decode JWT:', e);
        return null;
    }
}

/**
 * Get token expiry time
 */
function getTokenExpiry(token) {
    const payload = decodeJWT(token);
    if (payload && payload.exp) {
        return payload.exp * 1000; // Convert to milliseconds
    }
    return null;
}

/**
 * Check if token is about to expire (within 1 minute)
 */
function isTokenExpiring(token) {
    const expiry = getTokenExpiry(token);
    if (!expiry) return true;

    const now = Date.now();
    const timeUntilExpiry = expiry - now;

    // Refresh if less than 1 minute remaining
    return timeUntilExpiry < 60000;
}

/**
 * Refresh access token
 */
async function refreshToken() {
    if (isRefreshing) {
        console.log('Token refresh already in progress');
        return false;
    }

    isRefreshing = true;

    try {
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            credentials: 'include', // Important: include cookies
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            console.log('Token refreshed successfully');
            scheduleTokenRefresh(); // Schedule next refresh
            isRefreshing = false;
            return true;
        } else {
            console.error('Token refresh failed:', response.status);

            // If refresh fails with 401, redirect to login
            if (response.status === 401) {
                console.log('Refresh token invalid, redirecting to login');
                window.location.href = '/login';
            }

            isRefreshing = false;
            return false;
        }
    } catch (error) {
        console.error('Token refresh error:', error);
        isRefreshing = false;
        return false;
    }
}

/**
 * Schedule automatic token refresh
 */
function scheduleTokenRefresh() {
    // Clear existing timeout
    if (refreshTimeout) {
        clearTimeout(refreshTimeout);
    }

    // Schedule refresh after TOKEN_REFRESH_INTERVAL
    refreshTimeout = setTimeout(() => {
        console.log('Auto-refreshing token...');
        refreshToken();
    }, TOKEN_REFRESH_INTERVAL);

    console.log(`Token refresh scheduled in ${TOKEN_REFRESH_INTERVAL / 1000 / 60} minutes`);
}

/**
 * Enhanced fetch wrapper that handles 401 errors with token refresh
 */
async function authenticatedFetch(url, options = {}) {
    // Ensure credentials are included
    options.credentials = 'include';

    try {
        let response = await fetch(url, options);

        // If 401, attempt token refresh and retry
        if (response.status === 401) {
            console.log('Received 401, attempting token refresh...');

            const refreshed = await refreshToken();

            if (refreshed) {
                // Retry original request
                console.log('Retrying original request...');
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
                response = await fetch(url, options);
            } else {
                // Refresh failed, redirect to login
                console.log('Token refresh failed, redirecting to login');
                window.location.href = '/login';
                throw new Error('Authentication failed');
            }
        }

        return response;
    } catch (error) {
        console.error('Authenticated fetch error:', error);
        throw error;
    }
}

/**
 * Initialize auto-refresh on page load
 */
function initTokenRefresh() {
    // Start the auto-refresh cycle
    scheduleTokenRefresh();

    console.log('JWT auto-refresh initialized');
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTokenRefresh);
} else {
    initTokenRefresh();
}

// Export for use in other modules
window.authenticatedFetch = authenticatedFetch;
window.refreshToken = refreshToken;
