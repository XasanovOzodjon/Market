/* ═══════════════════════════════════════════
   API HELPER — Market Frontend
   ═══════════════════════════════════════════ */

const API_BASE = (window.APP_CONFIG && window.APP_CONFIG.BACKEND_URL) 
    ? window.APP_CONFIG.BACKEND_URL + "/api/v1" 
    : "http://127.0.0.1:8000/api/v1";

// ── Token boshqaruvi ──
function getAccessToken() {
    return localStorage.getItem("access_token");
}

function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

function setTokens(access, refresh) {
    localStorage.setItem("access_token", access);
    if (refresh) localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

// ── Asosiy fetch wrapper ──
async function apiFetch(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;

    const headers = options.headers || {};

    // Agar FormData bo'lmasa Content-Type qo'shamiz
    if (!(options.body instanceof FormData)) {
        headers["Content-Type"] = headers["Content-Type"] || "application/json";
    }

    const token = getAccessToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    let res = await fetch(url, { ...options, headers });

    // 401 → tokenni yangilash
    if (res.status === 401 && getRefreshToken()) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            headers["Authorization"] = `Bearer ${getAccessToken()}`;
            res = await fetch(url, { ...options, headers });
        } else {
            clearTokens();
            if (typeof updateAuthUI === "function") updateAuthUI();
        }
    }

    return res;
}

async function refreshAccessToken() {
    try {
        const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: getRefreshToken() }),
        });
        if (res.ok) {
            const data = await res.json();
            setTokens(data.access, data.refresh || getRefreshToken());
            return true;
        }
    } catch (e) {
        console.error("Token refresh xatolik:", e);
    }
    return false;
}

// ── Qulay API metodlar ──
const api = {
    get: (endpoint) => apiFetch(endpoint).then(r => r.json()),

    post: (endpoint, body) =>
        apiFetch(endpoint, {
            method: "POST",
            body: JSON.stringify(body),
        }),

    put: (endpoint, body) =>
        apiFetch(endpoint, {
            method: "PUT",
            body: JSON.stringify(body),
        }),

    patch: (endpoint, body) =>
        apiFetch(endpoint, {
            method: "PATCH",
            body: JSON.stringify(body),
        }),

    delete: (endpoint) =>
        apiFetch(endpoint, { method: "DELETE" }),

    upload: (endpoint, formData) =>
        apiFetch(endpoint, {
            method: "POST",
            body: formData,
        }),
};
