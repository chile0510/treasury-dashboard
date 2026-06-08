// ============================================
// TREASURY PORTFOLIO MANAGER — DASHBOARD JS
// ============================================
// DATA is loaded from authenticated server API only.
// No financial data is stored in this client-side file.

let DATA = null;

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
        data: { labels: data.map(x => x.bank), datasets: [{ label, data: data.map(x => x.amount / 1e9), backgroundColor: colors.map(c => c + '80'), borderColor: colors, borderWidth: 1, borderRadius: 6, maxBarThickness: 48 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1a1f35', borderColor: 'rgba(99,115,171,0.3)', borderWidth: 1, padding: 12, callbacks: { label: (ctx) => ` ${ctx.parsed.x.toLocaleString('vi-VN')} tỷ VND` } } }, scales: { x: { grid: { color: 'rgba(99,115,171,0.08)' }, ticks: { callback: v => v.toLocaleString() + ' tỷ' } }, y: { grid: { display: false } } } }
    });
}

// === LIMITS ===
function renderLimits() {
    const grid = document.getElementById('limits-grid');
    grid.innerHTML = '';
    DATA.limitControls.forEach((lc, idx) => {
        const icon = lc.status === 'danger' ? '🔴' : '🟢';
        const card = document.createElement('div');
        card.className = `limit-card ${lc.status}`;
        card.id = `limit-card-${lc.bank}`;
        card.innerHTML = `
            <div class="limit-top"><span class="limit-bank">${icon} ${lc.bank}</span><span class="limit-status-badge ${lc.status}">${lc.status === 'danger' ? 'Cạn Room' : 'Còn Room'}</span></div>
            <div class="limit-values"><span>Dư nợ: ${formatVND(lc.duNo)}</span><span>Hạn mức: ${formatVND(lc.hanMuc)}</span></div>
            <div class="limit-progress"><div class="limit-progress-bar" style="width:0%"></div></div>
            <div class="limit-util">${lc.util}%</div>
            <div class="limit-room">Room: ${formatVND(lc.room)}</div>`;
        grid.appendChild(card);
        setTimeout(() => { card.querySelector('.limit-progress-bar').style.width = lc.util + '%'; }, 300 + idx * 150);
    });
}

// === TABLES ===
function renderDurationMismatch() {
    const tbody = document.getElementById('tbody-duration');
    tbody.innerHTML = '';
    document.getElementById('count-duration').textContent = DATA.durationMismatches.length;
    if (DATA.durationMismatches.length === 0) { tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--accent-green);padding:24px;">✅ Tất cả các khoản khớp kỳ hạn</td></tr>'; return; }
    DATA.durationMismatches.forEach(dm => {
        let rc = 'low', rl = 'Thấp';
        if (dm.daysDiff > 30) { rc = 'high'; rl = 'Cao'; } else if (dm.daysDiff > 10) { rc = 'medium'; rl = 'TB'; }
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${dm.investBank}</strong></td><td>${dm.loanBank}</td><td>${formatDate(dm.investEnd)}</td><td>${formatDate(dm.loanEnd)}</td><td class="cell-days" style="color:${rc === 'high' ? 'var(--accent-red)' : rc === 'medium' ? 'var(--accent-yellow)' : 'var(--accent-green)'}">+${dm.daysDiff} ngày</td><td class="cell-amount">${formatVND(dm.investAmt)}</td><td><span class="risk-badge ${rc}">${rl}</span></td>`;
        tbody.appendChild(tr);
    });
}

function renderTSDB() {
    const tbody = document.getElementById('tbody-tsdb');
    tbody.innerHTML = '';
    document.getElementById('count-tsdb').textContent = DATA.tsdbAnomalies.length;
    DATA.tsdbAnomalies.forEach(a => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${a.bank}</strong></td><td class="cell-amount">${formatVND(a.amount)}</td><td>${a.reasons.map(r => `<span class="risk-badge high">${r}</span>`).join(' ')}</td>`;
        tbody.appendChild(tr);
    });
}

function renderLoansTable() {
    const tbody = document.getElementById('tbody-loans');
    tbody.innerHTML = '';
    document.getElementById('count-loans').textContent = DATA.loans.length;
    DATA.loans.forEach((l, idx) => {
        const days = daysFromNow(l.endDate);
        let dc = days <= 15 ? 'urgent' : days <= 45 ? 'soon' : 'ok';
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${idx+1}</td><td><strong>${l.bank}</strong></td><td class="cell-amount">${formatVND(l.amount)}</td><td class="cell-rate">${l.rate}%</td><td>${formatDate(l.startDate)}</td><td>${formatDate(l.endDate)}</td><td><span class="days-remaining ${dc}">${days > 0 ? days + ' ngày' : 'Đáo hạn!'}</span></td>`;
        tbody.appendChild(tr);
    });
}

function renderInvestmentsTable() {
    const tbody = document.getElementById('tbody-investments');
    tbody.innerHTML = '';
    document.getElementById('count-investments').textContent = DATA.investments.length;
    DATA.investments.forEach((inv, idx) => {
        const days = daysFromNow(inv.endDate);
        let dc = days <= 15 ? 'urgent' : days <= 45 ? 'soon' : 'ok';
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${idx+1}</td><td><strong>${inv.bank}</strong></td><td><span class="type-badge ${inv.type.toLowerCase()}">${inv.type}</span></td><td class="cell-amount">${formatVND(inv.amount)}</td><td class="cell-rate">${inv.rate}%</td><td>${formatDate(inv.startDate)}</td><td>${formatDate(inv.endDate)}</td><td><span class="days-remaining ${dc}">${days > 0 ? days + ' ngày' : 'Đáo hạn!'}</span></td>`;
        tbody.appendChild(tr);
    });
}

