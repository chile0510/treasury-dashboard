// ============================================
// GOOGLE AUTH — Server-Side Verification
// ============================================

const ALLOWED_DOMAIN = 'ghn.vn';

// Check if already authenticated this session
(async function checkExistingAuth() {
    try {
        const res = await fetch('/api/auth/me', { credentials: 'same-origin' });
        if (res.ok) {
            const user = await res.json();
            showDashboard(user);
            return;
        }
    } catch (e) {
        // API not available, fall through to login
    }
    // Show login, hide dashboard
    document.getElementById('login-overlay').style.display = 'flex';
    document.getElementById('app-header').style.display = 'none';
    document.getElementById('dashboard-main').style.display = 'none';
    document.getElementById('app-footer').style.display = 'none';
})();

// Google Sign-In callback — sends credential to SERVER for verification
async function handleGoogleLogin(response) {
    const errorEl = document.getElementById('login-error');
    errorEl.style.display = 'none';

    try {
        const res = await fetch('/api/auth/google', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credential: response.credential })
        });

        const data = await res.json();

        if (!res.ok) {
            errorEl.textContent = data.error || 'Đăng nhập thất bại';
            errorEl.style.display = 'block';
            return;
        }

        // Server verified OK and set httpOnly cookie
        showDashboard(data);
        // Now load financial data from authenticated API
        if (typeof loadDataAfterAuth === 'function') {
            loadDataAfterAuth();
        }

    } catch (e) {
        errorEl.textContent = 'Lỗi kết nối server. Vui lòng thử lại.';
        errorEl.style.display = 'block';
    }
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

        // Safe DOM construction — no innerHTML with user data
        const img = document.createElement('img');
        img.className = 'user-avatar';
        img.alt = '';
        if (user.picture && user.picture.startsWith('https://')) {
            img.src = user.picture;
        }
        img.onerror = function() { this.style.display = 'none'; };

        const nameSpan = document.createElement('span');
        nameSpan.textContent = user.name || user.email;

        const logoutBtn = document.createElement('button');
        logoutBtn.id = 'btn-logout';
        logoutBtn.className = 'btn-logout';
        logoutBtn.title = 'Đăng xuất';
        // Safe SVG construction via DOM API
        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.setAttribute('width', '14'); svg.setAttribute('height', '14');
        svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '2');
        const path = document.createElementNS(svgNS, 'path');
        path.setAttribute('d', 'M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4');
        const polyline = document.createElementNS(svgNS, 'polyline');
        polyline.setAttribute('points', '16 17 21 12 16 7');
        const line = document.createElementNS(svgNS, 'line');
        line.setAttribute('x1', '21'); line.setAttribute('y1', '12');
        line.setAttribute('x2', '9'); line.setAttribute('y2', '12');
        svg.appendChild(path); svg.appendChild(polyline); svg.appendChild(line);
        logoutBtn.appendChild(svg);

        userBadge.appendChild(img);
        userBadge.appendChild(nameSpan);
        userBadge.appendChild(logoutBtn);
        headerRight.appendChild(userBadge);

        // Logout handler — calls server to clear httpOnly cookie
        logoutBtn.addEventListener('click', async () => {
            await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
            google.accounts.id.disableAutoSelect();
            location.reload();
        });
    }
}
