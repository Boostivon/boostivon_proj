// Theme Toggle
const initThemeToggle = () => {
  const themeToggle = document.getElementById('themeToggle');
  const htmlElement = document.documentElement;
  const body = document.body;

  // Check for saved theme preference or default to 'light'
  const currentTheme = localStorage.getItem('theme') || 'light';
  
  if (currentTheme === 'dark') {
    body.classList.add('dark-mode');
    updateThemeIcon(true);
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      body.classList.toggle('dark-mode');
      const isDarkMode = body.classList.contains('dark-mode');
      
      // Save theme preference
      localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
      updateThemeIcon(isDarkMode);
    });
  }
};

const updateThemeIcon = (isDarkMode) => {
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.innerHTML = isDarkMode ? '<span class="theme-icon">☀️</span>' : '<span class="theme-icon">🌙</span>';
  }
};

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', () => {
  // Initialize theme toggle
  initThemeToggle();
  const navbarMenu = document.getElementById('navbarMenu');

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
      navbarMenu.classList.toggle('active');
      mobileMenuBtn.classList.toggle('active');
    });

    // Close menu when a link is clicked
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        navbarMenu.classList.remove('active');
        mobileMenuBtn.classList.remove('active');
      });
    });
  }

  // Scroll animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
  };

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in-up');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe cards and sections
  document.querySelectorAll('.feature-card, .about-card, .service-item, .testimonial, .stat').forEach(el => {
    observer.observe(el);
  });

  // Counter animation for stats
  const animateCounters = () => {
    const stats = document.querySelectorAll('.stat-number');
    stats.forEach(stat => {
      const text = stat.textContent;
      const numbers = text.match(/\d+/g);
      
      if (numbers) {
        const finalValue = parseInt(numbers[0]);
        let currentValue = 0;
        const increment = Math.ceil(finalValue / 50);

        const counter = setInterval(() => {
          currentValue += increment;
          if (currentValue >= finalValue) {
            currentValue = finalValue;
            clearInterval(counter);
          }
          stat.textContent = text.replace(/\d+/, currentValue.toLocaleString());
        }, 30);
      }
    });
  };

  // Trigger counter animation when stats section is visible
  const statsSection = document.querySelector('.social-proof');
  if (statsSection) {
    const statsObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounters();
          statsObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    statsObserver.observe(statsSection);
  }

  // Navbar background on scroll
  const navbar = document.querySelector('.navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
    } else {
      navbar.style.boxShadow = 'none';
    }
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#' && href !== '#contact') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          const offsetTop = target.offsetTop - 80;
          window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
          });
        }
      }
    });
  });

  // Add fade-in class to hero content on load
  const heroLeft = document.querySelector('.hero-left');
  if (heroLeft) {
    heroLeft.style.opacity = '0';
    heroLeft.style.animation = 'fadeInUp 0.8s ease-out 0.2s forwards';
  }

  // Parallax effect on dashboard cards
  const dashboardMock = document.querySelector('.dashboard-mock');
  if (dashboardMock) {
    window.addEventListener('scroll', () => {
      const scrolled = window.pageYOffset;
      const element = document.querySelector('.hero-right');
      if (element) {
        element.style.transform = `translateY(${scrolled * 0.5}px)`;
      }
    });
  }

  // Keyboard navigation for mobile menu
  const navItems = document.querySelectorAll('.nav-link, .btn');
  navItems.forEach((item, index) => {
    item.setAttribute('tabindex', index);
  });

  // Form submission example for contact
  const handleContactClick = () => {
    console.log('Contact clicked - integrate with your contact form');
  };

  const contactLinks = document.querySelectorAll('[href="#contact"]');
  contactLinks.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      handleContactClick();
    });
  });
});

// Preload images for better performance
function preloadImages() {
  const images = [
    '/static/img/logo.svg',
    '/static/img/favicon.svg'
  ];

  images.forEach(img => {
    const image = new Image();
    image.src = img;
  });
}

// Call preload on page load
window.addEventListener('load', preloadImages);

// Handle hash navigation with smooth scroll
window.addEventListener('hashchange', () => {
  const hash = window.location.hash;
  if (hash && hash !== '#') {
    const element = document.querySelector(hash);
    if (element) {
      setTimeout(() => {
        const offsetTop = element.offsetTop - 80;
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
      }, 100);
    }
  }
});
