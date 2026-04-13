# ⚡ FLUX — Autonomous AI Wealth Engine

### *Replacing the cashback dependency trap with actual fractional wealth generation.*

**Built for the Finvasia Hackathon**

---

## 🚀 The Problem: The "Cashback Illusion"
Modern fintech apps have addicted users to **"Cashback"**. Users frequently spend ₹1,000 just to earn a ₹10 reward—a net loss of ₹990. This creates a psychological illusion of saving money while actually encouraging chronic overspending and poor financial health. 

**Our Solution:** FLUX flips the script. We don't give you cashback points. Instead, our engine transparently takes a 5% margin of your expenditure and **auto-invests it**. Instead of a ₹10 gamified reward, your daily spending habits generate a real fractional portfolio.

---

## ✨ System Architecture & Key Features

### 1. 🤖 The Auto-Invest Engine (Cashback Replacement)
Every single expense logged triggers a secure backend API event. The 5% equivalent "cashback" is mathematically fractionalized into a Mock Portfolio (60% S&P 500 Index, 30% Sovereign Gold, 10% Liquid Cash) perfectly simulating an integration via Finvasia's Shoonya APIs.

### 2. 🛡️ Pre-Spend Impact & Hard Budget Lockdown Tool
Before an expense is recorded, a `/api/predict-impact` calculation is made showing how the transaction will negatively affect wealth velocity. If the expense exceeds a mathematical 90% income threshold, the system enforces a **"🚨 BUDGET LOCKDOWN ENGAGED"** UI block prohibiting the action, serving as a functional tool to alter behavior.

### 3. 🤔 Explainable AI Nudges & Triggers
A heavily optimized `dashboard` renders "AI Wealth Nudges & Triggers" using highly visible animated styling. Instead of a black-box suggestion, the UI features an explicit "Explainable AI Reasoning" breakdown (e.g., *Pattern: Weekend Overspend, Action: Lock Delta*), allowing users to trust the machine-learning rationale.

### 4. 🔮 Interactive Future Wealth Simulator
We replaced static text with a fully interactive Compound Interest simulation tool. Users can input any number of years to aggressively compare the long-term difference between letting their surplus sit in a 3% savings account versus FLUX's 12% automated Shoonya integrations.

### 5. 🔌 Dual-Layer API Architecture
This application is heavily API-driven to ensure a modern, decoupled structure:
*   **Internal Flask APIs:** Handles all core business logic, including a new transaction payload parsing to generate real-time **Financial Personality Tags** (e.g., "Weekend Spender" vs "Disciplined Saver").
*   **External AI API (Google Gemini 2.5 Flash):** We integrated Google’s Generative AI to power the Voice Chatbot (supports spoken English & Hindi). The system dynamically injects live SQLite data (goals, real-time balance) for targeted insights. Note: To prevent transcription errors, voice commands drop into an input field for user review before sending.
*   **Graceful API Degradation:** To ensure a flawless UI experience, we engineered a custom fallback exception handler in Python. If Google's API hits a rate limit (429) or is unavailable (503), the backend gracefully intercepts the failure and simulates realistic responses natively without ever crashing the frontend.

### 6. 📈 Mathematical Spending Forecasting
Rather than relying purely on LLMs for guessing, we wrote a native Python **Linear Regression model** utilizing Numpy to mathematically project the user's next 3 days of expenses alongside a 30-day savings projection algorithm.

### 7. ⚡ FLUX Score
We engineered a proprietary algorithmic score (out of 1000) that calculates your "Wealth Velocity" based on savings rates. It renders on the frontend using dynamic progress bars alongside the user's Level.

### 8. 📄 Native PDF Wealth Reporting
We bypass standard browser printing via a built-in Python `reportlab` generator that parses the user's database footprint and issues an official monthly PDF breakdown of their asset accumulation.

### 9. 🎨 Premium UI/UX & Data Visualizations
Integrated **Three.js** to generate interactive 3D particle data visualizations representing the strength of the user's wealth engine. It utilizes cutting-edge CSS glassmorphism, responsive Grid layouts, automated UI Confetti drops, and VanillaTilt.js micro-animations.

---

## 💼 Business Viability & Growth Loop

While our core focus is technical excellence, FLUX is designed as a highly scalable startup with clear pathways for user growth and monetization:

### Monetization Strategy (How FLUX Makes Money)
1. **B2B API & Brokerage Partnerships:** By routing user micro-investments to partnered brokerages (like Finvasia's Shoonya), FLUX earns lead-generation premiums and fractional AUM (Assets Under Management) share.
2. **Freemium 'Flux Pro' Analytics:** While core tracking is free, advanced AI predictive wealth forecasting and native tax-reporting generation is gated behind a premium SaaS subscription.

### User Growth Strategy (Acquisition & Retention)
*   **Intrinsic Retention:** Replacing traditional cashback solves churn. Users checking their compounding "Wealth Velocity" and daily AI nudges return to the app naturally, avoiding the "churn-and-burn" cycle of credit card reward hoppers.
*   **Gamified Virality:** Achievement badges and the "FLUX Score (Out of 1000)" introduce competitive social mechanics. Users can share their "Wealth Level" on platforms like LinkedIn or X, driving organic, zero-Cost-of-Acquisition (CAC) user growth.

---

## 🏃‍♂️ How to Run Locally for Judging

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Environment Setup
We have provided an `.env.example` file to show how the APIs are securely managed without exposing keys. To run the app, simply duplicate it:
```bash
cd backend
cp .env.example .env
```
Open the `.env` file and insert:
*   Your `EMAIL_SENDER` and `EMAIL_PASSWORD` (App password) for the OTP login system.
*   Your `GEMINI_API_KEY` to unlock the LLM logic in `ml_engine.py`.

### 3. Install Dependencies
```bash
pip install flask flask-cors python-dotenv google-genai numpy reportlab 
```

### 4. Start the FLUX Engine
```bash
python app.py
```
> The local SQLite database will automatically initialize itself. Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser to view the application in action.

---

## 🎥 Required Demo Video
Because this project utilizes live email-sending protocols and the **Google Gemini API**, we highly recommend watching our official 3-minute demo video. This guarantees you can review all of our AI and gamification logic even if you don't have your own API Keys ready or hit a rate limit during local testing!

**[ 🔗 Watch the Official FLUX Demo Video (YouTube) ](https://youtu.be/kFnPAkM8CHc)**

---

**Built with ❤️ for Finvasia.**
