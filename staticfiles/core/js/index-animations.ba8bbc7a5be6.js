// Animaciones y funcionalidades mejoradas para index.html

// Configuración de Intersection Observer para animaciones
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
};

// Función para animar contadores
function animateCounter(element, target, duration = 2000) {
  // No animar contadores en el dashboard
  if (window.location.pathname.includes('dashusuario')) {
    element.textContent = target.toLocaleString();
    return;
  }
  
  let start = 0;
  const increment = target / (duration / 16);
  
  const timer = setInterval(() => {
    start += increment;
    if (start >= target) {
      element.textContent = target.toLocaleString();
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(start).toLocaleString();
    }
  }, 16);
}

// Función para animar barras de progreso
function animateProgressBar(element, percentage) {
  element.style.width = '0%';
  setTimeout(() => {
    element.style.width = percentage + '%';
  }, 100);
}

// Observer para animaciones de entrada
const fadeInObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate-fade-in');
      
      // Animar contadores si el elemento los contiene
      const counters = entry.target.querySelectorAll('.counter-number');
      counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        if (target) {
          animateCounter(counter, target);
        }
      });
      
      // Animar barras de progreso
      const progressBars = entry.target.querySelectorAll('.progress-bar');
      progressBars.forEach(bar => {
        const percentage = parseInt(bar.getAttribute('data-percentage')) || 75;
        animateProgressBar(bar, percentage);
      });
      
      fadeInObserver.unobserve(entry.target);
    }
  });
}, observerOptions);

// Observer para animaciones de deslizamiento
const slideInObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate-slide-in');
      slideInObserver.unobserve(entry.target);
    }
  });
}, observerOptions);

// Función para manejar el scroll de la navbar
function handleNavbarScroll() {
  const navbar = document.querySelector('.navbar-eco');
  if (!navbar) return;
  
  const scrolled = window.scrollY > 50;
  navbar.classList.toggle('scrolled', scrolled);
  
  // Cambiar opacidad del fondo
  navbar.style.backgroundColor = scrolled 
    ? 'rgba(255, 255, 255, 0.98)' 
    : 'rgba(255, 255, 255, 0.95)';
}

// Función para destacar enlaces de navegación activos
function highlightActiveNavLink() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link-eco');
  
  if (sections.length === 0 || navLinks.length === 0) return;
  
  const scrollPosition = window.scrollY + 100;
  
  sections.forEach(section => {
    const sectionTop = section.offsetTop;
    const sectionHeight = section.offsetHeight;
    const sectionId = section.getAttribute('id');
    
    if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + sectionId) {
          link.classList.add('active');
        }
      });
    }
  });
}

// Función para scroll suave
function smoothScroll() {
  const links = document.querySelectorAll('a[href^="#"]');
  
  links.forEach(link => {
    link.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const offsetTop = target.offsetTop - 80; // Ajuste para navbar fija
        
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
      }
    });
  });
}

// Función para manejar el video del hero
function handleHeroVideo() {
  const video = document.querySelector('.hero-video');
  if (!video) return;
  
  video.addEventListener('loadeddata', function() {
    this.style.opacity = '1';
  });
  
  video.addEventListener('error', function() {
    console.log('Error al cargar el video de fondo');
    this.style.display = 'none';
  });
  
  // Pausar video cuando no esté visible
  const videoObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        video.play().catch(e => console.log('Error al reproducir video:', e));
      } else {
        video.pause();
      }
    });
  });
  
  videoObserver.observe(video);
}

// Función para lazy loading de imágenes
function setupLazyLoading() {
  const images = document.querySelectorAll('img[data-src]');
  
  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.add('loaded');
        imageObserver.unobserve(img);
      }
    });
  });
  
  images.forEach(img => imageObserver.observe(img));
}

// Función para efectos de parallax suave
function setupParallax() {
  const parallaxElements = document.querySelectorAll('.parallax');
  
  function updateParallax() {
    const scrolled = window.pageYOffset;
    
    parallaxElements.forEach(element => {
      const rate = scrolled * -0.5;
      element.style.transform = `translateY(${rate}px)`;
    });
  }
  
  // Usar requestAnimationFrame para mejor rendimiento
  let ticking = false;
  
  function requestTick() {
    if (!ticking) {
      requestAnimationFrame(updateParallax);
      ticking = true;
    }
  }
  
  window.addEventListener('scroll', () => {
    requestTick();
    ticking = false;
  });
}

