// ── Config ──
// Change cette URL par celle de ton backend Render après déploiement
const BACKEND_URL = "https://TON-BACKEND.onrender.com";

// ── État ──
const sessionId = crypto.randomUUID();
let isLoading = false;

// ── DOM ──
const messages   = document.getElementById("messages");
const inputField = document.getElementById("inputField");
const sendBtn    = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");
const statusDot  = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

// ── Init ──
checkBackend();
inputField.focus();

// ── Events ──
sendBtn.addEventListener("click", sendMessage);

inputField.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

inputField.addEventListener("input", () => {
  inputField.style.height = "auto";
  inputField.style.height = Math.min(inputField.scrollHeight, 180) + "px";
});

newChatBtn.addEventListener("click", () => {
  resetSession();
});

// ── Fonctions ──
async function sendMessage() {
  const text = inputField.value.trim();
  if (!text || isLoading) return;

  // Vide l'input
  inputField.value = "";
  inputField.style.height = "auto";

  // Cache le welcome si présent
  const welcome = document.querySelector(".welcome");
  if (welcome) welcome.remove();

  // Ajoute le message utilisateur
  appendMessage("user", text);

  // Affiche le typing indicator
  const typingEl = appendTyping();

  isLoading = true;
  sendBtn.disabled = true;

  try {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `Erreur ${res.status}`);
    }

    const data = await res.json();
    typingEl.remove();
    appendMessage("agent", data.response);

  } catch (err) {
    typingEl.remove();
    appendMessage("agent", `❌ Erreur : ${err.message}`);
  } finally {
    isLoading = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
}

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "T" : "⬡";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  // Render markdown
  bubble.innerHTML = marked.parse(text);

  // Highlight code blocks
  bubble.querySelectorAll("pre code").forEach((block) => {
    hljs.highlightElement(block);
  });

  div.appendChild(avatar);
  div.appendChild(bubble);
  messages.appendChild(div);

  // Scroll vers le bas
  messages.scrollTop = messages.scrollHeight;

  return div;
}

function appendTyping() {
  const div = document.createElement("div");
  div.className = "message agent";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "⬡";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = `
    <div class="typing-indicator">
      <span></span><span></span><span></span>
    </div>`;

  div.appendChild(avatar);
  div.appendChild(bubble);
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;

  return div;
}

async function resetSession() {
  try {
    await fetch(`${BACKEND_URL}/reset?session_id=${sessionId}`, { method: "POST" });
  } catch (_) {}

  messages.innerHTML = `
    <div class="welcome">
      <h1>Prêt.</h1>
      <p>Pose ta question, colle du code, demande une commande Linux —<br/>je m'occupe du reste.</p>
    </div>`;
}

async function checkBackend() {
  try {
    const res = await fetch(`${BACKEND_URL}/`);
    if (res.ok) {
      statusDot.className = "status-dot online";
      statusText.textContent = "En ligne";
    } else {
      throw new Error();
    }
  } catch {
    statusDot.className = "status-dot offline";
    statusText.textContent = "Hors ligne";
  }
}
