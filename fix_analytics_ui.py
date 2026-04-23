import re

target2 = "frontend/analytics_overview.html"
with open(target2, "r") as f:
    a_cont = f.read()

# Make the Total Principal Intercepted mathematically perfectly match "extractedSpend"
a_cont = a_cont.replace(
    "document.querySelectorAll('.m-value')[0].innerText = '₹ ' + Math.round(extractedSpend + insIntercept + fluxCashback).toLocaleString('en-IN');",
    "document.querySelectorAll('.m-value')[0].innerText = '₹ ' + Math.round(extractedSpend).toLocaleString('en-IN');"
)

# And explicitly make Total extracted prominently labelled to ease user confusion
a_cont = a_cont.replace(
    "document.querySelectorAll('.b-val')[0].innerText = '₹ ' + Math.round(extractedSpend).toLocaleString('en-IN');",
    "document.querySelectorAll('.b-val')[0].innerText = '₹ ' + Math.round(extractedSpend).toLocaleString('en-IN'); document.querySelector('.b-name').innerText = 'Statement CSV Auto-Invest';"
)

with open(target2, "w") as f:
    f.write(a_cont)

print("UI labels heavily clarified for clarity")
