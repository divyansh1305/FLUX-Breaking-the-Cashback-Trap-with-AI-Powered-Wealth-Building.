from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from io import BytesIO
from datetime import datetime

def generate_monthly_report(user_data):
    """
    Generates a professional PDF Monthly Financial Report.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(0.1, 0.1, 0.5)
    c.drawString(50, height - 50, "FLUX: Wealth Engine Report")
    
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(50, height - 70, f"Generated on: {datetime.now().strftime('%B %d, %Y')}")
    
    # User Details
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, f"Client Profile: {user_data.get('name', 'User')}")
    
    c.setFont("Helvetica", 12)
    y = height - 150
    c.drawString(50, y, f"Total Income Logged: INR {user_data.get('income', 0):,.2f}")
    c.drawString(50, y - 20, f"Total Expenses: INR {user_data.get('expenses', 0):,.2f}")
    c.drawString(50, y - 40, f"Flux Auto-Invested (Shoonya): INR {user_data.get('investments', 0):,.2f}")
    
    # Financial Health
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y - 80, "Financial Health Analysis")
    c.setFont("Helvetica", 12)
    
    spend_ratio = 0
    if user_data.get('income', 0) > 0:
        spend_ratio = (user_data.get('expenses', 0) / user_data.get('income', 1)) * 100
        
    c.drawString(50, y - 100, f"Expense Ratio: {spend_ratio:.1f}%")
    
    profile_tag = "Disciplined Saver"
    if spend_ratio > 80: profile_tag = "High Spender"
    elif spend_ratio < 40: profile_tag = "Aggressive Investor"
    
    c.drawString(50, y - 120, f"AI Profile Tag: {profile_tag}")
    
    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 50, "Powered by FLUX | Finvasia Integration Simulated")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer
