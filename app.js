// ============================================
// TREASURY PORTFOLIO MANAGER — DASHBOARD JS
// ============================================

// === DATA (embedded from extract) ===
const DATA = {
  "limitControls": [
    { "bank": "Cathay", "duNo": 200000000000, "hanMuc": 200000000000, "util": 100.0, "room": 0, "status": "danger" },
    { "bank": "VCB", "duNo": 749962921699, "hanMuc": 750000000000, "util": 100.0, "room": 37078301, "status": "danger" },
    { "bank": "Shinhan", "duNo": 159921586864, "hanMuc": 160000000000, "util": 100.0, "room": 78413136, "status": "danger" },
    { "bank": "BIDV", "duNo": 94536165147, "hanMuc": 250000000000, "util": 37.8, "room": 155463834853, "status": "safe" },
    { "bank": "HSBC", "duNo": 0, "hanMuc": 250000000000, "util": 0.0, "room": 250000000000, "status": "safe" }
  ],
  "summary": {
    "totalLoan": 1204420673710,
    "fundingRate": 6.88,
    "totalInvest": 1021603094800,
    "investYield": 8.65,
    "netSpread": 1.77,
    "netPL": 21689414582.4,
    "tdPct": 28.9,
    "bondPct": 71.1,
    "tdAmount": 736000000000,
    "bondAmount": 1814203094800,
    "totalTSDB": 240500000000,
    "tsdbYield": 6.86
  },
  "loans": [
    { "bank": "VCB", "amount": 79744415313, "rate": 5.8, "startDate": "2025-12-16", "endDate": "2026-06-15", "status": "Outstanding" },
    { "bank": "VCB", "amount": 16317332243, "rate": 5.8, "startDate": "2025-12-17", "endDate": "2026-06-15", "status": "Outstanding" },
    { "bank": "VCB", "amount": 74100000000, "rate": 6.0, "startDate": "2025-12-22", "endDate": "2026-06-19", "status": "Outstanding" },
    { "bank": "VCB", "amount": 119000000000, "rate": 6.0, "startDate": "2026-01-05", "endDate": "2026-07-03", "status": "Outstanding" },
    { "bank": "VCB", "amount": 87701174143, "rate": 6.0, "startDate": "2026-01-15", "endDate": "2026-07-13", "status": "Outstanding" },
    { "bank": "VCB", "amount": 72100000000, "rate": 6.0, "startDate": "2026-01-20", "endDate": "2026-07-20", "status": "Outstanding" },
    { "bank": "Cathay", "amount": 200000000000, "rate": 7.2, "startDate": "2026-02-05", "endDate": "2026-08-04", "status": "Outstanding" },
    { "bank": "Shinhan", "amount": 143663435630, "rate": 6.9, "startDate": "2026-04-15", "endDate": "2026-10-15", "status": "Outstanding" },
    { "bank": "Shinhan", "amount": 9637371651, "rate": 6.9, "startDate": "2026-04-20", "endDate": "2026-10-20", "status": "Outstanding" },
    { "bank": "Shinhan", "amount": 6620779583, "rate": 6.9, "startDate": "2026-04-23", "endDate": "2026-10-23", "status": "Outstanding" },
    { "bank": "VCB", "amount": 124000000000, "rate": 8.0, "startDate": "2026-04-20", "endDate": "2026-10-19", "status": "Outstanding" },
    { "bank": "VCB", "amount": 177000000000, "rate": 8.0, "startDate": "2026-05-05", "endDate": "2026-11-02", "status": "Outstanding" },
    { "bank": "BIDV", "amount": 14709047762, "rate": 7.0, "startDate": "2026-05-05", "endDate": "2026-11-02", "status": "Outstanding" },
    { "bank": "BIDV", "amount": 79827117385, "rate": 7.0, "startDate": "2026-05-11", "endDate": "2026-11-06", "status": "Outstanding" }
  ],
  "investments": [
    { "bank": "TCBS", "amount": 221128300000, "rate": 8.0, "type": "BOND", "startDate": "2025-12-16", "endDate": "2026-06-16", "status": "Outstanding" },
    { "bank": "TCBS", "amount": 120736438800, "rate": 8.5, "type": "BOND", "startDate": "2026-01-28", "endDate": "2026-07-28", "status": "Outstanding" },
    { "bank": "VPB", "amount": 100000000000, "rate": 8.3, "type": "TD", "startDate": "2026-01-28", "endDate": "2026-07-28", "status": "Outstanding" },
    { "bank": "VPB", "amount": 70000000000, "rate": 8.3, "type": "TD", "startDate": "2026-01-28", "endDate": "2026-07-28", "status": "Outstanding" },
    { "bank": "VHM", "amount": 207457534000, "rate": 9.0, "type": "BOND", "startDate": "2026-02-06", "endDate": "2026-08-06", "status": "Outstanding" },
    { "bank": "TVS", "amount": 150000000000, "rate": 9.0, "type": "BOND", "startDate": "2026-03-16", "endDate": "2026-06-16", "status": "Outstanding" },
    { "bank": "TVS", "amount": 152280822000, "rate": 9.3, "type": "BOND", "startDate": "2026-05-28", "endDate": "2026-11-30", "status": "Outstanding" }
  ],
  "durationMismatches": [
    { "investBank": "TCBS", "loanBank": "VCB", "investEnd": "2026-07-28", "loanEnd": "2026-07-03", "daysDiff": 25, "investAmt": 120736438800, "loanAmt": 119000000000 },
    { "investBank": "VPB", "loanBank": "VCB", "investEnd": "2026-07-28", "loanEnd": "2026-07-13", "daysDiff": 15, "investAmt": 100000000000, "loanAmt": 87701174143 },
    { "investBank": "VPB", "loanBank": "VCB", "investEnd": "2026-07-28", "loanEnd": "2026-07-20", "daysDiff": 8, "investAmt": 70000000000, "loanAmt": 72100000000 },
    { "investBank": "VHM", "loanBank": "Cathay", "investEnd": "2026-08-06", "loanEnd": "2026-08-04", "daysDiff": 2, "investAmt": 207457534000, "loanAmt": 200000000000 },
    { "investBank": "TVS", "loanBank": "Shinhan", "investEnd": "2026-11-30", "loanEnd": "2026-10-23", "daysDiff": 38, "investAmt": 152280822000, "loanAmt": 6620779583 }
  ],
  "tsdbAnomalies": [
    { "bank": "BIDV", "amount": 87500000000, "reasons": ["Đã hết hạn (2025-03-20)"] },
    { "bank": "VCB", "amount": 15000000000, "reasons": ["Đã hết hạn (2025-04-10)"] },
    { "bank": "VCB", "amount": 35000000000, "reasons": ["Đã hết hạn (2025-06-12)"] },
    { "bank": "VCB", "amount": 25000000000, "reasons": ["Đã hết hạn (2025-06-18)"] },
    { "bank": "VIB", "amount": 85000000000, "reasons": ["Đã hết hạn (2025-06-16)"] },
    { "bank": "Shinhan", "amount": 48000000000, "reasons": ["Đã hết hạn (2025-09-20)"] },
    { "bank": "Cathay", "amount": 30000000000, "reasons": ["Đã hết hạn (2026-02-04)"] },
    { "bank": "N/A", "amount": 30000000000, "reasons": ["Đã hết hạn (2026-01-28)"] },
    { "bank": "N/A", "amount": 355500000000, "reasons": ["Lãi suất bằng 0 hoặc trống"] }
  ],
  "loanByBank": [
    { "bank": "VCB", "amount": 749962921699 },
    { "bank": "Cathay", "amount": 200000000000 },
    { "bank": "Shinhan", "amount": 159921586864 },
    { "bank": "BIDV", "amount": 94536165147 }
  ],
  "investByBank": [
    { "bank": "TCBS", "amount": 341864738800 },
    { "bank": "VPB", "amount": 170000000000 },
    { "bank": "VHM", "amount": 207457534000 },
    { "bank": "TVS", "amount": 302280822000 }
  ]
};