// Función para animar elementos al hacer hover
function setupHoverAnimations() {
  const cards = document.querySelectorAll('.categoria-card, .testimonial-card, .step-card, .impact-counter');
  
  cards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.willChange = 'transform';
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.willChange = 'auto';
    });
  });
}

// Función para manejar el carousel de testimonios (si existe)
function setupTestimonialCarousel() {
  const carousel = document.querySelector('.testimonial-carousel');
  if (!carousel) return;
  
  const cards = carousel.querySelectorAll('.testimonial-card');
  if (cards.length <= 3) return; // No necesita carousel si hay 3 o menos
  
  let currentIndex = 0;
  const cardsToShow = 3;
  
  function showCards() {
    cards.forEach((card, index) => {
      card.style.display = 'none';
      if (index >= currentIndex && index < currentIndex + cardsToShow) {
        card.style.display = 'block';
      }
    });
  }
  
  function nextSlide() {
    currentIndex = (currentIndex + 1) % (cards.length - cardsToShow + 1);
    showCards();
  }
  
  // Auto-rotate cada 5 segundos
  setInterval(nextSlide, 5000);
  showCards();
}

// Función para optimizar rendimiento
function optimizePerformance() {
  // Preload de imágenes críticas
  const criticalImages = [
    '/static/core/img/eco.jpg',
    '/static/core/img/plasticos.jpg',
    '/static/core/img/vidrio.jpg',
    '/static/core/img/papel.jpg',
    '/static/core/img/metales.jpg'
  ];
  
  criticalImages.forEach(src => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = src;
    document.head.appendChild(link);
  });
  
  // Reducir animaciones en dispositivos con batería baja
  if ('getBattery' in navigator) {
    navigator.getBattery().then(battery => {
      if (battery.level < 0.2) {
        document.body.classList.add('reduce-motion');
      }
    });
  }
}

// Función para manejar errores de carga
function handleLoadErrors() {
  // Manejar errores de imágenes
  document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
      e.target.src = '/static/core/img/placeholder.jpg';
      e.target.alt = 'Imagen no disponible';
    }
  }, true);
}

// Función de inicialización principal
function initializeIndex() {
  // Configurar observadores para animaciones
  const fadeElements = document.querySelectorAll('.fade-in-element, .impact-counter, .step-card');
  fadeElements.forEach(el => fadeInObserver.observe(el));
  
  const slideElements = document.querySelectorAll('.slide-in-element, .categoria-card, .testimonial-card');
  slideElements.forEach(el => slideInObserver.observe(el));
  
  // Configurar funcionalidades
  handleHeroVideo();
  setupLazyLoading();
  setupParallax();
  setupHoverAnimations();
  setupTestimonialCarousel();
  smoothScroll();
  optimizePerformance();
  handleLoadErrors();
  
  // Event listeners para scroll
  let scrollTimeout;
  window.addEventListener('scroll', () => {
    handleNavbarScroll();
    
    // Throttle para mejor rendimiento
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
    }
    scrollTimeout = setTimeout(highlightActiveNavLink, 10);
  });
  
  // Ejecutar una vez al cargar
  highlightActiveNavLink();
  
  console.log('✅ Index animations initialized successfully');
}

// CSS para animaciones (se inyecta dinámicamente)
const animationStyles = `
  .animate-fade-in {
    animation: none !important;
  }
  
  .animate-slide-in {
    animation: none !important;
  }
  
  @keyframes fadeInUp {
    from {
      opacity: 1;
      transform: translateY(0);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes slideInLeft {
    from {
      opacity: 1;
      transform: translateX(0);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  .loaded {
    opacity: 1;
    transition: opacity 0.3s ease;
  }
  
  img[data-src] {
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .reduce-motion * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Desactivar específicamente animaciones del hero */
  .hero-content {
    animation: none !important;
    transform: none !important;
  }
`;

// Inyectar estilos
const styleSheet = document.createElement('style');
styleSheet.textContent = animationStyles;
document.head.appendChild(styleSheet);

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeIndex);
} else {
  initializeIndex();
}