(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Active nav links are set at build time (class="is-active"), so no path matching here.
  function bindChrome() {
    const drawer = qs("[data-drawer]");
    const openBtn = qs("[data-open-drawer]");
    const closeBtn = qs("[data-close-drawer]");
    if (openBtn && drawer) openBtn.addEventListener("click", () => drawer.classList.add("is-open"));
    if (closeBtn && drawer) closeBtn.addEventListener("click", () => drawer.classList.remove("is-open"));
    if (drawer) drawer.addEventListener("click", (e) => {
      if (e.target === drawer) drawer.classList.remove("is-open");
    });

    qsa("[data-drawer-tab]").forEach((tab) => {
      tab.addEventListener("click", () => {
        qsa("[data-drawer-tab]").forEach((t) => t.classList.remove("is-active"));
        qsa("[data-drawer-panel]").forEach((p) => p.classList.remove("is-active"));
        tab.classList.add("is-active");
        const panel = qs('[data-drawer-panel="' + tab.dataset.drawerTab + '"]');
        if (panel) panel.classList.add("is-active");
      });
    });
  }

  function bindHero() {
    const hero = qs(".hero");
    const slides = qsa("[data-hero-slide]");
    if (!hero || !slides.length) return;
    const dots = qsa("[data-hero-dot]");
    let i = 0;
    let timer = null;
    const show = (n) => {
      slides[i].classList.remove("is-active");
      dots[i]?.classList.remove("is-active");
      i = (n + slides.length) % slides.length;
      slides[i].classList.add("is-active");
      // Restart the dot's progress animation.
      if (dots[i]) {
        void dots[i].offsetWidth;
        dots[i].classList.add("is-active");
      }
    };
    const start = () => { stop(); timer = setInterval(() => show(i + 1), 7000); };
    const stop = () => { if (timer) clearInterval(timer); timer = null; };

    qs("[data-hero-prev]")?.addEventListener("click", () => { show(i - 1); start(); });
    qs("[data-hero-next]")?.addEventListener("click", () => { show(i + 1); start(); });
    dots.forEach((dot, n) => dot.addEventListener("click", () => { show(n); start(); }));
    hero.addEventListener("mouseenter", () => { stop(); hero.classList.add("is-paused"); });
    hero.addEventListener("mouseleave", () => { start(); hero.classList.remove("is-paused"); });
    dots[0]?.classList.add("is-active");
    start();
  }

  function bindCarousels() {
    qsa("[data-carousel]").forEach((wrap) => {
      const track = qs("[data-track]", wrap);
      if (!track) return;
      qs("[data-prev]", wrap)?.addEventListener("click", () => {
        track.scrollBy({ left: -track.clientWidth * 0.8, behavior: "smooth" });
      });
      qs("[data-next]", wrap)?.addEventListener("click", () => {
        track.scrollBy({ left: track.clientWidth * 0.8, behavior: "smooth" });
      });
    });
  }

  function bindScrollChrome() {
    const header = qs(".site-header");
    const toTop = qs("[data-to-top]");
    const onScroll = () => {
      const y = window.scrollY;
      header?.classList.toggle("is-scrolled", y > 8);
      toTop?.classList.toggle("is-visible", y > 600);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    toTop?.addEventListener("click", () => window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" }));
  }

  // Fade-up elements as they enter the viewport; siblings are staggered.
  function bindReveal() {
    const selector = [
      ".section-head", ".card", ".stat", ".about-card", ".contact-card", ".map-card",
      ".intro-block > *", ".about-intro > div:first-child", ".brand-list.large li",
      ".cta-inner > *", ".detail-grid > *", ".product-layout > *", ".page-hero .container",
      ".chips",
    ].join(",");
    const items = qsa(selector).filter((el) => !el.closest(".hero"));
    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-in"));
      return;
    }
    items.forEach((el) => {
      el.classList.add("reveal");
      const siblings = Array.from(el.parentElement.children).filter((c) => c.matches(selector));
      const idx = siblings.indexOf(el);
      el.style.transitionDelay = `${(idx % 4) * 80}ms`;
    });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        el.classList.add("is-in");
        io.unobserve(el);
        // Drop the stagger delay once revealed so hover effects respond instantly.
        setTimeout(() => { el.style.transitionDelay = ""; }, 1000);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach((el) => io.observe(el));
  }

  // Count stat figures up from zero the first time they are seen.
  function bindCounters() {
    const nums = qsa(".stat strong");
    if (!nums.length) return;
    const run = (el) => {
      const match = el.textContent.trim().match(/^(\d+)(.*)$/);
      if (!match) return;
      const target = parseInt(match[1], 10);
      const suffix = match[2];
      // Years look odd counting from 0, so start them close to the target.
      const from = target > 1900 && target < 2100 ? target - 30 : 0;
      const duration = 1400;
      const t0 = performance.now();
      const step = (t) => {
        const p = Math.min((t - t0) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(from + (target - from) * eased) + suffix;
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    if (reduceMotion || !("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        run(entry.target);
        io.unobserve(entry.target);
      });
    }, { threshold: 0.6 });
    nums.forEach((el) => io.observe(el));
  }

  function boot() {
    bindChrome();
    bindHero();
    bindCarousels();
    bindScrollChrome();
    bindReveal();
    bindCounters();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
