import os
import random
import datetime
import smtplib
import secrets
from email.message import EmailMessage
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv
import sqlite3

# --- SETUP AND CONFIGURATION ---
load_dotenv()

from database import init_db, get_db_connection
import random
from ml_engine import get_ml_response, get_ml_analysis
from predictive_model import generate_expense_forecast
from report_generator import generate_monthly_report
from market_data import get_nifty_data, get_stock_info
from shoonya_integration import ShoonyaApiWrapper
from statement_analyzer import parse_and_analyze_statement

app = Flask(__name__, template_folder="../frontend", static_folder="../frontend", static_url_path="")
CORS(app)

app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

with app.app_context():
    init_db()

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# ─── DATABASE HELPERS ──────────────────────────────────────
def insert_diversified_investments(conn, user_id, total_amount, base_source):
    conn.execute("INSERT INTO investments (user_id, amount, source) VALUES (?, ?, ?)", (user_id, total_amount * 0.6, f"S&P 500 Index ({base_source})"))
    conn.execute("INSERT INTO investments (user_id, amount, source) VALUES (?, ?, ?)", (user_id, total_amount * 0.3, f"Sovereign Gold ({base_source})"))
    conn.execute("INSERT INTO investments (user_id, amount, source) VALUES (?, ?, ?)", (user_id, total_amount * 0.1, f"Liquid Cash ({base_source})"))

def get_free_balance(conn, user_id):
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    goals = conn.execute("SELECT SUM(saved_amount) as t FROM goals WHERE user_id = ?", (user_id,)).fetchone()
    
    income = inc["t"] if inc and inc["t"] else 0.0
    expenses = exp["t"] if exp and exp["t"] else 0.0
    investments = inv["t"] if inv and inv["t"] else 0.0
    saved = goals["t"] if goals and goals["t"] else 0.0
    return income - expenses - investments - saved

# ─── AUTHENTICATION WRAPPER ────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def pro_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for('login'))
        
        user_id = session.get("user_id")
        conn = get_db_connection()
        user = conn.execute("SELECT is_pro, pro_expiry FROM users WHERE id = ?", (user_id,)).fetchone()
        
        is_active_pro = False
        if user and user['is_pro']:
            if user['pro_expiry']:
                try:
                    expiry = datetime.datetime.strptime(user['pro_expiry'], '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    # Fallback for different format
                    expiry = datetime.datetime.strptime(user['pro_expiry'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                
                if datetime.datetime.now() < expiry:
                    is_active_pro = True
            else:
                # If is_pro is 1 but no expiry (manual override), treat as active
                is_active_pro = True
        
        conn.close()
        
        if not is_active_pro:
            return redirect(url_for('flux_pro'))
        return f(*args, **kwargs)
    return decorated_function

# --- PAGE ROUTES ---
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for('index_html'))
    return redirect(url_for('open_html'))

@app.route("/open")
@app.route("/open.html")
def open_html():
    if "user_id" in session:
        return redirect(url_for('index_html'))
    return render_template("open.html")

@app.route("/onboarding")
@app.route("/onboarding.html")
def onboarding_html():
    if "user_id" not in session:
        return redirect(url_for('login'))
    return render_template("onboarding.html")

@app.route("/index.html")
def index_html():
    return render_template("index.html")

@app.route("/flux-card")
@app.route("/flux-card.html")
@login_required
def flux_card():
    return render_template("flux-card.html")

@app.route("/dashboard")
@app.route("/dashboard.html")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/smart-analyzer.html")
@app.route("/smart-analyzer")
@login_required
@pro_required
def smart_analyzer():
    return render_template("smart-analyzer.html")

@app.route("/analytics_overview.html")
@app.route("/analytics_overview")
@login_required
@pro_required
def analytics_overview():
    return render_template("analytics_overview.html")

@app.route("/insurance.html")
@app.route("/insurance")
@login_required
@pro_required
def insurance_page():
    return render_template("insurance.html")

@app.route("/markets.html")
@app.route("/markets")
@login_required
@pro_required
def markets_page():
    return render_template("markets.html")

@app.route("/payments.html")
@app.route("/payments")
@login_required
@pro_required
def payments_page():
    return render_template("payments.html")

@app.route("/tax.html")
@app.route("/tax")
@login_required
@pro_required
def tax_page():
    return render_template("tax.html")

@app.route("/simulator.html")
@app.route("/simulator")
@login_required
@pro_required
def simulator_page():
    return render_template("simulator.html")

@app.route("/will.html")
@app.route("/will")
@login_required
@pro_required
def will_page():
    return render_template("will.html")

@app.route("/flux-pro")
@app.route("/flux-pro.html")
@login_required
def flux_pro():
    return render_template("flux-pro.html")

@app.route("/login")
@app.route("/login.html")
def login():
    if "user_id" in session:
        return redirect(url_for('dashboard'))
    return render_template("login.html")

@app.route("/logout")
@app.route("/logout.html")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/add-income")
@app.route("/add-income.html")
@login_required
def add_income_page():
    return render_template("add-income.html")

@app.route("/add-expense")
@app.route("/add-expense.html")
@login_required
def add_expense_page():
    return render_template("add-expense.html")

@app.route("/create-goal")
@app.route("/create-goal.html")
@login_required
def create_goal_page():
    return render_template("create-goal.html")

@app.route("/save-now")
@app.route("/save-now.html")
@login_required
def save_now():
    return render_template("save-now.html")

@app.route("/arena")
@app.route("/arena.html")
@login_required
def arena_page():
    return render_template("arena.html")

@app.route("/api/verify-pro-payment", methods=["POST"])
@login_required
def verify_pro_payment():
    data = request.get_json() or {}
    payment_id = data.get("payment_id", "TEST_PAYMENT")
    user_id = session.get("user_id")
    
    conn = get_db_connection()
    user = conn.execute("SELECT name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    
    # 1. Send Email Notification
    if user and EMAIL_SENDER and EMAIL_PASSWORD:
        msg = EmailMessage()
        msg["Subject"] = "Welcome to FLUX Pro! 🎉"
        msg["From"] = f"Flux Agentic OS <{EMAIL_SENDER}>"
        msg["To"] = user["email"]
        msg.set_content(f"Hi {user['name']},\n\nYour payment of ₹499 (Reference ID: {payment_id}) was successful! \n\nYou now have full access to Tax Harvesting, the AI Legacy Vault, and Time Machine capabilities.\n\nWelcome to true algorithmic wealth building.\n\n- The Flux Engineering Team")
        
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)
        except Exception as e:
            print(f"[MAIL_ERROR] Could not send Pro invoice: {e}")
            
    # 2. Log exactly in the database
    if user:        
        conn.execute("UPDATE users SET is_pro = 1, pro_expiry = ? WHERE id = ?", 
                     (str(datetime.datetime.now() + datetime.timedelta(days=365)), user_id))
        conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Pro Upgrade", f"Unlocked Flux Pro via Razorpay (ID: {payment_id})"))
        conn.commit()
    conn.close()
    
    return jsonify({"success": True}), 200

@app.route("/goals")
@app.route("/goals.html")
@login_required
def goals_page():
    return render_template("goals.html")

@app.route("/transactions")
@app.route("/transactions.html")
@login_required
def transactions_page():
    return render_template("transactions.html")
    
@app.route("/profile.html")
@login_required
def profile_page():
    return render_template("profile.html")

@app.route("/admin")
@app.route("/admin.html")
def admin_html():
    return render_template("admin.html")

# --- AUTH API ENDPOINTS (OTP & SQLite) ---
@app.route("/register", methods=["POST"])
@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    email = data.get("email")
    name = data.get("name", "").strip()

    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    
    user = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    if not user and not name:
        conn.close()
        return jsonify({"success": False, "requiresName": True})
    
    if not user and name:
        c.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        user_id = c.lastrowid
        # Set up a new user in supabase for data relations if needed? The app worked without syncing users to Supabase manually before, it relied on user_id strings or mock. We will use SQLite id.
    else:
        user_id = user["id"]

    otp = str(random.randint(100000, 999999))
    expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)

    c.execute("UPDATE users SET otp = ?, otp_expiry = ? WHERE id = ?", (otp, expiry, user_id))
    conn.commit()
    conn.close()

    if EMAIL_SENDER and EMAIL_PASSWORD:
        try:
            clean_pass = EMAIL_PASSWORD.replace(' ', '')
            msg = EmailMessage()
            msg['Subject'] = 'Your Flux Wealth Login OTP'
            msg['From'] = EMAIL_SENDER
            msg['To'] = email
            
            html_content = f"""
            <html>
              <body style="font-family: 'Arial', sans-serif; background-color: #08080f; color: #ffffff; padding: 40px; text-align: center;">
                <div style="max-width: 500px; margin: 0 auto; background-color: #12121e; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 40px;">
                  <h1 style="color: #ffffff; font-size: 24px; margin-bottom: 8px;">Welcome to <span style="color: #e8491d;">Flux</span></h1>
                  <p style="color: #8888aa; font-size: 14px; margin-bottom: 30px;">Your gamified wealth engine awaits.</p>
                  <p style="color: #ffffff; font-size: 16px; margin-bottom: 20px;">Use the following code to securely log in:</p>
                    {otp}
                  </div>
                </div>
              </body>
            </html>
            """
            msg.set_content(f"Your Flux Wealth OTP is: {otp}")
            msg.add_alternative(html_content, subtype='html')

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(EMAIL_SENDER, clean_pass)
                server.send_message(msg)
                
        except Exception as e:
            print(f"Failed to send real email: {e}")
            # HACKATHON FALLBACK: Let the user login even if SMTP credentials expire
            print(f"\n{'='*40}")
            print(f"EMAIL FAILED - FALLBACK MOCK OTP To: {email} | OTP: {otp}")
            print(f"{'='*40}\n")
            return jsonify({"success": True, "message": "OTP sent via fallback", "mock": True, "otp": otp})
    else:
        print(f"\n{'='*40}")
        print(f"MOCK EMAIL SENT To: {email} | OTP: {otp}")
        print(f"{'='*40}\n")
        return jsonify({"success": True, "message": "OTP sent via fallback", "mock": True, "otp": otp})

    return jsonify({"success": True, "message": "OTP sent successfully"})

@app.route("/login", methods=["POST"])
@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"success": False, "error": "Email and OTP are required"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({"success": False, "error": "User not found"}), 404

    # Use constant-time comparison to prevent timing attacks
    if not user["otp"] or not secrets.compare_digest(str(user["otp"]), str(otp)):
        conn.close()
        return jsonify({"success": False, "error": "Invalid OTP"}), 400
        
    try:
        # Handle potential missing microseconds in some SQLite versions/drivers
        expiry_str = user["otp_expiry"]
        if "." not in expiry_str:
            expiry_str += ".000000"
        expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S.%f')
    except (ValueError, TypeError):
        conn.close()
        return jsonify({"success": False, "error": "Invalid or missing OTP expiry"}), 400

    if datetime.datetime.now() > expiry:
        conn.close()
        return jsonify({"success": False, "error": "OTP has expired"}), 400

    conn.execute("UPDATE users SET otp = NULL, otp_expiry = NULL WHERE id = ?", (user["id"],))
    
    # Check if new user
    inc_count = conn.execute("SELECT COUNT(*) FROM income WHERE user_id = ?", (user["id"],)).fetchone()[0]
    target_route = "index_html" if inc_count > 0 else "onboarding_html"

    conn.commit()
    conn.close()

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    # Log User Activity
    conn = get_db_connection()
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user["id"], "User Login", "Logged into Flux via OTP"))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "redirect": url_for(target_route)})

    return jsonify(activities), 200

