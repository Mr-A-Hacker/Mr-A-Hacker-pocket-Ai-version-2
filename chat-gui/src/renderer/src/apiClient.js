import { API_BASE_URL } from './config.js';

/**
 * Fetch with resp.ok check. Throws with a message if not ok.
 * @param {string} path - Path relative to API_BASE_URL (e.g. '/conversations')
 * @param {RequestInit} [options] - fetch options
 * @returns {Promise<unknown>} - Parsed JSON body
 */
export async function apiFetch(path, options = {}) {
    const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;
    const res = await fetch(url, options);
    let body;
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
        try {
            body = await res.json();
        } catch {
            body = null;
        }
    } else {
        body = null;
    }
    if (!res.ok) {
        let msg = null;
        if (body != null) {
            if (body.detail != null) msg = body.detail;
            else if (body.message != null) msg = body.message;
            else if (typeof body === 'string') msg = body;
        }
        if (msg == null) msg = res.statusText || `Request failed (${res.status})`;
        const err = new Error(msg);
        err.status = res.status;
        err.body = body;
        throw err;
    }
    return body;
}
