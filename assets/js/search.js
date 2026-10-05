(function () {
  function root() { return window.TTC?.root || "./"; }

  async function loadProducts() {
    if (window.TTC.products) return window.TTC.products;
    const res = await fetch(root() + "data/products.json");
    window.TTC.products = await res.json();
    return window.TTC.products;
  }

  function render(list) {
    const box = document.querySelector("[data-search-results]");
    if (!box) return;
    if (!list.length) {
      box.innerHTML = "<p>No matching products.</p>";
      return;
    }
    box.innerHTML = list.slice(0, 12).map((p) => `
      <a href="${root()}product/${p.slug}/">
        <img src="${root()}${p.image}" alt="${p.name}">
        <span>
          <strong>${p.name}</strong><br>
          <small>${p.brand || ""} ${p.sku ? "· " + p.sku : ""}</small>
        </span>
      </a>
    `).join("");
  }

  async function onSubmit(e) {
    e.preventDefault();
    const q = (e.target.querySelector("input[name='q']")?.value || "").trim().toLowerCase();
    const overlay = document.querySelector("[data-search-overlay]");
    if (overlay) overlay.classList.add("is-open");
    const products = await loadProducts();
    if (!q) {
      render(products.slice(0, 8));
      return;
    }
    render(products.filter((p) => {
      const hay = [p.name, p.sku, p.brand, p.description, ...(p.categories || []).map((c) => c.name)].join(" ").toLowerCase();
      return hay.includes(q);
    }));
  }

  document.addEventListener("submit", (e) => {
    if (e.target.matches("[data-search-form]")) onSubmit(e);
  });

  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-close-search]")) {
      document.querySelector("[data-search-overlay]")?.classList.remove("is-open");
    }
  });
})();
