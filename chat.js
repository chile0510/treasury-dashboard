// ============================================
// CHAT WIDGET — Treasury AI Assistant
// ============================================
(function() {
'use strict';

const fab = document.getElementById('chat-fab');
const panel = document.getElementById('chat-panel');
const closeBtn = document.getElementById('chat-close');
const input = document.getElementById('chat-input');
const sendBtn = document.getElementById('chat-send');
const messagesEl = document.getElementById('chat-messages');
const quickBtns = document.querySelectorAll('.chat-quick-btn');

let isOpen = false;
let isSending = false;

// Toggle panel
fab.addEventListener('click', () => {
    isOpen = !isOpen;
    panel.classList.toggle('hidden', !isOpen);
    fab.classList.toggle('active', isOpen);
    if (isOpen) {
        input.focus();
        scrollToBottom();
    }
});

closeBtn.addEventListener('click', () => {
    isOpen = false;
    panel.classList.add('hidden');
    fab.classList.remove('active');
});

// Quick action buttons
quickBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const msg = btn.dataset.msg;
        if (msg) sendMessage(msg);
    });
});

// Send on Enter
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const msg = input.value.trim();
        if (msg) sendMessage(msg);
    }
});

// Send button click
sendBtn.addEventListener('click', () => {
    const msg = input.value.trim();
    if (msg) sendMessage(msg);
});

function scrollToBottom() {
    requestAnimationFrame(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    });
}

function addMessage(text, isBot) {
    const wrapper = document.createElement('div');
    wrapper.className = `chat-msg ${isBot ? 'bot' : 'user'}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-msg-bubble';

    if (isBot) {
        // Convert markdown-like formatting to HTML
        bubble.innerHTML = formatBotReply(text);
    } else {
        bubble.textContent = text;
    }

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
}

function addTypingIndicator() {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-msg bot';
    wrapper.id = 'chat-typing';

    const bubble = document.createElement('div');
    bubble.className = 'chat-msg-bubble chat-typing';
    bubble.innerHTML = '<span></span><span></span><span></span>';

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
}

function removeTypingIndicator() {
    const el = document.getElementById('chat-typing');
    if (el) el.remove();
}

function formatBotReply(text) {
    // Escape HTML first
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Convert markdown
    html = html
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold**
        .replace(/_(.+?)_/g, '<em>$1</em>')                 // _italic_
        .replace(/\n/g, '<br>');                             // newlines

    return html;
}

async function sendMessage(text) {
    if (isSending) return;
    isSending = true;

    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;

    // Add user message
    addMessage(text, false);

    // Show typing indicator
    addTypingIndicator();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        removeTypingIndicator();

        if (res.status === 401) {
            addMessage('⚠️ Phiên đăng nhập hết hạn. Vui lòng tải lại trang.', true);
        } else if (!res.ok) {
            addMessage('❌ Lỗi kết nối. Vui lòng thử lại.', true);
        } else {
            const data = await res.json();
            if (data.ok) {
                addMessage(data.reply, true);
            } else {
                addMessage('❌ ' + (data.error || 'Lỗi không xác định'), true);
            }
        }
    } catch (err) {
        removeTypingIndicator();
        addMessage('❌ Không thể kết nối server. Vui lòng thử lại.', true);
    }

    input.disabled = false;
    sendBtn.disabled = false;
    isSending = false;
    input.focus();
}

})();
