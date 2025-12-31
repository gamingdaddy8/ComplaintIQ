from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def header(self):
        # Title
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ComplaintIQ - Executive Resolution Report', 0, 1, 'C')
        
        # Subtitle with Date
        self.set_font('Arial', 'I', 10)
        date_str = datetime.now().strftime("%d-%b-%Y")
        self.cell(0, 10, f'Generated on: {date_str}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def generate_table(self, data):
        # Table Header
        self.set_font('Arial', 'B', 9) # Slightly smaller font for header to fit text
        self.set_fill_color(240, 240, 240) # Light Gray

        # --- Adjusted Column Widths (Total ~190mm) ---
        w_id = 15
        w_name = 35      # Reduced from 40
        w_acc = 30       # <--- NEW COLUMN
        w_cat = 25       # Reduced from 30
        w_status = 20    # Reduced from 25
        w_action = 65    # Reduced from 80 to fit page

        self.cell(w_id, 10, 'ID', 1, 0, 'C', 1)
        self.cell(w_name, 10, 'Customer', 1, 0, 'C', 1)
        self.cell(w_acc, 10, 'Account No.', 1, 0, 'C', 1) # <--- NEW HEADER
        self.cell(w_cat, 10, 'Category', 1, 0, 'C', 1)
        self.cell(w_status, 10, 'Status', 1, 0, 'C', 1)
        self.cell(w_action, 10, 'Action Taken', 1, 1, 'C', 1)

        # Table Rows
        self.set_font('Arial', '', 8) # Smaller font for data
        for row in data:
            # Handle potential None values safely
            c_name = str(row.get('customer_name', 'Unknown'))[:18] # Truncate to fit 35mm
            acc_num = str(row.get('account_number', 'N/A'))        # <--- NEW DATA
            cat = str(row.get('category', 'General'))[:15]
            status = str(row.get('status', 'Open'))
            action = str(row.get('action', ''))[:40]               # Truncate to fit 65mm

            self.cell(w_id, 10, str(row['id']), 1)
            self.cell(w_name, 10, c_name, 1)
            self.cell(w_acc, 10, acc_num, 1)          # <--- NEW CELL
            self.cell(w_cat, 10, cat, 1)
            self.cell(w_status, 10, status, 1)
            self.cell(w_action, 10, action, 1, 1) # '1' at end means new line

def generate_pdf_report(complaints_list):
    """Creates the PDF and returns the byte content."""
    pdf = PDFReport()
    pdf.add_page()
    
    # Add Summary
    total = len(complaints_list)
    resolved = sum(1 for c in complaints_list if c.get('status') == 'Resolved')
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Total Records: {total} | Resolved Cases: {resolved}", 0, 1, 'L')
    pdf.ln(5)

    # Add Table
    pdf.generate_table(complaints_list)
    
    # Return PDF as bytes string
    return pdf.output(dest='S').encode('latin-1')