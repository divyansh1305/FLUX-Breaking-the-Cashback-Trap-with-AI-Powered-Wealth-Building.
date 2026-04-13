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

from database import init_db, get_db_connection
from ml_engine import get_ml_response, get_ml_analysis
from predictive_model import generate_expense_forecast
from report_generator import generate_monthly_report
from market_data import get_nifty_data

# --- SETUP AND CONFIGURATION ---
load_dotenv()

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

@app.route("/analytics")
@app.route("/analytics.html")
@login_required
def analytics():
    return render_template("analytics.html")

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
                  <div style="background-color: rgba(124, 92, 191, 0.1); border: 2px dashed #7c5cbf; border-radius: 12px; padding: 20px; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #9b79e0; margin-bottom: 30px;">
                    {otp}
                  </div>
                </div>
              </body>
            </html>
            """
            msg.set_content(f"Your Flux Wealth OTP is: {otp}")
            msg.add_alternative(html_content, subtype='html')

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
                
        except Exception as e:
            print(f"Failed to send real email: {e}")
    else:
        print(f"\n{'='*40}")
        print(f"MOCK EMAIL SENT To: {email} | OTP: {otp}")
        print(f"{'='*40}\n")

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

@app.route("/api/user-activities", methods=["GET"])
@login_required
def get_user_activities():
    user_id = session.get("user_id")
    conn = get_db_connection()
    rows = conn.execute("SELECT action_type, description, timestamp FROM user_activities WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50", (user_id,)).fetchall()
    conn.close()
    
    activities = []
    for r in rows:
        activities.append({
            "action_type": r["action_type"],
            "description": r["description"],
            "timestamp": r["timestamp"]
        })
    return jsonify(activities), 200

@app.route("/api/user")
@login_required
def api_user():
    return jsonify({
        "name": session.get("user_name"),
        "email": session.get("user_email")
    })

# --- DATA API ENDPOINTS (SQLite) ---

def calculate_score(user_id, conn):
    # Phase 2: Wealth Score Engine
    # Formula Mock: Base score + points + streak + wealth velocity
    user = conn.execute("SELECT income, points, streak_days FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user: return 0
    
    # Calculate savings rate
    inc_res = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    total_income = inc_res["t"] if inc_res and inc_res["t"] else 0.0
    
    inv_res = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    total_investments = inv_res["t"] if inv_res and inv_res["t"] else 0.0
    
    velocity = (total_investments / total_income) * 100 if total_income > 0 else 0
    
    score = int(300 + (user["streak_days"] * 20) + (user["points"] * 5) + (velocity * 10))
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
    balance = total_income - total_expenses
    # Total wealth: Cash + value stored in goals (investments are already part of expenses)
    total_wealth = balance + total_goals
    
    velocity = (total_investments / total_income) * 100 if total_income > 0 else 0
    
    # Simple Insight logic attached to dashboard as well
    insights = []
    if total_expenses > total_income and total_income > 0:
        insights.append("You're overspending")
    elif total_income > 0 and total_investments > 0 and (total_investments/total_income) > 0.1:
        insights.append("Great financial discipline")
    elif total_investments == 0:
        insights.append("Start investing mechanically via auto-save.")
        
    # Financial Persona & Projections Engine
    try:
        rows = conn.execute("SELECT amount, date FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10", (user_id,)).fetchall()
        import datetime as dt
        weekend_spend = sum(r["amount"] for r in rows if dt.datetime.strptime(r["date"], "%Y-%m-%d").weekday() >= 5)
        weekday_spend = sum(r["amount"] for r in rows if dt.datetime.strptime(r["date"], "%Y-%m-%d").weekday() < 5)
        persona = "Weekend Spender" if weekend_spend > weekday_spend and weekend_spend > 0 else "Disciplined Saver"
        projected_monthly_savings = max(0, total_income - (total_expenses * (30/max(1, len(rows)))) if rows else total_income * 0.2)
    except:
        persona = "Balanced Saver"
        projected_monthly_savings = 12500

    conn.close()
    
    return jsonify({
        "income": total_income,
        "expenses": total_expenses,
        "investments": total_investments,
        "savings": total_goals,
        "balance": balance,
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
    conn.close()
    
    total_inc = inc["t"] if inc["t"] else 0.0
    total_exp = exp["t"] if exp["t"] else 0.0
    
    is_overspending = False
    if total_inc > 0 and (total_exp + amount) > (total_inc * 0.9):
        is_overspending = True

    score_drop = int(amount * 0.01)
    goal_delay = int(amount / 500)
    
    return jsonify({
        "score_drop": score_drop,
        "goal_delay": goal_delay,
        "is_overspending": is_overspending,
        "message": f"This expense will temporarily reduce your FLUX Score potential by {score_drop} points and delay your active goal target by ~{goal_delay} days."
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
    
    # 2. Auto-Invest Logic (Phase 1)
    cashback_equivalent = amount * 0.05
    insert_diversified_investments(conn, user_id, cashback_equivalent, "cashback_conversion")
    
    # Gamification Tracking (Strict daily increment logic)
    user = conn.execute("SELECT streak_days, points, level, last_streak_date FROM users WHERE id = ?", (user_id,)).fetchone()
    streak = user["streak_days"]
    points = user["points"]
    level = user["level"]
    last_date = user["last_streak_date"]
    
    # Track today's date
    today_str = str(datetime.date.today())
    
    # Check if budget is sound
    exp_res = conn.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    inc_res = conn.execute("SELECT SUM(amount) as t FROM income WHERE user_id = ?", (user_id,)).fetchone()
    tot_exp = exp_res["t"] if exp_res and exp_res["t"] else 0
    tot_inc = inc_res["t"] if inc_res and inc_res["t"] else 0
    
    # Only increment if first time today AND budget is under control
    if today_str != last_date and tot_exp <= tot_inc:
        streak += 1
        points += 10
        if points >= 100:
            level += 1
            points = 0
        conn.execute("UPDATE users SET streak_days = ?, points = ?, level = ?, last_streak_date = ? WHERE id = ?", 
                    (streak, points, level, today_str, user_id))
    else:
        # Just update points if already had streak today? Or just commit other changes.
        # User explicitly asked to only increment ONCE a day.
        pass
        
    # Log User Activity
    conn.execute("INSERT INTO user_activities (user_id, action_type, description) VALUES (?, ?, ?)", 
                 (user_id, "Added Expense", f"₹{amount} for {category} (Auto-invested ₹{cashback_equivalent})"))
            
    conn.commit()
    conn.close()

    return jsonify({"success": True, "invested": cashback_equivalent}), 201

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
def get_gamification():
    # Phase 5: Gamification Engine
    user_id = session.get("user_id")
    conn = get_db_connection()
    user = conn.execute("SELECT streak_days, points, level FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        return jsonify({
            "streak_days": user["streak_days"],
            "points": user["points"],
            "level": user["level"]
        }), 200
    return jsonify({"error": "User not found"}), 404

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
        if free_balance > 2000:
            suggest_invest = 1000
            message = f"You can invest ₹{suggest_invest:,.0f} safely"
        elif free_balance > 0:
            suggest_invest = free_balance * 0.1
            message = f"You can safely invest ₹{suggest_invest:,.0f}"
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
    
    conn.execute("UPDATE goals SET saved_amount = ? WHERE id = ?", (new_amount, goal_id))
    
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
@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip().lower()
    user_id = session.get("user_id")
    
    if not message:
        return jsonify({"reply": "Ask me anything about your finances! 💬"}), 200
    
    conn = get_db_connection()
    
    user = conn.execute("SELECT name, streak_days, points, level FROM users WHERE id = ?", (user_id,)).fetchone()
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
        "name": user["name"] if user else "User",
        "streak": user["streak_days"] if user else 0,
        "points": user["points"] if user else 0,
        "level": user["level"] if user else 1,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_investments": total_investments,
        "goals": [{"title": g["title"], "target_amount": g["target_amount"], "saved_amount": g["saved_amount"]} for g in goal_list],
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
    
    user = conn.execute("SELECT streak_days, points, level FROM users WHERE id = ?", (user_id,)).fetchone()
    inv = conn.execute("SELECT SUM(amount) as t FROM investments WHERE user_id = ?", (user_id,)).fetchone()
    exp_count = conn.execute("SELECT COUNT(*) as c FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    inc_count = conn.execute("SELECT COUNT(*) as c FROM income WHERE user_id = ?", (user_id,)).fetchone()
    goal_count = conn.execute("SELECT COUNT(*) as c FROM goals WHERE user_id = ?", (user_id,)).fetchone()
    
    total_inv = inv["t"] if inv and inv["t"] else 0
    streak = user["streak_days"] if user else 0
    points = user["points"] if user else 0
    level = user["level"] if user else 1
    expenses = exp_count["c"] if exp_count else 0
    incomes = inc_count["c"] if inc_count else 0
    goals = goal_count["c"] if goal_count else 0
    
    conn.close()
    
    badges = [
        {"id": "first_income", "icon": "💵", "name": "First Earnings", "desc": "Logged your first income", "unlocked": incomes >= 1},
        {"id": "first_expense", "icon": "🧾", "name": "Expense Tracker", "desc": "Logged your first expense", "unlocked": expenses >= 1},
        {"id": "first_invest", "icon": "🌱", "name": "Seed Planted", "desc": "First auto-investment triggered", "unlocked": total_inv > 0},
        {"id": "streak_3", "icon": "🔥", "name": "On Fire", "desc": "3-day no-overspending streak", "unlocked": streak >= 3},
        {"id": "streak_7", "icon": "⚡", "name": "Unstoppable", "desc": "7-day streak achieved", "unlocked": streak >= 7},
        {"id": "goal_setter", "icon": "🎯", "name": "Goal Setter", "desc": "Created your first wealth goal", "unlocked": goals >= 1},
        {"id": "inv_1k", "icon": "💎", "name": "Diamond Hands", "desc": "Auto-invested over ₹1,000", "unlocked": total_inv >= 1000},
        {"id": "inv_5k", "icon": "🚀", "name": "Wealth Rocket", "desc": "Auto-invested over ₹5,000", "unlocked": total_inv >= 5000},
        {"id": "inv_10k", "icon": "👑", "name": "Wealth King", "desc": "Auto-invested over ₹10,000", "unlocked": total_inv >= 10000},
        {"id": "level_3", "icon": "🏆", "name": "Level 3 Pro", "desc": "Reached Level 3", "unlocked": level >= 3},
        {"id": "expense_10", "icon": "📊", "name": "Data Driven", "desc": "Tracked 10+ expenses", "unlocked": expenses >= 10},
        {"id": "points_50", "icon": "⭐", "name": "Star Player", "desc": "Earned 50+ points", "unlocked": points >= 50},
    ]
    
    return jsonify(badges), 200

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
