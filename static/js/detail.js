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
        tableContainer.innerHTML = '<div class="p-8 text-center text-slate-500 text-sm space-y-2">Data kosong</div>';
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
    const welcomeState = document.getElementById('welcome-state');
    if (welcomeState) welcomeState.remove();

    const div = document.createElement('div');
    div.className = 'flex gap-3 items-start ' + (role === 'user' ? 'justify-end' : '');

    if (role === 'user') {
        div.innerHTML = `<div class="bg-brand-600 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[75%] whitespace-pre-wrap">${text}</div>`;
    } else {
        div.innerHTML = `
            <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5">
                <i class="bi bi-robot text-sm"></i>
            </div>
            <div class="text-sm text-slate-700 dark:text-dm-200 max-w-[85%] prose prose-sm dark:prose-invert prose-p:my-1 prose-headings:my-2 leading-relaxed">${marked.parse(text)}</div>
        `;
    }

    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function generateSummary() {
    const btn = document.getElementById('btn-summary');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-arrow-repeat animate-spin text-xs"></i> Meringkas...';

    try {
        const resp = await authenticatedFetch('/api/ai/summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId })
        });
        const data = await resp.json();

        if (data.error) {
            appendMessage('ai', 'Gagal membuat ringkasan: ' + data.error);
        } else {
            appendMessage('ai', '**Ringkasan Artikel**\n\n' + data.summary);
        }
    } catch (e) {
        appendMessage('ai', 'Gagal mengakses AI: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-file-text text-xs"></i> Ringkasan';
    }
}

