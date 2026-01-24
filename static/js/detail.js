const modal = document.getElementById('dataModal');
const backdrop = document.getElementById('modalBackdrop');
const panel = document.getElementById('modalPanel');
const tableContainer = document.getElementById('tableContainer');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const downloadBtn = document.getElementById('downloadBtn');
const sourceBtn = document.getElementById('sourceBtn');

function previewData(url) {
    // Show modal
    modal.classList.remove('hidden');
    // Animate in
    setTimeout(() => {
        backdrop.classList.remove('opacity-0');
        panel.classList.remove('opacity-0', 'scale-95');
    }, 10);

    // Set content

    sourceBtn.link = url;
    tableContainer.innerHTML = '';
    tableContainer.classList.add('hidden');
    errorState.classList.add('hidden');
    loadingState.classList.remove('hidden');

    // Fetch and parse
    Papa.parse(url, {
        download: true,
        header: true,
        preview: 20, // Limit rows for preview
        skipEmptyLines: true,
        complete: function (results) {
            renderTable(results.data, results.meta.fields);
            loadingState.classList.add('hidden');
            tableContainer.classList.remove('hidden');
        },
        error: function (err) {
            console.error(err);
            loadingState.classList.add('hidden');
            errorState.classList.remove('hidden');
            document.getElementById('errorMessage').textContent = "Gagal parsing CSV: " + err.message;
        }
    });
}

