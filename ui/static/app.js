const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("prompt");
const ingestBtn = document.getElementById("ingest-btn");
const ingestStatus = document.getElementById("ingest-status");

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMessage(text) {
  addMessage("user", text);
  addMessage("assistant", "Thinking...");
  const pending = chat.querySelector(".message.assistant:last-child .bubble");

  try {
    const res = await fetch("/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "nim",
        messages: [{ role: "user", content: text }],
        stream: false,
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || "Request failed");
    }

    const data = await res.json();
    const content = data.choices?.[0]?.message?.content || "No response";
    pending.textContent = content;
  } catch (err) {
    pending.textContent = `Error: ${err.message}`;
  }
}

async function ingestDocs() {
  ingestBtn.disabled = true;
  ingestStatus.textContent = "Ingesting...";

  try {
    const res = await fetch("/ingest", { method: "POST" });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || "Ingest failed");
    }
    const data = await res.json();
    ingestStatus.textContent = `Ingested ${data.files} files / ${data.chunks} chunks`;
  } catch (err) {
    ingestStatus.textContent = `Error: ${err.message}`;
  } finally {
    ingestBtn.disabled = false;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendMessage(text);
});

ingestBtn.addEventListener("click", ingestDocs);
