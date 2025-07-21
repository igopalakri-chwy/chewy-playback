// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling to all elements
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                
                // Reset after a delay (in case of errors)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });

    // Add hover effects to interactive elements
    const interactiveElements = document.querySelectorAll('button, .nav-btn, .nav-dot');
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Add touch feedback for mobile
    if ('ontouchstart' in window) {
        const touchElements = document.querySelectorAll('button, .nav-btn, .nav-dot');
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.95)';
            });
            
            element.addEventListener('touchend', function() {
                this.style.transform = 'scale(1)';
            });
        });
    }

    // Add parallax effect to floating elements
    const floatingElements = document.querySelectorAll('.floating-paw');
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        floatingElements.forEach((element, index) => {
            const speed = 0.5 + (index * 0.1);
            element.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Escape key to go home
        if (e.key === 'Escape') {
            if (window.location.pathname !== '/') {
                window.location.href = '/';
            }
        }
        
        // Space bar to advance slides (if on experience page)
        if (e.key === ' ' && window.location.pathname.includes('/experience/')) {
            e.preventDefault();
            if (typeof nextSlide === 'function') {
                nextSlide();
            }
        }
    });

    // Add smooth transitions for page loads
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease-in-out';
        document.body.style.opacity = '1';
    }, 100);

    // Add error handling for images
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            this.style.display = 'none';
            const fallback = document.createElement('div');
            fallback.className = 'image-fallback';
            fallback.innerHTML = '<i class="fas fa-image"></i><p>Image not available</p>';
            this.parentNode.appendChild(fallback);
        });
    });

    // Add loading animations for dynamic content
    function addLoadingAnimation(element) {
        element.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';
    }

    // Add success animations
    function addSuccessAnimation(element) {
        element.classList.add('success-animation');
        setTimeout(() => {
            element.classList.remove('success-animation');
        }, 1000);
    }

    // Add confetti effect for special moments
    function createConfetti() {
        const colors = ['#4a90e2', '#2a5298', '#1e3c72', '#ff6b9d', '#90caf9'];
        const confettiCount = 50;
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.width = '8px';
            confetti.style.height = '8px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.top = '-10px';
            confetti.style.borderRadius = '50%';
            confetti.style.pointerEvents = 'none';
            confetti.style.zIndex = '9999';
            confetti.style.animation = `confettiFall ${Math.random() * 3 + 2}s linear forwards`;
            
            document.body.appendChild(confetti);
            
            setTimeout(() => {
                confetti.remove();
            }, 5000);
        }
    }

    // Add sparkle effect to important elements
    function addSparkleEffect(element) {
        const sparkle = document.createElement('div');
        sparkle.className = 'sparkle-effect';
        sparkle.innerHTML = '<i class="fas fa-star"></i>';
        element.appendChild(sparkle);
        
        setTimeout(() => {
            sparkle.remove();
        }, 2000);
    }

    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        .loading-spinner {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #7f8c8d;
        }
        
        .image-fallback {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #95a5a6;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
        }
        
        .image-fallback i {
            font-size: 32px;
            margin-bottom: 8px;
            opacity: 0.5;
        }
        
        .image-fallback p {
            font-size: 12px;
            margin: 0;
        }
        
        .success-animation {
            animation: successPulse 0.5s ease-in-out;
        }
        
        @keyframes successPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        


        @keyframes confettiFall {
            to {
                transform: translateY(100vh) rotate(360deg);
                opacity: 0;
            }
        }

        .sparkle-effect {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #ff6b9d;
            font-size: 24px;
            animation: sparkle 2s ease-in-out;
            pointer-events: none;
            z-index: 10;
        }

        @keyframes sparkle {
            0% { 
                opacity: 0; 
                transform: translate(-50%, -50%) scale(0) rotate(0deg); 
            }
            50% { 
                opacity: 1; 
                transform: translate(-50%, -50%) scale(1.2) rotate(180deg); 
            }
            100% { 
                opacity: 0; 
                transform: translate(-50%, -50%) scale(0) rotate(360deg); 
            }
        }

        .slide-title {
            animation: titleGlow 3s ease-in-out infinite;
        }

        @keyframes titleGlow {
            0%, 100% { 
                text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            }
            50% { 
                text-shadow: 0 4px 16px rgba(255, 255, 255, 0.4);
            }
        }

        .logo-container {
            animation: logoFloat 4s ease-in-out infinite;
        }

        @keyframes logoFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }

                .pet-avatar {
            animation: avatarBounce 2s ease-in-out infinite;
            animation-delay: calc(var(--avatar-index, 0) * 0.2s);
        }
        
        @keyframes avatarBounce {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            25% { transform: translateY(-8px) rotate(2deg); }
            50% { transform: translateY(-12px) rotate(0deg); }
            75% { transform: translateY(-8px) rotate(-2deg); }
        }

        .pet-avatar i {
            animation: pawWiggle 3s ease-in-out infinite;
            animation-delay: calc(var(--avatar-index, 0) * 0.3s);
        }

        @keyframes pawWiggle {
            0%, 100% { transform: rotate(0deg) scale(1); }
            25% { transform: rotate(5deg) scale(1.1); }
            50% { transform: rotate(0deg) scale(1.05); }
            75% { transform: rotate(-5deg) scale(1.1); }
        }

        .logo-icon {
            animation: pawBounce 4s ease-in-out infinite;
        }

        @keyframes pawBounce {
            0%, 100% { transform: scale(1) rotate(0deg); }
            25% { transform: scale(1.1) rotate(5deg); }
            50% { transform: scale(1.05) rotate(0deg); }
            75% { transform: scale(1.1) rotate(-5deg); }
        }

        .floating-paw {
            animation: pawFloat 8s ease-in-out infinite;
        }

        @keyframes pawFloat {
            0%, 100% { 
                transform: translateY(0px) rotate(0deg) scale(1); 
                opacity: 0.3;
            }
            25% { 
                transform: translateY(-20px) rotate(10deg) scale(1.2); 
                opacity: 0.6;
            }
            50% { 
                transform: translateY(-30px) rotate(0deg) scale(1.1); 
                opacity: 0.4;
            }
            75% { 
                transform: translateY(-20px) rotate(-10deg) scale(1.2); 
                opacity: 0.6;
            }
        }

        .slide-title i {
            animation: iconSparkle 2s ease-in-out infinite;
        }

        @keyframes iconSparkle {
            0%, 100% { 
                transform: scale(1) rotate(0deg); 
                filter: drop-shadow(0 2px 4px rgba(255, 107, 157, 0.3));
            }
            50% { 
                transform: scale(1.2) rotate(10deg); 
                filter: drop-shadow(0 4px 8px rgba(255, 107, 157, 0.5));
            }
        }

        .badge-title {
            animation: titleGlow 3s ease-in-out infinite;
        }

        @keyframes titleGlow {
            0%, 100% { 
                background: linear-gradient(135deg, #1e3c72, #4a90e2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            50% { 
                background: linear-gradient(135deg, #4a90e2, #ff6b9d);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
        }

        .letter-text {
            animation: letterReveal 1.2s ease-out;
        }

        @keyframes letterReveal {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .letter-text::before {
            animation: paperLines 10s ease-in-out infinite;
        }

        @keyframes paperLines {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.6; }
        }

        .portrait-image {
            animation: portraitGlow 4s ease-in-out infinite;
        }

        @keyframes portraitGlow {
            0%, 100% { 
                box-shadow: 
                    0 10px 25px rgba(0, 0, 0, 0.15),
                    0 0 0 2px rgba(255, 255, 255, 0.1);
            }
            50% { 
                box-shadow: 
                    0 15px 35px rgba(74, 144, 226, 0.3),
                    0 0 0 4px rgba(255, 255, 255, 0.2);
            }
        }

        .nav-dot {
            animation: dotPulse 2s ease-in-out infinite;
            animation-delay: calc(var(--dot-index, 0) * 0.3s);
        }

        @keyframes dotPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .submit-btn, .start-btn {
            animation: buttonGlow 3s ease-in-out infinite;
        }

        @keyframes buttonGlow {
            0%, 100% { 
                box-shadow: 
                    0 8px 25px rgba(74, 144, 226, 0.4),
                    0 0 0 1px rgba(255, 255, 255, 0.1);
            }
            50% { 
                box-shadow: 
                    0 12px 35px rgba(74, 144, 226, 0.6),
                    0 0 0 2px rgba(255, 255, 255, 0.2);
            }
        }

        .badge-display {
            animation: badgeReveal 1.2s ease-out;
        }

        @keyframes badgeReveal {
            from {
                opacity: 0;
                transform: scale(0.8) rotate(-10deg);
            }
            to {
                opacity: 1;
                transform: scale(1) rotate(0deg);
            }
        }

        .portrait-display {
            animation: portraitReveal 1.5s ease-out;
        }

        @keyframes portraitReveal {
            from {
                opacity: 0;
                transform: scale(0.9) translateY(30px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }

        .badge-image-container {
            animation: badgeRotate 10s linear infinite;
        }

        @keyframes badgeRotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .portrait-image {
            animation: portraitGlow 4s ease-in-out infinite;
        }

        @keyframes portraitGlow {
            0%, 100% { 
                box-shadow: 
                    0 10px 25px rgba(0, 0, 0, 0.15),
                    0 0 0 2px rgba(255, 255, 255, 0.1);
            }
            50% { 
                box-shadow: 
                    0 15px 35px rgba(74, 144, 226, 0.3),
                    0 0 0 4px rgba(255, 255, 255, 0.2);
            }
        }

        .nav-dot {
            animation: dotPulse 2s ease-in-out infinite;
            animation-delay: calc(var(--dot-index, 0) * 0.3s);
        }

        @keyframes dotPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .submit-btn, .start-btn {
            animation: buttonGlow 3s ease-in-out infinite;
        }

        @keyframes buttonGlow {
            0%, 100% { 
                box-shadow: 
                    0 8px 25px rgba(74, 144, 226, 0.4),
                    0 0 0 1px rgba(255, 255, 255, 0.1);
            }
            50% { 
                box-shadow: 
                    0 12px 35px rgba(74, 144, 226, 0.6),
                    0 0 0 2px rgba(255, 255, 255, 0.2);
            }
        }

                .letter-text {
            animation: letterReveal 1.2s ease-out;
        }
        
        @keyframes letterReveal {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .badge-display {
            animation: badgeReveal 1.2s ease-out;
        }

        @keyframes badgeReveal {
            from {
                opacity: 0;
                transform: scale(0.8) rotate(-10deg);
            }
            to {
                opacity: 1;
                transform: scale(1) rotate(0deg);
            }
        }

        .portrait-display {
            animation: portraitReveal 1.5s ease-out;
        }

        @keyframes portraitReveal {
            from {
                opacity: 0;
                transform: scale(0.9) translateY(30px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }
    `;
    document.head.appendChild(style);

    // Add avatar bounce animation delays
    document.querySelectorAll('.pet-avatar').forEach((avatar, index) => {
        avatar.style.setProperty('--avatar-index', index);
    });

    // Add dot pulse animation delays
    document.querySelectorAll('.nav-dot').forEach((dot, index) => {
        dot.style.setProperty('--dot-index', index);
    });

    // Add sparkle effects to important elements on hover
    const importantElements = document.querySelectorAll('.logo-container, .badge-image-container, .portrait-image');
    importantElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            addSparkleEffect(this);
        });
    });

    // Add confetti effect when starting the journey
    const startBtn = document.querySelector('.start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', function() {
            setTimeout(() => {
                createConfetti();
            }, 500);
        });
    }

    // Add confetti effect when completing the experience
    const homeBtn = document.querySelector('.home-btn');
    if (homeBtn) {
        homeBtn.addEventListener('click', function() {
            createConfetti();
        });
    }



    // Add beautiful letter reveal animation
    const letterText = document.querySelector('.letter-text');
    if (letterText && letterText.textContent.trim()) {
        letterText.style.opacity = '0';
        letterText.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            letterText.style.transition = 'all 1s ease-out';
            letterText.style.opacity = '1';
            letterText.style.transform = 'translateY(0)';
        }, 800);
    }
});

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Add smooth scrolling polyfill for older browsers
if (!('scrollBehavior' in document.documentElement.style)) {
    const smoothScrollPolyfill = function(target, duration) {
        const targetPosition = target.getBoundingClientRect().top;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        let startTime = null;

        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const run = ease(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
        }

        function ease(t, b, c, d) {
            t /= d / 2;
            if (t < 1) return c / 2 * t * t + b;
            t--;
            return -c / 2 * (t * (t - 2) - 1) + b;
        }

        requestAnimationFrame(animation);
    };

    // Override the native scrollIntoView
    Element.prototype.scrollIntoView = function(options) {
        if (options && options.behavior === 'smooth') {
            smoothScrollPolyfill(this, 300);
        } else {
            // Fallback to default behavior
            this.scrollIntoView();
        }
    };
} 