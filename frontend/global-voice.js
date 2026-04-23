// global-voice.js -> ADVANCED AGENTIC VERSION
document.addEventListener('DOMContentLoaded', () => {
    if (typeof annyang === 'undefined') return;

    // 1. CREATE VOICE INDICATOR UI
    const indicator = document.createElement('div');
    indicator.id = 'ghost-ai-indicator';
    indicator.innerHTML = `
        <div class="ghost-ring"></div>
        <div class="ghost-core">⚡</div>
        <div class="ghost-status">READY</div>
    `;
    document.body.appendChild(indicator);

    const style = document.createElement('style');
    style.innerHTML = `
        #ghost-ai-indicator {
            position: fixed; bottom: 30px; right: 30px; width: 60px; height: 60px;
            z-index: 9999; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: 0.3s;
        }
        .ghost-ring {
            position: absolute; width: 100%; height: 100%; border: 2px solid #3b82f6;
            border-radius: 50%; animation: ghost-pulse 2s infinite; opacity: 0.5;
        }
        .ghost-core {
            width: 40px; height: 40px; background: linear-gradient(135deg, #3b82f6, #06b6d4);
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            color: white; font-weight: 900; font-size: 18px; box-shadow: 0 0 15px rgba(59,130,246,0.5);
        }
        .ghost-status {
            position: absolute; top: -25px; right: 0; font-size: 10px; font-weight: 800;
            color: #3b82f6; letter-spacing: 1px; text-transform: uppercase; white-space: nowrap;
        }
        @keyframes ghost-pulse {
            0% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.4); opacity: 0; }
            100% { transform: scale(1); opacity: 0.5; }
        }
        .ghost-listening .ghost-ring { border-color: #ef4444; animation-duration: 1s; }
        .ghost-listening .ghost-status { color: #ef4444; }
        .ghost-speaking .ghost-ring { border-color: #10b981; animation-duration: 0.5s; }
        .ghost-speaking .ghost-status { color: #10b981; }
    `;
    document.head.appendChild(style);

    let isMuted = false;

    const updateStatus = (status) => {
        const s = indicator.querySelector('.ghost-status');
        if(s) s.innerText = status;
        
        indicator.className = ''; // reset
        if (status === 'LISTENING') indicator.classList.add('ghost-listening');
        if (status === 'SPEAKING') indicator.classList.add('ghost-speaking');
        if (status === 'MUTED') indicator.classList.add('ghost-muted');
        if (status === 'THINKING') indicator.classList.add('ghost-thinking');
    };

    // Add Muted Style
    const mutedStyle = document.createElement('style');
    mutedStyle.innerHTML = `
        .ghost-muted .ghost-ring { border-color: #6b7280; animation: none; opacity: 0.2; }
        .ghost-muted .ghost-core { background: #374151; filter: grayscale(1); }
        .ghost-muted .ghost-status { color: #6b7280; }
        .ghost-thinking .ghost-ring { border-color: #a855f7; animation-duration: 0.8s; }
        .ghost-thinking .ghost-status { color: #a855f7; }
    `;
    document.head.appendChild(mutedStyle);

    // 2. VOICE CORE
    let isSpeaking = false;

    const speak = (text) => {
        if (!text || isSpeaking) return;
        isSpeaking = true;
        updateStatus('SPEAKING');
        
        try { annyang.abort(); } catch(e){}
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0; 
        
        utterance.onend = () => {
            setTimeout(() => {
                isSpeaking = false;
                if (!isMuted) {
                    updateStatus('LISTENING');
                    try { annyang.start({ autoRestart: true, continuous: true }); } catch(e){}
                } else {
                    updateStatus('MUTED');
                }
            }, 500);
        };
        window.speechSynthesis.speak(utterance);
    };

    let scrollInt = null;

    const exec = (actions) => {
        if (!actions) return;
        actions.forEach(a => {
            if (a.type === 'navigate') {
                const remaining = actions.filter(act => act !== a);
                if (remaining.length > 0) sessionStorage.setItem('pending_actions', JSON.stringify(remaining));
                window.location.href = a.url;
            }
            else if (a.type === 'agent_type') {
                const el = document.getElementById(a.id);
                if (el) { 
                    el.value = a.value; 
                    el.dispatchEvent(new Event('input', {bubbles:true})); 
                    el.dispatchEvent(new Event('change', {bubbles:true}));
                }
            } else if (a.type === 'agent_click') {
                const el = document.getElementById(a.id);
                if (el) el.click();
            } else if (a.type === 'scroll') {
                if (scrollInt) clearInterval(scrollInt);
                const s = (a.direction === 'up' ? -5 : 5);
                scrollInt = setInterval(() => {
                    window.scrollBy(0, s);
                    if (s > 0 && (window.innerHeight + window.pageYOffset) >= document.body.offsetHeight) clearInterval(scrollInt);
                    if (s < 0 && window.pageYOffset <= 0) clearInterval(scrollInt);
                }, 15);
            } else if (a.type === 'stop_scroll') {
                if (scrollInt) clearInterval(scrollInt);
                scrollInt = null;
            }
        });
    };

    const pending = sessionStorage.getItem('pending_actions');
    if (pending) {
        sessionStorage.removeItem('pending_actions');
        setTimeout(() => exec(JSON.parse(pending)), 1000);
    }

    annyang.addCommands({
        '*speech': async (speech) => {
            if (isSpeaking || isMuted) return;
            console.log("Ghost captured:", speech);
            
            // ONE-SHOT MODE: Mute immediately after capturing
            isMuted = true; 
            updateStatus('THINKING');
            
            try {
                const res = await fetch('/api/voice-agent', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({transcript: speech})
                });
                const data = await res.json();
                speak(data.response);
                if (data.actions) exec(data.actions);
            } catch(e) {
                updateStatus('MUTED');
            }
        }
    });

    // Toggle Mute on Click or Spacebar
    const toggleAI = () => {
        isMuted = !isMuted;
        if (isMuted) {
            updateStatus('MUTED');
            try { annyang.abort(); } catch(e){}
        } else {
            updateStatus('LISTENING');
            try { annyang.start({ autoRestart: true, continuous: true }); } catch(e){}
        }
    };

    indicator.addEventListener('click', toggleAI);
    
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target === document.body) {
            e.preventDefault();
            toggleAI();
        }
    });

    // Start MUTED for professional recording
    isMuted = true;
    updateStatus('MUTED');

    console.log("🦾 GHOST AI AGENTIC CORE ONLINE");

    // 3. AUTO-GREETING (Dashboard Only)
    const isDashboard = window.location.pathname.includes('dashboard.html');
    if (isDashboard) {
        setTimeout(() => {
            speak("Welcome to Flux AI. Your autonomous wealth engine is online and ready for optimization.");
        }, 1500);
    }
});
