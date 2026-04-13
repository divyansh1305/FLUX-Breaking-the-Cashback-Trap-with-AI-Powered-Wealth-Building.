// frontend/app.js
/* ASYNC STATE MANAGEMENT AND AUTH LOGIC */

let appState = {
  user: null,
};

// Initialize app from backend session
async function initApp() {
  try {
    const res = await fetch('/api/user');
    if (res.ok) {
      appState.user = await res.json();
    } else {
      appState.user = null;
    }
  } catch (e) {
    appState.user = null;
  }
}

async function logoutUser() {
  await fetch('/logout');
  window.location.href = 'login.html';
}

function isLoggedIn() {
  return appState.user && appState.user.email;
}

// To be safe against race conditions on page load, 
// we will export an initialization promise that other scripts can optionally await
let initAppPromise = initApp();

async function requireAuth(event, url) {
  if (!isLoggedIn()) {
    if (event) event.preventDefault();
    alert("Login to unlock exclusive features.");
    window.location.href = 'login.html';
    return false;
  }
  if (url && event && event.type === 'click') {
    window.location.href = url;
  }
  return true;
}

// Transactions
async function addExpense(category, amount) {
  try {
    await fetch('/add-expense', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, amount })
    });
  } catch(e) {
    console.error("Error adding expense", e);
  }
}

async function addIncome(category, amount) {
  try {
    await fetch('/add-income', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, amount })
    });
  } catch(e) {
    console.error("Error adding income", e);
  }
}

async function smartSaveSuggestion() {
  try {
    const res = await fetch('/invest');
    if(res.ok) return await res.json();
  } catch(e) {}
  return { suggestion: "Build your balance to unlock smart saves.", amount: 0 };
}

async function smartSave(amount) {
  try {
    const res = await fetch('/invest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount })
    });
    return await res.json();
  } catch(e) {
    console.error("Error doing smart save", e);
  }
}

async function getTransactions() {
  try {
    const res = await fetch('/api/transactions');
    if(res.ok) return await res.json();
  } catch(e) {}
  return [];
}

// Goals
async function addGoal(title, targetAmount, currentAmount = 0, icon = '🎯') {
  try {
    await fetch('/create-goal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, target_amount: targetAmount })
    });
  } catch(e) {
    console.error("Error adding goal", e);
  }
}

async function updateGoal(goal_id, added_amount) {
  try {
    const res = await fetch('/update-goal', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal_id, added_amount })
    });
    return await res.json();
  } catch(e) {
    console.error("Error updating goal", e);
    return {error: "Network error"};
  }
}

async function getGoals() {
  try {
    const res = await fetch('/goal-progress');
    if(res.ok) return await res.json();
  } catch(e) {}
  return [];
}

// Stats & Phase APIs
async function getDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    if(res.ok) return await res.json();
  } catch(e) {}
  return {
    income: 0, expenses: 0, investments: 0, savings: 0, balance: 0,
    totalSaved: 0, totalWealth: 0, wealthVelocity: '0%', score: 0, insights: []
  };
}

async function getGamification() {
  try {
    const res = await fetch('/api/gamification');
    if(res.ok) return await res.json();
  } catch(e) {}
  return { streak_days: 0, points: 0, level: 1 };
}

async function getInsights() {
  try {
    const res = await fetch('/api/insights');
    if(res.ok) return await res.json();
  } catch(e) {}
  return { insight: "" };
}

// Update Nav User UI globally
function updateNavUI() {
  const navUser = document.querySelector('.nav-user');
  const navRight = document.querySelector('.nav-right');
  
  if (!navRight) return;

  if (isLoggedIn()) {
    if(navUser) {
      navUser.style.display = 'flex';
      const nameStr = appState.user?.name || "User";
      const initials = nameStr.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase();
      const shortName = nameStr.split(' ')[0];
      navUser.innerHTML = `<a href="profile.html" style="text-decoration:none; display:flex; align-items:center; gap:10px; color:white;"><div class="avatar" style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,var(--purple),var(--blue)); display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:600;">${initials}</div><span>${shortName}</span></a>`;
    }
    
    let logoutBtn = document.querySelector('.btn-logout');
    if (!logoutBtn) {
      logoutBtn = document.createElement('a');
      logoutBtn.href = "#";
      logoutBtn.className = "btn-logout";
      navRight.appendChild(logoutBtn);
    }
    logoutBtn.innerText = "Log out";
    logoutBtn.onclick = (e) => { 
        e.preventDefault(); 
        logoutUser(); 
    };
  } else {
    // Not logged in
    if(navUser) {
      navUser.style.display = 'none';
    }
    
    let btn = document.querySelector('.btn-logout');
    if(!btn) {
      btn = document.createElement('a');
      btn.className = "btn-logout";
      navRight.appendChild(btn);
    }
    btn.href = "login.html";
    btn.innerText = "Log in";
    btn.style.borderColor = "var(--orange)";
    btn.style.color = "var(--orange)";
    btn.onclick = null;
  }
}