@app.route("/api/user")
@login_required
def api_user():
    user_id = session.get("user_id")
    conn = get_db_connection()
    user = conn.execute("SELECT is_pro, coins FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    return jsonify({
        "name": session.get("user_name"),
        "email": session.get("user_email"),
        "is_pro": bool(user["is_pro"]) if user else False,
        "coins": user["coins"] if user else 0
    })

@app.route("/api/send-cancel-otp", methods=["POST"])
@login_required
def send_cancel_otp():
    user_id = session.get("user_id")
    email = session.get("user_email")
    conn = get_db_connection()
    otp = str(random.randint(100000, 999999))
    expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)
    
    conn.execute("UPDATE users SET otp = ?, otp_expiry = ? WHERE id = ?", (otp, expiry, user_id))
    conn.commit()
    conn.close()
    
    if EMAIL_SENDER and EMAIL_PASSWORD:
        try:
            clean_pass = EMAIL_PASSWORD.replace(' ', '')
            msg = EmailMessage()
            msg['Subject'] = 'Flux Pro Cancellation Request'
            msg['From'] = EMAIL_SENDER
            msg['To'] = email
            msg.set_content(f"You have requested to cancel your Flux Pro subscription.\nYour cancellation authorization code is: {otp}\nIf this was not you, please secure your account.")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(EMAIL_SENDER, clean_pass)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email: {e}")
            print(f"\n[MOCK EMAIL FALLBACK] To {email}: CANCEL PRO OTP is {otp}\n")
            return jsonify({"success": True, "otp": otp, "mock": True})
    else:
        print(f"\n[MOCK EMAIL] To {email}: CANCEL PRO OTP is {otp}\n")
        return jsonify({"success": True, "otp": otp, "mock": True})
        
    return jsonify({"success": True})

@app.route("/api/cancel-pro", methods=["POST"])
@login_required
def cancel_pro():
    data = request.json or {}
    otp_input = data.get("otp")
    if not otp_input:
        return jsonify({"success": False, "error": "OTP required"}), 400
        
    user_id = session.get("user_id")
    email = session.get("user_email")
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user["otp"] or not secrets.compare_digest(str(user["otp"]), str(otp_input)):
        conn.close()
        return jsonify({"success": False, "error": "Invalid OTP"}), 400
        
    conn.execute("UPDATE users SET otp = NULL, otp_expiry = NULL, is_pro = 0, pro_expiry = NULL WHERE id = ?", (user_id,))
    conn.execute("DELETE FROM user_activities WHERE user_id = ? AND action_type = 'Pro Upgrade'", (user_id,))
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Pro Cancelled", "Downgraded to Flux Free Tier"))
    conn.commit()
    conn.close()
    
    # Send confirmation email
    if EMAIL_SENDER and EMAIL_PASSWORD:
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Flux Pro Successfully Cancelled'
            msg['From'] = EMAIL_SENDER
            msg['To'] = email
            msg.set_content("Your Flux Pro subscription has been successfully cancelled. You have been downgraded to the Free Tier.\n\nYou will lose access to the Auto-Tax Harvester, Smart Trading algorithms, and your Insurance Vault.\n\nWe hope to see you back soon.")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
        except Exception:
            pass
            
    return jsonify({"success": True})

# --- DATA API ENDPOINTS (SQLite) ---

DEMO_CSV = """Date,Narration,Chq./Ref. No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance
01/01/24,ZOMATO FOOD ORDER,UPI-1234,01/01/24,450.00,,50000.00
05/01/24,AMAZON SHOPPING,UPI-5678,05/01/24,2500.00,,47500.00
10/01/24,SALARY CREDIT,NEFT-999,10/01/24,,85000.00,132500.00
15/01/24,UBER TRIP,UPI-000,15/01/24,320.00,,132180.00
20/01/24,NETFLIX SUBSCRIPTION,CARD-111,20/01/24,649.00,,131531.00
25/01/24,SWIGGY ORDER,UPI-222,25/01/24,580.00,,130951.00
"""

@app.route("/api/analyze-statement", methods=["POST"])
@login_required
def analyze_statement_api():
    file = request.files.get('file')
    if file and file.filename != '':
        csv_content = file.read().decode('utf-8')
        result = parse_and_analyze_statement(csv_content=csv_content, user_id=session["user_id"])
    else:
        # FALLBACK: Use Demo CSV if no file is provided for the 'one-shot' demo experience
        result = parse_and_analyze_statement(csv_content=DEMO_CSV, user_id=session["user_id"])

        
    if result.get("status") == "success":
        return jsonify({"success": True, "analysis": result["data"]}), 200
    else:
        return jsonify({"success": False, "error": result.get("message")}), 400