// === UTILITIES ===
function formatVND(num) {
    if (Math.abs(num) >= 1e12) return (num / 1e12).toFixed(1) + ' nghìn tỷ';
    if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(1) + ' tỷ';
    if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(0) + ' triệu';
    return num.toLocaleString('vi-VN');
}

function formatFullVND(num) {
    return num.toLocaleString('vi-VN') + ' ₫';
}

function daysFromNow(dateStr) {
    const target = new Date(dateStr);
    const now = new Date();
    const diff = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
    return diff;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// === ANIMATED COUNTER ===
function animateValue(element, start, end, duration, formatter) {
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        const current = start + (end - start) * eased;
        element.textContent = formatter(current);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// === CHART.JS CONFIG ===
Chart.defaults.color = '#8b95b0';
Chart.defaults.font.family = 'Inter';
Chart.defaults.font.size = 11;

const CHART_COLORS = ['#60a5fa', '#a78bfa', '#34d399', '#fb923c', '#f472b6', '#22d3ee', '#fbbf24'];

// === RENDER FUNCTIONS ===

function renderKPIs() {
    const s = DATA.summary;

    // Animate KPI values
    animateValue(document.getElementById('kpi-loan-value'), 0, s.totalLoan, 1200, formatVND);
    animateValue(document.getElementById('kpi-invest-value'), 0, s.totalInvest, 1200, formatVND);

    document.getElementById('kpi-funding-rate').textContent = s.fundingRate + '%';
    document.getElementById('kpi-invest-yield').textContent = s.investYield + '%';

    const spreadEl = document.getElementById('kpi-spread-value');
    spreadEl.textContent = '+' + s.netSpread + '%';

    const plEl = document.getElementById('kpi-pl-value');
    animateValue(plEl, 0, s.netPL, 1200, (v) => '+' + formatVND(v));

    // TSDB KPIs
    animateValue(document.getElementById('kpi-tsdb-value'), 0, s.totalTSDB, 1200, formatVND);
    document.getElementById('kpi-tsdb-yield-value').textContent = s.tsdbYield + '%';
}

function renderAllocationChart() {
    const ctx = document.getElementById('chartAllocation').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Tiền gửi (TD)', 'Trái phiếu (Bond)'],
            datasets: [{
                data: [DATA.summary.tdPct, DATA.summary.bondPct],
                backgroundColor: ['#60a5fa', '#a78bfa'],
                borderColor: ['rgba(96,165,250,0.3)', 'rgba(167,139,250,0.3)'],
                borderWidth: 2,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 16, usePointStyle: true, pointStyleWidth: 10 }
                },
                tooltip: {
                    backgroundColor: '#1a1f35',
                    borderColor: 'rgba(99,115,171,0.3)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${ctx.parsed}%`
                    }
                }
            }
        }
    });
}

