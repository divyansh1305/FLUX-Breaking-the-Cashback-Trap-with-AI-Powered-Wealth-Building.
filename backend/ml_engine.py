import os
import json
import traceback

# Optional: Real LLM Backend using google.genai
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
    # Securely get key from env - NO HARDCODED KEYS FOR GITHUB
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        HAS_GENAI = False
except ImportError:
    HAS_GENAI = False

def get_ml_response(message, user_data):
    """
    Generate response based on a real LLM for the Ultimate 100/100 Chatbot Experience.
    """
    if not HAS_GENAI:
        return "🔄 My core engine is currently syncing. To see your live balance or goals, please refer to your dashboard while my neural link resets!"

    try:
        # Construct a rich prompt using user context
        context = f"""
        You are 'Flux AI', an advanced financial advisor chatbot for a wealth-building app called 'Flux'.
        You act as an intelligent behavioral layer on top of Finvasia and Shoonya.
        Your job is to talk to the user and give them aggressive, high-quality, smart financial advice.
        
        APP NAVIGATION & RULES:
        1. If the user asks where a feature is: 'Flux Card' has its own dedicated tab on the Left Sidebar Menu! 'Goals', 'Analytics' and 'Simulator' also have their own tabs on the left menu.
        2. If the user uses inappropriate language, bad words, or asks about drugs/illegal things, firmly but politely censor the conversation and redirect them to their financial goals.
        3. Never break out of character. You are part of the app. Do not say you cannot perform app functions.
        4. "Growth Score", "Flux Score", or "Score" refers to their 'FLUX Score' below (calculated out of 1000).
        
        USER DATA CONTEXT:
        Name: {user_data.get('name', 'User')}
        Level: {user_data.get('level', 1)}
        Points: {user_data.get('points', 0)}
        Active Streak: {user_data.get('streak', 0)} days
        FLUX Score: {user_data.get('score', 0)} / 1000
        
        Financials:
        Free Balance: ₹{user_data.get('balance', 0):,.2f}
        Total Income Logged: ₹{user_data.get('total_income', 0):,.2f}
        Total Expenses Logged: ₹{user_data.get('total_expenses', 0):,.2f}
        Total Investments (Auto-saved via Flux to Shoonya): ₹{user_data.get('total_investments', 0):,.2f}
        
        Goals: {json.dumps(user_data.get('goals', []), indent=2)}
        
        Respond directly to their message accurately, concisely, and with emojis! Max 4 sentences.
        
        User's message: "{message}"
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=context
        )
        return response.text
    except Exception as e:
        print("Gemini API Error:", traceback.format_exc())
        # Graceful fallback instead of raw error codes during a live demo
        message = message.lower()
        if "score" in message or "growth" in message or "level" in message:
             return f"🏆 You are currently Level {user_data.get('level', 1)} with {user_data.get('points', 0)} points! Keep saving to level up."
        elif "spend" in message or "expense" in message:
             return f"📉 You have currently logged ₹{user_data.get('total_expenses', 0):,.0f} in total expenses. Stay disciplined to maximize your Flux score!"
        elif "do" in message or "what" in message or "flux" in message:
             return "✨ Flux is an autonomous AI Wealth Engine! Instead of giving you meaningless cashback, we mechanically auto-invest 5% of your expenses into a fractional portfolio to build you massive long-term wealth."
        elif "balance" in message or "how much" in message:
             return f"💰 Your current free balance is ₹{user_data.get('balance', 0):,.0f}."
        elif "invest" in message or "wealth" in message:
             return f"🚀 Flux has auto-invested ₹{user_data.get('total_investments', 0):,.0f} for you automatically!"
        elif "card" in message:
             return "💳 You can view your Flux Card details anytime by clicking the 'Flux Card' tab on the left sidebar menu!"
        else:
             return "🔄 My financial engine is analyzing a large data batch. Check your dashboard for immediate insights!"

def get_ml_analysis(income, expenses, savings):
    """
    Hackathon-ready pure spending analysis function localized without api key failure risks.
    Or use LLM if available.
    """
    if HAS_GENAI:
       try:
           sys_prompt = f"You are Flux AI. Analyze this profile: Income {income}, Expenses {expenses}, Savings {savings}. Give 3 short bullet points (in HTML format, using <strong> tags for emphasis) describing their financial health and one actionable step. Total response must be raw HTML string ready to render."
           response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=sys_prompt
            )
           html_out = response.text.replace("```html", "").replace("```", "").strip()
           return html_out
       except: pass
       
    risk_level = "Low"
    spend_pct = (expenses / income * 100) if income > 0 else 0

    if spend_pct > 80:
        risk_level = "High"
    elif spend_pct > 50:
        risk_level = "Medium"

    return f'''
        <ul style="padding-left:20px; text-align:left;">
            <li style="margin-bottom:8px"><strong>Savings Tips:</strong> Track flexible spending closely, aim to keep expenses under 75% of income.</li>
            <li style="margin-bottom:8px"><strong>Micro-investments:</strong> Setup a daily ₹50 auto-SIP.</li>
            <li style="margin-bottom:8px"><strong>Risk level:</strong> <span style="color:#e8491d">{risk_level}</span></li>
            <li style="margin-bottom:8px"><strong>Action for today:</strong> Go to Goals and lock in a 5% milestone.</li>
        </ul>
    '''
