/**
 * MahaInsight Font Manager
 * Easily add new fonts here.
 */

const AVAILABLE_FONTS = [
    {
        name: "Default (Inter)",
        id: "inter",
        family: "'Inter', sans-serif",
        url: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap",
        type: "sans-serif"
    },
    {
        name: "Outfit (Modern)",
        id: "outfit",
        family: "'Outfit', sans-serif",
        url: "https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap",
        type: "sans-serif"
    },
    {
        name: "Merriweather (Classic)",
        id: "merriweather",
        family: "'Merriweather', serif",
        url: "https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&display=swap",
        type: "serif"
    },
    {
        name: "Lato (Clean)",
        id: "lato",
        family: "'Lato', sans-serif",
        url: "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        type: "sans-serif"
    },
    {
        name: "Playfair Display (Elegant)",
        id: "playfair",
        family: "'Playfair Display', serif",
        url: "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&display=swap",
        type: "serif"
    },
    {
        name: "Fira Code (Code)",
        id: "fira",
        family: "'Fira Code', monospace",
        url: "https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&display=swap",
        type: "monospace"
    }
];

const AVAILABLE_SIZES = [
    { label: "S", value: "0.875rem", mobileValue: "0.875rem" },
    { label: "M", value: "1rem", mobileValue: "0.95rem" },
    { label: "L", value: "1.125rem", mobileValue: "1.05rem" }, // Default Desktop
    { label: "XL", value: "1.25rem", mobileValue: "1.15rem" },
    { label: "2XL", value: "1.5rem", mobileValue: "1.35rem" }
];

class FontManager {
    constructor() {
        this.currentFont = localStorage.getItem('mahainsight_font') || 'inter';
        // Check if user has a stored preference, otherwise use 'auto' to let CSS media queries handle it initially
        // But for simplicity in UI, let's pick a default index if none stored.
        // Actually, to support the "auto" mobile adjustment effectively while allowing manual override:
        // We can store a specific value if set.
        this.currentSizeIndex = localStorage.getItem('mahainsight_font_size_index');
        this.init();
    }

    init() {
        // Apply saved font on load
        this.applyFont(this.currentFont);

        // Apply saved size if exists
        if (this.currentSizeIndex !== null) {
            this.applyFontSize(parseInt(this.currentSizeIndex));
        }

        this.renderUI();
    }

    applyFont(fontId) {
        const font = AVAILABLE_FONTS.find(f => f.id === fontId);
        if (!font) return;

        // 1. Load Font (if not already loaded/default)
        if (font.id !== 'inter') {
            this.loadFontLink(font.url);
        }

        // 2. Set CSS Variables
        document.documentElement.style.setProperty('--font-body', font.family);

        // Optionally update display font too, or keep it distinct
        // Giving user choice to update display font or just body? 
        // Let's update body, keep display distinct UNLESS it's a serif theme
        if (font.type === 'serif') {
            document.documentElement.style.setProperty('--font-display', font.family);
        } else {
            // Reset display to Outfit (default) if sans/mono selected, or use same?
            // Let's keep Outfit as the distinct brand display font unless specifically overridden
            document.documentElement.style.setProperty('--font-display', "'Outfit', sans-serif");
        }

        if (font.id === 'outfit') {
            document.documentElement.style.setProperty('--font-body', "'Outfit', sans-serif");
            document.documentElement.style.setProperty('--font-display', "'Outfit', sans-serif");
        }

        // 3. Save preference
        localStorage.setItem('mahainsight_font', fontId);
        this.currentFont = fontId;

        // Update UI active state if UI exists
        this.updateUI();
    }

    applyFontSize(index) {
        if (index < 0 || index >= AVAILABLE_SIZES.length) return;

        const size = AVAILABLE_SIZES[index];

        // When user manually sets size, we enforce it as an override
        // We can set it directly on the root. 
        // Note: This overrides media queries if we set it inline on :root.
        // To keep mobile responsiveness for "manual" picks, we might need complex logic.
        // simplified approach: User picks "L", they get "L" size everywhere. 
        // OR: We can store the index and apply the specific value based on viewport width (requires JS listener).

        // Better approach for this task: Set the variable. If user strictly wants 18px, they get 18px.
        // However, the user asked for "adjust font dimobile agar lebih kecil secara otomatis".
        // This implies the DEFAULT behavior should be responsive. 
        // If I pick "XL" on desktop, it should probably be "XL" for mobile too (maybe slightly scaled?).
        // Let's use the `mobileValue` from my config above for a smarter manual override.

        const isMobile = window.innerWidth < 640;
        const val = isMobile ? size.mobileValue : size.value;

        document.documentElement.style.setProperty('--article-font-size', val);

        // Save preference
        localStorage.setItem('mahainsight_font_size_index', index);
        this.currentSizeIndex = index;

        this.updateUI();
    }

