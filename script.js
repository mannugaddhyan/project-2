// Enhanced Mobile Navigation with better touch handling
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');
    const navbar = document.getElementById('navbar');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Mobile menu toggle
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function(e) {
            e.preventDefault();
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
            
            // Prevent body scroll when menu is open
            document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
        });
        
        // Close menu when clicking on navigation links
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    // Enhanced navbar scroll effect
    let lastScrollTop = 0;
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScrollTop = scrollTop;
    }, { passive: true });
});

// Enhanced smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const headerOffset = 80;
            const elementPosition = target.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Enhanced counter animation with intersection observer
function animateCounter(element, target, duration = 2000, suffix = '') {
    if (element.dataset.animated) return;
    element.dataset.animated = 'true';
    
    let start = 0;
    const startTime = performance.now();
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Use easing function for smoother animation
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = Math.floor(start + (target - start) * easeOutQuart);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target.toLocaleString() + suffix;
        }
    }
    
    requestAnimationFrame(updateCounter);
}

// Enhanced Intersection Observer for animations
const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            
            // Animate counters when floating card comes into view
            if (entry.target.classList.contains('floating-card')) {
                const counters = entry.target.querySelectorAll('.metric-value');
                counters.forEach((counter, index) => {
                    const target = parseInt(counter.dataset.target);
                    const prefix = counter.parentNode.querySelector('.metric-prefix');
                    const suffix = counter.parentNode.querySelector('.metric-suffix');
                    
                    setTimeout(() => {
                        if (target === 1940) {
                            animateCounter(counter, target, 2500);
                        } else if (target === 94) {
                            animateCounter(counter, target, 2000);
                        } else if (target === 2.4) {
                            // Special handling for decimal number
                            let start = 0;
                            const duration = 2000;
                            const startTime = performance.now();
                            
                            function updateDecimal(currentTime) {
                                const elapsed = currentTime - startTime;
                                const progress = Math.min(elapsed / duration, 1);
                                const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                                const current = (start + (target - start) * easeOutQuart).toFixed(1);
                                
                                counter.textContent = current;
                                
                                if (progress < 1) {
                                    requestAnimationFrame(updateDecimal);
                                } else {
                                    counter.textContent = target.toFixed(1);
                                }
                            }
                            
                            if (!counter.dataset.animated) {
                                counter.dataset.animated = 'true';
                                requestAnimationFrame(updateDecimal);
                            }
                        }
                    }, index * 200);
                });
            }
            
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', function() {
    const animatedElements = document.querySelectorAll(
        '.feature-card, .tech-item, .floating-card, .token-card, .hero-content, .hero-visual'
    );
    animatedElements.forEach(el => observer.observe(el));
});