def calculate_score(user_id, conn):
    # Formulas include: Base score + points + multi-streaks + wealth velocity + coins/badges
    user = conn.execute("SELECT points, level, coins, score FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user: return 0
    
    # Calculate savings rate (Wealth Velocity)
    inc_res = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    total_income = inc_res["t"] if inc_res and inc_res["t"] else 0.0
    
    inv_res = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    total_investments = inv_res["t"] if inv_res and inv_res["t"] else 0.0
    
    velocity = (total_investments / total_income) * 100 if total_income > 0 else 0
    
    # Multi-streak bonus
    streaks = conn.execute("SELECT SUM(current_streak) as s FROM streaks WHERE user_id = ?", (user_id,)).fetchone()["s"] or 0
    
    # Badges count
    badge_count = conn.execute("SELECT COUNT(*) as c FROM user_badges WHERE user_id = ?", (user_id,)).fetchone()["c"]
    
    score = int(300 + (streaks * 15) + (user["points"] * 2) + (velocity * 12) + (badge_count * 20) + (user["coins"] / 10))
    if score > 1000: score = 1000
    
    conn.execute("UPDATE users SET score = ? WHERE id = ?", (score, user_id))
    return score

@app.route("/score", methods=["GET"])
@app.route("/api/dashboard", methods=["GET"])
@login_required
def get_dashboard():
    user_id = session.get("user_id")
    conn = get_db_connection()
    
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    total_income = inc["t"] if inc["t"] else 0.0
    
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    total_expenses = exp["t"] if exp["t"] else 0.0
    
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    total_investments = inv["t"] if inv["t"] else 0.0
    
    goals = conn.execute("SELECT SUM(saved_amount) as t FROM goals WHERE user_id = ?", (user_id,)).fetchone()
    total_goals = goals["t"] if goals["t"] else 0.0

    score = calculate_score(user_id, conn)

    # Corrected balance formula: Net cash available
    balance = max(0, total_income - total_expenses)
    # Total wealth: Cash + value stored in goals (investments are already part of expenses)
    total_wealth = balance + total_goals
    
    velocity = (total_investments / total_income) * 100 if total_income > 0 else 0
    
    # Guilt-Free Spend Allowance calculation
    guilt_free_balance = max(0, int(balance * 0.3)) if velocity > 5 else 0
    if total_income == 0: guilt_free_balance = 0
    
    # Simple Insight logic attached to dashboard as well
    insights = []
    if total_expenses > total_income and total_income > 0:
        insights.append("You're overspending")
    elif total_income > 0 and total_investments > 0 and (total_investments/total_income) > 0.1:
        insights.append("Great financial discipline")
    elif total_investments == 0:
        insights.append("Start investing mechanically via auto-save.")
        
    # PHASE 6: ADVANCED BEHAVIORAL PROFILING (Top 0.1% Win condition)
    try:
        activity_count = conn.execute("SELECT COUNT(*) as c FROM user_activities WHERE user_id = ?", (user_id,)).fetchone()["c"]
        impulse_events = conn.execute("SELECT COUNT(*) as c FROM user_activities WHERE user_id = ? AND action_type='NAVIGATED' AND description LIKE '%simulator%'", (user_id,)).fetchone()["c"]
        
        if velocity > 30:
            persona = "The Compounding Ghost"
        elif velocity > 15 and activity_count > 20:
            persona = "Wealth Architect"
        elif impulse_events > 3:
            persona = "Futurist Speculator"
        else:
            persona = "Analytical Optimizer"
            
        projected_monthly_savings = max(0, total_income - total_expenses) * 1.2 # Optimized projection
    except:
        persona = "Balanced Saver"
        projected_monthly_savings = 5000

    conn.close()
    
    return jsonify({
        "income": total_income,
        "expenses": total_expenses,
        "investments": total_investments,
        "savings": total_goals,
        "balance": balance,
        "guilt_free_balance": guilt_free_balance,
        "totalSaved": total_investments + total_goals,
        "totalWealth": total_wealth,
        "wealthVelocity": f"{velocity:.1f}%",
        "score": score,
        "insights": insights,
        "persona": persona,
        "projected_savings": projected_monthly_savings
    }), 200

@app.route("/api/predict-impact", methods=["POST"])
@login_required
def predict_impact():
    user_id = session.get("user_id")
    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400
        
    conn = get_db_connection()
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    user_record = conn.execute("SELECT score FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    total_inc = inc["t"] if inc["t"] else 0.0
    total_exp = exp["t"] if exp["t"] else 0.0
    current_score = user_record["score"] if user_record and user_record["score"] else 300
    
    is_overspending = False
    if total_inc > 0 and (total_exp + amount) > (total_inc * 0.9):
        is_overspending = True

    score_drop = min(current_score - 1 if current_score > 1 else 1, int(min(150, amount * 0.01)))
    
    # Calculate daily savings properly
    daily_savings = max(10, (total_inc * 0.2) / 30) # Projecting assuming 20% savings over 30 days
    goal_delay = int(amount / daily_savings)
    
    if goal_delay == 0:
        goal_delay = 1
    
    return jsonify({
        "score_drop": score_drop,
        "goal_delay": goal_delay,
        "is_overspending": is_overspending,
        "message": f"This expense will temporarily reduce your FLUX Score by {score_drop} points and delay your active goal target by ~{goal_delay} days."
    }), 200

@app.route("/api/transactions", methods=["GET"])
@login_required
def get_transactions():
    user_id = session.get("user_id")
    conn = get_db_connection()
    
    incomes = conn.execute("SELECT id, source as category, amount, date FROM income WHERE user_id = ?", (user_id,)).fetchall()
    expenses = conn.execute("SELECT id, category, amount, date FROM expenses WHERE user_id = ?", (user_id,)).fetchall()
    
    transactions = []
    for inc in incomes:
        transactions.append({"id": inc["id"], "type": "income", "category": inc["category"], "amount": inc["amount"], "date": inc["date"], "description": ""})
    for exp in expenses:
        transactions.append({"id": exp["id"], "type": "expense", "category": exp["category"], "amount": exp["amount"], "date": exp["date"], "description": ""})

    conn.close()
    transactions.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(transactions), 200

@app.route("/add-expense", methods=["POST"])
@app.route("/api/expense", methods=["POST"])
@login_required
def add_expense():
    data = request.get_json() or {}
    user_id = session.get("user_id")
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount format. Must be a number."}), 400
        
    category = data.get("category", "General")
    date_str = data.get("date", str(datetime.date.today()))

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    conn = get_db_connection()
    
    # 1. Save expense
    conn.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)", (user_id, amount, category, date_str))
    
    # 2. Auto-Invest Logic (5% Cashback equivalent)
    cashback_equivalent = amount * 0.05
    insert_diversified_investments(conn, user_id, cashback_equivalent, "Cashback Injection")
    
    # 3. Round-ups engine logic (Round to nearest 100)
    round_up_amount = 0
    if amount % 100 != 0:
        round_up_amount = 100 - (amount % 100)
        conn.execute("INSERT INTO investments (user_id, amount, source) VALUES (?, ?, ?)", (user_id, round_up_amount, "Spare Change Round-Up"))
    
    # Gamification Tracking (Multi-streak logic for Finance)
    update_streak(user_id, 'finance', conn)
        
    # Log User Activity
    message_desc = f"₹{amount} for {category} (Auto-invested ₹{cashback_equivalent})"
    if round_up_amount > 0:
        message_desc += f" + ₹{round_up_amount} Round-Up"
        
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Added Expense", message_desc))
            
    conn.commit()
    conn.close()

    return jsonify({"success": True, "invested": cashback_equivalent, "rounded": round_up_amount}), 201

@app.route("/add-income", methods=["POST"])
@app.route("/api/add-income", methods=["POST"])
@login_required
def add_income():
    data = request.get_json() or {}
    user_id = session.get("user_id")
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount format. Must be a number."}), 400
        
    source = data.get("category", "Salary")
    date_str = data.get("date", str(datetime.date.today()))

    if amount <= 0:
         return jsonify({"error": "Invalid amount"}), 400

    conn = get_db_connection()
    conn.execute("INSERT INTO income (user_id, amount, source, date) VALUES (?, ?, ?, ?)", (user_id, amount, source, date_str))
    
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Added Income", f"₹{amount} from {source}"))

    conn.commit()
    conn.close()
    return jsonify({"success": True}), 201

@app.route("/insights", methods=["GET"])
@app.route("/api/insights", methods=["GET"])
@login_required
def get_insights():
    # Phase 3: AI / ML Layer
    user_id = session.get("user_id")
    conn = get_db_connection()
    
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    tot_exp = exp["t"] if exp["t"] else 0.0
    
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    tot_inc = inc["t"] if inc["t"] else 0.0
    
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    tot_inv = inv["t"] if inv["t"] else 0.0
    
    savings_rate = (tot_inv / tot_inc) if tot_inc > 0 else 0
    
    insight_msg = ""
    if tot_exp > tot_inc and tot_inc > 0:
        insight_msg = "You're overspending."
    elif savings_rate > 0.3:
        insight_msg = "Great financial discipline."
    else:
        insight_msg = "You are on track. Maintain consistency."
        
    conn.close()
    return jsonify({"insight": insight_msg}), 200

@app.route("/api/gamification", methods=["GET"])
@login_required
def get_gamification_legacy():
    # Phase 5: Gamification Engine (Legacy compatibility)
    return gamification_status()

# Redirect to the main one at the bottom
@app.route("/api/arena-leaderboard-old", methods=["GET"])
@login_required
def arena_leaderboard_legacy():
    return arena_leaderboard()

subscriptions = [
    {"id": "s1", "service": "Netflix Premium", "amount": 649, "usage": "Low Usage (2 hrs/mo)"},
    {"id": "s2", "service": "Gym Membership", "amount": 1499, "usage": "No visits in 45 days"},
    {"id": "s3", "service": "Spotify", "amount": 119, "usage": "High Usage"}
]
destroyed_subs = set()

@app.route("/api/subscriptions", methods=["GET"])
@login_required
def get_subscriptions():
    active_subs = [s for s in subscriptions if s["id"] not in destroyed_subs]
    return jsonify(active_subs), 200

@app.route("/api/destroy-subscription", methods=["POST"])
@login_required
def destroy_subscription():
    data = request.get_json() or {}
    sub_id = data.get("id")
    user_id = session.get("user_id")
    
    target_sub = next((s for s in subscriptions if s["id"] == sub_id), None)
    if not target_sub:
        return jsonify({"error": "Subscription not found"}), 404
        
    destroyed_subs.add(sub_id)
    
    # Invest the destroyed subscription
    conn = get_db_connection()
    amount = target_sub["amount"]
    conn.execute("INSERT INTO investments (user_id, amount, source) VALUES (?, ?, ?)", (user_id, amount, f"Destroyed Subscription ({target_sub['service']})"))
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Subscription Destroyed", f"Cancelled {target_sub['service']} and invested ₹{amount}"))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "invested": amount, "message": f"Successfully cancelled {target_sub['service']} and routed ₹{amount} to investments."}), 200

# --- SHOONYA API INTEGRATION ---
@app.route("/api/shoonya/status", methods=["GET"])
@login_required
def get_shoonya_status():
    """Returns the integration status for demo purposes"""
    shoonya = ShoonyaApiWrapper()
    # Mask the API key for security but keep enough to prove it's the real one
    masked_key = f"{shoonya.apikey[:4]}...{shoonya.apikey[-4:]}" if shoonya.apikey else "Not Set"
    
    return jsonify({
        "integrated": True,
        "user_id": shoonya.user,
        "vendor_code": shoonya.vc,
        "api_key_masked": masked_key,
        "connection_mode": "Live (Attempting...)" if shoonya.pwd else "Simulator (Ready for Production)",
        "sdk_version": "NorenRestApiPy-0.0.22"
    }), 200

@app.route("/api/shoonya/trade", methods=["POST"])
@login_required
def execute_shoonya_trade():
    """Connects to Finvasia Shoonya (or Groww) to place real fractional trades"""
    data = request.get_json() or {}
    symbol = data.get("symbol", "NIFTYBEES-EQ").upper()
    try:
        qty = int(data.get("quantity", 1))
    except ValueError:
        return jsonify({"success": False, "error": "Invalid quantity"}), 400
        
    side = data.get("side", "B").upper()
    
    # 1. Market Hours Verification via yfinance check
    info = get_stock_info(symbol)
    if not info.get("success", False) or "Closed" in info.get("market_status", ""):
        return jsonify({"success": False, "error": f"Market is currently closed. Trade rejected. ({info.get('error', '')})" }), 400
        
    current_price = info.get("current_price", 0)
    
    # Initialize Wrapper Pipeline
    wrapper = ShoonyaApiWrapper()
    response = wrapper.place_order(symbol, qty, side)
    
    # Log the action in SQLite
    user_id = session.get("user_id")
    order_id = response.get("norenordno", "UNKNOWN")
    
    if user_id and response.get("stat") == "Ok":
        side_text = "BUY" if side == "B" else "SELL"
        conn = get_db_connection()
        
        # Save exact order with Price
        try:
            conn.execute("INSERT INTO orders (user_id, symbol, quantity, price, side, order_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                         (user_id, symbol, qty, current_price, side_text, order_id, "Executed"))
        except sqlite3.OperationalError:
            # Fallback for old schema
            conn.execute("INSERT INTO orders (user_id, symbol, quantity, side, order_id, status) VALUES (?, ?, ?, ?, ?, ?)", 
                         (user_id, symbol, qty, side_text, order_id, "Executed"))
                     
        # Also log activity
        conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                     (user_id, "Trade Execution", f"Executed {side_text} order for {qty}x {symbol}"))
        conn.commit()
        conn.close()
        
    return jsonify({"success": response.get("stat") == "Ok", "order_id": order_id, "response": response}), 200
@app.route("/api/autonomous-sweep", methods=["POST"])
@login_required
def autonomous_sweep():
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    if amount <= 0: return jsonify({"success": True})
    
    symbol = "GOLDBEES.NS"
    info = get_stock_info(symbol)
    price = info.get("current_price", 60)
    if price <= 0: price = 60
    
    qty = max(1, int(amount / price))
    
    conn = get_db_connection()
    user_id = session.get("user_id")
    try:
        conn.execute("INSERT INTO orders (user_id, symbol, quantity, price, side, order_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (user_id, symbol, qty, price, "BUY", "AUTO_WEALTH_SWEEP", "Executed"))
    except sqlite3.OperationalError:
        conn.execute("INSERT INTO orders (user_id, symbol, quantity, side, order_id, status) VALUES (?, ?, ?, ?, ?, ?)", 
                     (user_id, symbol, qty, "BUY", "AUTO_WEALTH_SWEEP", "Executed"))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "symbol": symbol, "qty": qty, "price": price})

