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

class FontManager {
    constructor() {
        this.currentFont = localStorage.getItem('mahainsight_font') || 'inter';
        this.init();
    }

    init() {
        // Apply saved font on load
        this.applyFont(this.currentFont);
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

        container.innerHTML = AVAILABLE_FONTS.map(font => `
            <button onclick="fontManager.applyFont('${font.id}')" 
                class="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 flex items-center justify-between group ${this.currentFont === font.id ? 'text-brand-600 bg-brand-50' : 'text-slate-700'}">
                <span style="font-family: ${font.family}">${font.name}</span>
                ${this.currentFont === font.id ? '<i class="bi bi-check-lg"></i>' : ''}
            </button>
        `).join('');
    }

    updateUI() {
        this.renderUI(); // Re-render to update checkmarks
    }
}

// Initialize global instance
window.fontManager = new FontManager();
