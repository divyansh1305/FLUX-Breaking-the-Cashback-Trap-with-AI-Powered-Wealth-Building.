from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from io import BytesIO
from datetime import datetime

def generate_monthly_report(user_data):
    """
    Generates a professional PDF Monthly Financial Report with Flux branding.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Background - Dark Theme
    c.setFillColorRGB(0.05, 0.05, 0.09) # #08080f
    c.rect(0, 0, width, height, fill=1)
    
    # Header Banner - Darker card background
    c.setFillColorRGB(0.09, 0.09, 0.16) # #181828
    c.rect(0, height - 120, width, 120, fill=1, stroke=0)
    
    # Top Orange Line
    c.setFillColorRGB(0.91, 0.28, 0.11) # #e8491d
    c.rect(0, height - 5, width, 5, fill=1, stroke=0)
    
    # Logo / Title
    c.setFillColorRGB(0.91, 0.28, 0.11)
    c.setFont("Helvetica-Bold", 32)
    c.drawString(40, height - 60, "FLUX")
    
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(135, height - 58, "WEALTH ENGINE REPORT")
    
    # Date
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0.6, 0.6, 0.7)
    c.drawString(40, height - 85, f"Generated on: {datetime.now().strftime('%B %d, %Y')}")
    
    # Client Name Box
    y = height - 170
    c.setFillColorRGB(0.1, 0.1, 0.18)
    c.roundRect(40, y - 10, width - 80, 45, 8, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, y + 10, f"Client Profile:")
    c.setFillColorRGB(0.5, 0.4, 0.8) # Purple accent
    c.drawString(160, y + 10, f"{user_data.get('name', 'User').upper()}")
    
    # Financial Overview Section
    y -= 70
    c.setFillColorRGB(0.91, 0.28, 0.11)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "FINANCIAL OVERVIEW")
    c.rect(40, y - 8, 180, 2, fill=1, stroke=0)
    
    y -= 40
    # Stat boxes
    box_w = (width - 100) / 3
    box_h = 70
    
    def draw_stat_box(bx, by, label, value, val_color=(1,1,1)):
        c.setFillColorRGB(0.1, 0.1, 0.15)
        c.roundRect(bx, by, box_w, box_h, 8, fill=1, stroke=0)
        c.setFillColorRGB(0.6, 0.6, 0.7)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(bx + box_w/2, by + box_h - 25, label.upper())
        c.setFillColorRGB(*val_color)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(bx + box_w/2, by + 18, value)

    draw_stat_box(40, y - box_h, "Total Income Logged", f"INR {user_data.get('income', 0):,.2f}")
    draw_stat_box(40 + box_w + 10, y - box_h, "Total Expenses", f"INR {user_data.get('expenses', 0):,.2f}", (0.9, 0.3, 0.3))
    draw_stat_box(40 + 2*(box_w + 10), y - box_h, "Flux Auto-Invested", f"INR {user_data.get('investments', 0):,.2f}", (0.2, 0.8, 0.5))
    
    y -= (box_h + 50)
    
    # Health Analysis
    c.setFillColorRGB(0.5, 0.4, 0.8)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "AI HEALTH ANALYSIS")
    c.rect(40, y - 8, 180, 2, fill=1, stroke=0)
    
    y -= 50
    spend_ratio = 0
    if user_data.get('income', 0) > 0:
        spend_ratio = (user_data.get('expenses', 0) / user_data.get('income', 1)) * 100
        
    profile_tag = "Disciplined Saver"
    if spend_ratio > 80: profile_tag = "High Spender"
    elif spend_ratio < 40: profile_tag = "Aggressive Investor"
    
    c.setFillColorRGB(0.1, 0.1, 0.15)
    c.roundRect(40, y - 50, width - 80, 70, 8, fill=1, stroke=0)
    
    c.setFillColorRGB(0.6, 0.6, 0.7)
    c.setFont("Helvetica", 12)
    c.drawString(60, y - 10, f"Expense Ratio: {spend_ratio:.1f}%")
    c.drawString(60, y - 35, f"AI Profile Tag: ")
    
    c.setFillColorRGB(0.2, 0.8, 0.5) if spend_ratio <= 80 else c.setFillColorRGB(0.9, 0.3, 0.3)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(145, y - 35, f"{profile_tag}")
    
    # Footer
    c.setFillColorRGB(0.2, 0.2, 0.3)
    c.rect(0, 0, width, 50, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(width / 2, 20, "POWERED BY FLUX OS | CONFIDENTIAL REPORT")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer
