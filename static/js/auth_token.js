/**
 * JWT Token Auto-Refresh Module for MahaInsight
 * Automatically refreshes access token before expiry
 * Handles 401 errors by attempting token refresh
 */

// Configuration
const TOKEN_REFRESH_INTERVAL = 14 * 60 * 1000; // 14 minutes (refresh 1 min before 15 min expiry)
const TOKEN_EXPIRY_BUFFER = 60 * 1000; // 1 minute buffer before expiry
const RETRY_DELAY = 500; // 500ms delay before retry after refresh

let refreshTimeout = null;
let isRefreshing = false;
let refreshPromise = null;

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
 * Get token expiry time from payload
 */
function getTokenExpiry(payload) {
    if (payload && payload.exp) {
        return payload.exp * 1000; // Convert to milliseconds
    }
    return null;
}

/**
 * Check if token is expired or about to expire
 */
function isTokenExpiredOrExpiring(expiry) {
    if (!expiry) return true;
    const now = Date.now();
    return (expiry - now) < TOKEN_EXPIRY_BUFFER;
}

/**
 * Refresh access token - returns a promise to handle concurrent refresh requests
 */
async function refreshToken() {
    // If already refreshing, return the existing promise
    if (isRefreshing && refreshPromise) {
        console.log('Token refresh already in progress, waiting...');
        return refreshPromise;
    }

    isRefreshing = true;

    refreshPromise = (async () => {
        try {
            console.log('Refreshing access token...');
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
                return true;
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('Token refresh failed:', response.status, errorData);

                // If refresh fails with 401, session is truly expired
                if (response.status === 401) {
                    console.log('Refresh token invalid or expired, redirecting to login');
                    // Don't redirect if we're on auth pages
                    if (!window.location.pathname.startsWith('/login') &&
                        !window.location.pathname.startsWith('/register')) {
                        window.location.href = '/login?expired=1';
                    }
                }

                return false;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        } finally {
            isRefreshing = false;
            refreshPromise = null;
        }
    })();

    return refreshPromise;
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
        console.log('Auto-refreshing token (scheduled)...');
        refreshToken();
    }, TOKEN_REFRESH_INTERVAL);

    console.log(`Next token refresh scheduled in ${TOKEN_REFRESH_INTERVAL / 1000 / 60} minutes`);
}

/**
 * Check authentication status and refresh if needed
 * Called on page load to ensure we have a valid access token
 */
async function checkAndRefreshToken() {
    try {
        // Make a lightweight check to our auth status endpoint
        const response = await fetch('/api/auth/status', {
            method: 'GET',
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            if (data.authenticated) {
                console.log('User authenticated, access token valid');
                scheduleTokenRefresh();
                return true;
            }
        }

        // Access token invalid/expired, try to refresh
        if (response.status === 401) {
            console.log('Access token expired, attempting refresh...');
            return await refreshToken();
        }

        return false;
    } catch (error) {
        console.error('Auth check error:', error);
        // On error, try to refresh token anyway
        return await refreshToken();
    }
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
                // Retry original request after short delay
                console.log('Retrying original request...');
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
                response = await fetch(url, options);
            } else {
                // Refresh failed, will be redirected by refreshToken
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
    console.log('JWT auto-refresh initializing...');

    // Check and refresh token immediately on page load
    checkAndRefreshToken().then(success => {
        if (success) {
            console.log('JWT auto-refresh active');
        } else {
            console.log('Initial token refresh may have failed, will retry on next API call');
        }
    });
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
window.checkAndRefreshToken = checkAndRefreshToken;

