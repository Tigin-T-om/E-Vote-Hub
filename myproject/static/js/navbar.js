// This code is already included in the base.html, but if you prefer to keep it in a separate file,
// you can save this as script.js and include it in your base.html

document.addEventListener('DOMContentLoaded', function() {
    const header = document.querySelector('.fixed-header');
    let lastScrollTop = 0;
    const scrollThreshold = 10; // Minimum scroll amount to trigger show/hide
    
    // Add initial styles (these are already in CSS, but reinforced here)
    header.style.position = 'fixed';
    header.style.top = '0';
    header.style.width = '100%';
    header.style.transition = 'transform 0.3s ease-in-out';
    
    // Adjust the content wrapper to account for the fixed header
    const contentWrapper = document.querySelector('.content-wrapper');
    const headerHeight = header.offsetHeight;
    contentWrapper.style.paddingTop = headerHeight + 'px';
    
    window.addEventListener('scroll', function() {
        let currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Check if we've scrolled more than the threshold
        if (Math.abs(lastScrollTop - currentScrollTop) <= scrollThreshold) {
            return;
        }
        
        // Scrolling down
        if (currentScrollTop > lastScrollTop && currentScrollTop > headerHeight) {
            header.style.transform = 'translateY(-100%)'; // Hide navbar
        } 
        // Scrolling up
        else {
            header.style.transform = 'translateY(0)'; // Show navbar
        }
        
        lastScrollTop = currentScrollTop;
    });
});