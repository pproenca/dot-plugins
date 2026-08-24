const state = { plugins: [], client: "codex", query: "" };

const grid = document.querySelector("#plugin-grid");
const emptyState = document.querySelector("#empty-state");
const dialog = document.querySelector("#plugin-dialog");
const dialogContent = document.querySelector("#dialog-content");
const toast = document.querySelector(".toast");

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character]);

function installCommand(plugin) {
  if (state.client === "claude") return `/plugin install ${plugin.name}@dot-plugins`;
  return `codex plugin add ${plugin.name}@dot-plugins`;
}

function iconMarkup(plugin) {
  if (!plugin.icon) return `<span aria-hidden="true">✦</span>`;
  return `<img src="${escapeHtml(plugin.icon)}" alt="" />`;
}

function pluginCard(plugin) {
  const keywords = plugin.keywords.slice(0, 3).map((keyword) => `<span>${escapeHtml(keyword)}</span>`).join("");
  return `
    <article class="plugin-card" style="--card-color:${escapeHtml(plugin.brandColor)}">
      <div class="card-top">
        <div class="plugin-icon">${iconMarkup(plugin)}</div>
        <span class="version">v${escapeHtml(plugin.version)}</span>
      </div>
      <h3>${escapeHtml(plugin.displayName)}</h3>
      <p class="byline">by ${escapeHtml(plugin.author)}</p>
      <p class="card-description">${escapeHtml(plugin.shortDescription)}</p>
      <div class="card-tags">${keywords}</div>
      <div class="card-footer">
        <small>${plugin.skillCount} ${plugin.skillCount === 1 ? "skill" : "skills"}</small>
        <button class="view-plugin" type="button" data-plugin="${escapeHtml(plugin.name)}">View plugin</button>
      </div>
    </article>`;
}

function render() {
  const query = state.query.trim().toLowerCase();
  const filtered = state.plugins.filter((plugin) => {
    const haystack = [plugin.name, plugin.displayName, plugin.author, plugin.description, ...plugin.keywords, ...plugin.skills]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
  grid.innerHTML = filtered.map(pluginCard).join("");
  grid.setAttribute("aria-busy", "false");
  emptyState.hidden = filtered.length > 0;
}

function showPlugin(plugin) {
  const license = plugin.license ? escapeHtml(plugin.license) : "No license stated upstream";
  const prompts = plugin.prompts.map((prompt) => `<li>“${escapeHtml(prompt)}”</li>`).join("");
  dialogContent.innerHTML = `
    <div class="dialog-body">
      <div class="dialog-heading">
        <div class="plugin-icon" style="--card-color:${escapeHtml(plugin.brandColor)}">${iconMarkup(plugin)}</div>
        <div><p class="dialog-kicker">v${escapeHtml(plugin.version)} · ${license}</p><h2 id="dialog-title">${escapeHtml(plugin.displayName)}</h2></div>
      </div>
      <p class="dialog-description">${escapeHtml(plugin.longDescription)}</p>
      <div class="dialog-section">
        <h3>Install for ${state.client === "claude" ? "Claude Code" : "Codex"}</h3>
        <div class="install-box"><code>${escapeHtml(installCommand(plugin))}</code><button type="button" data-copy="${escapeHtml(installCommand(plugin))}">Copy</button></div>
      </div>
      ${prompts ? `<div class="dialog-section"><h3>Try asking</h3><ul class="prompt-list">${prompts}</ul></div>` : ""}
      <div class="dialog-links"><a href="${escapeHtml(plugin.source)}">View source ↗</a><a href="${escapeHtml(plugin.homepage)}">Homepage ↗</a></div>
    </div>`;
  dialog.showModal();
}

function notifyCopied() {
  toast.classList.add("visible");
  window.clearTimeout(notifyCopied.timeout);
  notifyCopied.timeout = window.setTimeout(() => toast.classList.remove("visible"), 1800);
}

async function copyText(text) {
  await navigator.clipboard.writeText(text);
  notifyCopied();
}

document.querySelector("#search").addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

document.querySelectorAll("[data-client]").forEach((button) => {
  button.addEventListener("click", () => {
    state.client = button.dataset.client;
    document.querySelectorAll("[data-client]").forEach((candidate) => {
      const active = candidate === button;
      candidate.classList.toggle("active", active);
      candidate.setAttribute("aria-pressed", active);
    });
  });
});

document.addEventListener("click", (event) => {
  const pluginButton = event.target.closest("[data-plugin]");
  if (pluginButton) showPlugin(state.plugins.find((plugin) => plugin.name === pluginButton.dataset.plugin));

  const copyButton = event.target.closest("[data-copy], [data-copy-target]");
  if (copyButton) {
    const text = copyButton.dataset.copy ?? document.querySelector(`#${copyButton.dataset.copyTarget}`).textContent.replace(/^\$\s*/, "");
    copyText(text).catch(() => {});
  }
});

document.querySelector(".dialog-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  const bounds = dialog.getBoundingClientRect();
  const outside = event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom;
  if (outside) dialog.close();
});

fetch("data/plugins.json")
  .then((response) => {
    if (!response.ok) throw new Error(`Marketplace data failed with ${response.status}`);
    return response.json();
  })
  .then((data) => {
    state.plugins = data.plugins;
    document.querySelector("#plugin-stat").textContent = data.pluginCount;
    document.querySelector("#skill-stat").textContent = data.skillCount;
    render();
  })
  .catch(() => {
    grid.innerHTML = '<div class="loading-card">The collection could not be loaded. Please refresh or visit the GitHub repository.</div>';
    grid.setAttribute("aria-busy", "false");
  });
