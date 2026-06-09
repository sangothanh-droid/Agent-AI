const BACKEND_URL = "https://agent-ai-1r9d.onrender.com";

// ── État ──
let currentConversationId = null;
let currentProjectId = null;
let projects = [];
let conversations = [];

// ── DOM ──
const messagesEl       = document.getElementById("messages");
const inputField       = document.getElementById("inputField");
const sendBtn          = document.getElementById("sendBtn");
const statusDot        = document.getElementById("statusDot");
const statusText       = document.getElementById("statusText");
const projectsList     = document.getElementById("projectsList");
const convList         = document.getElementById("convList");
const newChatBtn       = document.getElementById("newChatBtn");
const newProjectBtn    = document.getElementById("newProjectBtn");
const searchInput      = document.getElementById("searchInput");
const searchResults    = document.getElementById("searchResults");

// ── Init ──
checkBackend();
loadProjects();
loadConversations();

// ── Events ──
sendBtn.addEventListener("click", sendMessage);
inputField.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
inputField.addEventListener("input", () => {
  inputField.style.height = "auto";
  inputField.style.height = Math.min(inputField.scrollHeight, 180) + "px";
});
newChatBtn.addEventListener("click", () => startNewConversation());
newProjectBtn.addEventListener("click", createProject);

let searchTimeout;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  const q = searchInput.value.trim();
  if (q.length < 2) { searchResults.innerHTML = ""; searchResults.classList.remove("open"); return; }
  searchTimeout = setTimeout(() => doSearch(q), 400);
});

document.addEventListener("click", (e) => {
  if (!searchResults.contains(e.target) && e.target !== searchInput) {
    searchResults.classList.remove("open");
  }
});

// ── Backend check ──
async function checkBackend() {
  try {
    const r = await fetch(`${BACKEND_URL}/`);
    if (r.ok) { statusDot.className = "status-dot online"; statusText.textContent = "En ligne"; }
    else throw new Error();
  } catch {
    statusDot.className = "status-dot offline"; statusText.textContent = "Hors ligne";
  }
}

// ── Projets ──
async function loadProjects() {
  try {
    const r = await fetch(`${BACKEND_URL}/projects`);
    projects = await r.json();
    renderProjects();
  } catch (e) { console.error("Erreur chargement projets", e); }
}

function renderProjects() {
  projectsList.innerHTML = "";
  projects.forEach(p => {
    const li = document.createElement("li");
    li.className = "project-item" + (currentProjectId === p.id ? " active" : "");
    li.innerHTML = `
      <span class="project-name" data-id="${p.id}">📁 ${p.name}</span>
      <button class="delete-btn" data-id="${p.id}" title="Supprimer">✕</button>`;
    li.querySelector(".project-name").addEventListener("click", () => selectProject(p.id));
    li.querySelector(".delete-btn").addEventListener("click", (e) => { e.stopPropagation(); deleteProject(p.id); });
    projectsList.appendChild(li);
  });
}

async function createProject() {
  const name = prompt("Nom du projet :");
  if (!name?.trim()) return;
  try {
    const r = await fetch(`${BACKEND_URL}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim() })
    });
    const p = await r.json();
    projects.unshift(p);
    renderProjects();
  } catch (e) { alert("Erreur création projet"); }
}

async function deleteProject(id) {
  if (!confirm("Supprimer ce projet et toutes ses conversations ?")) return;
  await fetch(`${BACKEND_URL}/projects/${id}`, { method: "DELETE" });
  if (currentProjectId === id) { currentProjectId = null; }
  await loadProjects();
  await loadConversations();
}

function selectProject(id) {
  currentProjectId = currentProjectId === id ? null : id;
  renderProjects();
  loadConversations(currentProjectId);
}

// ── Conversations ──
async function loadConversations(projectId = null) {
  try {
    const url = projectId
      ? `${BACKEND_URL}/conversations?project_id=${projectId}`
      : `${BACKEND_URL}/conversations`;
    const r = await fetch(url);
    conversations = await r.json();
    renderConversations();
  } catch (e) { console.error("Erreur chargement conversations", e); }
}

function renderConversations() {
  convList.innerHTML = "";
  if (conversations.length === 0) {
    convList.innerHTML = `<li class="conv-empty">Aucune conversation</li>`;
    return;
  }
  conversations.forEach(c => {
    const li = document.createElement("li");
    li.className = "conv-item" + (currentConversationId === c.id ? " active" : "");
    li.innerHTML = `
      <span class="conv-title" data-id="${c.id}" title="${c.title}">${c.title}</span>
      <button class="delete-btn" data-id="${c.id}" title="Supprimer">✕</button>`;
    li.querySelector(".conv-title").addEventListener("click", () => loadConversation(c.id, c.title));
    li.querySelector(".delete-btn").addEventListener("click", (e) => { e.stopPropagation(); deleteConversation(c.id); });
    convList.appendChild(li);
  });
}

async function loadConversation(id, title) {
  currentConversationId = id;
  renderConversations();
  messagesEl.innerHTML = "";
  document.getElementById("chatTitle").textContent = title;
  try {
    const r = await fetch(`${BACKEND_URL}/conversations/${id}/messages`);
    const msgs = await r.json();
    if (msgs.length === 0) showWelcome();
    else msgs.forEach(m => appendMessage(m.role === "user" ? "user" : "agent", m.content));
  } catch (e) { showWelcome(); }
}

async function startNewConversation(projectId = null) {
  const title = "Nouvelle conversation";
  try {
    const r = await fetch(`${BACKEND_URL}/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, project_id: projectId || currentProjectId || null })
    });
    const conv = await r.json();
    currentConversationId = conv.id;
    conversations.unshift(conv);
    renderConversations();
    messagesEl.innerHTML = "";
    document.getElementById("chatTitle").textContent = title;
    showWelcome();
    inputField.focus();
  } catch (e) { alert("Erreur création conversation"); }
}