function renderLoanDistChart() {
    const ctx = document.getElementById('chartLoanDist').getContext('2d');
    const labels = DATA.loanByBank.map(x => x.bank);
    const values = DATA.loanByBank.map(x => x.amount / 1e9);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Dư nợ (tỷ VND)',
                data: values,
                backgroundColor: CHART_COLORS.map(c => c + '80'),
                borderColor: CHART_COLORS,
                borderWidth: 1,
                borderRadius: 6,
                maxBarThickness: 48
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1a1f35',
                    borderColor: 'rgba(99,115,171,0.3)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => ` ${ctx.parsed.x.toLocaleString('vi-VN')} tỷ VND`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(99,115,171,0.08)' },
                    ticks: { callback: v => v.toLocaleString() + ' tỷ' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderInvestDistChart() {
    const ctx = document.getElementById('chartInvestDist').getContext('2d');
    const labels = DATA.investByBank.map(x => x.bank);
    const values = DATA.investByBank.map(x => x.amount / 1e9);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Đầu tư (tỷ VND)',
                data: values,
                backgroundColor: ['#22d3ee80', '#34d39980', '#a78bfa80', '#fb923c80'],
                borderColor: ['#22d3ee', '#34d399', '#a78bfa', '#fb923c'],
                borderWidth: 1,
                borderRadius: 6,
                maxBarThickness: 48
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1a1f35',
                    borderColor: 'rgba(99,115,171,0.3)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => ` ${ctx.parsed.x.toLocaleString('vi-VN')} tỷ VND`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(99,115,171,0.08)' },
                    ticks: { callback: v => v.toLocaleString() + ' tỷ' }
                },
                y: { grid: { display: false } }
            }
        }
    });
}

