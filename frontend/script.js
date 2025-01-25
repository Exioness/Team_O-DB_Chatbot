// ---------------------------------------------------------------------------
// 1. Configure your backend URL here
// ---------------------------------------------------------------------------
const API_BASE_URL = "http://194.182.77.175:8000"; // example backend URL

// ---------------------------------------------------------------------------
// 2. Authentication Management (LocalStorage token handling)
// ---------------------------------------------------------------------------
function setAuthToken(token) {
  localStorage.setItem("authToken", token);
}
function getAuthToken() {
  return localStorage.getItem("authToken");
}
function removeAuthToken() {
  localStorage.removeItem("authToken");
}

// ---------------------------------------------------------------------------
// 3. State Management
// ---------------------------------------------------------------------------
let activeChatId = null;
let messages = new Map();  // chatId -> array of messages
let isBotResponding = false;

// The AbortController reference will be set whenever we start a streaming fetch.
let abortController = null;

// ---------------------------------------------------------------------------
// 4. DOMContentLoaded: Set up all event listeners
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const elements = {
    goRegister: document.getElementById("goRegister"),
    goLogin: document.getElementById("goLogin"),
    toggleThemeBtn: document.getElementById("toggleThemeBtn"),
    btnNewChat: document.getElementById("btnNewChat"),
    btnShowChats: document.getElementById("btnShowChats"),
    btnLogout: document.getElementById("btnLogout"),
    btnShowSchema: document.getElementById("btnShowSchema"),
    btnProcessQuery: document.getElementById("btnProcessQuery"),
    btnClearChats: document.getElementById("btnClearChats"),
    chatInput: document.getElementById("chatInput"),
    registerForm: document.getElementById("registerForm"),
    loginForm: document.getElementById("loginForm"),
    authError: document.getElementById("authError"),
    mainUI: document.getElementById("mainUI"),
    authSection: document.getElementById("authSection"),
    welcomeSection: document.getElementById("welcomeSection"),
    chatWindow: document.getElementById("chatWindow")
  };

  // Switch to Registration form
  if (elements.goRegister) {
    elements.goRegister.addEventListener("click", () => {
      showRegistrationForm();
    });
  }
  // Switch to Login form
  if (elements.goLogin) {
    elements.goLogin.addEventListener("click", () => {
      showLoginForm();
    });
  }
  // Toggle Theme
  if (elements.toggleThemeBtn) {
    elements.toggleThemeBtn.addEventListener("click", toggleTheme);
  }
  // New Chat
  if (elements.btnNewChat) {
    elements.btnNewChat.addEventListener("click", createNewChat);
  }
  // Show Chats
  if (elements.btnShowChats) {
    elements.btnShowChats.addEventListener("click", loadChats);
  }
  // Logout
  if (elements.btnLogout) {
    elements.btnLogout.addEventListener("click", logout);
  }
  // Show Schema
  if (elements.btnShowSchema) {
    elements.btnShowSchema.addEventListener("click", fetchSchema);
  }
  // Process Query (on the landing page)
  if (elements.btnProcessQuery) {
    elements.btnProcessQuery.addEventListener("click", () => {
      processQuery("Sample question, or use the chat input!");
    });
  }
  // Clear Chats
  if (elements.btnClearChats) {
    elements.btnClearChats.addEventListener("click", deleteAllChats);
  }
  // Send message on Enter
  if (elements.chatInput) {
    elements.chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        sendMessage();
      }
    });
  }
  // Register Form Submit
  if (elements.registerForm) {
    elements.registerForm.addEventListener("submit", handleRegistration);
  }
  // Login Form Submit
  if (elements.loginForm) {
    elements.loginForm.addEventListener("submit", handleLogin);
  }
  // Set up chat interactions
  setupChatInteraction();

  // If there is an auth token, go directly to main UI
  if (getAuthToken()) {
    showMainUI();
  } else {
    showWelcome(); 
  }
});

// ---------------------------------------------------------------------------
// 5. Show/Hide different sections
// ---------------------------------------------------------------------------
function showWelcome() {
  document.getElementById("welcomeSection").classList.remove("hidden");
  document.getElementById("authSection").classList.add("hidden");
  document.getElementById("mainUI").classList.add("hidden");
}