// Enhanced particle system for hero background
function createParticles() {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    
    const particleCount = window.innerWidth < 768 ? 20 : 30; // Fewer particles on mobile
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: ${Math.random() * 3 + 1}px;
            height: ${Math.random() * 3 + 1}px;
            background: rgba(102, 126, 234, ${Math.random() * 0.5 + 0.2});
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            pointer-events: none;
            z-index: 1;
            animation: particle-float ${Math.random() * 20 + 20}s linear infinite;
            animation-delay: ${Math.random() * 10}s;
        `;
        hero.appendChild(particle);
    }
    
    // Add CSS animation for particles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes particle-float {
            0% {
                transform: translateY(100vh) translateX(0px) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100px) translateX(${Math.random() * 200 - 100}px) rotate(360deg);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Initialize particles on load
document.addEventListener('DOMContentLoaded', createParticles);

// Copy to clipboard functionality for contract address
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification('Contract address copied to clipboard!', 'success');
        }).catch(function() {
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Contract address copied to clipboard!', 'success');
    } catch (err) {
        showNotification('Failed to copy contract address', 'error');
    }
    
    document.body.removeChild(textArea);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#667eea'};
        color: white;
        padding: 12px 24px;
        border-radius: 12px;
        z-index: 10000;
        font-weight: 600;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Animate out and remove
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Add click handler for contract address
document.addEventListener('DOMContentLoaded', function() {
    const contractAddress = document.querySelector('.contract-address');
    if (contractAddress) {
        contractAddress.addEventListener('click', function() {
            copyToClipboard('B8bFLQUZg9exegB1RWV9D7eRsQw1EjyfKU22jf1fpump');
        });
    }
});

// Enhanced button loading states
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.btn:not([href^="#"])');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.classList.contains('loading')) return;
            
            const originalText = this.innerHTML;
            const isExternal = this.href && !this.href.includes('#');
            
            if (!isExternal || this.textContent.includes('Coming Soon')) {
                e.preventDefault();
                
                this.classList.add('loading');
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                this.style.pointerEvents = 'none';
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.style.pointerEvents = 'auto';
                    this.classList.remove('loading');
                }, 1500);
            }
        });
    });
});

// Enhanced scroll performance with throttling
let ticking = false;
function updateScrollEffects() {
    const scrollTop = window.pageYOffset;
    const windowHeight = window.innerHeight;
    
    // Parallax effect for hero background (disabled on mobile for performance)
    if (window.innerWidth > 768) {
        const heroBackground = document.querySelector('.hero-background');
        if (heroBackground) {
            const translateY = scrollTop * 0.5;
            heroBackground.style.transform = `translateY(${translateY}px)`;
        }
    }
    
    ticking = false;
}

function requestScrollUpdate() {
    if (!ticking) {
        requestAnimationFrame(updateScrollEffects);
        ticking = true;
    }
}

window.addEventListener('scroll', requestScrollUpdate, { passive: true });

// Performance monitoring and optimization
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Register service worker for better caching (if available)
        // This is optional and would require a separate service worker file
    });
}

// Preload critical resources
document.addEventListener('DOMContentLoaded', function() {
    // Preload important images
    const importantImages = [
        // Add any critical images here
    ];
    
    importantImages.forEach(src => {
        const img = new Image();
        img.src = src;
    });
});

// Error handling for failed resources
window.addEventListener('error', function(e) {
    console.warn('Resource failed to load:', e.target);
    // Handle failed resource loading gracefully
}, true);

// Accessibility improvements
document.addEventListener('keydown', function(e) {
    // Handle escape key to close mobile menu
    if (e.key === 'Escape') {
        const hamburger = document.getElementById('hamburger');
        const navMenu = document.getElementById('nav-menu');
        if (hamburger && navMenu && navMenu.classList.contains('active')) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
});

// Enhanced AOS (Animate On Scroll) implementation
function initAOS() {
    const elements = document.querySelectorAll('[data-aos]');
    
    const aosObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const delay = element.dataset.aosDelay || 0;
                
                setTimeout(() => {
                    element.classList.add('aos-animate');
                }, delay);
                
                aosObserver.unobserve(element);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -10% 0px'
    });
    
    elements.forEach(el => aosObserver.observe(el));
}

// Initialize AOS on load
document.addEventListener('DOMContentLoaded', initAOS);

// Add CSS for AOS animations
const aosStyle = document.createElement('style');
aosStyle.textContent = `
    [data-aos] {
        opacity: 0;
        transform: translateY(30px);
        transition: opacity 0.6s ease, transform 0.6s ease;
    }
    
    [data-aos="fade-up"] {
        transform: translateY(30px);
    }
    
    [data-aos="zoom-in"] {
        transform: scale(0.9);
    }
    
    [data-aos].aos-animate {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
`;
document.head.appendChild(aosStyle);

// Console branding
console.log(`
%c🚀 PolyTale - AI-Powered Polymarket Intelligence
%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

%cThanks for exploring our code! 
We're building the future of prediction market intelligence.

%c🐦 Follow us: @polytale_
🌐 Website: https://polytale.ai
💎 Token: $PolyTale

%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`,
'color: #667eea; font-weight: bold; font-size: 16px;',
'color: #764ba2;',
'color: #ffffff; font-size: 14px;',
'color: #667eea; font-size: 12px;',
'color: #764ba2;'
);