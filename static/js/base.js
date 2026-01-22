const navbar = document.getElementById('navbar');
const mobileBtn = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
const menuIcon = document.getElementById('menu-icon');
const mobileLinks = document.querySelectorAll('.mobile-link');
const mainContent = document.getElementById('main-content');
const flashContainer = document.getElementById('flash-container'); // Handle Flash too

// Mobile Menu Toggle
mobileBtn.addEventListener('click', () => {
    mobileMenu.classList.toggle('hidden');

    // Toggle Icon
    if (mobileMenu.classList.contains('hidden')) {
        // CLOSED
        menuIcon.classList.remove('bi-x');
        menuIcon.classList.add('bi-list');

        // Reset Push
        mainContent.style.marginTop = '0px';
        flashContainer.style.marginTop = '0px';
    } else {
        // OPENED
        menuIcon.classList.remove('bi-list');
        menuIcon.classList.add('bi-x');

        // Push Content Down
        // We add margin equal to menu height to the first content container
        const menuHeight = mobileMenu.scrollHeight;
        flashContainer.style.marginTop = menuHeight + 'px';
    }
});

// Close menu when clicking links
mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
        mobileMenu.classList.add('hidden');
        menuIcon.classList.remove('bi-x');
        menuIcon.classList.add('bi-list');
        mainContent.style.marginTop = '0px';
        flashContainer.style.marginTop = '0px';
    });
});

// Scroll Behavior (Pop out / Autohide)
let lastScroll = 0;
const threshold = 100;

window.addEventListener('scroll', () => {
    // Don't hide navbar if mobile menu is open
    if (!mobileMenu.classList.contains('hidden')) return;

    const currentScroll = window.pageYOffset;

    // Determine scroll direction
    if (currentScroll > lastScroll && currentScroll > threshold) {
        // Scrolling Down -> Hide Navbar
        navbar.classList.add('-translate-y-full');
    } else {
        // Scrolling Up -> Show Navbar
        navbar.classList.remove('-translate-y-full');
    }

    // Add shadow when scrolled
    if (currentScroll > 20) {
        navbar.classList.add('shadow-md');
        navbar.classList.replace('bg-white/70', 'bg-white/90');
    } else {
        navbar.classList.remove('shadow-md');
        navbar.classList.replace('bg-white/90', 'bg-white/70');
    }

    lastScroll = currentScroll;
});

// Initialize Font Manager UI after load if it didn't run
document.addEventListener('DOMContentLoaded', () => {
    if (window.fontManager) window.fontManager.renderUI();
});