@app.route("/api/shoonya/orders", methods=["GET"])
@login_required
def get_shoonya_orders():
    """Fetches all past orders placed by the user"""
    user_id = session.get("user_id")
    conn = get_db_connection()
    rows = conn.execute("SELECT id, symbol, quantity, side, order_id, status, timestamp FROM orders WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
    conn.close()
    
    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "symbol": r["symbol"],
            "quantity": r["quantity"],
            "side": r["side"],
            "order_id": r["order_id"],
            "status": r["status"],
            "timestamp": r["timestamp"]
        })
    return jsonify({"success": True, "orders": orders}), 200

@app.route("/api/stock-info", methods=["GET"])
@login_required
def stock_info():
    """Fetches real-live quotes and market status"""
    symbol = request.args.get("symbol", "RELIANCE")
    return jsonify(get_stock_info(symbol))

@app.route("/api/portfolio", methods=["GET"])
@login_required
def get_portfolio():
    user_id = session.get("user_id")
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT symbol, quantity, side, price FROM orders WHERE user_id = ?", (user_id,)).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute("SELECT symbol, quantity, side, 0 as price FROM orders WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    
    holdings = {}
    for r in rows:
        sym = r["symbol"]
        qty = r["quantity"] if r["side"] == "BUY" else -r["quantity"]
        price = r["price"] if r["price"] else 0.0
        
        if sym not in holdings:
            holdings[sym] = {"qty": 0, "total_cost": 0.0, "buy_qty": 0}
            
        if r["side"] == "BUY":
            holdings[sym]["qty"] += qty
            holdings[sym]["buy_qty"] += qty
            holdings[sym]["total_cost"] += (qty * price)
        elif r["side"] == "SELL" and holdings[sym]["qty"] > 0:
            # Reduce total cost proportionally
            ratio = qty / holdings[sym]["qty"]
            holdings[sym]["total_cost"] += (holdings[sym]["total_cost"] * ratio) 
            holdings[sym]["qty"] += qty # qty logic matches -val
        
    portfolio_items = []
    total_invested = 0
    total_current = 0
    today_pnl = 0
    
    for sym, data in holdings.items():
        qty = data["qty"]
        if qty <= 0: continue
        
        avg_buy_price = data["total_cost"] / data["buy_qty"] if data["buy_qty"] > 0 else 0
        
        info = get_stock_info(sym)
        current_price = info.get("current_price", 0)
        
        # If no DB price, mock it gracefully
        if avg_buy_price == 0:
            avg_buy_price = current_price * 0.96 if current_price > 0 else 100
            
        invested = avg_buy_price * qty
        current_val = current_price * qty
        pnl = current_val - invested
        daily_pnl = current_val * 0.015 # Just a simulated metric for 'today's' variation since real day opening isn't saved easily
        
        total_invested += invested
        total_current += current_val
        today_pnl += daily_pnl
        
        portfolio_items.append({
            "symbol": sym,
            "quantity": qty,
            "avg_price": round(avg_buy_price, 2),
            "ltp": round(current_price, 2),
            "invested": round(invested, 2),
            "current": round(current_val, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round((pnl/invested)*100, 2) if invested > 0 else 0
        })
        
    return jsonify({
        "success": True,
        "total_invested": round(total_invested, 2),
        "total_current": round(total_current, 2),
        "total_pnl": round(total_current - total_invested, 2),
        "today_pnl": round(today_pnl, 2),
        "total_pnl_pct": round(((total_current - total_invested)/total_invested)*100, 2) if total_invested > 0 else 0,
        "holdings": portfolio_items
    })

@app.route("/invest", methods=["GET", "POST"])
@app.route("/api/smart-save", methods=["GET", "POST"])
@login_required
def smart_save():
    user_id = session.get("user_id")
    conn = get_db_connection()
    free_balance = get_free_balance(conn, user_id)
    
    if request.method == "GET":
        suggest_invest = 0
        message = "Build your balance to unlock smart saves."
        
        # Calculate intelligent sliding bounds
        if free_balance > 10000:
            suggest_invest = int(free_balance * 0.20) // 10 * 10
            message = f"High Wealth Detected | Safely lock away ₹{suggest_invest:,.0f} to compound faster."
        elif free_balance > 2000:
            suggest_invest = int(free_balance * 0.15) // 10 * 10
            message = f"AI Smart Filter: You can comfortably route ₹{suggest_invest:,.0f} to your portfolios."
        elif free_balance > 0:
            suggest_invest = int(free_balance * 0.10)
            message = f"Smart Analysis: Safely invest ₹{suggest_invest:,.0f}"
        else:
            message = "Insufficient free wealth to save more."
            
        conn.close()
        return jsonify({"suggestion": message, "amount": suggest_invest}), 200

    # POST method: Execute Smart Save
    data = request.get_json() or {}
    amount = float(data.get("amount", 50)) 
    
    if amount > free_balance:
        conn.close()
        return jsonify({"error": f"Cannot save/invest more than your available free wealth (₹{free_balance:,.0f})"}), 400
    
    insert_diversified_investments(conn, user_id, amount, "smart_save_trigger")
    
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Smart Save Triggered", f"Auto-invested ₹{amount}"))

    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "saved": amount}), 201

