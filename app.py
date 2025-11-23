from flask import Flask, render_template, redirect, request, flash, session, send_file, url_for
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
import datetime
import random
import io
import requests
import os
from dotenv import load_dotenv  

load_dotenv()  


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_key_for_local_testing')  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    
    customer_name = request.form.get('customer_name', '').strip()
    customer_address = request.form.get('customer_address', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    customer_email = request.form.get('customer_email', '').strip()
    
    
    item_names = request.form.getlist('item_name[]')
    quantities = request.form.getlist('quantity[]')
    amounts = request.form.getlist('amount[]')
    
    
    if not customer_name:
        flash("Customer Name is required.", 'error')
        return render_template('index.html')
    
    
    items = []
    grand_total = 0.0
    errors = []
    for i, (name, qty, amt) in enumerate(zip(item_names, quantities, amounts)):
        if not name or not qty or not amt:
            errors.append(f"Row {i+1}: All fields are required.")
            continue
        try:
            qty = int(qty)
            amt = float(amt)
            if qty <= 0 or amt < 0:
                errors.append(f"Row {i+1}: Quantity must be positive, amount non-negative.")
                continue
            total = qty * amt
            items.append({'name': name, 'quantity': qty, 'amount': amt, 'total': total})
            grand_total += total
        except ValueError:
            errors.append(f"Row {i+1}: Invalid number format.")
    
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('index.html')
    
    
    logo_url = "static/hotel_logo.png" 
    company_address = "123 Hotel Street, Thane , Mumbai, PIN - 401107\n Phone: +91-8945678902 | Email: info@bayhotels.com"
    
    
    invoice_number = f"INV-{random.randint(100000, 999999)}"
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    session['invoice_data'] = {
        'customer_name': customer_name,
        'customer_address': customer_address,
        'customer_phone': customer_phone,
        'customer_email': customer_email,
        'items': items,
        'grand_total': grand_total,
        'logo_url': logo_url,
        'company_address': company_address,
        'invoice_number': invoice_number,
        'invoice_date': invoice_date
    }
    
    return render_template('invoice.html', 
                           customer_name=customer_name, customer_address=customer_address, 
                           customer_phone=customer_phone, customer_email=customer_email,
                           items=items, grand_total=grand_total, 
                           logo_url=logo_url, invoice_number=invoice_number, invoice_date=invoice_date)

@app.route('/download_pdf/<invoice_number>')
def download_pdf(invoice_number):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
    from reportlab.lib.units import inch
    import io, os

    
    if 'invoice_data' not in session or session['invoice_data']['invoice_number'] != invoice_number:
        flash("Invoice data not found or expired.")
        return redirect(url_for('index'))

    data = session['invoice_data']

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30, leftMargin=40, rightMargin=40)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, fontSize=14, spaceAfter=8))

    story = []

    
    try:
        logo_path = os.path.join('static', 'hotel_logo.png')
        if os.path.exists(logo_path):
            story.append(Image(logo_path, 2*inch, 0.8*inch))
            story.append(Spacer(1, 0.2*inch))
    except Exception as e:
        print(f"Logo load failed: {e}")

    
    
    story.append(Paragraph("123 Hotel Street, Thane , Mumbai, PIN - 401107 | Phone: +91-8945678902 | Email: info@bayhotels.com", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    
    story.append(Paragraph(f"<b>Invoice Number:</b> {data['invoice_number']}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {data['invoice_date']}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    
    story.append(Paragraph("<b>Bill To:</b>", styles['Normal']))
    story.append(Paragraph(data['customer_name'], styles['Normal']))
    story.append(Paragraph(data['customer_address'], styles['Normal']))
    story.append(Paragraph(f"Phone: {data['customer_phone']}", styles['Normal']))
    story.append(Paragraph(f"Email: {data['customer_email']}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    
    table_data = [[
        Paragraph("<b>Description</b>", styles['Normal']),
        Paragraph("<b>Quantity</b>", styles['Normal']),
        Paragraph("<b>Rate (Rs.)</b>", styles['Normal']),
        Paragraph("<b>Amount (Rs.)</b>", styles['Normal'])
    ]]

    for item in data['items']:
        table_data.append([
            Paragraph(item['name'], styles['Normal']),
            Paragraph(str(item['quantity']), styles['Normal']),
            Paragraph(f"Rs. {item['amount']:.2f}", styles['Normal']),
            Paragraph(f"Rs. {item['total']:.2f}", styles['Normal'])
        ])

    table_data.append([
        Paragraph("<b>Total</b>", styles['Normal']),
        "", "", Paragraph(f"<b>Rs. {data['grand_total']:.2f}</b>", styles['Normal']) 
    ])

    table = Table(table_data, colWidths=[180, 80, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.8, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph("By: <b>Bay Hotels</b>", styles['Normal']))

    doc.build(story)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"Invoice_{invoice_number}.pdf",
                     mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)