function appendMessageWithThinking(thinking, answer, elapsedSeconds) {
    const welcomeState = document.getElementById('welcome-state');
    if (welcomeState) welcomeState.remove();

    const timeLabel = elapsedSeconds != null
        ? (elapsedSeconds >= 60
            ? Math.floor(elapsedSeconds / 60) + 'm ' + (elapsedSeconds % 60) + 's'
            : elapsedSeconds + 's')
        : '';

    const div = document.createElement('div');
    div.className = 'flex gap-3 items-start';
    div.innerHTML = `
        <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5">
            <i class="bi bi-robot text-sm"></i>
        </div>
        <div class="text-sm max-w-[85%]">
            <details class="group mb-2">
                <summary class="list-none flex items-center gap-1.5 cursor-pointer text-[11px] text-slate-400 dark:text-dm-500 hover:text-brand-500 transition py-0.5">
                    <i class="bi bi-cpu text-[10px]"></i>
                    <span>Tampilkan proses analisis</span>
                    ${timeLabel ? `<span class="ml-1 px-1.5 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 rounded text-[10px] font-medium"><i class="bi bi-clock text-[9px] mr-0.5"></i>${timeLabel}</span>` : ''}
                    <i class="bi bi-chevron-down text-[9px] transition-transform group-open:rotate-180 ml-0.5"></i>
                </summary>
                <div class="mt-1.5 pl-3 border-l border-slate-200 dark:border-dm-600">
                    <div class="text-xs text-slate-500 dark:text-dm-400 prose prose-xs dark:prose-invert max-w-none leading-relaxed">
                        ${marked.parse(thinking)}
                    </div>
                </div>
            </details>
            <div class="prose prose-sm dark:prose-invert leading-relaxed text-slate-700 dark:text-dm-200">
                ${marked.parse(answer)}
            </div>
        </div>
    `;

    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function createStreamingBubble() {
    const welcomeState = document.getElementById('welcome-state');
    if (welcomeState) welcomeState.remove();

    const div = document.createElement('div');
    div.className = 'flex gap-3 items-start';
    div.innerHTML = `
        <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5">
            <i class="bi bi-robot text-sm"></i>
        </div>
        <div class="text-sm text-slate-700 dark:text-dm-200 max-w-[85%] prose prose-sm dark:prose-invert prose-p:my-1 prose-headings:my-2 leading-relaxed" id="stream-content">
            <span class="inline-block w-1.5 h-4 bg-brand-500 animate-pulse rounded-sm align-middle"></span>
        </div>
    `;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}

function createStreamingBubbleWithThinking() {
    const welcomeState = document.getElementById('welcome-state');
    if (welcomeState) welcomeState.remove();

    const div = document.createElement('div');
    div.className = 'flex gap-3 items-start';
    div.innerHTML = `
        <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5">
            <i class="bi bi-robot text-sm"></i>
        </div>
        <div class="text-sm max-w-[85%]">
            <details class="group mb-2" open id="stream-thinking-details">
                <summary class="list-none flex items-center gap-1.5 cursor-pointer text-[11px] text-slate-400 dark:text-dm-500 hover:text-brand-500 transition py-0.5">
                    <i class="bi bi-cpu text-[10px]"></i>
                    <span>Proses analisis</span>
                    <span class="ml-1 px-1.5 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 rounded text-[10px] font-medium" id="stream-thinking-timer"><i class="bi bi-clock text-[9px] mr-0.5"></i>0s</span>
                    <i class="bi bi-chevron-down text-[9px] transition-transform group-open:rotate-180 ml-0.5"></i>
                </summary>
                <div class="mt-1.5 pl-3 border-l border-slate-200 dark:border-dm-600">
                    <div class="text-xs text-slate-500 dark:text-dm-400 prose prose-xs dark:prose-invert max-w-none leading-relaxed" id="stream-thinking-content">
                        <span class="inline-block w-1.5 h-3 bg-slate-400 animate-pulse rounded-sm align-middle"></span>
                    </div>
                </div>
            </details>
            <div class="prose prose-sm dark:prose-invert leading-relaxed text-slate-700 dark:text-dm-200 hidden" id="stream-answer-content"></div>
        </div>
    `;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}

async function sendChat() {
    const question = chatInput.value.trim();

    // Reset textarea height after send
    chatInput.style.height = '';
    if (!question) return;

    const thinkingEnabled = document.getElementById('thinking-toggle')?.checked || false;

    appendMessage('user', question);
    chatInput.value = '';
    chatInput.disabled = true;
    btnSend.disabled = true;

    // Track start time
    const startTime = Date.now();
    let timerInterval = null;

    // Show typing indicator while waiting for first token
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = 'flex gap-3 items-start';

    if (thinkingEnabled) {
        typingDiv.innerHTML = `
            <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5"><i class="bi bi-robot text-sm"></i></div>
            <div class="text-sm text-slate-500 dark:text-dm-400">
                <div class="flex items-center gap-2">
                    <div class="flex items-center gap-1.5 px-2.5 py-1 bg-brand-50 dark:bg-brand-900/20 rounded-lg border border-brand-100 dark:border-brand-800">
                        <i class="bi bi-cpu text-[10px] text-brand-500 animate-pulse"></i>
                        <span class="text-[11px] font-medium text-brand-600 dark:text-brand-400">Deep Thinking</span>
                        <span class="text-[10px] font-mono text-brand-500 dark:text-brand-400 ml-1" id="thinking-timer">0s</span>
                    </div>
                </div>
                <div class="mt-1.5 flex items-center gap-1 text-[10px] text-slate-400 dark:text-dm-500">
                    <span class="inline-block w-1 h-1 bg-brand-400 rounded-full animate-ping"></span>
                    Menganalisis data dan menyusun jawaban...
                </div>
            </div>
        `;
        timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            // Update both the typing indicator timer and the streaming bubble timer
            const timerEl = document.getElementById('thinking-timer');
            if (timerEl) {
                timerEl.textContent = elapsed >= 60
                    ? Math.floor(elapsed / 60) + 'm ' + (elapsed % 60) + 's'
                    : elapsed + 's';
            }
            const streamTimerEl = document.getElementById('stream-thinking-timer');
            if (streamTimerEl) {
                const label = elapsed >= 60
                    ? Math.floor(elapsed / 60) + 'm ' + (elapsed % 60) + 's'
                    : elapsed + 's';
                streamTimerEl.innerHTML = `<i class="bi bi-clock text-[9px] mr-0.5"></i>${label}`;
            }
        }, 1000);
    } else {
        typingDiv.innerHTML = `
            <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5"><i class="bi bi-robot text-sm"></i></div>
            <div class="text-sm text-slate-400 dark:text-dm-500">
                <span class="animate-pulse flex items-center gap-1.5">Mengetik...</span>
            </div>
        `;
    }
    chatHistory.appendChild(typingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        const resp = await authenticatedFetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId, question: question, thinking: thinkingEnabled })
        });

        // Check if the response is an error (non-stream JSON)
        const contentType = resp.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            if (timerInterval) clearInterval(timerInterval);
            document.getElementById(typingId)?.remove();
            const data = await resp.json();
            if (data.error === "Limit exhausted") {
                appendMessage('ai', "Maaf, batas pertanyaan untuk sesi ini sudah habis (Maks 3). Silakan refresh atau coba lagi nanti.");
            } else {
                appendMessage('ai', "Error: " + (data.message || data.error));
            }
            return;
        }

        // Remove typing indicator and create streaming bubble
        document.getElementById(typingId)?.remove();

        let streamBubble;
        let fullText = '';
        let streamContentEl;

        if (thinkingEnabled) {
            streamBubble = createStreamingBubbleWithThinking();
            streamContentEl = document.getElementById('stream-thinking-content');
        } else {
            streamBubble = createStreamingBubble();
            streamContentEl = document.getElementById('stream-content');
        }

        // Parse SSE stream
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        // For thinking mode: track which phase we're in
        let phase = thinkingEnabled ? 'thinking' : 'answer'; // 'thinking' or 'answer'
        let thinkingText = '';
        let answerText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE lines
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.slice(6);

                let event;
                try { event = JSON.parse(jsonStr); } catch { continue; }

                if (event.type === 'token') {
                    fullText += event.content;

                    if (thinkingEnabled) {
                        // Parse <thinking>...</thinking> and <answer>...</answer> on the fly
                        if (phase === 'thinking') {
                            // Check if we've hit </thinking>
                            const thinkEndIdx = fullText.indexOf('</thinking>');
                            if (thinkEndIdx !== -1) {
                                // Extract thinking content (strip <thinking> tag)
                                let rawThinking = fullText.substring(0, thinkEndIdx);
                                rawThinking = rawThinking.replace('<thinking>', '').trim();
                                thinkingText = rawThinking;

                                // Render final thinking
                                const thinkEl = document.getElementById('stream-thinking-content');
                                if (thinkEl) thinkEl.innerHTML = marked.parse(thinkingText);

                                // Close the details and switch to answer phase
                                const details = document.getElementById('stream-thinking-details');
                                if (details) details.removeAttribute('open');

                                // Show answer container
                                const answerEl = document.getElementById('stream-answer-content');
                                if (answerEl) {
                                    answerEl.classList.remove('hidden');
                                    answerEl.innerHTML = '<span class="inline-block w-1.5 h-4 bg-brand-500 animate-pulse rounded-sm align-middle"></span>';
                                }

                                // Update fullText to only contain post-</thinking> content
                                fullText = fullText.substring(thinkEndIdx + '</thinking>'.length);
                                phase = 'answer';
                            } else {
                                // Still in thinking phase, render streaming
                                let rawThinking = fullText.replace('<thinking>', '').trim();
                                const thinkEl = document.getElementById('stream-thinking-content');
                                if (thinkEl) {
                                    thinkEl.innerHTML = marked.parse(rawThinking) + '<span class="inline-block w-1.5 h-3 bg-slate-400 animate-pulse rounded-sm align-middle ml-0.5"></span>';
                                }
                            }
                        }

                        if (phase === 'answer') {
                            // Strip <answer> tag if present
                            let answerRaw = fullText.replace('<answer>', '').replace('</answer>', '').trim();
                            answerText = answerRaw;
                            const answerEl = document.getElementById('stream-answer-content');
                            if (answerEl && answerText) {
                                answerEl.innerHTML = marked.parse(answerText) + '<span class="inline-block w-1.5 h-4 bg-brand-500 animate-pulse rounded-sm align-middle ml-0.5"></span>';
                            }
                        }
                    } else {
                        // Normal mode: stream directly
                        streamContentEl.innerHTML = marked.parse(fullText) + '<span class="inline-block w-1.5 h-4 bg-brand-500 animate-pulse rounded-sm align-middle ml-0.5"></span>';
                    }

                    chatHistory.scrollTop = chatHistory.scrollHeight;
                } else if (event.type === 'done') {
                    // Stop timer
                    if (timerInterval) clearInterval(timerInterval);
                    const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);

                    // Remove cursor animation
                    if (thinkingEnabled) {
                        // Final render without cursor
                        const thinkEl = document.getElementById('stream-thinking-content');
                        if (thinkEl && thinkingText) thinkEl.innerHTML = marked.parse(thinkingText);
                        const answerEl = document.getElementById('stream-answer-content');
                        if (answerEl && answerText) answerEl.innerHTML = marked.parse(answerText);

                        // Update timer badge to final value
                        const timerBadge = document.getElementById('stream-thinking-timer');
                        if (timerBadge) {
                            const label = elapsedSeconds >= 60
                                ? Math.floor(elapsedSeconds / 60) + 'm ' + (elapsedSeconds % 60) + 's'
                                : elapsedSeconds + 's';
                            timerBadge.innerHTML = `<i class="bi bi-clock text-[9px] mr-0.5"></i>${label}`;
                        }
                    } else {
                        streamContentEl.innerHTML = marked.parse(fullText);
                    }

                    // Update quota
                    const remaining = event.remaining;
                    counterBadge.innerHTML = `<i class="bi bi-chat-dots"></i> ${remaining} Pertanyaan Tersisa`;
                    if (remaining <= 0) {
                        chatInput.disabled = true;
                        btnSend.disabled = true;
                        chatInput.placeholder = "Batas pertanyaan tercapai";
                    }
                } else if (event.type === 'error') {
                    if (timerInterval) clearInterval(timerInterval);
                    streamBubble.remove();
                    appendMessage('ai', "Error: " + event.message);
                }
            }
        }
    } catch (e) {
        if (timerInterval) clearInterval(timerInterval);
        document.getElementById(typingId)?.remove();
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

// ============== QUIZ MODE ==============
let quizQuestions = [];
let currentQuestionIndex = 0;
let quizScore = 0;
let quizAnswered = false;

async function startQuiz() {
    const btn = document.getElementById('btn-quiz');
    const loading = document.getElementById('quiz-loading');
    const container = document.getElementById('quiz-container');
    const results = document.getElementById('quiz-results');
    const modal = document.getElementById('quiz-modal');

    quizQuestions = [];
    currentQuestionIndex = 0;
    quizScore = 0;
    quizAnswered = false;

    // Open modal and show loading
    modal.classList.remove('hidden');
    container.classList.add('hidden');
    results.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const resp = await authenticatedFetch('/api/ai/quiz/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId })
        });
        const data = await resp.json();

        if (data.error) {
            loading.classList.add('hidden');
            closeQuizModal();
            appendMessage('ai', 'Gagal membuat quiz: ' + (data.message || data.error));
            return;
        }

        quizQuestions = data.questions;
        loading.classList.add('hidden');
        container.classList.remove('hidden');
        renderQuestion();
    } catch (e) {
        loading.classList.add('hidden');
        closeQuizModal();
        appendMessage('ai', 'Gagal membuat quiz: ' + e.message);
    }
}

function closeQuizModal() {
    const modal = document.getElementById('quiz-modal');
    if (modal) modal.classList.add('hidden');
    removeQuizFloatingBtn();
}

function minimizeQuiz() {
    const modal = document.getElementById('quiz-modal');
    if (modal) modal.classList.add('hidden');

    // Show floating restore button
    if (!document.getElementById('quiz-floating-btn')) {
        const btn = document.createElement('button');
        btn.id = 'quiz-floating-btn';
        btn.onclick = restoreQuiz;
        btn.className = 'fixed bottom-6 right-6 z-[60] flex items-center gap-2 px-4 py-3 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-2xl shadow-xl shadow-brand-500/30 transition-all duration-300 animate-bounce-once ring-2 ring-brand-400/30';
        btn.innerHTML = `
            <i class="bi bi-puzzle text-base"></i>
            <span>Lanjut Quiz</span>
            <span class="ml-1 px-1.5 py-0.5 bg-white/20 rounded text-[10px] font-medium">${currentQuestionIndex + 1}/${quizQuestions.length}</span>
        `;
        document.body.appendChild(btn);

        // Stop bounce after 2s
        setTimeout(() => btn.classList.remove('animate-bounce-once'), 2000);
    }
}

function restoreQuiz() {
    const modal = document.getElementById('quiz-modal');
    if (modal) modal.classList.remove('hidden');
    removeQuizFloatingBtn();
}

function removeQuizFloatingBtn() {
    const btn = document.getElementById('quiz-floating-btn');
    if (btn) btn.remove();
}

function renderQuestion() {
    const q = quizQuestions[currentQuestionIndex];
    const questionText = document.getElementById('quiz-question-text');
    const optionsContainer = document.getElementById('quiz-options');
    const progressText = document.getElementById('quiz-progress-text');
    const scoreText = document.getElementById('quiz-score-text');
    const progressBar = document.getElementById('quiz-progress-bar');
    const explanation = document.getElementById('quiz-explanation');
    const nextBtn = document.getElementById('btn-next-question');

    quizAnswered = false;

    questionText.textContent = (currentQuestionIndex + 1) + '. ' + q.question;
    progressText.textContent = 'Pertanyaan ' + (currentQuestionIndex + 1) + ' dari ' + quizQuestions.length;
    scoreText.textContent = 'Skor: ' + quizScore + '/' + currentQuestionIndex;
    progressBar.style.width = ((currentQuestionIndex + 1) / quizQuestions.length * 100) + '%';

    explanation.classList.add('hidden');
    nextBtn.classList.add('hidden');

    optionsContainer.innerHTML = '';
    Object.entries(q.options).forEach(function ([key, value]) {
        const btn = document.createElement('button');
        btn.className = 'w-full text-left px-4 py-3 rounded-lg border border-slate-200 dark:border-dm-600 bg-white dark:bg-dm-700 text-sm text-slate-700 dark:text-dm-200 hover:border-brand-400 dark:hover:border-brand-500 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition';
        btn.innerHTML = '<span class="font-semibold text-brand-600 dark:text-brand-400 mr-2">' + key + '.</span> ' + value;
        btn.onclick = function () { selectAnswer(key); };
        btn.dataset.key = key;
        optionsContainer.appendChild(btn);
    });
}

function selectAnswer(selectedKey) {
    if (quizAnswered) return;
    quizAnswered = true;

    const q = quizQuestions[currentQuestionIndex];
    const isCorrect = selectedKey === q.correct;
    if (isCorrect) quizScore++;

    const buttons = document.querySelectorAll('#quiz-options button');
    buttons.forEach(function (btn) {
        const key = btn.dataset.key;
        btn.disabled = true;
        btn.classList.remove('hover:border-brand-400', 'hover:bg-brand-50', 'dark:hover:border-brand-500', 'dark:hover:bg-brand-900/20');

        if (key === q.correct) {
            btn.classList.remove('border-slate-200', 'dark:border-dm-600', 'bg-white', 'dark:bg-dm-700');
            btn.classList.add('border-green-400', 'dark:border-green-600', 'bg-green-50', 'dark:bg-green-900/20', 'text-green-700', 'dark:text-green-300');
        } else if (key === selectedKey && !isCorrect) {
            btn.classList.remove('border-slate-200', 'dark:border-dm-600', 'bg-white', 'dark:bg-dm-700');
            btn.classList.add('border-red-400', 'dark:border-red-600', 'bg-red-50', 'dark:bg-red-900/20', 'text-red-700', 'dark:text-red-300');
        }
    });

    document.getElementById('quiz-score-text').textContent = 'Skor: ' + quizScore + '/' + (currentQuestionIndex + 1);

    // Show explanation
    const explanation = document.getElementById('quiz-explanation');
    if (explanation) {
        explanation.classList.remove('hidden', 'border-red-200', 'bg-red-50', 'border-green-200', 'bg-green-50', 'dark:border-red-900/30', 'dark:bg-red-900/10', 'dark:border-green-900/30', 'dark:bg-green-900/10');

        const isCorrectClass = isCorrect
            ? ['border-green-200', 'bg-green-50', 'dark:border-green-900/30', 'dark:bg-green-900/10']
            : ['border-red-200', 'bg-red-50', 'dark:border-red-900/30', 'dark:bg-red-900/10'];

        explanation.classList.add(...isCorrectClass);
        explanation.innerHTML = `
            <div class="flex items-start gap-2">
                <i class="bi bi-info-circle-fill text-brand-500 mt-0.5"></i>
                <div>
                    <span class="font-bold text-slate-700 dark:text-dm-200">Penjelasan:</span>
                    <div class="prose prose-sm dark:prose-invert leading-relaxed text-slate-600 dark:text-dm-300 mt-1">
                        ${marked.parse(q.explanation || 'Tidak ada penjelasan.')}
                    </div>
                </div>
            </div>
        `;
        explanation.classList.remove('hidden');
    }

    const nextBtn = document.getElementById('btn-next-question');
    nextBtn.classList.remove('hidden');
    if (currentQuestionIndex < quizQuestions.length - 1) {
        nextBtn.innerHTML = 'Selanjutnya <i class="bi bi-arrow-right ml-1"></i>';
        nextBtn.onclick = nextQuestion;
    } else {
        nextBtn.innerHTML = 'Lihat Hasil <i class="bi bi-trophy ml-1"></i>';
        nextBtn.onclick = showQuizResults;
    }
}