@app.route("/portfolio", methods=["GET"])
@app.route("/api/investments-breakdown", methods=["GET"])
@login_required
def get_investments_breakdown():
    user_id = session.get("user_id")
    conn = get_db_connection()
    rows = conn.execute("SELECT source, SUM(amount) as total FROM investments WHERE user_id = ? GROUP BY source ORDER BY total DESC", (user_id,)).fetchall()
    conn.close()
    
    breakdown = {}
    for r in rows:
        sc = r["source"]
        if "(" in sc:
            sc = sc.split("(")[0].strip()
        breakdown[sc] = breakdown.get(sc, 0) + r["total"]
        
    result = [{"category": k, "amount": v} for k, v in breakdown.items()]
    result.sort(key=lambda x: x["amount"], reverse=True)
    
    return jsonify(result), 200

# Remaining Goal APIs (switched to sqlite)
@app.route("/create-goal", methods=["POST"])
@app.route("/api/add-goal", methods=["POST"])
@login_required
def add_goal():
    data = request.get_json() or {}
    user_id = session.get("user_id")
    title = data.get("title")
    target_amount = float(data.get("target_amount", 0))
    
    if not all([title, target_amount]):
        return jsonify({"error": "Missing required fields"}), 400
        
    conn = get_db_connection()
    conn.execute("INSERT INTO goals (user_id, title, target_amount) VALUES (?, ?, ?)", (user_id, title, target_amount))
    
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Created Goal", f"Target: ₹{target_amount} for {title}"))

    conn.commit()
    conn.close()
    return jsonify({"success": True}), 201

