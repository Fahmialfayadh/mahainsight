/**
 * Interactive Background
 * Features:
 * - Purple ambient hover glow (Mouse trail)
 * - Clean background (No particles)
 */

class InteractiveBackground {
    constructor() {
        this.canvas = document.getElementById('bg-canvas');
        this.ctx = this.canvas.getContext('2d');

        this.mouse = { x: -1000, y: -1000 };
        this.resizeTimeout = null;

        // Configuration
        this.config = {
            glowRadius: 400,
            glowColor: 'rgba(124, 58, 237, 0.12)' // Purple-600 low opacity
        };

        this.init();
    }

    init() {
        this.resize();
        this.addEventListeners();
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    addEventListeners() {
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.resize();
            }, 200);
        });

        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });

        window.addEventListener('mouseleave', () => {
            this.mouse.x = -1000;
            this.mouse.y = -1000;
        });
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw Mouse Glow
        if (this.mouse.x > 0) {
            const glow = this.ctx.createRadialGradient(
                this.mouse.x, this.mouse.y, 0,
                this.mouse.x, this.mouse.y, this.config.glowRadius
            );
            // Inner color
            glow.addColorStop(0, this.config.glowColor);
            // Outer color (fade to transparent)
            glow.addColorStop(1, 'rgba(124, 58, 237, 0)');

            this.ctx.fillStyle = glow;
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        }

        requestAnimationFrame(() => this.draw());
    }

    animate() {
        this.draw();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('bg-canvas')) {
        new InteractiveBackground();
    }
});
