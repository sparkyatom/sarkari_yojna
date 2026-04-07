/* ═══════════════════════════════════════════════════
   api.js — All HTTP calls to the Django REST backend
   Base URL: http://localhost:8000/api
═══════════════════════════════════════════════════ */

const API_BASE = 'http://127.0.0.1:8000/api';

// ─── TOKEN HELPERS ───
const Auth = {
  getToken()  { return localStorage.getItem('sy_access_token'); },
  getRefresh(){ return localStorage.getItem('sy_refresh_token'); },
  setTokens(access, refresh) {
    localStorage.setItem('sy_access_token', access);
    localStorage.setItem('sy_refresh_token', refresh);
  },
  clearTokens() {
    localStorage.removeItem('sy_access_token');
    localStorage.removeItem('sy_refresh_token');
    localStorage.removeItem('sy_user');
  },
  getUser()  { 
    const u = localStorage.getItem('sy_user');
    return u ? JSON.parse(u) : null;
  },
  setUser(u) { localStorage.setItem('sy_user', JSON.stringify(u)); },
  isLoggedIn(){ return !!this.getToken(); },
  isAdmin()  { const u = this.getUser(); return u && u.is_admin; }
};

// ─── CORE FETCH WRAPPER ───
async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  const isAuthFree = path.includes('/auth/login') || path.includes('/auth/register');
  const token = Auth.getToken();
  if (token && !isAuthFree) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  // Token expired → try refresh
  if (res.status === 401 && Auth.getRefresh()) {
    const refreshed = await refreshToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${Auth.getToken()}`;
      const retry = await fetch(`${API_BASE}${path}`, {
        ...options, headers,
        body: options.body ? JSON.stringify(options.body) : undefined
      });
      const data = await retry.json();
      if (!retry.ok) throw data;
      return data;
    } else {
      Auth.clearTokens();
      window.location.href = '/login.html';
      return;
    }
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
  console.error("API Error:", data);
  throw data;
  }
  return data;
}

async function refreshToken() {
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: Auth.getRefresh() })
    });
    if (!res.ok) return false;
    const data = await res.json();
    Auth.setTokens(data.access, Auth.getRefresh());
    return true;
  } catch { return false; }
}

// Form data fetch (for file uploads)
async function apiFetchForm(path, formData) {
  const headers = {};
  const token = Auth.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST', headers, body: formData
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data;
  return data;
}

// ═══════════════════════════════════
// AUTH APIs
// ═══════════════════════════════════
const AuthAPI = {
  async register(payload) {
    return apiFetch('/auth/register/', { method: 'POST', body: payload });
  },
  async login(username, password) {
    const data = await apiFetch('/auth/login/', { method: 'POST', body: { username, password } });
    Auth.setTokens(data.access, data.refresh);
    Auth.setUser(data.user);
    return data;
  },
  async logout() {
    try { await apiFetch('/auth/logout/', { method: 'POST', body: { refresh: Auth.getRefresh() } }); }
    catch {}
    Auth.clearTokens();
  },
  async getProfile() {
    return apiFetch('/auth/profile/');
  },
  async updateProfile(payload) {
    return apiFetch('/auth/profile/', { method: 'PATCH', body: payload });
  }
};

// ═══════════════════════════════════
// SCHEMES APIs
// ═══════════════════════════════════
const SchemesAPI = {
  async list(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/schemes/${qs ? '?' + qs : ''}`);
  },
  async getEligible() {
    return apiFetch('/schemes/eligible/');
  },
  async getDetail(id) {
    return apiFetch(`/schemes/${id}/`);
  },
  async search(query) {
    return apiFetch(`/schemes/?search=${encodeURIComponent(query)}`);
  }
};

