(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

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

    const path = location.pathname.replace(/\/index\.html$/, "/");
    qsa("[data-nav]").forEach((link) => {
      const href = link.getAttribute("href") || "";
      const clean = href.replace(window.TTC?.root || "", "");
      if ((clean === "./" || clean === "/") && (path === "/" || path === "")) {
        link.classList.add("is-active");
      } else if (clean !== "./" && clean !== "/" && path.includes(clean.replace(/^\.\//, ""))) {
        link.classList.add("is-active");
      }
    });
  }

  function bindHero() {
    const slides = qsa("[data-hero-slide]");
    if (!slides.length) return;
    let i = 0;
    const show = (n) => {
      slides.forEach((s) => s.classList.remove("is-active"));
      i = (n + slides.length) % slides.length;
      slides[i].classList.add("is-active");
    };
    qs("[data-hero-prev]")?.addEventListener("click", () => show(i - 1));
    qs("[data-hero-next]")?.addEventListener("click", () => show(i + 1));
    setInterval(() => show(i + 1), 7000);
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

  function boot() {
    bindChrome();
    bindHero();
    bindCarousels();
  }

  document.addEventListener("ttc:includes-ready", bindChrome);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