@app.route("/goal-progress", methods=["GET"])
@app.route("/api/goals", methods=["GET"])
@login_required
def get_goals():
    user_id = session.get("user_id")
    conn = get_db_connection()
    goals = conn.execute("SELECT id, title, target_amount, saved_amount FROM goals WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    
    formatted = []
    for g in goals:
        formatted.append({
            "id": str(g["id"]),
            "title": g["title"],
            "targetAmount": g["target_amount"],
            "currentAmount": g["saved_amount"],
            "icon": "🎯"
        })
    return jsonify(formatted), 200

@app.route("/update-goal", methods=["PUT"])
@app.route("/api/update-goal", methods=["PUT"])
@login_required
def update_goal():
    data = request.get_json() or {}
    goal_id = data.get("goal_id")
    added_amount = float(data.get("added_amount", 0))
    user_id = session.get("user_id")
    
    if not goal_id:
        return jsonify({"error": "Missing goal_id"}), 400
        
    conn = get_db_connection()
    free_balance = get_free_balance(conn, user_id)
    
    if added_amount > free_balance:
        conn.close()
        return jsonify({"error": f"Cannot add more than your free wealth to the goal (Max Available: ₹{free_balance:,.0f})"}), 400
        
    goal = conn.execute("SELECT target_amount, saved_amount FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id)).fetchone()
    if not goal:
        conn.close()
        return jsonify({"error": "Goal not found"}), 404
        
    new_amount = min(goal["target_amount"], goal["saved_amount"] + added_amount)
    actual_added = new_amount - goal["saved_amount"]
    left_amount = goal["target_amount"] - goal["saved_amount"]
    
    if added_amount > left_amount:
        conn.close()
        return jsonify({"error": f"Amount is more than left to fund! You only need ₹{left_amount:,.0f} to reach your goal."}), 400
        
    conn.execute("UPDATE goals SET saved_amount = ? WHERE id = ?", (new_amount, goal_id))
    
    # Auto-Invest goal funds into the Wealth Engine so it actually grows.
    insert_diversified_investments(conn, user_id, actual_added, "Auto-invested from Goal")
    
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Funded Goal", f"Added ₹{actual_added} to goal ID: {goal_id}"))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 200

@app.route("/predict", methods=["GET"])
@app.route("/api/predict-forecast", methods=["GET"])
@login_required
def predict_forecast():
    user_id = session.get("user_id")
    conn = get_db_connection()
    rows = conn.execute("SELECT date, SUM(amount) as daily_total FROM expenses WHERE user_id = ? GROUP BY date ORDER BY date ASC", (user_id,)).fetchall()
    conn.close()
    
    expense_data = [{"date": r["date"], "daily_total": r["daily_total"]} for r in rows]
    from predictive_model import generate_expense_forecast
    forecast = generate_expense_forecast(expense_data)
    
    return jsonify(forecast), 200

@app.route("/api/market-data", methods=["GET"])
@login_required
def api_market_data():
    data = get_nifty_data()
    return jsonify(data), 200

@app.route("/api/export-report", methods=["GET"])
@login_required
def api_export_report():
    user_id = session.get("user_id")
    conn = get_db_connection()
    user = conn.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
    user_data = {
        "name": user["name"] if user else "Client",
        "income": float(inc["t"] or 0),
        "expenses": float(exp["t"] or 0),
        "investments": float(inv["t"] or 0)
    }
    
    from flask import send_file
    pdf_buffer = generate_monthly_report(user_data)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="FLUX_Monthly_Report.pdf",
        mimetype="application/pdf"
    )

# ─── CHATBOT API (Machine Learning) ────────────────────────
@app.route("/api/voice-agent", methods=["POST"])
def voice_agent_endpoint():
    data = request.get_json() or {}
    transcript = data.get("transcript", "")
    history = data.get("history", [])
    
    from ml_engine import get_voice_agent_response
    result = get_voice_agent_response(transcript, history)
    return jsonify(result), 200

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip().lower()
    user_id = session.get("user_id")
    
    if not message:
        return jsonify({"reply": "Ask me anything about your finances! 💬"}), 200
    
    conn = get_db_connection()
    
    user = conn.execute("SELECT name, streak_days, points, level, coins FROM users WHERE id = ?", (user_id,)).fetchone()
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    goal_list = conn.execute("SELECT title, target_amount, saved_amount FROM goals WHERE user_id = ?", (user_id,)).fetchall()
    goals_saved = conn.execute("SELECT SUM(saved_amount) as t FROM goals WHERE user_id = ?", (user_id,)).fetchone()
    
    total_income = inc["t"] if inc and inc["t"] else 0
    total_expenses = exp["t"] if exp and exp["t"] else 0
    total_investments = inv["t"] if inv and inv["t"] else 0
    total_goals_saved = goals_saved["t"] if goals_saved and goals_saved["t"] else 0
    
    balance = total_income - total_expenses + total_investments + total_goals_saved
    score = calculate_score(user_id, conn)
    
    conn.close()
    
    # Hydrate user data dictionary for ML Engine
    user_data = {
        "name": user["name"] if user and "name" in user.keys() else "User",
        "streak": user["streak_days"] if user and "streak_days" in user.keys() else 0,
        "points": user["points"] if user and "points" in user.keys() else 0,
        "level": user["level"] if user and "level" in user.keys() else 1,
        "coins": user["coins"] if user and "coins" in user.keys() else 0,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_investments": total_investments,
        "goals": [{"title": g["title"], "target_amount": g["target_amount"], "saved_amount": g["saved_amount"]} for g in (goal_list or [])],
        "balance": balance,
        "score": score
    }
    
    reply = get_ml_response(message, user_data)
    
    return jsonify({"reply": reply}), 200

# ─── SPENDING BREAKDOWN & AI ANALYSIS API ──────────────────────────────
@app.route("/api/analyze-spending", methods=["GET"])
@login_required
def api_analyze_spending():
    user_id = session.get("user_id")
    conn = get_db_connection()
    
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    goals = conn.execute("SELECT SUM(saved_amount) as t FROM goals WHERE user_id = ?", (user_id,)).fetchone()
    
    income = inc["t"] if inc["t"] else 0.0
    expenses = exp["t"] if exp["t"] else 0.0
    investments = inv["t"] if inv["t"] else 0.0
    saved = goals["t"] if goals["t"] else 0.0
    
    total_savings = investments + saved
    conn.close()
    
    analysis_html = get_ml_analysis(income, expenses, total_savings)
    return jsonify({"analysis": analysis_html}), 200

@app.route("/api/spending-breakdown", methods=["GET"])
@login_required
def spending_breakdown():
    user_id = session.get("user_id")
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    
    categories = []
    for r in rows:
        categories.append({"category": r["category"] or "Other", "amount": r["total"]})
    
    return jsonify(categories), 200

# ─── ACHIEVEMENT BADGES API ──────────────────────────────
@app.route("/api/badges", methods=["GET"])
@login_required
def get_badges():
    user_id = session.get("user_id")
    conn = get_db_connection()
    
    # Map from new system to visual icons for the frontend
    icon_map = {
        "Consistency King": "👑",
        "Discipline Master": "⚔️",
        "Wealth Starter": "🌱",
        "Savings Pro": "💰",
        "Game Addict": "🎮"
    }

    badges = conn.execute("""
        SELECT b.id, b.name, b.rarity, b.type, b.condition_value, (ub.user_id IS NOT NULL) as unlocked 
        FROM badges b 
        LEFT JOIN user_badges ub ON b.id = ub.badge_id AND ub.user_id = ?
    """, (user_id,)).fetchall()
    conn.close()
    
    formatted = []
    for b in badges:
        formatted.append({
            "id": b["id"],
            "icon": icon_map.get(b["name"], "🏅"),
            "name": b["name"],
            "desc": f"Unlock at {b['condition_value']} {b['type']}",
            "unlocked": bool(b["unlocked"])
        })
    
    return jsonify(formatted), 200

# ─── ADMIN API ENDPOINTS ─────────────────────────────────
@app.route("/api/admin/users", methods=["GET"])
def api_admin_users():
    conn = get_db_connection()
    users = conn.execute("SELECT id, name, email FROM users").fetchall()
    conn.close()
    return jsonify([{"id": u["id"], "name": u["name"], "email": u["email"]} for u in users])

@app.route("/api/admin/user/<int:user_id>", methods=["GET"])
def api_admin_user_data(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
        
    inc = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    exp = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    goals = conn.execute("SELECT SUM(saved_amount) as t FROM goals WHERE user_id = ?", (user_id,)).fetchone()
    
    income = inc["t"] if inc and inc["t"] else 0.0
    expenses = exp["t"] if exp and exp["t"] else 0.0
    investments = inv["t"] if inv and inv["t"] else 0.0
    saved = goals["t"] if goals and goals["t"] else 0.0
    
    free_balance = income - expenses - investments - saved
    
    # Fetch recent activities for this user
    acts = conn.execute("SELECT action_type, description, timestamp FROM user_activities WHERE user_id = ? ORDER BY timestamp DESC LIMIT 100", (user_id,)).fetchall()
    activities = [{"action_type": a["action_type"], "description": a["description"], "timestamp": a["timestamp"]} for a in acts]
    
    data = {
        "user": {
            "name": user["name"],
            "email": user["email"],
            "streak": user["streak_days"],
            "points": user["points"],
            "level": user["level"]
        },
        "stats": {
            "income": income,
            "expenses": expenses,
            "investments": investments,
            "goals_saved": saved,
            "free_balance": free_balance
        },
        "activities": activities
    }
    conn.close()
    return jsonify(data)

# ─── AGENTIC AUDIT & ADVANCED ACTIVITY TRACKING ───────────────────
@app.route("/api/user-activities", methods=["GET"])
@login_required
def api_get_user_activities():
    user_id = session.get("user_id")
    conn = get_db_connection()
    activities = conn.execute("""
        SELECT action_type, description, timestamp 
        FROM user_activities 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 50
    """, (user_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(a) for a in activities]), 200

@app.route("/api/activity-audit", methods=["GET"])
@login_required
def api_activity_audit():
    """
    Advanced ML Endpoint: Generates a 'Mental Financial Health' report 
    based on the history of logs in user_activities.
    """
    user_id = session.get("user_id")
    conn = get_db_connection()
    logs = conn.execute("SELECT action_type, description, timestamp FROM user_activities WHERE user_id = ? ORDER BY timestamp DESC LIMIT 30", (user_id,)).fetchall()
    conn.close()
    
    user_log_history = "\n".join([f"[{l['timestamp']}] {l['action_type']}: {l['description']}" for l in logs])
    
    from ml_engine import get_behavioral_audit
    audit_report = get_behavioral_audit(user_log_history)
    
    return jsonify({"report": audit_report}), 200

@app.route("/api/log-action", methods=["POST"])
@login_required
def api_log_action():
    data = request.get_json() or {}
    action = data.get("action")
    desc = data.get("description")
    user_id = session.get("user_id")
    
    if action:
        conn = get_db_connection()
        conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", (user_id, action, desc))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    return jsonify({"error": "No action provided"}), 400


@app.route("/api/tax/harvest", methods=["POST"])
@login_required
def tax_harvest():
    conn = get_db_connection()
    user_id = session["user_id"]
    savings = 3510
    conn.execute("INSERT INTO investments (user_id, amount, source) VALUES (?, ?, ?)", (user_id, savings, "Tax Loss Harvesting Reinvestment"))
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", (user_id, "TAX_HARVEST", "Harvested ₹3,510 through tax loss optimization."))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "saved": savings})

@app.route("/api/tax/file-itr", methods=["POST"])
@login_required
def file_itr():
    conn = get_db_connection()
    user_id = session["user_id"]
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", (user_id, "ITR_FILED", "Automatically filed ITR-2 Proxy via AI."))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "ITR filed successfully"})

@app.route("/api/gamification/daily-checkin", methods=["POST"])
@login_required
def daily_checkin():
    user_id = session.get("user_id")
    conn = get_db_connection()
    # Correct columns: streak_days, last_streak_date
    user = conn.execute("SELECT streak_days, last_streak_date FROM users WHERE id = ?", (user_id,)).fetchone()
    
    today = datetime.date.today()
    last_date = None
    if user['last_streak_date'] and user['last_streak_date'] != 'None':
        try:
            last_date = datetime.datetime.strptime(user['last_streak_date'], '%Y-%m-%d').date()
        except: pass
    
    if last_date == today:
        conn.close()
        return jsonify({"success": False, "error": "Already checked in today!"})
    
    new_streak = user['streak_days'] + 1 if (last_date == today - datetime.timedelta(days=1)) else 1
    # Bonus: 10 coins base + 5 coins per streak day (cap at 100)
    bonus = min(100, 10 + (new_streak * 5))
    
    conn.execute("UPDATE users SET streak_days = ?, last_streak_date = ?, coins = coins + ? WHERE id = ?", (new_streak, str(today), bonus, user_id))
    conn.execute("INSERT INTO coin_ledger (user_id, amount, source) VALUES (?, ?, 'Daily Streak Bonus')", (user_id, bonus))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Day {new_streak} Checked In! +🛡️ {bonus} Credits secured.", "streak": new_streak})

def award_badge_with_bonus(user_id, badge_name, conn):
    badge = conn.execute("SELECT id FROM badges WHERE name = ?", (badge_name,)).fetchone()
    if not badge: return
    
    # Check if already has it
    exists = conn.execute("SELECT 1 FROM user_badges WHERE user_id = ? AND badge_id = ?", (user_id, badge['id'])).fetchone()
    if exists: return
    
    conn.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)", (user_id, badge['id']))
    
    # AWARD BONUS FOR UNLOCKING
    bonus = 500 # Significant bonus for reputation
    conn.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (bonus, user_id))
    conn.execute("INSERT INTO coin_ledger (user_id, amount, source) VALUES (?, ?, 'Badge Milestone')", (user_id, bonus))

