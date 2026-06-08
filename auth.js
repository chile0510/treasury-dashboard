// ============================================
// GOOGLE AUTH — Restrict to @ghn.vn domain
// ============================================

const ALLOWED_DOMAIN = 'ghn.vn';

// Check if already authenticated this session
(function checkExistingAuth() {
    const savedUser = sessionStorage.getItem('treasury_user');
    if (savedUser) {
        const user = JSON.parse(savedUser);
        if (user.email && user.email.endsWith('@' + ALLOWED_DOMAIN)) {
            showDashboard(user);
            return;
        }
    }
    // Show login, hide dashboard
    document.getElementById('login-overlay').style.display = 'flex';
    document.getElementById('app-header').style.display = 'none';
    document.getElementById('dashboard-main').style.display = 'none';
    document.getElementById('app-footer').style.display = 'none';
})();

// Google Sign-In callback
function handleGoogleLogin(response) {
    // Decode JWT token
    const payload = JSON.parse(atob(response.credential.split('.')[1]));
    const email = payload.email;
    const name = payload.name;
    const picture = payload.picture;

    // Check domain
    if (!email.endsWith('@' + ALLOWED_DOMAIN)) {
        const errorEl = document.getElementById('login-error');
        errorEl.textContent = '⛔ Email ' + email + ' khong duoc phep truy cap. Chi chap nhan @' + ALLOWED_DOMAIN;
        errorEl.style.display = 'block';

        // Revoke the token
        google.accounts.id.revoke(email);
        return;
    }

    // Save to session
    const user = { email, name, picture };
    sessionStorage.setItem('treasury_user', JSON.stringify(user));
    showDashboard(user);
}

function showDashboard(user) {
    // Hide login
    document.getElementById('login-overlay').style.display = 'none';

    // Show dashboard
    document.getElementById('app-header').style.display = 'flex';
    document.getElementById('dashboard-main').style.display = 'block';
    document.getElementById('app-footer').style.display = 'block';

    // Add user info to header
    const headerRight = document.querySelector('.header-right');
    if (!document.getElementById('user-badge')) {
        const userBadge = document.createElement('div');
        userBadge.id = 'user-badge';
        userBadge.className = 'header-badge user-badge';
        userBadge.innerHTML = `
            <img src="${user.picture || ''}" alt="" class="user-avatar" onerror="this.style.display='none'">
            <span>${user.name || user.email}</span>
            <button id="btn-logout" class="btn-logout" title="Dang xuat">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            </button>
        `;
        headerRight.appendChild(userBadge);

        // Logout handler
        document.getElementById('btn-logout').addEventListener('click', () => {
            sessionStorage.removeItem('treasury_user');
            google.accounts.id.disableAutoSelect();
            location.reload();
        });
    }
}