// Formatting helpers
function formatCur(val) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${d.getDate()} ${months[d.getMonth()]}`;
}

async function getSpendingBreakdown() {
  try {
    const res = await fetch('/api/spending-breakdown');
    if (res.ok) return await res.json();
  } catch(e) { console.error(e); }
  return [];
}

async function getBadges() {
  try {
    const res = await fetch('/api/badges');
    if (res.ok) return await res.json();
  } catch(e) { console.error(e); }
  return [];
}

// Run init UI updates
document.addEventListener('DOMContentLoaded', async () => {
  await initAppPromise;
  updateNavUI();
  if (isLoggedIn()) injectChatWidget();
});

// ─── CHATBOT WIDGET ─────────────────────────────────────
function injectChatWidget() {
  // Don't add on login page
  if (window.location.pathname.includes('login')) return;

  const style = document.createElement('style');
  style.textContent = `
    #flux-chat-btn {
      position: fixed; bottom: 28px; right: 28px; z-index: 9999;
      width: 60px; height: 60px; border-radius: 50%;
      background: linear-gradient(135deg, #e8491d, #ff8c42);
      border: none; cursor: pointer; display: flex; align-items: center; justify-content: center;
      box-shadow: 0 6px 24px rgba(232,73,29,0.4);
      transition: transform 0.2s, box-shadow 0.2s;
      font-size: 26px; color: white;
    }
    #flux-chat-btn:hover { transform: scale(1.1); box-shadow: 0 10px 32px rgba(232,73,29,0.5); }
    #flux-chat-btn.open { border-radius: 16px; width: 48px; height: 48px; font-size: 20px; }

    #flux-chat-panel {
      position: fixed; bottom: 100px; right: 28px; z-index: 9998;
      width: 380px; max-height: 520px;
      background: rgba(14,14,26,0.95); backdrop-filter: blur(24px);
      border: 1px solid rgba(255,255,255,0.1); border-radius: 24px;
      display: none; flex-direction: column; overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.6);
      animation: chatSlideUp 0.3s ease;
    }
    #flux-chat-panel.visible { display: flex; }
    @keyframes chatSlideUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }

    .chat-header {
      padding: 18px 20px; display: flex; align-items: center; gap: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      background: rgba(24,24,40,0.8);
    }
    .chat-header-icon {
      width: 36px; height: 36px; border-radius: 12px;
      background: linear-gradient(135deg, #e8491d, #ff8c42);
      display: flex; align-items: center; justify-content: center; font-size: 18px;
    }
    .chat-header-text { font-weight: 700; font-size: 15px; color: #fff; }
    .chat-header-sub { font-size: 11px; color: #8888aa; }

    .chat-messages {
      flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px;
      max-height: 340px; min-height: 200px;
    }
    .chat-messages::-webkit-scrollbar { width: 4px; }
    .chat-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

    .chat-msg {
      max-width: 85%; padding: 12px 16px; border-radius: 18px; font-size: 13px;
      line-height: 1.6; white-space: pre-wrap; word-wrap: break-word;
    }
    .chat-msg.user {
      align-self: flex-end; background: linear-gradient(135deg, #e8491d, #c73a12);
      color: white; border-bottom-right-radius: 6px;
    }
    .chat-msg.bot {
      align-self: flex-start; background: rgba(255,255,255,0.07);
      color: #e0e0e0; border-bottom-left-radius: 6px; border: 1px solid rgba(255,255,255,0.05);
    }
    .chat-msg.bot.typing { color: #8888aa; font-style: italic; }

    .chat-input-area {
      padding: 12px 16px; border-top: 1px solid rgba(255,255,255,0.07);
      display: flex; gap: 10px; background: rgba(18,18,30,0.9);
    }
    .chat-input-area input {
      flex: 1; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1);
      color: white; padding: 12px 16px; border-radius: 40px; font-size: 13px;
      outline: none; transition: 0.2s; font-family: 'Inter', sans-serif;
    }
    .chat-input-area input:focus { border-color: #e8491d; box-shadow: 0 0 0 3px rgba(232,73,29,0.15); }
    .chat-input-area input::placeholder { color: #5a5a78; }
    .chat-input-area button {
      background: #e8491d; border: none; color: white; width: 42px; height: 42px;
      border-radius: 50%; cursor: pointer; font-size: 18px; transition: 0.2s;
      display: flex; align-items: center; justify-content: center;
    }
    .chat-input-area button:hover { background: #ff5722; transform: scale(1.05); }
    .chat-input-area button.mic-btn {
      background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #8888aa; width: 42px; font-size: 16px;
    }
    .chat-input-area button.mic-btn:hover { background: rgba(255,255,255,0.1); }
    .chat-input-area button.mic-btn.recording {
      background: rgba(239, 68, 68, 0.2); border-color: #ef4444; color: #ef4444; animation: pulseMic 1.5s infinite;
    }
    @keyframes pulseMic { 0% {box-shadow: 0 0 0 0 rgba(239,68,68,0.4);} 70% {box-shadow: 0 0 0 10px rgba(239,68,68,0);} 100% {box-shadow: 0 0 0 0 rgba(239,68,68,0);} }

    @media(max-width: 480px) {
      #flux-chat-panel { width: calc(100% - 32px); right: 16px; bottom: 90px; }
    }
  `;
  document.head.appendChild(style);

  // Chat button
  const btn = document.createElement('button');
  btn.id = 'flux-chat-btn';
  btn.innerHTML = '💬';
  btn.title = 'Chat with Flux AI';
  document.body.appendChild(btn);

  // Chat panel
  const panel = document.createElement('div');
  panel.id = 'flux-chat-panel';
  panel.innerHTML = `
    <div class="chat-header">
      <div class="chat-header-icon">⚡</div>
      <div>
        <div class="chat-header-text">Flux AI</div>
        <div class="chat-header-sub">Your financial assistant</div>
      </div>
    </div>
    <div class="chat-messages" id="chat-messages">
      <div class="chat-msg bot">Hey! 👋 I'm your Flux AI assistant.\n\nAsk me about your balance, spending, investments, goals, or score!</div>
    </div>
    <div class="chat-input-area">
      <input type="text" id="chat-input" placeholder="Ask about finances or speak..." autocomplete="off">
      <button id="chat-mic-btn" class="mic-btn" title="Speak in English/Hindi">🎙️</button>
      <button id="chat-send">➤</button>
    </div>
  `;
  document.body.appendChild(panel);

  // Toggle
  btn.addEventListener('click', () => {
    panel.classList.toggle('visible');
    btn.innerHTML = panel.classList.contains('visible') ? '✕' : '💬';
    btn.classList.toggle('open', panel.classList.contains('visible'));
    if (panel.classList.contains('visible')) {
      document.getElementById('chat-input').focus();
    }
  });

  // Send message
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');
  const messages = document.getElementById('chat-messages');

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-msg user';
    userMsg.textContent = text;
    messages.appendChild(userMsg);
    input.value = '';
    messages.scrollTop = messages.scrollHeight;

    // Show typing
    const typing = document.createElement('div');
    typing.className = 'chat-msg bot typing';
    typing.textContent = 'Thinking...';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      typing.remove();

      const botMsg = document.createElement('div');
      botMsg.className = 'chat-msg bot';
      botMsg.textContent = data.reply || "I couldn't process that. Try again!";
      messages.appendChild(botMsg);
    } catch(e) {
      typing.remove();
      const errMsg = document.createElement('div');
      errMsg.className = 'chat-msg bot';
      errMsg.textContent = "⚠️ Connection error. Make sure the backend is running.";
      messages.appendChild(errMsg);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

  // Web Speech API for voice typing
  const micBtn = document.getElementById('chat-mic-btn');
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechR();
    recognition.lang = 'en-IN'; // Supports Indian English and often picks up Hindi transliteration
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      input.value = transcript;
      micBtn.classList.remove('recording');
      
      // Do not auto-send! Let the user review and edit their voice input (English/Hindi) before clicking send.
      input.focus();
    };
    recognition.onerror = (e) => {
      console.error("Speech recognition error", e);
      micBtn.classList.remove('recording');
      input.placeholder = "Mic not supported/denied. Type here...";
    };
    recognition.onend = () => {
      micBtn.classList.remove('recording');
    };

    micBtn.addEventListener('click', () => {
      if (micBtn.classList.contains('recording')) {
        recognition.stop();
        micBtn.classList.remove('recording');
      } else {
        recognition.start();
        micBtn.classList.add('recording');
      }
    });
  } else {
    micBtn.style.display = 'none'; // Hide if browser doesn't support
  }
}
