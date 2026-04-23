import os

target = "frontend/smart-analyzer.html"
with open(target, "r") as f:
    text = f.read()

# Update the JS projection block to use the backend's new keys
old_js = """                // ETF Projections Engine
                const invested = analysis.cashback_journey.generated_from_spends;
                document.getElementById('etf-invested').innerText = formatCur(invested);
                document.getElementById('etf-1y').innerText = formatCur(invested * Math.pow(1.12, 1));
                document.getElementById('etf-3y').innerText = formatCur(invested * Math.pow(1.12, 3));
                document.getElementById('etf-10y').innerText = formatCur(invested * Math.pow(1.12, 10));"""

new_js = """                // ETF Projections Engine (Wired to High-Impact Step-up SIP Backend)
                const cj = analysis.cashback_journey;
                document.getElementById('etf-invested').innerText = formatCur(cj.current_value);
                document.getElementById('etf-1y').innerText = formatCur(cj.fv_1y);
                document.getElementById('etf-3y').innerText = formatCur(cj.fv_3y);
                document.getElementById('etf-10y').innerText = formatCur(cj.fv_10y);"""

text = text.replace(old_js, new_js)

with open(target, "w") as f:
    f.write(text)
print("Updated frontend analyzer to show Step-up SIP projections")