function nextQuestion() {
    currentQuestionIndex++;
    if (currentQuestionIndex < quizQuestions.length) {
        renderQuestion();
    }
}

function showQuizResults() {
    document.getElementById('quiz-container').classList.add('hidden');
    const results = document.getElementById('quiz-results');
    results.classList.remove('hidden');

    const percentage = Math.round((quizScore / quizQuestions.length) * 100);

    let icon, title, message;
    if (percentage === 100) {
        icon = '<i class="bi bi-trophy-fill text-amber-500"></i>';
        title = 'Sempurna!';
        message = 'Kamu memahami artikel ini dengan sangat baik.';
    } else if (percentage >= 60) {
        icon = '<i class="bi bi-check-circle-fill text-green-500"></i>';
        title = 'Bagus!';
        message = 'Pemahaman yang baik, tapi masih ada yang bisa dipelajari lagi.';
    } else {
        icon = '<i class="bi bi-book-half text-brand-500"></i>';
        title = 'Terus Belajar!';
        message = 'Coba baca artikelnya lagi dan ulangi quiz ini.';
    }

    document.getElementById('quiz-result-icon').innerHTML = icon;
    document.getElementById('quiz-result-title').textContent = title;
    document.getElementById('quiz-result-score').textContent = quizScore + '/' + quizQuestions.length;
    document.getElementById('quiz-result-message').textContent = message;
}

function resetQuiz() {
    closeQuizModal();
    removeQuizFloatingBtn();
    quizQuestions = [];
    currentQuestionIndex = 0;
    quizScore = 0;
    quizAnswered = false;
}

// ============== IMMERSIVE MODE ==============
let isImmersive = false;

function toggleImmersiveMode() {
    const container = document.getElementById('vercax-container');
    const icon = document.getElementById('immersive-icon');

    if (!container) return;

    if (!isImmersive) {
        // Enter Immersive
        container.classList.add('fixed', 'inset-0', 'z-[100]', 'rounded-none', 'h-screen', 'overflow-y-auto');
        container.classList.remove('rounded-2xl', 'mt-8');

        // Adjust grid for fullscreen - maybe centered max-width container inside?
        // Actually, let's keep it full width but added padding
        container.classList.add('p-6', 'md:p-8');

        document.body.style.overflow = 'hidden';
        icon.classList.remove('bi-arrows-fullscreen');
        icon.classList.add('bi-fullscreen-exit');
    } else {
        // Exit Immersive
        container.classList.remove('fixed', 'inset-0', 'z-[100]', 'rounded-none', 'h-screen', 'overflow-y-auto');
        container.classList.add('rounded-2xl', 'mt-8');
        container.classList.remove('p-6', 'md:p-8');

        document.body.style.overflow = '';
        icon.classList.remove('bi-fullscreen-exit');
        icon.classList.add('bi-arrows-fullscreen');
    }
    isImmersive = !isImmersive;
}