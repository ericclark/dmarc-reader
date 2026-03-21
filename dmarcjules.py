import xml.etree.ElementTree as ET
import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
from html import escape
from datetime import datetime
from ip2geotools.databases.noncommercial import DbIpCity
import argparse
import sys

def get_country(ip_address):
    """Performs IP to country lookup with error handling."""
    try:
        print(f"Attempting lookup for: {ip_address}")
        response = DbIpCity.get(ip_address, api_key='free')
        country = response.country
        print(f"Found: {country}")
        return country
    except Exception as e:
        print(f"Lookup failed for {ip_address}: {e}")
        return "Unknown"

def parse_report_xml(tree):
    """Extracts data from a DMARC XML ElementTree."""
    root = tree.getroot()

    # Metadata Extraction
    try:
        org_name = root.find('report_metadata/org_name').text
        email = root.find('report_metadata/email').text
        report_id = root.find('report_metadata/report_id').text
        date_start_timestamp = root.find('report_metadata/date_range/begin').text
        date_end_timestamp = root.find('report_metadata/date_range/end').text
        date_start = datetime.fromtimestamp(int(date_start_timestamp)).strftime('%Y-%m-%d')
        date_end = datetime.fromtimestamp(int(date_end_timestamp)).strftime('%Y-%m-%d')
    except AttributeError as e:
        print(f"Error parsing metadata: {e}")
        return None

    # Records Extraction
    records = []
    for record in root.findall('record'):
        source_ip = record.find('row/source_ip').text
        count = record.find('row/count').text
        disposition = record.find('row/policy_evaluated/disposition').text
        dkim = record.find('row/policy_evaluated/dkim').text
        spf = record.find('row/policy_evaluated/spf').text
        header_from = record.find('identifiers/header_from').text
        
        # Some reports might have different auth_results structure
        spf_domain = "N/A"
        spf_result = "N/A"
        spf_elem = root.find('.//auth_results/spf')
        if spf_elem is not None:
            spf_domain_elem = spf_elem.find('domain')
            spf_result_elem = spf_elem.find('result')
            if spf_domain_elem is not None: spf_domain = spf_domain_elem.text
            if spf_result_elem is not None: spf_result = spf_result_elem.text

        records.append({
            'source_ip': source_ip,
            'count': count,
            'disposition': disposition,
            'dkim': dkim,
            'spf': spf,
            'header_from': header_from,
            'spf_domain': spf_domain,
            'spf_result': spf_result,
            'country': get_country(source_ip)
        })

    return {
        'org_name': org_name,
        'report_id': report_id,
        'date_range': f"{date_start} to {date_end}",
        'records': records
    }

def generate_html_fragment(data):
    """Generates an HTML snippet for a single report's data."""
    if not data:
        return ""

    rows = []
    for r in data['records']:
        row_class = ""
        if r['dkim'] == 'fail' or r['spf_result'] == 'fail':
            row_class = 'class="fail"'
        
        rows.append(f"""
            <tr {row_class}>
                <td>{escape(r['source_ip'])}</td>
                <td>{escape(r['country'])}</td>
                <td>{escape(r['count'])}</td>
                <td>{escape(r['disposition'])}</td>
                <td>{escape(r['dkim'])}</td>
                <td>{escape(r['spf'])}</td>
                <td>{escape(r['header_from'])}</td>
                <td>{escape(r['spf_domain'])}</td>
                <td>{escape(r['spf_result'])}</td>
            </tr>""")

    return f"""
    <div class="report">
        <h2>Org Name: {escape(data['org_name'])}</h2>
        <p><strong>Report ID:</strong> {escape(data['report_id'])}</p>
        <p><strong>Date Range:</strong> {escape(data['date_range'])}</p>
        <table>
            <thead>
                <tr>
                    <th>Source IP</th>
                    <th>Country</th>
                    <th>Count</th>
                    <th>Disposition</th>
                    <th>DKIM</th>
                    <th>SPF</th>
                    <th>Header From</th>
                    <th>SPF Domain</th>
                    <th>SPF Result</th>
                </tr> 
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """

