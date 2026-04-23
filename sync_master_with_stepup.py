import os

target = "frontend/analytics_overview.html"
with open(target, "r") as f:
    text = f.read()

# Update the SIP loop in analytics_overview.html to include the 8% Step-up (Inflation/Hike adjustment)
old_loop = """     let total_invested = 0;
     for(let i=1; i<=10; i++) { 
         total_invested += annualVelocity;
         accumulated_fv = (accumulated_fv + annualVelocity) * 1.30;
         f1.push(total_invested);
         f2.push(accumulated_fv); 
     }"""

new_loop = """     let total_invested = 0;
     let current_annual_contrib = annualVelocity;
     let current_stock = currentTotalWealth;
     for(let i=1; i<=10; i++) { 
         total_invested += current_annual_contrib;
         // End of year compounding: Old stock grows + new contribution added
         current_stock = (current_stock * 1.30) + current_annual_contrib;
         
         f1.push(total_invested);
         f2.push(current_stock); 
         
         // Increase contribution by 8% (Step-up/Inflation/Salary adjustment)
         current_annual_contrib *= 1.08;
     }
     accumulated_fv = current_stock;"""

if old_loop in text:
    text = text.replace(old_loop, new_loop)
    with open(target, "w") as f:
        f.write(text)
    print("Updated Master Analytics with Step-up SIP logic")
else:
    print("Could not find loop to replace")