function renderTable(data, headers) {
    if (!data || data.length === 0) {
        tableContainer.innerHTML = '<div class="p-8 text-center text-slate-500 text-sm">Data kosong</div>';
        return;
    }

    let html = '<table class="min-w-full divide-y divide-slate-200 text-sm text-left">';

    // Header
    html += '<thead class="bg-slate-50"><tr>';
    headers.forEach(h => {
        html += `<th scope="col" class="px-3 py-3.5 font-semibold text-slate-900 whitespace-nowrap">${h}</th>`;
    });
    html += '</tr></thead>';

    // Body
    html += '<tbody class="divide-y divide-slate-200 bg-white">';
    data.forEach(row => {
        html += '<tr>';
        headers.forEach(h => {
            const cell = row[h] !== undefined ? row[h] : '';
            // Truncate long text
            const display = cell.length > 50 ? cell.substring(0, 50) + '...' : cell;
            html += `<td class="px-3 py-4 text-slate-500 whitespace-nowrap" title="${cell}">${display}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';

    tableContainer.innerHTML = html;
}

function closeModal() {
    backdrop.classList.add('opacity-0');
    panel.classList.add('opacity-0', 'scale-95');

    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300); // Match transition duration
}

// Close on clicking backdrop
modal.addEventListener('click', function (e) {
    if (e.target.id === 'modalBackdrop' || e.target.closest('#modalBackdrop')) {
        closeModal();
    }
});

// Close on ESC
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
        closeModal();
    }
});

// ============== MULTI-VISUALIZATION FULLSCREEN ==============
let activeFullscreen = null;

function toggleVizFullscreen(index) {
    const container = document.getElementById('viz-container-' + index);
    const iframe = container.querySelector('iframe');
    const icon = document.getElementById('fs-icon-' + index);

    if (activeFullscreen === index) {
        // Exit fullscreen
        container.classList.remove('fixed', 'inset-0', 'z-50', 'bg-white', 'p-4');
        iframe.style.height = '500px';
        icon.classList.remove('bi-fullscreen-exit');
        icon.classList.add('bi-arrows-fullscreen');
        document.body.style.overflow = '';
        activeFullscreen = null;
    } else {
        // Exit any other fullscreen first
        if (activeFullscreen !== null) {
            toggleVizFullscreen(activeFullscreen);
        }
        // Enter fullscreen
        container.classList.add('fixed', 'inset-0', 'z-50', 'bg-white', 'p-4');
        iframe.style.height = 'calc(100vh - 32px)';
        icon.classList.remove('bi-arrows-fullscreen');
        icon.classList.add('bi-fullscreen-exit');
        document.body.style.overflow = 'hidden';
        activeFullscreen = index;
    }
}

// ESC to exit fullscreen
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && activeFullscreen !== null) {
        toggleVizFullscreen(activeFullscreen);
    }
});

// ============== LAZY LOAD VISUALIZATIONS ==============
// Only load iframes when they come into view
document.addEventListener('DOMContentLoaded', function () {
    const vizIframes = document.querySelectorAll('.viz-iframe');

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const iframe = entry.target;
                    if (iframe.dataset.src && !iframe.src) {
                        iframe.src = iframe.dataset.src;
                        iframe.dataset.loaded = 'true';
                    }
                    observer.unobserve(iframe);
                }
            });
        }, {
            rootMargin: '100px',  // Start loading 100px before entering viewport
            threshold: 0.01
        });

        vizIframes.forEach(iframe => observer.observe(iframe));
    } else {
        // Fallback for older browsers
        vizIframes.forEach(iframe => {
            if (iframe.dataset.src) {
                iframe.src = iframe.dataset.src;
                iframe.dataset.loaded = 'true';
            }
        });
    }
});

// ============== MOBILE FOCUS MODE ==============
let focusModeActive = false;
let focusModeOverlay = null;

function openVizFocusMode(index, iframeSrc) {
    focusModeActive = true;

    // Create overlay
    focusModeOverlay = document.createElement('div');
    focusModeOverlay.id = 'viz-focus-overlay';
    focusModeOverlay.className = 'fixed inset-0 z-[100] bg-white flex flex-col';
    focusModeOverlay.innerHTML = `
            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 bg-slate-900 text-white shrink-0">
                <span class="text-sm font-medium">Mode Fokus - Visualisasi ${index}</span>
                <button onclick="closeVizFocusMode()" class="p-2 hover:bg-white/10 rounded-lg transition flex items-center gap-1">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            
            <!-- Visualization -->
            <div class="flex-1 relative overflow-hidden" id="focus-viz-container">
                <div id="focus-loading" class="absolute inset-0 flex items-center justify-center bg-white z-10">
                    <div class="text-center">
                        <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-slate-200 border-t-slate-600 mb-3"></div>
                        <p class="text-sm text-slate-500">Memuat visualisasi...</p>
                    </div>
                </div>
                <iframe id="focus-viz-iframe" src="${iframeSrc}" 
                    class="w-full h-full border-0 origin-center transition-transform duration-200" 
                    onload="document.getElementById('focus-loading').style.display='none'"
                    style="transform: scale(1);"></iframe>
            </div>
            
            <!-- Bottom Control Panel -->
            <div class="shrink-0 bg-slate-100 border-t border-slate-200 px-4 py-3">
                <!-- Instructions -->
                <p class="text-xs text-slate-500 text-center mb-3">
                    <i class="bi bi-info-circle"></i> Gunakan tombol di bawah untuk zoom dan geser visualisasi
                </p>
                
                <!-- Zoom Controls -->
                <div class="flex justify-center items-center gap-2">
                    <button onclick="focusZoom('out')" 
                        class="w-12 h-12 bg-white border border-slate-300 rounded-xl text-lg font-bold text-slate-700 hover:bg-slate-50 active:bg-slate-100 transition shadow-sm flex items-center justify-center">
                        <i class="bi bi-dash-lg"></i>
                    </button>
                    <button onclick="focusZoom('reset')" 
                        class="px-4 h-12 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 active:bg-slate-100 transition shadow-sm">
                        <i class="bi bi-arrow-counterclockwise mr-1"></i> Reset
                    </button>
                    <button onclick="focusZoom('in')" 
                        class="w-12 h-12 bg-slate-900 rounded-xl text-lg font-bold text-white hover:bg-slate-800 active:bg-slate-700 transition shadow-sm flex items-center justify-center">
                        <i class="bi bi-plus-lg"></i>
                    </button>
                </div>
                
                <!-- Zoom Level Indicator -->
                <p class="text-center text-xs text-slate-400 mt-2" id="zoom-level-text">Zoom: 100%</p>
            </div>
        `;

    document.body.appendChild(focusModeOverlay);
    document.body.style.overflow = 'hidden';

    // Prevent viewport zoom
    document.querySelector('meta[name="viewport"]')?.setAttribute('content',
        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
}

// Zoom control
let currentZoom = 1;
const ZOOM_STEP = 0.2;
const MAX_ZOOM = 3;
const MIN_ZOOM = 0.5;

function focusZoom(action) {
    const iframe = document.getElementById('focus-viz-iframe');
    const zoomText = document.getElementById('zoom-level-text');
    if (!iframe) return;

    if (action === 'in' && currentZoom < MAX_ZOOM) {
        currentZoom += ZOOM_STEP;
    } else if (action === 'out' && currentZoom > MIN_ZOOM) {
        currentZoom -= ZOOM_STEP;
    } else if (action === 'reset') {
        currentZoom = 1;
    }

    iframe.style.transform = `scale(${currentZoom})`;
    if (zoomText) {
        zoomText.textContent = `Zoom: ${Math.round(currentZoom * 100)}%`;
    }
}

function closeVizFocusMode() {
    if (focusModeOverlay) {
        focusModeOverlay.remove();
        focusModeOverlay = null;
    }
    focusModeActive = false;
    currentZoom = 1; // Reset zoom for next open
    document.body.style.overflow = '';

    // Restore viewport zoom
    document.querySelector('meta[name="viewport"]')?.setAttribute('content',
        'width=device-width, initial-scale=1.0');
}

// ESC to close focus mode
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && focusModeActive) {
        closeVizFocusMode();
    }
});
// ============== AI ASSISTANT ==============
const postId = typeof CURRENT_POST_ID !== 'undefined' ? CURRENT_POST_ID : 0;
const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const counterBadge = document.getElementById('ai-counter-badge');

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = "flex gap-3 " + (role === 'user' ? "flex-row-reverse" : "");

    const avatar = role === 'ai'
        ? `<div class="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 shrink-0"><i class="bi bi-robot"></i></div>`
        : `<div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 shrink-0"><i class="bi bi-person"></i></div>`;

    const bubble = role === 'ai'
        ? `<div class="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-700 max-w-[85%] prose prose-sm">${marked.parse(text)}</div>`
        : `<div class="bg-brand-600 p-3 rounded-2xl rounded-tr-none shadow-sm text-sm text-white max-w-[85%]">${text}</div>`;

    div.innerHTML = role === 'user' ? (bubble + avatar) : (avatar + bubble);
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function generateSummary() {
    const btn = document.getElementById('btn-summary');
    const content = document.getElementById('ai-summary-content');
    const loading = document.getElementById('summary-loading');

    btn.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const resp = await authenticatedFetch('/api/ai/summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId })
        });
        const data = await resp.json();

        loading.classList.add('hidden');
        content.classList.remove('hidden');

        if (data.error) {
            content.innerHTML = `<span class="text-red-500">Error: ${data.error}</span>`;
            btn.classList.remove('hidden');
        } else {
            content.innerHTML = marked.parse(data.summary);
        }
    } catch (e) {
        loading.classList.add('hidden');
        btn.classList.remove('hidden');
        alert("Gagal mengakses AI: " + e.message);
    }
}

async function sendChat() {
    const question = chatInput.value.trim();
    if (!question) return;

    appendMessage('user', question);
    chatInput.value = '';
    chatInput.disabled = true;
    btnSend.disabled = true;

    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = "flex gap-3";
    typingDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 shrink-0"><i class="bi bi-robot"></i></div>
            <div class="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-500">
                <span class="animate-pulse">...</span>
            </div>
        `;
    chatHistory.appendChild(typingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        const resp = await authenticatedFetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId, question: question })
        });
        const data = await resp.json();

        document.getElementById(typingId).remove();

        if (data.error) {
            if (data.error === "Limit exhausted") {
                appendMessage('ai', "Maaf, batas pertanyaan untuk sesi ini sudah habis (Maks 3). Silakan refresh atau coba lagi nanti.");
            } else {
                appendMessage('ai', "Error: " + data.error);
            }
        } else {
            appendMessage('ai', data.answer);
            counterBadge.innerHTML = `<i class="bi bi-chat-dots"></i> ${data.remaining} Pertanyaan Tersisa`;
            if (data.remaining <= 0) {
                chatInput.disabled = true;
                btnSend.disabled = true;
                chatInput.placeholder = "Batas pertanyaan tercapai";
            }
        }
    } catch (e) {
        document.getElementById(typingId).remove();
        appendMessage('ai', "Gagal menghubungi server.");
    } finally {
        if (chatInput.placeholder !== "Batas pertanyaan tercapai") {
            chatInput.disabled = false;
            btnSend.disabled = false;
            chatInput.focus();
        }
    }
}

// Enter key to send
chatInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendChat();
});

// Check initial quota on load
async function checkQuota() {
    try {
        // We can reuse the chat endpoint with a dummy check or create a specific endpoint
        // For now, let's just use the fact that we can store the quota in the template provided by the backend
        // But since we didn't update the render_template to pass it, let's do a quick fetch to a light endpoint or just checking via chat endpoint with a flag?
        // Actually, cleaner way: update app.py to pass quota in render_template.
        // But I'll stick to a simple fetch for now if I don't want to touch the route signature too much.
        // Let's optimize: Just ask the standard chat endpoint with empty question? No that returns error.

        // Alternative: The user just asked for "reflect remaining quota".
        // Since updating app.py is easy, I should have passed it in context. 
        // I will do a quick fetch to a new endpoint /api/ai/usage/<post_id>

        const resp = await authenticatedFetch(`/api/ai/usage/${postId}`);
        if (resp.ok) {
            const data = await resp.json();
            const remaining = data.remaining;
            const is_admin = data.is_admin;

            if (is_admin) {
                counterBadge.innerHTML = `<i class="bi bi-infinity"></i> Unlimited (Admin)`;
                counterBadge.classList.replace('bg-brand-50', 'bg-purple-100');
                counterBadge.classList.replace('text-brand-700', 'text-purple-700');
            } else {
                counterBadge.innerHTML = `<i class="bi bi-chat-dots"></i> ${remaining} Pertanyaan Tersisa`;
                if (remaining <= 0) {
                    chatInput.disabled = true;
                    btnSend.disabled = true;
                    chatInput.placeholder = "Batas pertanyaan tercapai";
                }
            }
        }
    } catch (e) {
        console.error("Failed to fetch quota", e);
        counterBadge.innerHTML = `<i class="bi bi-chat-dots"></i> ...`;
    }
}

// Call it
checkQuota();