def process_files(filepaths, output_file="consolidated_report.html"):
    """Processes multiple XML or ZIP files and generates a single HTML report."""
    all_fragments = []

    for path in filepaths:
        if path.endswith(".xml"):
            try:
                tree = ET.parse(path)
                data = parse_report_xml(tree)
                all_fragments.append(generate_html_fragment(data))
            except Exception as e:
                print(f"Error processing {path}: {e}")
        elif path.endswith(".zip"):
            try:
                with zipfile.ZipFile(path, "r") as z:
                    for filename in z.namelist():
                        if filename.endswith(".xml"):
                            with z.open(filename) as f:
                                tree = ET.parse(f)
                                data = parse_report_xml(tree)
                                all_fragments.append(generate_html_fragment(data))
            except Exception as e:
                print(f"Error processing zip {path}: {e}")

    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Consolidated DMARC Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background-color: #f4f7f6; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .report {{ background: white; padding: 20px; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        h2 {{ color: #2980b9; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; background: white; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:hover {{ background-color: #f1f1f1; }}
        tr.fail {{ background-color: #fadbd8; }}
        .fail td {{ color: #c0392b; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Consolidated DMARC Report</h1>
    {''.join(all_fragments)}
</body>
</html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Report successfully saved to: {output_file}")

def start_gui():
    """Starts the Tkinter GUI for file selection."""
    root = tk.Tk()
    root.title("DMARC Report Processor")
    root.geometry("500x300")
    
    selected_files = []

    def select_files():
        filepaths = filedialog.askopenfilenames(
            title="Select DMARC files",
            filetypes=(("DMARC Files", "*.xml *.zip"), ("XML Files", "*.xml"), ("ZIP Archives", "*.zip"), ("All Files", "*.*"))
        )
        if filepaths:
            selected_files.clear()
            selected_files.extend(filepaths)
            status_label.config(text=f"Selected {len(selected_files)} file(s)")

    def process():
        if not selected_files:
            messagebox.showwarning("Warning", "Please select files first.")
            return

        output_file = filedialog.asksaveasfilename(
            title="Save Consolidated Report",
            defaultextension=".html",
            filetypes=(("HTML Files", "*.html"), ("All Files", "*.*")),
            initialfile="consolidated_report.html"
        )
        if not output_file:
            return

        status_label.config(text="Processing...")
        root.update()

        try:
            process_files(selected_files, output_file)
            status_label.config(text=f"Done! Saved to {os.path.basename(output_file)}")
            messagebox.showinfo("Success", f"Report generated successfully.\nSaved to: {output_file}")
        except Exception as e:
            status_label.config(text="Error occurred.")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    tk.Label(root, text="DMARC Report Processor", font=("Arial", 16, "bold")).pack(pady=20)
    tk.Button(root, text="Step 1: Select DMARC Files (*.xml, *.zip)", command=select_files, width=40).pack(pady=10)
    tk.Button(root, text="Step 2: Process & Save Report", command=process, width=40, bg="#3498db", fg="white").pack(pady=10)
    status_label = tk.Label(root, text="Ready", fg="blue")
    status_label.pack(pady=20)

    root.mainloop()

def main():
    parser = argparse.ArgumentParser(description="Process DMARC XML reports into a consolidated HTML file.")
    parser.add_argument("--gui", action="store_true", help="Launch the GUI for file selection.")
    parser.add_argument("--dir", default="raw", help="Directory containing .xml or .zip reports (default: 'raw').")
    parser.add_argument("--out", default="consolidated_report.html", help="Path to save the output HTML (default: 'consolidated_report.html').")
    
    args = parser.parse_args()

    if args.gui:
        start_gui()
    else:
        # CLI Mode
        if not os.path.exists(args.dir):
            print(f"Error: Directory '{args.dir}' not found.")
            sys.exit(1)
            
        files = [os.path.join(args.dir, f) for f in os.listdir(args.dir) if f.endswith(('.xml', '.zip'))]
        if not files:
            print(f"No .xml or .zip files found in '{args.dir}'.")
            sys.exit(0)
            
        print(f"Processing {len(files)} files from '{args.dir}'...")
        process_files(files, args.out)

if __name__ == "__main__":
    main()