// === INSIGHTS ===
function renderInsights() {
    const grid = document.getElementById('insights-grid');
    const greenBanks = DATA.limitControls.filter(x => x.status === 'safe').sort((a, b) => b.room - a.room);
    const redBanks = DATA.limitControls.filter(x => x.status === 'danger');

    let insight1 = '';
    if (greenBanks.length > 0) {
        insight1 = `Ưu tiên giải ngân W/C tiếp theo qua <span class="insight-highlight">${greenBanks[0].bank}</span> (room: <span class="insight-highlight">${formatVND(greenBanks[0].room)}</span>).`;
        if (greenBanks.length > 1) insight1 += ` Tiếp theo: <span class="insight-highlight">${greenBanks[1].bank}</span> (room: ${formatVND(greenBanks[1].room)}).`;
    }

    let insight2 = '';
    if (redBanks.length > 0) {
        const names = redBanks.map(b => `<span class="insight-highlight">${b.bank}</span>`).join(', ');
        insight2 = `Cần hạn chế hoặc tất toán bớt các khoản vay tại ${names} để đưa tỷ lệ sử dụng hạn mức về mức an toàn (<90%).`;
    }

    // Insight 3: Investments nearing maturity (within 30 days)
    const now = new Date();
    const nearMaturity = DATA.investments
        .map(inv => ({ ...inv, daysLeft: daysFromNow(inv.endDate) }))
        .filter(inv => inv.daysLeft > 0 && inv.daysLeft <= 30)
        .sort((a, b) => a.daysLeft - b.daysLeft);

    let insight3 = '';
    if (nearMaturity.length > 0) {
        const items = nearMaturity.map(inv =>
            `<strong>${inv.bank}</strong> (${inv.type}) — <span class="insight-highlight">${formatVND(inv.amount)}</span>, đáo hạn ${formatDate(inv.endDate)} (<span class="insight-highlight">${inv.daysLeft} ngày</span>)`
        ).join('<br>');
        insight3 = `Các khoản đầu tư sắp đáo hạn cần roll:<br>${items}`;
    } else {
        // Check within 60 days if none within 30
        const near60 = DATA.investments
            .map(inv => ({ ...inv, daysLeft: daysFromNow(inv.endDate) }))
            .filter(inv => inv.daysLeft > 0 && inv.daysLeft <= 60)
            .sort((a, b) => a.daysLeft - b.daysLeft);
        if (near60.length > 0) {
            const items = near60.map(inv =>
                `<strong>${inv.bank}</strong> (${inv.type}) — <span class="insight-highlight">${formatVND(inv.amount)}</span>, đáo hạn ${formatDate(inv.endDate)} (<span class="insight-highlight">${inv.daysLeft} ngày</span>)`
            ).join('<br>');
            insight3 = `Các khoản đầu tư đáo hạn trong 60 ngày cần chuẩn bị roll:<br>${items}`;
        } else {
            insight3 = 'Không có khoản đầu tư nào sắp đáo hạn trong 60 ngày tới.';
        }
    }

    grid.innerHTML = `
        <div class="insight-card" id="insight-1">
            <div class="insight-number">1</div>
            <div><div class="insight-title">🟢 Cơ hội Giải ngân</div><div class="insight-desc">${insight1}</div></div>
        </div>
        <div class="insight-card" id="insight-2">
            <div class="insight-number">2</div>
            <div><div class="insight-title">🔴 Hạ tỷ trọng</div><div class="insight-desc">${insight2}</div></div>
        </div>
        <div class="insight-card insight-card-full" id="insight-3">
            <div class="insight-number">3</div>
            <div><div class="insight-title">🔄 Khoản đầu tư cần Roll</div><div class="insight-desc">${insight3}</div></div>
        </div>`;
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
    renderBarChart('chartLoanDist', DATA.loanByBank, 'Dư nợ', CHART_COLORS);
    renderBarChart('chartInvestDist', DATA.investByBank, 'Đầu tư', ['#22d3ee', '#34d399', '#a78bfa', '#fb923c']);
    renderLimits();
    renderDurationMismatch();
    renderTSDB();
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
                // Not authenticated — auth.js will handle showing login
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
            }
        })
        .catch(err => {
            console.error('[ERROR] Failed to load data:', err.message);
        });
});

// Called by auth.js after successful login
async function loadDataAfterAuth() {
    try {
        const res = await fetch('/api/data', { credentials: 'same-origin' });
        if (!res.ok) throw new Error('Failed to load data');
        DATA = await res.json();
        renderAll();
    } catch (err) {
        console.error('[ERROR] Failed to load data after auth:', err.message);
    }
}