function renderLimits() {
    const grid = document.getElementById('limits-grid');
    grid.innerHTML = '';

    DATA.limitControls.forEach((lc, idx) => {
        const card = document.createElement('div');
        card.className = `limit-card ${lc.status}`;
        card.id = `limit-card-${lc.bank}`;

        const icon = lc.status === 'danger' ? '🔴' : '🟢';

        card.innerHTML = `
            <div class="limit-top">
                <span class="limit-bank">${icon} ${lc.bank}</span>
                <span class="limit-status-badge ${lc.status}">${lc.status === 'danger' ? 'Cạn Room' : 'Còn Room'}</span>
            </div>
            <div class="limit-values">
                <span>Dư nợ: ${formatVND(lc.duNo)}</span>
                <span>Hạn mức: ${formatVND(lc.hanMuc)}</span>
            </div>
            <div class="limit-progress">
                <div class="limit-progress-bar" style="width: 0%" data-target="${lc.util}"></div>
            </div>
            <div class="limit-util">${lc.util}%</div>
            <div class="limit-room">Room: ${formatVND(lc.room)}</div>
        `;

        grid.appendChild(card);

        // Animate progress bar
        setTimeout(() => {
            const bar = card.querySelector('.limit-progress-bar');
            bar.style.width = lc.util + '%';
        }, 300 + idx * 150);
    });
}

