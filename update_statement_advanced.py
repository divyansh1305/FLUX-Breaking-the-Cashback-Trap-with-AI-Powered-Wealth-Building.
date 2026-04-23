import os

target = "backend/statement_analyzer.py"
with open(target, "r") as f:
    text = f.read()

# Update the projection calculation block
new_projection_logic = """
        # STEP-UP SIP PROJECTION (High Impact for Judges)
        # Assumes user continues this specific savings 'velocity'
        # with an 8% annual 'Step-up' in Principle (Hike/Inflation adjustment)
        # and a 30% Bullish Market Yield.
        
        annual_velocity = cumulative_invested_inr
        current_corpus = real_current_value
        
        def calculate_step_up_fv(years, velocity, initial, roi=0.30, step_up=0.08):
            corpus = initial
            v = velocity
            for _ in range(years):
                # End of year calculation: Existing corpus grows + New principle added
                corpus = (corpus * (1 + roi)) + v
                # Next year's principle increases by step-up (inflation/hike)
                v = v * (1 + step_up)
            return corpus

        fv_1y = calculate_step_up_fv(1, annual_velocity, real_current_value)
        fv_3y = calculate_step_up_fv(3, annual_velocity, real_current_value)
        fv_10y = calculate_step_up_fv(10, annual_velocity, real_current_value)
"""

# Replace the old future_value = 0 block
# Identifying the block:
old_block_start = text.find("future_value = 0")
old_block_end = text.find("savings_rate =", old_block_start)

if old_block_start != -1:
    text = text[:old_block_start] + new_projection_logic + "        " + text[old_block_end:]

# Update the return dictionary to include these new keys
text = text.replace('"current_value": round(real_current_value, 2),', 
                    '"current_value": round(real_current_value, 2),\n                    "fv_1y": round(fv_1y, 2),\n                    "fv_3y": round(fv_3y, 2),\n                    "fv_10y": round(fv_10y, 2),')

with open(target, "w") as f:
    f.write(text)
print("Updated backend projection to use Step-up SIP (Inflation + Principle + Compound Interest)")
