// ============================================
// TREASURY PORTFOLIO MANAGER — DASHBOARD JS
// ============================================
// DATA is loaded from authenticated server API only.
// No financial data is stored in this client-side file.

(function() {
'use strict';

let DATA = null;
let SESSION_TIMEOUT_ID = null;
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes auto-logout

// === SAFE DOM HELPERS (XSS Prevention) ===
function el(tag, className, textContent) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (textContent !== undefined) e.textContent = textContent;
    return e;
}

function addCells(tr, cells) {
    cells.forEach(c => {
        const td = document.createElement('td');
        if (c.className) td.className = c.className;
        if (c.style) td.style.cssText = c.style;
        if (c.html === true && c.el) {
            td.appendChild(c.el);
        } else {
            td.textContent = c.text || '';
        }
        if (c.strong) {
            const s = document.createElement('strong');
            s.textContent = c.text;
            td.textContent = '';
            td.appendChild(s);
        }
        tr.appendChild(td);
    });
}

// === UTILITIES ===
function formatVND(num) {
    if (Math.abs(num) >= 1e9) return Math.round(num / 1e9).toLocaleString('vi-VN') + ' tỷ';
    if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(0) + ' triệu';
    return num.toLocaleString('vi-VN');
}

function daysFromNow(dateStr) {
    const target = new Date(dateStr);
    const now = new Date();
    return Math.ceil((target - now) / (1000 * 60 * 60 * 24));
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function animateValue(element, start, end, duration, formatter) {
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = formatter(start + (end - start) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// === CHART.JS CONFIG ===
Chart.defaults.color = '#8b95b0';
Chart.defaults.font.family = 'Inter';
Chart.defaults.font.size = 11;
const CHART_COLORS = ['#60a5fa', '#a78bfa', '#34d399', '#fb923c', '#f472b6', '#22d3ee', '#fbbf24'];

// === RENDER KPIs ===
function renderKPIs() {
    const s = DATA.summary;
    animateValue(document.getElementById('kpi-loan-value'), 0, s.totalLoan, 1200, formatVND);
    animateValue(document.getElementById('kpi-invest-value'), 0, s.totalInvest, 1200, formatVND);
    document.getElementById('kpi-funding-rate').textContent = s.fundingRate + '%';
    document.getElementById('kpi-invest-yield').textContent = s.investYield + '%';
    document.getElementById('kpi-spread-value').textContent = '+' + s.netSpread + '%';
    animateValue(document.getElementById('kpi-pl-value'), 0, s.netPL, 1200, (v) => '+' + formatVND(v));
    if (s.netPLCumulative) {
        animateValue(document.getElementById('kpi-pl-cumulative'), 0, s.netPLCumulative, 1200, (v) => '+' + formatVND(v));
    }
    animateValue(document.getElementById('kpi-tsdb-value'), 0, s.totalTSDB, 1200, formatVND);
    animateValue(document.getElementById('kpi-hanmuc-value'), 0, s.totalHanMuc, 1200, formatVND);
}

// === CHARTS ===
function renderAllocationChart() {
    new Chart(document.getElementById('chartAllocation').getContext('2d'), {
        type: 'doughnut',
        data: { labels: ['Tiền gửi (TD)', 'Trái phiếu (Bond)'], datasets: [{ data: [DATA.summary.tdPct, DATA.summary.bondPct], backgroundColor: ['#60a5fa', '#a78bfa'], borderColor: ['rgba(96,165,250,0.3)', 'rgba(167,139,250,0.3)'], borderWidth: 2, hoverOffset: 8 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyleWidth: 10 } }, tooltip: { backgroundColor: '#1a1f35', borderColor: 'rgba(99,115,171,0.3)', borderWidth: 1, padding: 12, callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed}%` } } } }
    });
}

function renderBarChart(canvasId, data, label, colors) {
    new Chart(document.getElementById(canvasId).getContext('2d'), {
        type: 'bar',
        data: { labels: data.map(x => x.bank), datasets: [{ label, data: data.map(x => (x.total || x.amount || 0) / 1e9), backgroundColor: colors.slice(0, data.length).map(c => c + '80'), borderColor: colors.slice(0, data.length), borderWidth: 1, borderRadius: 6, maxBarThickness: 48 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1a1f35', borderColor: 'rgba(99,115,171,0.3)', borderWidth: 1, padding: 12, callbacks: { label: (ctx) => ` ${ctx.parsed.x.toLocaleString('vi-VN')} tỷ VND` } } }, scales: { x: { grid: { color: 'rgba(99,115,171,0.08)' }, ticks: { callback: v => v.toLocaleString() + ' tỷ' } }, y: { grid: { display: false } } } }
    });
}

// === LIMITS ===
function renderLimits() {
    const grid = document.getElementById('limits-grid');
    grid.textContent = '';
    DATA.limitControls.forEach((lc, idx) => {
        const icon = lc.status === 'danger' ? '🔴' : lc.status === 'warning' ? '🟡' : '🟢';
        const card = document.createElement('div');
        card.className = `limit-card ${lc.status}`;
        card.id = `limit-card-${idx}`;

        const top = el('div', 'limit-top');
        top.appendChild(el('span', 'limit-bank', icon + ' ' + lc.bank));
        const badgeText = lc.status === 'danger' ? 'Cạn Room' : lc.status === 'warning' ? 'Gần đầy' : 'Còn Room';
        top.appendChild(el('span', 'limit-status-badge ' + lc.status, badgeText));

        const vals = el('div', 'limit-values');
        vals.appendChild(el('span', null, 'Dư nợ: ' + formatVND(lc.duNo)));
        vals.appendChild(el('span', null, 'Hạn mức: ' + formatVND(lc.hanMuc)));

        const prog = el('div', 'limit-progress');
        const bar = el('div', 'limit-progress-bar');
        bar.style.width = '0%';
        prog.appendChild(bar);

        card.appendChild(top);
        card.appendChild(vals);
        card.appendChild(prog);
        card.appendChild(el('div', 'limit-util', lc.util + '%'));
        card.appendChild(el('div', 'limit-room', 'Room: ' + formatVND(lc.room)));

        grid.appendChild(card);
        setTimeout(() => { bar.style.width = lc.util + '%'; }, 300 + idx * 150);
    });
}

// === TABLES ===

function renderLoansTable() {
    const tbody = document.getElementById('tbody-loans');
    tbody.textContent = '';
    document.getElementById('count-loans').textContent = DATA.loans.length;
    DATA.loans.forEach((l, idx) => {
        const days = daysFromNow(l.endDate);
        let dc = days <= 15 ? 'urgent' : days <= 45 ? 'soon' : 'ok';
        const tr = document.createElement('tr');
        addCells(tr, [
            { text: String(idx + 1) },
            { text: l.bank, strong: true },
            { text: formatVND(l.amount), className: 'cell-amount' },
            { text: l.rate + '%', className: 'cell-rate' },
            { text: formatDate(l.startDate) },
            { text: formatDate(l.endDate) },
            { html: true, el: el('span', 'days-remaining ' + dc, days > 0 ? days + ' ngày' : 'Đáo hạn!') }
        ]);
        tbody.appendChild(tr);
    });
}

function renderInvestmentsTable() {
    const tbody = document.getElementById('tbody-investments');
    tbody.textContent = '';
    document.getElementById('count-investments').textContent = DATA.investments.length;
    DATA.investments.forEach((inv, idx) => {
        const days = daysFromNow(inv.endDate);
        let dc = days <= 15 ? 'urgent' : days <= 45 ? 'soon' : 'ok';
        const tr = document.createElement('tr');
        addCells(tr, [
            { text: String(idx + 1) },
            { text: inv.bank, strong: true },
            { html: true, el: el('span', 'type-badge ' + inv.type.toLowerCase(), inv.type) },
            { text: formatVND(inv.amount), className: 'cell-amount' },
            { text: inv.rate + '%', className: 'cell-rate' },
            { text: formatDate(inv.startDate) },
            { text: formatDate(inv.endDate) },
            { html: true, el: el('span', 'days-remaining ' + dc, days > 0 ? days + ' ngày' : 'Đáo hạn!') }
        ]);
        tbody.appendChild(tr);
    });
}

// === INSIGHTS ===
function renderInsights() {
    const grid = document.getElementById('insights-grid');
    grid.textContent = '';
    const greenBanks = DATA.limitControls.filter(x => x.status === 'safe').sort((a, b) => b.room - a.room);
    const redBanks = DATA.limitControls.filter(x => x.status === 'danger');

    // Build Insight 1
    const desc1 = document.createElement('div');
    desc1.className = 'insight-desc';
    if (greenBanks.length > 0) {
        desc1.appendChild(document.createTextNode('Ưu tiên giải ngân W/C tiếp theo qua '));
        desc1.appendChild(el('span', 'insight-highlight', greenBanks[0].bank));
        desc1.appendChild(document.createTextNode(' (room: '));
        desc1.appendChild(el('span', 'insight-highlight', formatVND(greenBanks[0].room)));
        desc1.appendChild(document.createTextNode(').'));
        if (greenBanks.length > 1) {
            desc1.appendChild(document.createTextNode(' Tiếp theo: '));
            desc1.appendChild(el('span', 'insight-highlight', greenBanks[1].bank));
            desc1.appendChild(document.createTextNode(' (room: '));
            desc1.appendChild(el('span', 'insight-highlight', formatVND(greenBanks[1].room)));
            desc1.appendChild(document.createTextNode(').'));
        }
    }

    // Build Insight 2
    const desc2 = document.createElement('div');
    desc2.className = 'insight-desc';
    if (redBanks.length > 0) {
        desc2.appendChild(document.createTextNode('Cần hạn chế hoặc tất toán bớt các khoản vay tại '));
        redBanks.forEach((b, i) => {
            if (i > 0) desc2.appendChild(document.createTextNode(', '));
            desc2.appendChild(el('span', 'insight-highlight', b.bank));
        });
        desc2.appendChild(document.createTextNode(' để đưa tỷ lệ sử dụng hạn mức về mức an toàn (<90%).'));
    }

    // Build Insight 3
    const desc3 = document.createElement('div');
    desc3.className = 'insight-desc';
    const nearList = DATA.investments
        .map(inv => ({ ...inv, daysLeft: daysFromNow(inv.endDate) }))
        .filter(inv => inv.daysLeft > 0 && inv.daysLeft <= 45)
        .sort((a, b) => a.daysLeft - b.daysLeft);
    if (nearList.length > 0) {
        desc3.appendChild(document.createTextNode('Các khoản đầu tư sắp đáo hạn trong 45 ngày:'));
        nearList.forEach(inv => {
            desc3.appendChild(document.createElement('br'));
            const b = document.createElement('strong');
            b.textContent = inv.bank;
            desc3.appendChild(b);
            desc3.appendChild(document.createTextNode(' (' + inv.type + ') — '));
            desc3.appendChild(el('span', 'insight-highlight', formatVND(inv.amount)));
            desc3.appendChild(document.createTextNode(', đáo hạn ' + formatDate(inv.endDate) + ' ('));
            desc3.appendChild(el('span', 'insight-highlight', inv.daysLeft + ' ngày'));
            desc3.appendChild(document.createTextNode(')'));
        });
    } else {
        desc3.textContent = 'Không có khoản đầu tư nào sắp đáo hạn trong 45 ngày tới.';
    }

    // Build Insight 4 — Loans maturing soon
    const desc4 = document.createElement('div');
    desc4.className = 'insight-desc';
    let nearLoans = DATA.loans
        .map(l => ({ ...l, daysLeft: daysFromNow(l.endDate) }))
        .filter(l => l.daysLeft > 0 && l.daysLeft <= 30)
        .sort((a, b) => a.daysLeft - b.daysLeft);
    let loanLabel = 'Các khoản vay sắp đáo hạn trong 30 ngày — cần chuẩn bị tất toán hoặc gia hạn:';
    if (nearLoans.length === 0) {
        nearLoans = DATA.loans
            .map(l => ({ ...l, daysLeft: daysFromNow(l.endDate) }))
            .filter(l => l.daysLeft > 0 && l.daysLeft <= 60)
            .sort((a, b) => a.daysLeft - b.daysLeft);
        loanLabel = 'Các khoản vay đáo hạn trong 60 ngày — cần lên kế hoạch:';
    }
    if (nearLoans.length > 0) {
        desc4.appendChild(document.createTextNode(loanLabel));
        nearLoans.forEach(l => {
            desc4.appendChild(document.createElement('br'));
            const b = document.createElement('strong');
            b.textContent = l.bank;
            desc4.appendChild(b);
            desc4.appendChild(document.createTextNode(' — '));
            desc4.appendChild(el('span', 'insight-highlight', formatVND(l.amount)));
            desc4.appendChild(document.createTextNode(' @ ' + l.rate + '%, đáo hạn ' + formatDate(l.endDate) + ' ('));
            const urgency = l.daysLeft <= 15 ? 'insight-highlight-urgent' : 'insight-highlight';
            desc4.appendChild(el('span', urgency, l.daysLeft + ' ngày'));
            desc4.appendChild(document.createTextNode(')'));
        });
    } else {
        desc4.textContent = 'Không có khoản vay nào sắp đáo hạn trong 60 ngày tới.';
    }

    // Build cards
    function makeCard(id, title, descEl, extraClass) {
        const card = el('div', 'insight-card' + (extraClass ? ' ' + extraClass : ''));
        card.id = id;
        card.appendChild(el('div', 'insight-number', id.split('-')[1]));
        const wrap = document.createElement('div');
        wrap.appendChild(el('div', 'insight-title', title));
        wrap.appendChild(descEl);
        card.appendChild(wrap);
        return card;
    }
    grid.appendChild(makeCard('insight-1', '🟢 Cơ hội Giải ngân', desc1));
    grid.appendChild(makeCard('insight-2', '🔴 Hạ tỷ trọng', desc2));
    grid.appendChild(makeCard('insight-3', '🔄 Khoản đầu tư sắp đáo hạn', desc3, 'insight-card-full'));
    grid.appendChild(makeCard('insight-4', '⏰ Khoản vay sắp đáo hạn', desc4, 'insight-card-full'));
}

// === TABS ===
function setupTabs() {
    document.querySelectorAll('.tab-nav').forEach(nav => {
        nav.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const parent = btn.closest('.dashboard-section');
                nav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                parent.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById(btn.dataset.tab).classList.add('active');
            });
        });
    });
}

// === INIT ===
function renderAll() {
    // Set today's date
    const today = new Date().toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
    document.getElementById('report-date-text').textContent = today;
    document.getElementById('footer-date').textContent = today;

    renderKPIs();
    renderAllocationChart();
    renderBarChart('chartLoanDist', [...DATA.loanByBank].sort((a, b) => (b.total || 0) - (a.total || 0)), 'Dư nợ', CHART_COLORS);
    renderBarChart('chartInvestDist', [...DATA.investByBank].sort((a, b) => (b.total || 0) - (a.total || 0)), 'Đầu tư', ['#22d3ee', '#34d399', '#a78bfa', '#fb923c']);
    renderLimits();

    renderLoansTable();
    renderInvestmentsTable();
    renderInsights();
    setupTabs();
}

document.addEventListener('DOMContentLoaded', () => {
    // Load data from authenticated server API only
    fetch('/api/data', { credentials: 'same-origin' })
        .then(res => {
            if (res.status === 401) {
                console.log('[AUTH] Not authenticated, waiting for login');
                return null;
            }
            if (!res.ok) throw new Error('API error');
            return res.json();
        })
        .then(serverData => {
            if (serverData) {
                DATA = serverData;
                console.log('[SECURE] Data loaded from authenticated API');
                renderAll();
                startSessionTimer();
            }
        })
        .catch(err => {
            console.error('[ERROR] Failed to load data:', err.message);
        });
});

// Session auto-expiry timer
function startSessionTimer() {
    clearTimeout(SESSION_TIMEOUT_ID);
    SESSION_TIMEOUT_ID = setTimeout(async () => {
        console.log('[SESSION] Auto-logout after 30 minutes of inactivity');
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
        DATA = null;
        alert('Đã hết phiên làm việc. Vui lòng đăng nhập lại.');
        location.reload();
    }, SESSION_TIMEOUT_MS);
}

// Reset timer on user activity
['click', 'keydown', 'mousemove', 'scroll'].forEach(evt => {
    document.addEventListener(evt, () => {
        if (DATA) startSessionTimer();
    }, { passive: true });
});

// Expose only what's needed globally
// handleGoogleLogin is required by Google Identity Services (data-callback)
// loadDataAfterAuth is called by auth.js after successful login
window.loadDataAfterAuth = async function() {
    try {
        const res = await fetch('/api/data', { credentials: 'same-origin' });
        if (!res.ok) throw new Error('Failed to load data');
        DATA = await res.json();
        renderAll();
        startSessionTimer();
    } catch (err) {
        console.error('[ERROR] Failed to load data after auth:', err.message);
    }
};

})(); // End IIFE