function renderDurationMismatch() {
    const tbody = document.getElementById('tbody-duration');
    tbody.innerHTML = '';
    document.getElementById('count-duration').textContent = DATA.durationMismatches.length;

    if (DATA.durationMismatches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--accent-green);padding:24px;">✅ Tất cả các khoản khớp kỳ hạn</td></tr>';
        return;
    }

    DATA.durationMismatches.forEach(dm => {
        let riskClass = 'low';
        let riskLabel = 'Thấp';
        if (dm.daysDiff > 30) { riskClass = 'high'; riskLabel = 'Cao'; }
        else if (dm.daysDiff > 10) { riskClass = 'medium'; riskLabel = 'Trung bình'; }

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${dm.investBank}</strong></td>
            <td>${dm.loanBank}</td>
            <td>${formatDate(dm.investEnd)}</td>
            <td>${formatDate(dm.loanEnd)}</td>
            <td class="cell-days" style="color: ${riskClass === 'high' ? 'var(--accent-red)' : riskClass === 'medium' ? 'var(--accent-yellow)' : 'var(--accent-green)'}">+${dm.daysDiff} ngày</td>
            <td class="cell-amount">${formatVND(dm.investAmt)}</td>
            <td><span class="risk-badge ${riskClass}">${riskLabel}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderTSDB() {
    const tbody = document.getElementById('tbody-tsdb');
    tbody.innerHTML = '';
    document.getElementById('count-tsdb').textContent = DATA.tsdbAnomalies.length;

    DATA.tsdbAnomalies.forEach(a => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${a.bank}</strong></td>
            <td class="cell-amount">${formatVND(a.amount)}</td>
            <td>${a.reasons.map(r => `<span class="risk-badge high">${r}</span>`).join(' ')}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderLoansTable() {
    const tbody = document.getElementById('tbody-loans');
    tbody.innerHTML = '';
    document.getElementById('count-loans').textContent = DATA.loans.length;

    DATA.loans.forEach((l, idx) => {
        const days = daysFromNow(l.endDate);
        let daysClass = 'ok';
        if (days <= 15) daysClass = 'urgent';
        else if (days <= 45) daysClass = 'soon';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td><strong>${l.bank}</strong></td>
            <td class="cell-amount">${formatVND(l.amount)}</td>
            <td class="cell-rate">${l.rate}%</td>
            <td>${formatDate(l.startDate)}</td>
            <td>${formatDate(l.endDate)}</td>
            <td><span class="days-remaining ${daysClass}">${days > 0 ? days + ' ngày' : 'Đáo hạn!'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderInvestmentsTable() {
    const tbody = document.getElementById('tbody-investments');
    tbody.innerHTML = '';
    document.getElementById('count-investments').textContent = DATA.investments.length;

    DATA.investments.forEach((inv, idx) => {
        const days = daysFromNow(inv.endDate);
        let daysClass = 'ok';
        if (days <= 15) daysClass = 'urgent';
        else if (days <= 45) daysClass = 'soon';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td><strong>${inv.bank}</strong></td>
            <td><span class="type-badge ${inv.type.toLowerCase()}">${inv.type}</span></td>
            <td class="cell-amount">${formatVND(inv.amount)}</td>
            <td class="cell-rate">${inv.rate}%</td>
            <td>${formatDate(inv.startDate)}</td>
            <td>${formatDate(inv.endDate)}</td>
            <td><span class="days-remaining ${daysClass}">${days > 0 ? days + ' ngày' : 'Đáo hạn!'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderInsights() {
    const grid = document.getElementById('insights-grid');

    // Find green banks
    const greenBanks = DATA.limitControls.filter(x => x.status === 'safe').sort((a, b) => b.room - a.room);
    const redBanks = DATA.limitControls.filter(x => x.status === 'danger');

    let insight1 = '';
    if (greenBanks.length > 0) {
        const best = greenBanks[0];
        insight1 = `Ưu tiên giải ngân W/C tiếp theo qua <span class="insight-highlight">${best.bank}</span> do còn dư địa lớn nhất (<span class="insight-highlight">${formatVND(best.room)}</span>). `;
        if (greenBanks.length > 1) {
            insight1 += `Tiếp theo là <span class="insight-highlight">${greenBanks[1].bank}</span> (room: ${formatVND(greenBanks[1].room)}).`;
        }
    }

    let insight2 = '';
    if (redBanks.length > 0) {
        const names = redBanks.map(b => `<span class="insight-highlight">${b.bank}</span>`).join(', ');
        insight2 = `Cần hạn chế hoặc tất toán bớt các khoản vay tại ${names} để đưa tỷ lệ sử dụng hạn mức về mức an toàn (<90%). Tổng dư nợ cần xử lý: <span class="insight-highlight">${formatVND(redBanks.reduce((s, b) => s + b.duNo, 0))}</span>.`;
    }

    grid.innerHTML = `
        <div class="insight-card" id="insight-1">
            <div class="insight-number">1</div>
            <div>
                <div class="insight-title">🟢 Cơ hội Giải ngân</div>
                <div class="insight-desc">${insight1}</div>
            </div>
        </div>
        <div class="insight-card" id="insight-2">
            <div class="insight-number">2</div>
            <div>
                <div class="insight-title">🔴 Hạ tỷ trọng</div>
                <div class="insight-desc">${insight2}</div>
            </div>
        </div>
    `;
}

// === TAB SWITCHING ===
function setupTabs() {
    document.querySelectorAll('.tab-nav').forEach(nav => {
        nav.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                const parent = btn.closest('.dashboard-section');

                // Deactivate siblings
                nav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                parent.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));

                // Activate clicked
                btn.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            });
        });
    });
}

// === INIT ===
document.addEventListener('DOMContentLoaded', () => {
    renderKPIs();
    renderAllocationChart();
    renderLoanDistChart();
    renderInvestDistChart();
    renderLimits();
    renderDurationMismatch();
    renderTSDB();
    renderLoansTable();
    renderInvestmentsTable();
    renderInsights();
    setupTabs();
});