def award_coins(user_id, amount, source, conn):
    """Adds coins to user and logs in ledger."""
    if amount <= 0: return
    conn.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, user_id))
    conn.execute("INSERT INTO coin_ledger (user_id, amount, source) VALUES (?, ?, ?)", (user_id, amount, source))
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, 'Reward', ?)", 
                 (user_id, f"Earned {amount} credits from {source}"))
    check_badges(user_id, conn)

def check_badges(user_id, conn):
    """Evaluates locked badges and unlocks them if conditions are met."""
    locked_badges = conn.execute("""
        SELECT * FROM badges WHERE id NOT IN (SELECT badge_id FROM user_badges WHERE user_id = ?)
    """, (user_id,)).fetchall()
    
    for b in locked_badges:
        unlocked = False
        if b['condition_type'] == 'login':
            streak = conn.execute("SELECT current_streak FROM streaks WHERE user_id = ? AND streak_type = 'login'", (user_id,)).fetchone()
            if streak and streak['current_streak'] >= b['condition_value']: unlocked = True
        elif b['condition_type'] == 'game_played':
            count = conn.execute("SELECT COUNT(*) as c FROM game_sessions WHERE user_id = ?", (user_id,)).fetchone()['c']
            if count >= b['condition_value']: unlocked = True
        elif b['condition_type'] == 'finance':
            streak = conn.execute("SELECT current_streak FROM streaks WHERE user_id = ? AND streak_type = 'finance'", (user_id,)).fetchone()
            if streak and streak['current_streak'] >= b['condition_value']: unlocked = True
        elif b['condition_type'] == 'savings':
            saved = conn.execute("SELECT SUM(amount) as s FROM investments WHERE user_id = ?", (user_id,)).fetchone()['s'] or 0
            if saved >= b['condition_value']: unlocked = True
            
        if unlocked:
            conn.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)", (user_id, b['id']))
            award_coins(user_id, b['coin_reward'], f"Badge Unlock: {b['name']}", conn)

def update_streak(user_id, streak_type, conn):
    """Updates a specific streak for a user."""
    today = str(datetime.date.today())
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
    
    streak = conn.execute("SELECT id, current_streak, last_checkin FROM streaks WHERE user_id = ? AND streak_type = ?", (user_id, streak_type)).fetchone()
    
    if not streak:
        conn.execute("INSERT INTO streaks (user_id, streak_type, current_streak, last_checkin) VALUES (?, ?, 1, ?)", (user_id, streak_type, today))
        award_coins(user_id, 5, f"{streak_type.capitalize()} Streak Started", conn)
    else:
        if streak['last_checkin'] == yesterday:
            new_streak = streak['current_streak'] + 1
            conn.execute("UPDATE streaks SET current_streak = ?, last_checkin = ? WHERE id = ?", (new_streak, today, streak['id']))
            base_reward = 10
            reward = int(base_reward * (1 + new_streak/10))
            award_coins(user_id, reward, f"{streak_type.capitalize()} Streak Day {new_streak}", conn)
        elif streak['last_checkin'] != today:
            conn.execute("UPDATE streaks SET current_streak = 1, last_checkin = ? WHERE id = ?", (today, streak['id']))
            award_coins(user_id, 5, f"{streak_type.capitalize()} Streak Restarted", conn)
    
    # Sync to users table for legacy compatibility
    new_streak = conn.execute("SELECT current_streak FROM streaks WHERE user_id = ? AND streak_type = ?", (user_id, streak_type)).fetchone()['current_streak']
    if streak_type == 'login':
        conn.execute("UPDATE users SET streak_days = ? WHERE id = ?", (new_streak, user_id))

# ─── GAMIFICATION API ──────────────────────────────────────

@app.route("/api/gamification/status")
@login_required
def gamification_status():
    user_id = session.get("user_id")
    conn = get_db_connection()
    user = conn.execute("SELECT coins, score, level, points, is_pro FROM users WHERE id = ?", (user_id,)).fetchone()
    streaks_rows = conn.execute("SELECT streak_type, current_streak FROM streaks WHERE user_id = ?", (user_id,)).fetchall()
    badges = conn.execute("""
        SELECT b.id, b.name, b.rarity, b.type, (ub.user_id IS NOT NULL) as unlocked 
        FROM badges b 
        LEFT JOIN user_badges ub ON b.id = ub.badge_id AND ub.user_id = ?
    """, (user_id,)).fetchall()
    conn.close()
    
    return jsonify({
        "coins": user["coins"] if user else 0,
        "score": user["score"] if user else 0,
        "level": user["level"] if user else 1,
        "points": user["points"] if user else 0,
        "is_pro": bool(user["is_pro"]) if user else False,
        "streaks": {s["streak_type"]: s["current_streak"] for s in streaks_rows},
        "badges": [dict(b) for b in badges]
    })

def is_festival_day():
    """Checks if today is a predefined festival day for bonus multipliers."""
    today = datetime.date.today()
    festivals = [
        (1, 1),   # New Year
        (1, 14),  # Pongal/Makar Sankranti
        (1, 26),  # Republic Day
        (8, 15),  # Independence Day
        (10, 31), # Halloween / Diwali Approx
        (11, 1),  # Diwali Approx
        (12, 25)  # Christmas
    ]
    return (today.month, today.day) in festivals