// ═══════════════════════════════════
// ADMIN APIs
// ═══════════════════════════════════
const AdminAPI = {
  async getStats() {
    return apiFetch('/admin/stats/');
  },
  async listSchemes(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/admin/schemes/${qs ? '?' + qs : ''}`);
  },
  async createScheme(payload) {
    return apiFetch('/admin/schemes/', { method: 'POST', body: payload });
  },
  async updateScheme(id, payload) {
    return apiFetch(`/admin/schemes/${id}/`, { method: 'PUT', body: payload });
  },
  async deleteScheme(id) {
    return apiFetch(`/admin/schemes/${id}/`, { method: 'DELETE' });
  },
  async uploadExcel(file) {
    const fd = new FormData();
    fd.append('file', file);
    return apiFetchForm('/admin/upload/excel/', fd);
  },
  async listUsers(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/admin/users/${qs ? '?' + qs : ''}`);
  },
  async getUploadHistory() {
    return apiFetch('/admin/uploads/');
  }
};



// ═══════════════════════════════════
// UI HELPERS (shared across pages)
// ═══════════════════════════════════

// Update navbar based on auth state
function updateNavbar() {
  const user = Auth.getUser();
  const userArea = document.getElementById('navbar-user-area');
  if (!userArea) return;
  if (user) {
    const initials = (user.name || user.username || 'U')[0].toUpperCase();
    userArea.innerHTML = `
      <div class="navbar-user">
        <span>${user.name || user.username}</span>
        <div class="navbar-avatar" onclick="handleLogout()">${initials}</div>
      </div>`;
  } else {
    userArea.innerHTML = `
      <div style="display:flex;gap:8px;">
        <a href="login.html" class="btn btn-ghost btn-sm">Login</a>
        <a href="signup.html" class="btn btn-primary btn-sm">Sign Up</a>
      </div>`;
  }
}

async function handleLogout() {
  await AuthAPI.logout();
  window.location.href = 'index.html';
}

// Toast notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container') 
    || (() => { const d=document.createElement('div'); d.id='toast-container'; document.body.appendChild(d); return d; })();
  
  const icons = { success:'✅', error:'❌', info:'ℹ️', warning:'⚠️' };
  const t = document.createElement('div');
  t.className = 'toast';
  if (type === 'error') t.style.borderLeftColor = 'var(--soft-red)';
  if (type === 'info') t.style.borderLeftColor = 'var(--gold)';
  t.innerHTML = `<span class="toast-icon">${icons[type]||'✅'}</span><span class="toast-msg">${message}</span>`;
  container.appendChild(t);
  setTimeout(() => { t.classList.add('removing'); setTimeout(()=>t.remove(), 300); }, 3500);
}

// Loading overlay
function showLoading(msg = 'Loading...') {
  let ov = document.getElementById('loading-overlay');
  if (!ov) {
    ov = document.createElement('div');
    ov.id = 'loading-overlay';
    ov.className = 'loading-overlay';
    ov.innerHTML = `<div class="spinner"></div><p>${msg}</p>`;
    document.body.appendChild(ov);
  }
  ov.querySelector('p').textContent = msg;
  ov.style.display = 'flex';
}
function hideLoading() {
  const ov = document.getElementById('loading-overlay');
  if (ov) ov.style.display = 'none';
}

// Modal helpers
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// Animated counter
function animateCounter(el, target, suffix = '') {
  let n = 0, duration = 1200, step = target / (duration / 16);
  const iv = setInterval(() => {
    n = Math.min(n + step, target);
    el.textContent = Math.round(n).toLocaleString('en-IN') + suffix;
    if (n >= target) clearInterval(iv);
  }, 16);
}

// Format currency
function formatINR(amount) {
  if (amount >= 100000) return `₹${(amount/100000).toFixed(1)}L`;
  if (amount >= 1000)   return `₹${(amount/1000).toFixed(0)}K`;
  return `₹${amount}`;
}

// Days left
function daysLeft(dateStr) {
  const d = new Date(dateStr) - new Date();
  return Math.ceil(d / 86400000);
}

// Format date
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' });
}

// Debounce
function debounce(fn, delay = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}