async function deleteConversation(id) {
  if (!confirm("Supprimer cette conversation ?")) return;
  await fetch(`${BACKEND_URL}/conversations/${id}`, { method: "DELETE" });
  if (currentConversationId === id) {
    currentConversationId = null;
    showWelcome();
    document.getElementById("chatTitle").textContent = "Agent IA";
  }
  conversations = conversations.filter(c => c.id !== id);
  renderConversations();
}

// ── Chat ──
let isLoading = false;

async function sendMessage() {
  const text = inputField.value.trim();
  if (!text || isLoading) return;

  // Crée une conversation si pas active
  if (!currentConversationId) {
    await startNewConversation();
    // Auto-titre basé sur le premier message
    const shortTitle = text.slice(0, 40) + (text.length > 40 ? "…" : "");
    await fetch(`${BACKEND_URL}/conversations/${currentConversationId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: shortTitle })
    });
    const idx = conversations.findIndex(c => c.id === currentConversationId);
    if (idx !== -1) { conversations[idx].title = shortTitle; renderConversations(); }
    document.getElementById("chatTitle").textContent = shortTitle;
  }

  inputField.value = "";
  inputField.style.height = "auto";
  const welcome = document.querySelector(".welcome");
  if (welcome) welcome.remove();

  appendMessage("user", text);
  const typingEl = appendTyping();
  isLoading = true;
  sendBtn.disabled = true;

  try {
    const r = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: currentConversationId, message: text })
    });
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail || `Erreur ${r.status}`); }
    const data = await r.json();
    typingEl.remove();
    appendMessage("agent", data.response);
  } catch (e) {
    typingEl.remove();
    appendMessage("agent", `❌ Erreur : ${e.message}`);
  } finally {
    isLoading = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
}

// ── Recherche ──
async function doSearch(q) {
  try {
    const r = await fetch(`${BACKEND_URL}/search?q=${encodeURIComponent(q)}`);
    const results = await r.json();
    renderSearchResults(results, q);
  } catch (e) {
    searchResults.innerHTML = `<div class="search-empty">Erreur de recherche</div>`;
    searchResults.classList.add("open");
  }
}

function renderSearchResults(results, q) {
  searchResults.innerHTML = "";
  if (!results.length) {
    searchResults.innerHTML = `<div class="search-empty">Aucun résultat pour "${q}"</div>`;
    searchResults.classList.add("open");
    return;
  }
  results.slice(0, 8).forEach(m => {
    const div = document.createElement("div");
    div.className = "search-item";
    const convTitle = m.conversation?.title || "Conversation";
    const snippet = m.content.slice(0, 100) + (m.content.length > 100 ? "…" : "");
    div.innerHTML = `
      <div class="search-conv">${convTitle}</div>
      <div class="search-snippet">${snippet}</div>`;
    div.addEventListener("click", () => {
      searchResults.classList.remove("open");
      searchInput.value = "";
      loadConversation(m.conversation_id, convTitle);
    });
    searchResults.appendChild(div);
  });
  searchResults.classList.add("open");
}

// ── UI helpers ──
function showWelcome() {
  messagesEl.innerHTML = `
    <div class="welcome">
      <h1>Prêt.</h1>
      <p>Pose ta question, colle du code, demande une commande Linux —<br/>je m'occupe du reste.</p>
    </div>`;
}

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "T" : "⬡";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = marked.parse(text);
  bubble.querySelectorAll("pre code").forEach(b => hljs.highlightElement(b));
  div.appendChild(avatar);
  div.appendChild(bubble);
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function appendTyping() {
  const div = document.createElement("div");
  div.className = "message agent";
  div.innerHTML = `
    <div class="avatar">⬡</div>
    <div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

showWelcome();