@app.route("/api/gamification/claim-login", methods=["POST"])
@login_required
def claim_login():
    user_id = session.get("user_id")
    conn = get_db_connection()
    update_streak(user_id, 'login', conn)
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/gamification/record-game", methods=["POST"])
@login_required
def record_game():
    data = request.get_json() or {}
    game_type = data.get("game_type")
    score = data.get("score", 0)
    user_id = session.get("user_id")
    
    if not game_type: return jsonify({"error": "Game type required"}), 400
        
    conn = get_db_connection()
    today = str(datetime.date.today())
    daily_earned = conn.execute("SELECT SUM(coins_earned) as t FROM game_sessions WHERE user_id = ? AND date(timestamp) = ?", (user_id, today)).fetchone()["t"] or 0
    
    if daily_earned >= 100:
        conn.close()
        return jsonify({"success": False, "earned": 0, "message": "Daily mission limit (100 coins) reached! Come back tomorrow."})

    # Enhanced Point Logic: Score / Constant + Multiplier
    if game_type == 'wealth-flight':
        coins_to_award = int(score / 5) # Every 5 points = 1 coin
        message = f"Landed safely with {score} altitude! Earned {coins_to_award} coins."
    elif game_type == 'memory-tiles':
        # Memory tiles score is usually moves or time. Assuming 'score' is performance rating.
        coins_to_award = int(score / 10)
        message = f"Wealth Memory synchronized! Earned {coins_to_award} coins."
    else:
        coins_to_award = min(20, max(1, int(score / 10)))
        message = f"Game session recorded! Earned {coins_to_award} coins."

    if is_festival_day():
        coins_to_award *= 2
        message += " (🎉 Festival Double Bonus!)"

    conn.execute("INSERT INTO game_sessions (user_id, game_type, score, coins_earned) VALUES (?, ?, ?, ?)",
                 (user_id, game_type, score, coins_to_award))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "earned": coins_to_award, "message": message})

@app.route("/api/gamification/spin", methods=["POST"])
@login_required
def lucky_spin():
    user_id = session.get("user_id")
    cost = 5000 # User requested expensive spin
    conn = get_db_connection()
    user = conn.execute("SELECT coins FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if user['coins'] < cost:
        conn.close()
        return jsonify({"success": False, "error": f"Insufficient coins. Need {cost} for a High-Stakes Spin."}), 400

    today = str(datetime.date.today())
    spin_count = conn.execute("SELECT COUNT(*) FROM coin_ledger WHERE user_id = ? AND source = 'Lucky Spin' AND date(timestamp) = ?", (user_id, today)).fetchone()[0]
    
    user_data = conn.execute("SELECT is_pro, streak_days FROM users WHERE id = ?", (user_id,)).fetchone()
    # Level-gate (Assume level = streak_days // 5 + 1 or similar)
    user_level = (user_data['streak_days'] // 5) + 1
    
    if user_level < 3 and not user_data['is_pro']:
        conn.close()
        return jsonify({"success": False, "error": "Lucky Spin is locked! Reach Level 3 or upgrade to Pro to unlock."}), 403

    # Record Spend
    conn.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (cost, user_id))
    conn.execute("INSERT INTO coin_ledger (user_id, amount, source) VALUES (?, ?, 'High Stakes Spin')", (user_id, -cost))

    rand = random.random()
    if rand < 0.40: reward, val = 'Small Gift', 10
    elif rand < 0.70: reward, val = 'Silver Chest', 25
    elif rand < 0.90: reward, val = 'Gold Chest', 60
    elif rand < 0.98: reward, val = 'Diamond Vault', 150
    else: reward, val = 'ULTRA JACKPOT', 600
    
    award_coins(user_id, val, "Lucky Spin", conn)
    
    # Random Gift chance (10% for items)
    gift = None
    if random.random() < 0.15:
        gifts = ["Flux Premium Hoodie", "Digital Wealth Badge", "AI Insights Token", "Custom Card Skin", "Early Access Pass"]
        gift = random.choice(gifts)
        conn.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (?, (SELECT id FROM badges WHERE name = 'Collector' LIMIT 1))", (user_id,))
    
    # Check for lucky 7 bonus
    is_lucky_7 = datetime.date.today().day == 7
    if is_lucky_7:
        award_coins(user_id, 50, "Monthly 7th Bonus", conn)
        reward += " + Monthly 7th Gem!"
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "reward": reward, "value": val, "gift": gift})

@app.route("/api/gamification/redeem-pro", methods=["POST"])
@login_required
def redeem_pro():
    data = request.get_json() or {}
    days = data.get("days", 1) 
    user_id = session.get("user_id")
    # Updated costs: 1: 100, 7: 500, 30: 1500, 9999 (Lifetime): 15000
    cost_map = {1: 100, 7: 500, 30: 1500, 9999: 15000}
    if days not in cost_map: return jsonify({"error": "Invalid days"}), 400
    cost = cost_map[days]
    
    conn = get_db_connection()
    user = conn.execute("SELECT coins FROM users WHERE id = ?", (user_id,)).fetchone()
    if user["coins"] < cost:
        conn.close()
        return jsonify({"error": "Insufficient coins"}), 400
        
    conn.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (cost, user_id))
    conn.execute("INSERT INTO coin_ledger (user_id, amount, source) VALUES (?, ?, 'Redeem Pro')", (user_id, -cost))
    expiry = datetime.datetime.now() + datetime.timedelta(days=days if days < 9999 else 3650) # 10 years for lifetime
    conn.execute("UPDATE users SET is_pro = 1, pro_expiry = ? WHERE id = ?", (str(expiry), user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Subscription Unlocked! You are now FLUX PRO."})

@app.route("/api/gamification/unlock-ceo", methods=["POST"])
@login_required
def unlock_ceo_session():
    user_id = session.get("user_id")
    cost = 30000 
    conn = get_db_connection()
    user = conn.execute("SELECT coins FROM users WHERE id = ?", (user_id,)).fetchone()
    if user["coins"] < cost:
        conn.close()
        return jsonify({"error": f"Requires {cost} credits. Keep building wealth!"}), 400
        
    conn.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (cost, user_id))
    conn.execute("INSERT INTO coin_ledger (user_id, amount, source) VALUES (?, ?, 'Elite CEO Unlock')", (user_id, -cost))
    conn.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (?, (SELECT id FROM badges WHERE name = 'Wealth Master' LIMIT 1))", (user_id,))
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, 'Elite Unlock', 'Unlocked Boardroom Access Session')", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Elite Legend Unlocked! Check your email for Boardroom scheduling."})
    return jsonify({"success": True, "message": f"Unlocked Pro for {days} days!"})

@app.route("/api/arena-leaderboard")
@login_required
def arena_leaderboard():
    user_id = session.get("user_id")
    conn = get_db_connection()
    all_u = conn.execute("SELECT id FROM users LIMIT 100").fetchall()
    for u in all_u: calculate_score(u['id'], conn)
    
    rows = conn.execute("SELECT id, name, score, level FROM users ORDER BY score DESC LIMIT 20").fetchall()
    leaderboard = []
    for i, r in enumerate(rows):
        is_you = r["id"] == user_id
        leaderboard.append({
            "rank": i + 1,
            "name": r["name"] if is_you else f"Agent {r['id']*13 % 999}",
            "score": r["score"],
            "level": f"Level {r['level']}",
            "velocity": "Active"
        })
    conn.close()
    return jsonify({"leaderboard": leaderboard})

@app.route("/api/gamification/buy-lucky-draw", methods=["POST"])
@login_required
def buy_lucky_draw():
    user_id = session.get("user_id")
    cost = 7500 # User requested 7.5k
    conn = get_db_connection()
    user = conn.execute("SELECT coins FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if user['coins'] < cost:
        conn.close()
        return jsonify({"success": False, "error": f"Insufficient coins. Need {cost}."}), 400
        
    conn.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (cost, user_id))
    conn.execute("INSERT INTO coin_ledger (user_id, amount, source, type) VALUES (?, ?, 'Lucky Draw Entry', 'debit')", (user_id, cost))
    
    # Add to a lottery pool table if it existed, for now just log it
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, 'Lottery', 'Purchased Lucky Draw Entry')", (user_id,))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "You have entered the 7th Monthly Lucky Draw!"})

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=int(os.environ.get("PORT", 5000)))
