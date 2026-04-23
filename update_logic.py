import re

# UPDATE STATEMENT ANALYZER LOGIC TO 30% ETF RETURNS
target1 = "backend/statement_analyzer.py"
with open(target1, "r") as f:
    s_cont = f.read()

s_cont = s_cont.replace("1.12 ** years_ago", "1.30 ** years_ago")
s_cont = s_cont.replace("real_current_value * (1.12 ** 3)", "real_current_value * (1.30 ** 3)")

with open(target1, "w") as f:
    f.write(s_cont)

# UPDATE MASTER ANALYTICS
target2 = "frontend/analytics_overview.html"
with open(target2, "r") as f:
    a_cont = f.read()

# Fix the Fetch to safely capture session cookies just in case
a_cont = a_cont.replace('fetch("/api/analyze-statement", { method: "POST" });', 'fetch("/api/analyze-statement", { method: "POST", credentials: "same-origin" });')
a_cont = a_cont.replace('Math.pow(1.12, i/2)', 'Math.pow(1.30, i/2)')

with open(target2, "w") as f:
    f.write(a_cont)

print("Updated returns to 30% and fixed JS fetch logic")
