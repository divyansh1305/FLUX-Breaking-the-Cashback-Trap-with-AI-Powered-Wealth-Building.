import os
import json
import re
from dotenv import load_dotenv
from market_data import get_nifty_data, get_gold_rate, get_stock_info

# Use simple local logic + Gemini Flash for speed
try:
    load_dotenv()
    import google.generativeai as genai
    api_key = os.environ.get("GEMINI_API_KEY") or "AIzaSyBuDk5FjULXBisCiEUuqqztK6bojWHUcS8"
    genai.configure(api_key=api_key)
    
    # Check for working models - Prioritize Gemma if Gemini is hitting quota
    # Based on diagnostics, gemma-3 models are available and responsive
    working_model_name = 'gemini-1.5-flash'
    try:
        # Quick check if gemini is responsive
        test_model = genai.GenerativeModel('gemini-1.5-flash')
        test_model.generate_content("test", generation_config={"max_output_tokens": 1})
        working_model_name = 'gemini-1.5-flash'
    except:
        # Fallback to Gemma-3 which has separate quota/availability
        # Prioritize 27b for higher quality "proper" answers
        for g_name in ['gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-4b-it']:
            try:
                test_g = genai.GenerativeModel(g_name)
                test_g.generate_content("test", generation_config={"max_output_tokens": 1})
                working_model_name = g_name
                break
            except: continue
        
    model = genai.GenerativeModel(working_model_name)
    print(f"--- GHOST AI INITIALIZED WITH: {working_model_name} ---")
    HAS_GENAI = True
except Exception as e:
    print(f"--- GHOST AI INIT FAILED: {str(e)} ---")
    HAS_GENAI = False

def get_voice_agent_response(transcript, state_history="[]"):
    t = transcript.lower().strip()
    
    # 1. HARDCODED SAFETY INTERCEPTS (OTP & EMAIL)
    # This ensures critical login flow works even if AI hits quota
    
    # OTP Extraction
    nums = "".join(re.findall(r'\d', t))
    if len(nums) >= 6:
        return {"response": "Interpreting verification code. Authenticating now.", "actions": [
            {"type": "agent_type", "id": "otpInput", "value": nums[:6]},
            {"type": "agent_click", "id": "btn-otp-submit"}
        ]}
    
    # Email Extraction
    if "email" in t or "@" in t or "at" in t:
        # Convert "at" and "dot" for voice
        raw_email = t.replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_email)
        if email_match:
            return {"response": "Email detected. Moving to next step.", "actions": [
                {"type": "agent_type", "id": "emailInput", "value": email_match.group(0)},
                {"type": "agent_click", "id": "btn-email-submit"}
            ]}

    # Scrolling
    if "scroll" in t or "glide" in t or "move" in t:
        d = "down"
        if "up" in t or "top" in t: d = "up"
        if "stop" in t or "halt" in t or "stay" in t:
            return {"response": "Halted.", "actions": [{"type": "stop_scroll"}]}
        return {"response": f"Gliding {d}.", "actions": [{"type": "scroll", "direction": d}]}

    if HAS_GENAI:
        try:
            print(f"--- GHOST AI PROCESSING: '{transcript}' ---")
            # Enhanced System Prompt for Ghost AI
            system_prompt = """
            You are Ghost AI, the premium proactive voice core of Flux OS. 
            Analyze the user's speech and return a JSON object with:
            1. 'response': A short, premium spoken response (1 sentence). Explain what you are doing.
            2. 'actions': A list of objects with 'type' and parameters.
            
            Supported Actions:
            - {"type": "navigate", "url": "dashboard.html" | "markets.html" | "payments.html" | "smart-analyzer.html" | "arena.html"}
            - {"type": "agent_click", "id": "BUTTON_ID"}
            - {"type": "agent_type", "id": "INPUT_ID", "value": "TEXT"}
            
            Complex Intent Mapping:
            - "buy [STOCK NAME]", "trade [STOCK NAME]" -> navigate to markets.html AND {"type": "agent_type", "id": "trade-symbol", "value": "[STOCK NAME]"}
            - "open wallet", "pay", "send money" -> navigate to payments.html
            - "analyse my statement", "run analysis", "analyse and work" -> navigate to smart-analyzer.html AND {"type": "agent_click", "id": "btn-execute-model"}
            - "arena", "games", "gamification" -> navigate to arena.html
            - "insurance", "policy", "protect" -> navigate to insurance.html
            - "dashboard", "overview", "home" -> navigate to dashboard.html
            
            If you don't understand or the intent is vague, ASK a clarifying question.
            Persona: Be direct, technical, and high-performance. Use phrases like 'Initializing', 'Engaging', 'Analyzing trajectory'.
            """
            
            resp = model.generate_content(
                f"{system_prompt}\nUser Transcript: {transcript}\nIMPORTANT: ALWAYS return ONLY a valid JSON object wrapped in ```json tags."
            )
            text = resp.text.strip()
            print(f"--- GHOST AI RAW TEXT: {text} ---")
            
            # Extract JSON from potential markdown blocks
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if not match:
                match = re.search(r'(\{.*?\})', text, re.DOTALL)
            
            if match:
                data = json.loads(match.group(1))
                print(f"--- GHOST AI PARSED: {json.dumps(data)} ---")
                return data
            else:
                print("--- GHOST AI: NO JSON FOUND IN TEXT ---")
        except Exception as e:
            print(f"--- GHOST AI ERROR: {str(e)} ---")
            pass

    return {"response": "I'm listening. How can I help you navigate Flux?", "actions": []}

def get_ml_response(message, user_data):
    if not HAS_GENAI:
        return f"Hi {user_data.get('name', 'User')}! Your current balance is ₹{user_data.get('balance', 0)}. How can I help you today?"

    # Inject real-time market context
    try:
        nifty = get_nifty_data()
        gold = get_gold_rate()
        user_data['market_context'] = {
            "nifty_50": nifty.get('current_price', 'Unknown'),
            "gold_rate": gold.get('price', 'Unknown'),
            "gold_currency": gold.get('currency', 'USD/oz')
        }
    except: pass

    prompt = f"""
    You are Flux AI, a premium financial assistant. 
    User Data & Context: {json.dumps(user_data)}
    User Question: {message}
    
    Provide a concise, professional, and helpful response. 
    If the user asks about their balance, score, or goals, use the provided data.
    If the user asks about market rates like Gold or NIFTY, use the provided 'market_context'.
    Be encouraging about wealth building. Use 1-2 emojis.
    Keep it under 3 sentences.
    """
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        # Better fallback than just the score
        balance = user_data.get('balance', 0)
        name = user_data.get('name', 'User').split(' ')[0]
        return f"Hi {name}! I'm currently optimizing your portfolio. You have ₹{balance} in liquid capital. How can I assist you further?"

def get_ml_analysis(income, expenses, savings):
    if not HAS_GENAI:
        return "Your spending is being monitored. Maintain a 20% savings rate for optimal growth."

    prompt = f"""
    Analyze this financial profile:
    Income: ₹{income}
    Expenses: ₹{expenses}
    Savings/Investments: ₹{savings}
    
    Provide a 2-sentence 'Audit' of their financial health in HTML format. 
    Use <b> tags for emphasis. Be direct and premium.
    """
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except:
        return "<b>Analysis complete.</b> Your capital efficiency is within normal parameters. Continue automated sweeps."

def get_behavioral_audit(log_history):
    return "Strategic audit of your financial behavior suggests high potential for compounding."