function navigateTo(sectionId) {
  // For a super-simple approach: hide welcome & show auth
  document.getElementById("welcomeSection").classList.add("hidden");
  document.getElementById("authSection").classList.remove("hidden");
}

function showAuthSection() {
  document.getElementById("authSection").classList.remove("hidden");
  document.getElementById("mainUI").classList.add("hidden");
}

function showMainUI() {
  document.getElementById("welcomeSection").classList.add("hidden");
  document.getElementById("authSection").classList.add("hidden");
  document.getElementById("mainUI").classList.remove("hidden");
}

function showLoginForm() {
  document.getElementById("registerForm").classList.add("hidden");
  document.getElementById("loginForm").classList.remove("hidden");
  document.getElementById("authError").classList.add("hidden");
}

function showRegistrationForm() {
  document.getElementById("loginForm").classList.add("hidden");
  document.getElementById("registerForm").classList.remove("hidden");
  document.getElementById("authError").classList.add("hidden");
}

function showChatView() {
  document.getElementById("landingView").classList.add("hidden");
  document.getElementById("chatView").classList.remove("hidden");
  // Focus input
  document.getElementById("chatInput").focus();
}

// ---------------------------------------------------------------------------
// 6. Authentication: Login / Registration
// ---------------------------------------------------------------------------
async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value.trim();

  if (!username || !password) {
    showError("Both username and password are required.");
    return;
  }

  const payload = new URLSearchParams();
  payload.append("grant_type", "password");
  payload.append("username", username);
  payload.append("password", password);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload.toString(),
    });

    const data = await response.json();
    if (response.ok) {
      setAuthToken(data.access_token);
      showMainUI();
    } else {
      throw new Error(data.detail || "Login failed.");
    }
  } catch (error) {
    showError(`Error: ${error.message}`);
  }
}

async function handleRegistration(e) {
  e.preventDefault();
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value.trim();

  if (!email || !password) {
    showError("Please enter email and password to register.");
    return;
  }

  const payload = {
    username: email,
    email: email,
    password: password,
  };
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (response.ok) {
      alert("Registration successful! Please log in.");
      e.target.reset(); // Clear the form
      showLoginForm();
    } else {
      throw new Error(data.detail || "Registration failed.");
    }
  } catch (error) {
    showError(`Error: ${error.message}`);
  }
}

function logout() {
  removeAuthToken();
  window.location.reload();
}

// ---------------------------------------------------------------------------
// 7. Chat Management
// ---------------------------------------------------------------------------
async function loadChats() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chats`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    });
    if (response.ok) {
      const chats = await response.json();
      renderChatList(chats);
      // Auto-select first chat if none is selected
      if (!activeChatId && chats.length > 0) {
        activeChatId = chats[0].id;
        showChatView();
        loadChatMessages(activeChatId);
      }
    } else {
      throw new Error("Unable to load chats.");
    }
  } catch (error) {
    showError(`Error loading chats: ${error.message}`);
  }
}

function renderChatList(chatsData) {
  const chatList = document.getElementById("chatList");
  if (!chatList) return;

  chatList.innerHTML = chatsData.map(chat => `
    <div class="chat-item ${chat.id == activeChatId ? 'active' : ''}" data-id="${chat.id}">
      <span class="chat-name">${chat.title}</span>
      <button class="delete-btn" onclick="event.stopPropagation(); deleteChat(${chat.id})">×</button>
    </div>
  `).join("");

  document.querySelectorAll(".chat-item").forEach(item => {
    item.addEventListener("click", async () => {
      const newChatId = parseInt(item.dataset.id);
      if (newChatId !== activeChatId) {
        activeChatId = newChatId;
        showChatView();
        await loadChatMessages(activeChatId);
      }
    });
  });
}

async function loadChatMessages(chatId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chats/${chatId}/messages`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    });
    if (!response.ok) {
      throw new Error("Failed to load messages.");
    }
    const chatData = await response.json();
    console.log("Received chat data:", chatData);
    
    // Clear existing messages first
    const chatWindow = document.getElementById("chatWindow");
    if (chatWindow) {
      chatWindow.innerHTML = "";
    }
    
    // Ensure chatData is an array
    const messagesArray = Array.isArray(chatData) ? chatData : chatData.messages || [];
    
    const mapped = messagesArray.map(msg => {
      // More explicit role handling
      let sender;
      if (msg.role === 'assistant' || msg.role === 'bot') {
        sender = 'bot';
      } else if (msg.role === 'user') {
        sender = 'user';
      } else {
        // Default to user if role is undefined or unknown
        sender = 'user';
      }

      return {
        sender: sender,
        text: msg.content || msg.message || '',
        timestamp: msg.created_at || new Date().toISOString()
      };
    });

    console.log("Mapped messages:", mapped);
    
    messages.set(chatId, mapped);
    renderMessages(mapped);

    // Ensure chat view is visible and scroll to bottom
    document.getElementById("landingView")?.classList.add("hidden");
    document.getElementById("chatView")?.classList.remove("hidden");
    
    if (chatWindow) {
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  } catch (error) {
    console.error("Load messages error:", error);
    showError(`Could not load messages: ${error.message}`);
  }
}

function formatMessageText(text) {
  // Convert markdown bold (**text**) to HTML
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Convert markdown italic (*text*) to HTML
  text = text.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
  
  // If it's a numbered list, add line breaks
  if (text.match(/^\d+\./m)) {
    // Split into lines and join with HTML line breaks
    return text.split('\n').join('<br>');
  }
  
  return text;
}

function renderMessages(messageList) {
  const chatWindow = document.getElementById("chatWindow");
  if (!chatWindow) return;

  chatWindow.innerHTML = "";
  if (!messageList || !messageList.length) {
    console.log("No messages to render"); // Debug log
    return;
  }

  console.log("Rendering messages:", messageList); // Debug log

  messageList.forEach(msg => {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${msg.sender}`;
    messageDiv.innerHTML = `
      <p>${formatMessageText(msg.text || '')}</p>
      <small>${new Date(msg.timestamp).toLocaleTimeString()}</small>
    `;
    chatWindow.appendChild(messageDiv);
  });

  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function createNewChat() {
  const chatName = prompt("Enter the chat name:") || "New Chat";
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chats`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify({ title: chatName }),
    });
    if (!response.ok) {
      throw new Error("Failed to create chat.");
    }
    const newChat = await response.json();
    activeChatId = newChat.id;
    messages.set(activeChatId, []);
    showChatView();
    renderMessages(messages.get(activeChatId));
    loadChats();
  } catch (error) {
    showError(`Chat creation failed: ${error.message}`);
  }
}

async function deleteChat(chatId) {
  if (!confirm(`Are you sure you want to delete chat ${chatId}?`)) return;
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chats/${chatId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    });
    if (!response.ok) {
      throw new Error("Failed to delete chat.");
    }
    alert("Chat deleted successfully!");
    if (activeChatId == chatId) {
      activeChatId = null;
      document.getElementById("chatWindow").innerHTML = "";
    }
    loadChats();
  } catch (error) {
    showError(`Error: ${error.message}`);
  }
}

async function deleteAllChats() {
  if (!confirm("Are you sure you want to delete all chats?")) return;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chats`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    });
    if (response.ok) {
      alert("All chats deleted successfully!");
      activeChatId = null;
      document.getElementById("chatWindow").innerHTML = "";
      loadChats();
    } else {
      throw new Error("Failed to delete all chats.");
    }
  } catch (error) {
    showError(`Error: ${error.message}`);
  }
}

// ---------------------------------------------------------------------------
// 8. Sending a Message & SSE streaming with STOP / ABORT logic
// ---------------------------------------------------------------------------
async function sendMessage() {
  const userInput = document.getElementById("chatInput").value.trim();
  if (!userInput) return;

  document.getElementById("chatInput").value = "";
  addMessage("user", userInput);

  // Create a new AbortController for this request
  abortController = new AbortController();

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        Authorization: `Bearer ${getAuthToken()}`,
      },
      // Pass the signal so we can cancel
      signal: abortController.signal,
      body: JSON.stringify({ question: userInput, chat_id: activeChatId }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let botResponse = "";
    let partialLine = "";

    const botDiv = addMessage("bot", "");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      partialLine += decoder.decode(value, { stream: true });
      const lines = partialLine.split("\n");
      partialLine = lines.pop(); // keep incomplete chunk

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const { type, content } = JSON.parse(line.slice(6));
          if (type === "token") {
            botResponse += content;
            botDiv.querySelector("p").textContent = botResponse;
          } else if (type === "end") {
            saveToHistory(userInput, botResponse);
          }
        } catch (e) {
          console.error("Error parsing SSE line:", e);
          botDiv.querySelector("p").textContent = "Error processing response.";
        }
      }
      // Scroll to bottom
      document.getElementById("chatWindow").scrollTop =
        document.getElementById("chatWindow").scrollHeight;
    }
  } catch (error) {
    if (error.name === "AbortError") {
      // Request was aborted
      addMessage("error", "Generation was stopped.");
    } else {
      addMessage("error", `Failed to get response: ${error.message}`);
    }
  } finally {
    // Reset the controller for the next request
    abortController = null;
  }
}

function addMessage(sender, text) {
  const chatWindow = document.getElementById("chatWindow");
  if (!chatWindow) return null;

  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.innerHTML = `<p>${formatMessageText(text)}</p>`;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function saveToHistory(userMsg, botMsg) {
  if (!activeChatId) return;
  if (!messages.has(activeChatId)) {
    messages.set(activeChatId, []);
  }
  messages.get(activeChatId).push({
    sender: "user",
    text: userMsg,
    timestamp: new Date().toISOString()
  });
  messages.get(activeChatId).push({
    sender: "bot",
    text: botMsg,
    timestamp: new Date().toISOString()
  });
  renderMessages(messages.get(activeChatId));
}

// ---------------------------------------------------------------------------
// 9. processQuery / fetchSchema
// ---------------------------------------------------------------------------
async function processQuery(question, chatId = activeChatId) {
  if (!question) {
    showError("No query provided.");
    return;
  }
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify({ question, chat_id: chatId }),
    });
    if (response.ok) {
      const result = await response.json();
      addMessage("bot", result.result || JSON.stringify(result));
    } else {
      throw new Error("Query failed.");
    }
  } catch (error) {
    showError(`Query failed: ${error.message}`);
  }
}

async function fetchSchema() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/schema`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    });
    if (response.ok) {
      const schema = await response.json();
      console.log("Database Schema:", schema);
      alert("Schema fetched successfully. Check the console.");
    } else {
      throw new Error("Failed to fetch schema.");
    }
  } catch (error) {
    showError(`Error: ${error.message}`);
  }
}

// ---------------------------------------------------------------------------
// 10. Toggle Theme
// ---------------------------------------------------------------------------
function toggleTheme() {
  document.body.classList.toggle("dark-mode");
  const themeBtn = document.getElementById("toggleThemeBtn");
  themeBtn.textContent = document.body.classList.contains("dark-mode")
    ? "Light Mode"
    : "Dark Mode";
}

// ---------------------------------------------------------------------------
// 11. Error Helper
// ---------------------------------------------------------------------------
function showError(message) {
  const authError = document.getElementById("authError");
  if (authError) {
    authError.textContent = message;
    authError.classList.remove("hidden");
    // Hide after 5 seconds
    setTimeout(() => authError.classList.add("hidden"), 5000);
  }
}

// ---------------------------------------------------------------------------
// 12. Chat Interaction Setup
// ---------------------------------------------------------------------------
function setupChatInteraction() {
  const sendBtn = document.getElementById("sendBtn");
  if (sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
  }

  const stopBtn = document.getElementById("stopBtn");
  if (stopBtn) {
    // Call a separate function or inline logic
    stopBtn.addEventListener("click", () => {
      if (abortController) {
        abortController.abort();
      }
    });
  }
}
