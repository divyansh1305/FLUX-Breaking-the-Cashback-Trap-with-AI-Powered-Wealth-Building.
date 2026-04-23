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
      
      // Global Activity Monitoring: Log page transitions in SQLite
      const path = window.location.pathname.split('/').pop() || 'index.html';
      if (!path.includes('login') && !path.includes('logout') && !path.includes('onboarding')) {
          fetch('/api/log-action', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  action: "NAVIGATED",
                  description: `Viewed ${path}`
              })
          }).catch(() => {});
      }
    } else {
      appState.user = null;
    }
  } catch (e) {
    appState.user = null;
  }

  // GLOBAL PRO ROUTE GUARD
  const lockedPages = ['markets.html', 'insurance.html', 'payments.html', 'tax.html', 'simulator.html', 'will.html'];
  const curPage = window.location.pathname.split('/').pop();
  
  if (lockedPages.includes(curPage)) {
      if (!appState.user || !appState.user.is_pro) {
          const overlay = document.createElement('div');
          overlay.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(8,8,15,0.85);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);z-index:999999;display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity 0.4s ease;";
          
          const modal = document.createElement('div');
          modal.style.cssText = "background:linear-gradient(145deg, rgba(24,24,40,0.95), rgba(18,18,30,0.95));border:1px solid rgba(255,255,255,0.1);border-radius:24px;padding:40px;max-width:420px;width:90%;text-align:center;box-shadow:0 30px 60px rgba(0,0,0,0.7);transform:translateY(30px) scale(0.95);transition:all 0.4s cubic-bezier(0.16, 1, 0.3, 1);";
          
          modal.innerHTML = `
            <div style="background:linear-gradient(135deg, #fbbf24, #f59e0b);width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;box-shadow:0 0 30px rgba(251,191,36,0.4);">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
            </div>
            <h2 style="color:white;font-size:28px;font-weight:800;margin:0 0 12px;font-family:'Inter',sans-serif;">Unlock Flux PRO</h2>
            <p style="color:#8888aa;font-size:15px;line-height:1.6;margin:0 0 32px;font-family:'Inter',sans-serif;">This feature is locked. To enable this feature, unlock Flux PRO and get full access.</p>
            <div style="display:flex;flex-direction:column;gap:12px;">
              <button id="btn-unlock-pro" style="background:#e8491d;border:none;color:white;padding:16px 24px;border-radius:16px;font-size:16px;font-weight:700;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif;box-shadow:0 4px 15px rgba(232,73,29,0.3);">Buy Flux PRO</button>
              <button id="btn-cancel-pro-lock" style="background:transparent;border:1px solid rgba(255,255,255,0.1);color:#8888aa;padding:16px 24px;border-radius:16px;font-size:16px;font-weight:600;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif;">No, Thanks</button>
            </div>
          `;
          
          overlay.appendChild(modal);
          document.body.appendChild(overlay);
          
          // Animate in
          requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            modal.style.transform = 'translateY(0) scale(1)';
          });
          
          // Hover effects
          const btnUnlock = modal.querySelector('#btn-unlock-pro');
          const btnMaybe = modal.querySelector('#btn-cancel-pro-lock');
          
          btnUnlock.onmouseover = () => btnUnlock.style.background = '#ff5722';
          btnUnlock.onmouseout = () => btnUnlock.style.background = '#e8491d';
          btnMaybe.onmouseover = () => { btnMaybe.style.background = 'rgba(255,255,255,0.05)'; btnMaybe.style.color = '#fff'; };
          btnMaybe.onmouseout = () => { btnMaybe.style.background = 'transparent'; btnMaybe.style.color = '#8888aa'; };
          
          // Actions
          btnUnlock.onclick = () => window.location.href = 'flux-pro.html';
          btnMaybe.onclick = () => window.location.href = 'index.html';
      }
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
    const res = await fetch('/add-expense', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, amount })
    });
    return await res.json();
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