    loadFontLink(url) {
        // Check if link already exists
        if (document.querySelector(`link[href="${url}"]`)) return;

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        document.head.appendChild(link);
    }

    renderUI() {
        // Will be called by base.html to render Dropdown items
        const container = document.getElementById('font-options-container');
        if (!container) return;

        // Font Family Section
        let html = `<div class="mb-3 space-y-1">`;
        html += AVAILABLE_FONTS.map(font => `
            <button onclick="fontManager.applyFont('${font.id}')" 
                class="w-full text-left px-3 py-2 text-sm rounded-lg hover:bg-slate-50 flex items-center justify-between group transition ${this.currentFont === font.id ? 'text-brand-600 bg-brand-50 font-medium' : 'text-slate-600'}">
                <span style="font-family: ${font.family}">${font.name}</span>
                ${this.currentFont === font.id ? '<i class="bi bi-check-lg"></i>' : ''}
            </button>
        `).join('');
        html += `</div>`;

        // Font Size Section
        html += `
            <div class="px-3 py-1 border-t border-slate-100 mt-2 pt-2">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Ukuran Text</div>
                <div class="flex items-center justify-between bg-slate-50 rounded-lg p-1 border border-slate-200">
                    <!-- Reset / Auto Button -->
                     <button onclick="fontManager.resetFontSize()" title="Reset ke Auto"
                        class="p-1 px-2 text-xs rounded hover:bg-white hover:shadow-sm text-slate-500 transition">
                        Auto
                    </button>
                    
                    <div class="flex items-center gap-1">
                        <button onclick="fontManager.stepFontSize(-1)" class="w-7 h-7 flex items-center justify-center rounded hover:bg-white hover:shadow-sm text-slate-600 disabled:opacity-30 transition" ${this.currentSizeIndex == 0 ? 'disabled' : ''}>
                            <i class="bi bi-dash-lg"></i>
                        </button>
                        
                        <span class="text-xs font-medium text-slate-700 w-8 text-center">
                            ${this.currentSizeIndex !== null && this.currentSizeIndex !== undefined ? AVAILABLE_SIZES[this.currentSizeIndex].label : 'Auto'}
                        </span>
                        
                        <button onclick="fontManager.stepFontSize(1)" class="w-7 h-7 flex items-center justify-center rounded hover:bg-white hover:shadow-sm text-slate-600 disabled:opacity-30 transition" ${this.currentSizeIndex == AVAILABLE_SIZES.length - 1 ? 'disabled' : ''}>
                            <i class="bi bi-plus-lg"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    stepFontSize(direction) {
        // If not set yet, determine default based on screen size
        let idx;
        if (this.currentSizeIndex !== null) {
            idx = parseInt(this.currentSizeIndex);
        } else {
            // Default: Mobile = M (1), Desktop = L (2)
            idx = window.innerWidth < 640 ? 1 : 2;
        }

        idx += direction;

        if (idx >= 0 && idx < AVAILABLE_SIZES.length) {
            this.applyFontSize(idx);
        }
    }

    resetFontSize() {
        localStorage.removeItem('mahainsight_font_size_index');
        this.currentSizeIndex = null;
        document.documentElement.style.removeProperty('--article-font-size');
        this.updateUI();
    }

    updateUI() {
        this.renderUI(); // Re-render to update checkmarks
    }
}

// Initialize global instance
window.fontManager = new FontManager();

// Handle window resize to adjust font size if a manual preference is set 
// (because we used value/mobileValue logic in JS)
window.addEventListener('resize', () => {
    if (window.fontManager && window.fontManager.currentSizeIndex !== null) {
        // Re-apply to catch the viewport change
        window.fontManager.applyFontSize(parseInt(window.fontManager.currentSizeIndex));
    }
});
