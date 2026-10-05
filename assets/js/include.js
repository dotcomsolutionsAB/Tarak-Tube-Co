(function () {
  function rootPrefix() {
    const parts = location.pathname.replace(/\/index\.html$/, "").split("/").filter(Boolean);
    return parts.length === 0 ? "./" : "../".repeat(parts.length);
  }

  window.TTC = window.TTC || {};
  window.TTC.root = rootPrefix();

  document.querySelectorAll("[data-include]").forEach(async (node) => {
    const file = node.getAttribute("data-include");
    try {
      const res = await fetch(window.TTC.root + file);
      if (!res.ok) return;
      node.innerHTML = await res.text();
      node.querySelectorAll("[data-href]").forEach((el) => {
        el.setAttribute("href", window.TTC.root + el.getAttribute("data-href"));
      });
      node.querySelectorAll("[data-src]").forEach((el) => {
        el.setAttribute("src", window.TTC.root + el.getAttribute("data-src"));
      });
      document.dispatchEvent(new CustomEvent("ttc:includes-ready"));
    } catch (err) {
      console.warn("Include failed", file, err);
    }
  });
})();