// Global Cancel PRO method so it works on all pages
window.cancelProSubscription = async function() {
    try {
        const overlay = document.createElement('div');
        overlay.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(8,8,15,0.85);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);z-index:999999;display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity 0.4s ease;";
        
        const modal = document.createElement('div');
        modal.style.cssText = "background:linear-gradient(145deg, rgba(24,24,40,0.95), rgba(18,18,30,0.95));border:1px solid rgba(255,255,255,0.1);border-radius:24px;padding:40px;max-width:420px;width:90%;text-align:center;box-shadow:0 30px 60px rgba(0,0,0,0.7);transform:translateY(30px) scale(0.95);transition:all 0.4s cubic-bezier(0.16, 1, 0.3, 1);";
        
        modal.innerHTML = `
          <div style="background:rgba(239,68,68,0.1);color:#ef4444;width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;font-size:32px;border:2px solid #ef4444;">
            !
          </div>
          <h2 style="color:white;font-size:28px;font-weight:800;margin:0 0 12px;font-family:'Inter',sans-serif;">Cancel Pro?</h2>
          <p id="cancel-status-text" style="color:#8888aa;font-size:15px;line-height:1.6;margin:0 0 24px;font-family:'Inter',sans-serif;">Sending a secure 6-digit verification code to your email...</p>
          <div id="otp-container" style="display:none;flex-direction:column;gap:16px;">
            <input type="text" id="cancelOtpInput" placeholder="●●●●●●" maxlength="6" style="
              width: 100%; max-width: 240px; margin: 0 auto; display: block;
              background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.12);
              color: white; padding: 18px; border-radius: 16px; 
              font-size: 32px; font-weight: 700; letter-spacing: 12px; 
              text-align: center; outline: none; transition: 0.2s;
              box-sizing: border-box; font-family:'Inter', sans-serif;
            " onfocus="this.style.borderColor='#e8491d'; this.style.boxShadow='0 0 0 4px rgba(232,73,29,0.15)'" onblur="this.style.borderColor='rgba(255,255,255,0.12)'; this.style.boxShadow='none'">
            <button id="btn-verify-cancel" style="background:#e8491d;border:none;color:white;padding:16px 24px;border-radius:16px;font-size:16px;font-weight:700;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif;box-shadow:0 4px 15px rgba(232,73,29,0.3);">Verify & Revoke</button>
          </div>
          <button id="btn-keep-pro" style="background:transparent;border:none;color:#8888aa;text-decoration:underline;padding:12px;font-size:14px;cursor:pointer;font-family:'Inter',sans-serif;margin-top:12px;">Keep Pro Account</button>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        requestAnimationFrame(() => {
          overlay.style.opacity = '1';
          modal.style.transform = 'translateY(0) scale(1)';
        });
        
        const btnKeep = modal.querySelector('#btn-keep-pro');
        const btnVerify = modal.querySelector('#btn-verify-cancel');
        const otpContainer = modal.querySelector('#otp-container');
        const statusText = modal.querySelector('#cancel-status-text');
        const otpInput = modal.querySelector('#cancelOtpInput');
        
        btnKeep.onclick = () => {
          overlay.style.opacity = '0';
          setTimeout(() => overlay.remove(), 400);
        };

        const req = await fetch('/api/send-cancel-otp', { method: 'POST' });
        if (!req.ok) {
            statusText.innerText = "Error requesting OTP. Please try again later.";
            statusText.style.color = "#ef4444";
            return;
        }

        const reqData = await req.json();

        statusText.innerText = "We sent a 6-digit code to your email. Enter it below to downgrade your account.";
        otpContainer.style.display = "flex";
        otpInput.focus();

        if (reqData.otp) {
            alert("Demo Mode: Your Cancel OTP is " + reqData.otp);
            otpInput.value = reqData.otp;
        }

        btnVerify.onclick = async () => {
            const otp = otpInput.value.trim();
            if (!otp || otp.length !== 6) {
                otpInput.style.borderColor = '#ef4444';
                return;
            }
            
            btnVerify.innerText = "Processing...";
            btnVerify.disabled = true;

            try {
                const res = await fetch('/api/cancel-pro', { 
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ otp: otp })
                });
                const data = await res.json();
                
                if (data.success) {
                    statusText.innerText = "Your Flux Pro subscription has been cancelled.";
                    statusText.style.color = "#10b981";
                    otpContainer.style.display = "none";
                    btnKeep.style.display = "none";
                    
                    modal.innerHTML = `
                        <div style="background:rgba(16,185,129,0.1);color:#10b981;width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;font-size:32px;border:2px solid #10b981;">✔</div>
                        <h2 style="color:white;font-size:28px;font-weight:800;margin:0 0 12px;font-family:'Inter',sans-serif;">Access Revoked</h2>
                        <p style="color:#8888aa;font-size:15px;line-height:1.6;margin:0 0 24px;font-family:'Inter',sans-serif;">Your Flux Pro subscription has been securely cancelled.</p>
                        <button onclick="window.location.reload()" style="background:#10b981;border:none;color:white;padding:16px 24px;border-radius:16px;font-size:16px;font-weight:700;cursor:pointer;width:100%;">Continue</button>
                    `;
                } else {
                    statusText.innerText = data.error || 'The OTP code was incorrect.';
                    statusText.style.color = "#ef4444";
                    btnVerify.innerText = "Verify & Revoke";
                    btnVerify.disabled = false;
                }
            } catch(e) {
                statusText.innerText = "Connection error.";
                btnVerify.innerText = "Verify & Revoke";
                btnVerify.disabled = false;
            }
        };

    } catch (e) { console.error(e); }
};

// Update Nav User UI globally
function updateNavUI() {
  const navUser = document.querySelector('.nav-user');
  const navRight = document.querySelector('.nav-right');
  const isPro = appState.user && appState.user.is_pro;
  
  if (!navRight) return;

  if (isLoggedIn()) {
    // Inject Cancel Pro button if pro
    if (isPro) {
      let cancelBtn = document.querySelector('.btn-cancel-pro');
      if (!cancelBtn) {
        cancelBtn = document.createElement('a');
        cancelBtn.href = "#";
        cancelBtn.className = "btn-cancel-pro";
        cancelBtn.style.cssText = "background:rgba(239,68,68,0.1); border:1px solid #ef4444; color:#ef4444; padding:6px 14px; border-radius:20px; font-weight:700; font-size:12px; text-decoration:none; margin-right:8px;";
        cancelBtn.innerText = "✖ Cancel Pro";
        cancelBtn.onclick = (e) => { e.preventDefault(); cancelProSubscription(); };
        navRight.prepend(cancelBtn);
      }
    }

    if(navUser) {
      navUser.style.display = 'flex';
      const nameStr = appState.user?.name || "User";
      const initials = nameStr.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase();
      const shortName = nameStr.split(' ')[0];
      
      if (isPro) {
          navUser.innerHTML = `<a href="profile.html" style="text-decoration:none; display:flex; align-items:center; gap:10px; color:white;"><div class="avatar" style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,#fbbf24,#f59e0b); display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:800; color:#000; box-shadow: 0 0 10px rgba(251,191,36,0.4);">PR</div><span>${shortName} <span style="font-size:10px;color:#fbbf24;font-weight:700;">PRO</span></span></a>`;
      } else {
          navUser.innerHTML = `<a href="profile.html" style="text-decoration:none; display:flex; align-items:center; gap:10px; color:white;"><div class="avatar" style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,var(--purple),var(--blue)); display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:600;">${initials}</div><span>${shortName}</span></a>`;
      }
    }
    
    // Convert all "★ Upgrade Pro" buttons to "✔ PRO Active" globally
    document.querySelectorAll('a').forEach(btn => {
        if (isPro && btn.href.includes('flux-pro.html') && btn.textContent.includes('Upgrade')) {
            btn.outerHTML = '<span style="background:rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color:#10b981; padding:6px 14px; border-radius:20px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px;"><span style="font-size:14px;">✔</span> PRO Active</span>';
        }
    });
    
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
    // Disable send button to prevent duplicate submissions
    sendBtn.disabled = true;

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
      const replyText = data.reply || "I couldn't process that. Try again!";
      botMsg.textContent = replyText;
      messages.appendChild(botMsg);
      
      // Speak the reply out loud for the Voice Chatbot experience!
      if ('speechSynthesis' in window && replyText) {
        window.speechSynthesis.cancel(); // Cancel any ongoing speech
        const utterance = new SpeechSynthesisUtterance(replyText);
        
        const voices = window.speechSynthesis.getVoices();
        let voice = voices.find(v => v.name.includes("Google US English") || v.name.includes("Samantha"));
        if (!voice) voice = voices.find(v => v.lang.startsWith("en"));
        if (voice) utterance.voice = voice;
        
        utterance.rate = 1.05;
        window.speechSynthesis.speak(utterance);
      }
      
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
      
      // Auto-send the voice command immediately to feel like a real conversational chatbot!
      sendMessage();
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
