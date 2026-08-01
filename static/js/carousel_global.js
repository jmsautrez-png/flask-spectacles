(function () {
  var CAROUSEL_SELECTOR = '[data-carousel]';
  // Toutes les cartes visibles à l'écran défilent : l'IntersectionObserver met
  // déjà en pause celles hors du viewport, ce qui suffit pour la performance.
  var MAX_AUTOPLAY = Infinity;
  var DEFAULT_INTERVAL_MS = 8000;
  var instances = [];
  var observer = null;

  function getInterval(carouselEl) {
    var raw = parseInt(carouselEl.getAttribute('data-carousel-interval') || '', 10);
    if (!isNaN(raw) && raw >= 3000) return raw;
    return DEFAULT_INTERVAL_MS;
  }

  function isDetailMode(carouselEl) {
    return carouselEl.classList.contains('detail-carousel') || !!carouselEl.querySelector('.carousel-dot');
  }

  function createInstance(carouselEl) {
    var slides = Array.prototype.slice.call(carouselEl.querySelectorAll('.carousel-slide'));
    if (slides.length <= 1) return null;

    var detailMode = isDetailMode(carouselEl);
    var slidesContainer = detailMode ? null : carouselEl.querySelector('.carousel-slides');
    var indicators = detailMode
      ? Array.prototype.slice.call(carouselEl.querySelectorAll('.carousel-dot'))
      : Array.prototype.slice.call(carouselEl.querySelectorAll('.carousel-indicator'));
    var prevBtn = carouselEl.querySelector('.carousel-prev');
    var nextBtn = carouselEl.querySelector('.carousel-next');
    var counter = detailMode ? carouselEl.querySelector('.current-photo') : null;

    var state = {
      el: carouselEl,
      slides: slides,
      slidesContainer: slidesContainer,
      indicators: indicators,
      prevBtn: prevBtn,
      nextBtn: nextBtn,
      counter: counter,
      detailMode: detailMode,
      index: 0,
      inViewport: true,
      paused: false,
      running: false,
      timer: null,
      intervalMs: getInterval(carouselEl),
    };

    for (var i = 0; i < slides.length; i++) {
      if (slides[i].classList.contains('active')) {
        state.index = i;
        break;
      }
    }

    function render() {
      if (state.detailMode) {
        for (var i = 0; i < state.slides.length; i++) {
          state.slides[i].classList.toggle('active', i === state.index);
        }
      } else if (state.slidesContainer) {
        state.slidesContainer.style.transform = 'translateX(-' + (state.index * 100) + '%)';
      }

      for (var j = 0; j < state.indicators.length; j++) {
        var active = j === state.index;
        state.indicators[j].classList.toggle('active', active);
        if (state.detailMode) {
          state.indicators[j].style.background = active ? 'white' : 'transparent';
        }
      }

      if (state.counter) {
        state.counter.textContent = String(state.index + 1);
      }
    }

    function goToSlide(nextIndex) {
      if (nextIndex < 0) nextIndex = state.slides.length - 1;
      if (nextIndex >= state.slides.length) nextIndex = 0;
      state.index = nextIndex;
      render();
    }

    function nextSlide() {
      goToSlide(state.index + 1);
    }

    function prevSlide() {
      goToSlide(state.index - 1);
    }

    function stopAutoplay() {
      if (state.timer) {
        window.clearInterval(state.timer);
        state.timer = null;
      }
      state.running = false;
    }

    function startAutoplay() {
      if (state.running || state.paused || !state.inViewport || document.hidden) return;
      state.timer = window.setInterval(nextSlide, state.intervalMs);
      state.running = true;
    }

    function restartAutoplay() {
      stopAutoplay();
      startAutoplay();
    }

    state.goToSlide = goToSlide;
    state.nextSlide = nextSlide;
    state.prevSlide = prevSlide;
    state.startAutoplay = startAutoplay;
    state.stopAutoplay = stopAutoplay;
    state.restartAutoplay = restartAutoplay;

    if (state.prevBtn) {
      state.prevBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        prevSlide();
        restartAutoplay();
      });
    }

    if (state.nextBtn) {
      state.nextBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        nextSlide();
        restartAutoplay();
      });
    }

    for (var k = 0; k < state.indicators.length; k++) {
      (function (slideIndex) {
        state.indicators[slideIndex].addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          goToSlide(slideIndex);
          restartAutoplay();
        });
      })(k);
    }

    state.el.addEventListener('mouseenter', function () {
      state.paused = true;
      stopAutoplay();
    });
    state.el.addEventListener('mouseleave', function () {
      state.paused = false;
      rebalanceAutoplay();
    });
    state.el.addEventListener('touchstart', function () {
      state.paused = true;
      stopAutoplay();
    }, { passive: true });
    state.el.addEventListener('touchend', function () {
      state.paused = false;
      rebalanceAutoplay();
    }, { passive: true });

    render();
    return state;
  }

  function rebalanceAutoplay() {
    var eligible = [];
    for (var i = 0; i < instances.length; i++) {
      var inst = instances[i];
      if (!document.body.contains(inst.el)) {
        inst.stopAutoplay();
        continue;
      }
      if (!inst.inViewport || inst.paused || document.hidden) {
        inst.stopAutoplay();
        continue;
      }
      eligible.push(inst);
    }

    for (var j = 0; j < eligible.length; j++) {
      if (j < MAX_AUTOPLAY) eligible[j].startAutoplay();
      else eligible[j].stopAutoplay();
    }
  }

  function ensureObserver() {
    if (observer || !('IntersectionObserver' in window)) return;
    observer = new IntersectionObserver(function (entries) {
      for (var i = 0; i < entries.length; i++) {
        var entry = entries[i];
        var target = entry.target;
        for (var j = 0; j < instances.length; j++) {
          if (instances[j].el === target) {
            instances[j].inViewport = entry.isIntersecting;
            break;
          }
        }
      }
      rebalanceAutoplay();
    }, { threshold: 0.2 });
  }

  function initCarousels(root) {
    var scope = root || document;
    var nodes = scope.querySelectorAll(CAROUSEL_SELECTOR);

    ensureObserver();

    for (var i = 0; i < nodes.length; i++) {
      var carousel = nodes[i];
      if (carousel.dataset.carouselInit === '1') continue;
      carousel.dataset.carouselInit = '1';

      var instance = createInstance(carousel);
      if (!instance) continue;

      if (observer) {
        observer.observe(carousel);
      } else {
        instance.inViewport = true;
      }

      instances.push(instance);
    }

    rebalanceAutoplay();
  }

  document.addEventListener('visibilitychange', rebalanceAutoplay);
  document.addEventListener('DOMContentLoaded', function () {
    initCarousels(document);
  });

  window.initCarousels = initCarousels;
})();
