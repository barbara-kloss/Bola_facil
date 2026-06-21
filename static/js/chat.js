const messagesEl = document.querySelector("#chatMessages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#chatInput");

function appendMessage(message) {
  const item = document.createElement("div");
  item.className = "chat-message";
  item.innerHTML = `<strong>${message.name}</strong><p>${message.text}</p>`;
  messagesEl.appendChild(item);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function loadMessages() {
  const response = await fetch("/chat/messages");
  const messages = await response.json();
  messagesEl.innerHTML = "";
  messages.forEach(appendMessage);
}

if (formEl) {
  loadMessages();
  formEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = inputEl.value.trim();
    if (!text) return;
    const response = await fetch("/chat/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    appendMessage(await response.json());
    inputEl.value = "";
  });
}
