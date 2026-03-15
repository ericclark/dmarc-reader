import xml.etree.ElementTree as ET
import os
from html import escape
from datetime import datetime 
from ip2geotools.databases.noncommercial import DbIpCity 

def process_dmarc_report(xml_file):
    """Parses a DMARC XML report and generates an HTML report."""

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Metadata Extraction
    org_name = root.find('report_metadata/org_name').text
    email = root.find('report_metadata/email').text
    report_id = root.find('report_metadata/report_id').text
    date_start_timestamp = root.find('report_metadata/date_range/begin').text
    date_end_timestamp = root.find('report_metadata/date_range/end').text
    date_start = datetime.fromtimestamp(int(date_start_timestamp)).strftime('%Y-%m-%d')
    date_end = datetime.fromtimestamp(int(date_end_timestamp)).strftime('%Y-%m-%d')

    # Policy Information
    domain = root.find('policy_published/domain').text
    p_policy = root.find('policy_published/p').text

    # Table Data (Records)
    records = []
    for record in root.findall('record'):
        source_ip = record.find('row/source_ip').text
        count = record.find('row/count').text
        disposition = record.find('row/policy_evaluated/disposition').text
        dkim = record.find('row/policy_evaluated/dkim').text
        spf = record.find('row/policy_evaluated/spf').text
        header_from = record.find('identifiers/header_from').text
        spf_domain = record.find('auth_results/spf/domain').text
        spf_result = record.find('auth_results/spf/result').text

        records.append({
            'source_ip': source_ip,
            'count': count,
            'disposition': disposition,
            'dkim': dkim,
            'spf': spf,
            'header_from': header_from,
            'spf_domain': spf_domain,
            'spf_result': spf_result
        })

    # Local IP-Country Database Setup. This is an alternative to using the ip2geotools API. The free API has a 1000/day limit.
    # db_path = "/path/to//IP2LOCATION-LITE-DB1.CSV" 

    # Look up Country
    for record in records:
        ip_address = record['source_ip']
        try:
            print("Attempting lookup for:", ip_address)
            response = DbIpCity.get(ip_address, api_key='free') # You can specify the local IP database here if desired.
            country = response.country
            print(country)
        except Exception:  # Handle potential errors gracefully
            country = "Unknown" 

        record['country'] = country

    # Generate HTML
    html_str = f""" 
    <h2>Org Name: {escape(org_name)}</h2>
    <p>Report ID: {escape(report_id)}</p>
    <p>Date Range: {escape(date_start)} to {escape(date_end)}</p>
    <h3>Records</h3>
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
            { ''.join(
                f'<tr class="{"dkim-fail" if r["dkim"] == "fail" else ""} {"spf-fail" if r["spf_result"] == "fail" else ""}"><td>{escape(r["source_ip"])}</td><td>{escape(r["country"])}</td><td>{escape(r["count"])}</td><td>{escape(r["disposition"])}</td><td>{escape(r["dkim"])}</td><td>{escape(r["spf"])}</td><td>{escape(r["header_from"])}</td><td>{escape(r["spf_domain"])}</td><td>{escape(r["spf_result"])}</td></tr>'
                for r in records)  
            }
        </tbody>
    </table> 
    """

    return html_str  # Return the HTML content snippet 

# Script Execution
report_directory = "/home/eric/dmarc/raw"  

all_html = ""  # To store the combined HTML from all reports

for filename in os.listdir(report_directory):
    if filename.endswith(".xml"):
        filepath = os.path.join(report_directory, filename)
        html_fragment = process_dmarc_report(filepath)  
        all_html += html_fragment

# Complete HTML Structure
complete_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Consolidated DMARC Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: sans-serif; }}
        td {{ padding: 8px; }}
        tr.dkim-fail, tr.spf-fail {{ background-color: #ffcccc; }}
    </style>
</head>
<body>
    <h1>Consolidated DMARC Report</h1>
    {all_html} 
</body>
</html>
"""

# Save the consolidated report
with open("consolidated_report.html", "w") as f:
    f.write(complete_html)
import xml.etree.ElementTree as ET
import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
from html import escape
from datetime import datetime
from ip2geotools.databases.noncommercial import DbIpCity

def process_dmarc_report(tree):
    """Parses a DMARC XML report and generates an HTML report."""

    root = tree.getroot()

    # Metadata Extraction
    org_name = root.find('report_metadata/org_name').text
    email = root.find('report_metadata/email').text
    report_id = root.find('report_metadata/report_id').text
    date_start_timestamp = root.find('report_metadata/date_range/begin').text
    date_end_timestamp = root.find('report_metadata/date_range/end').text
    date_start = datetime.fromtimestamp(int(date_start_timestamp)).strftime('%Y-%m-%d')
    date_end = datetime.fromtimestamp(int(date_end_timestamp)).strftime('%Y-%m-%d')

    # Policy Information
    domain = root.find('policy_published/domain').text
    p_policy = root.find('policy_published/p').text

    # Table Data (Records)
    records = []
    for record in root.findall('record'):
        source_ip = record.find('row/source_ip').text
        count = record.find('row/count').text
        disposition = record.find('row/policy_evaluated/disposition').text
        dkim = record.find('row/policy_evaluated/dkim').text
        spf = record.find('row/policy_evaluated/spf').text
        header_from = record.find('identifiers/header_from').text
        spf_domain = record.find('auth_results/spf/domain').text
        spf_result = record.find('auth_results/spf/result').text

        records.append({
            'source_ip': source_ip,
            'count': count,
            'disposition': disposition,
            'dkim': dkim,
            'spf': spf,
            'header_from': header_from,
            'spf_domain': spf_domain,
            'spf_result': spf_result
        })

    # Local IP-Country Database Setup. This is an alternative to using the ip2geotools API. The free API has a 1000/day limit.
    # db_path = "/path/to//IP2LOCATION-LITE-DB1.CSV"

    # Look up Country
    for record in records:
        ip_address = record['source_ip']
        try:
            print("Attempting lookup for:", ip_address)
            response = DbIpCity.get(ip_address, api_key='free') # You can specify the local IP database here if desired.
            country = response.country
            print(country)
        except Exception:  # Handle potential errors gracefully
            country = "Unknown"

        record['country'] = country

    # Generate HTML
    html_str = f"""
    <h2>Org Name: {org_name}</h2>
    <p>Report ID: {report_id}</p>
    <p>Date Range: {date_start} to {date_end}</p>
    <h3>Records</h3>
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
            { ''.join(
                f'<tr class={"dkim-fail" if r["dkim"] == "fail" else ""} {"spf-fail" if r["spf_result"] == "fail" else ""}><td>{r["source_ip"]}</td><td>{r["country"]}</td><td>{r["count"]}</td><td>{r["disposition"]}</td><td>{r["dkim"]}</td><td>{r["spf"]}</td><td>{escape(r["header_from"])}</td><td>{r["spf_domain"]}</td><td>{r["spf_result"]}</td></tr>'
                for r in records)
            }
        </tbody>
    </table>
    """

    return html_str  # Return the HTML content snippet

def process_files(filepaths, output_file="consolidated_report.html"):
    all_html = ""  # To store the combined HTML from all reports

    for filepath in filepaths:
        if filepath.endswith(".xml"):
            try:
                tree = ET.parse(filepath)
                html_fragment = process_dmarc_report(tree)
                all_html += html_fragment
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
        elif filepath.endswith(".zip"):
            try:
                with zipfile.ZipFile(filepath, "r") as z:
                    for filename in z.namelist():
                        if filename.endswith(".xml"):
                            try:
                                with z.open(filename) as f:
                                    tree = ET.parse(f)
                                    html_fragment = process_dmarc_report(tree)
                                    all_html += html_fragment
                            except Exception as e:
                                print(f"Error processing {filename} in {filepath}: {e}")
            except Exception as e:
                print(f"Error processing zip {filepath}: {e}")

    # Complete HTML Structure
    complete_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Consolidated DMARC Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: sans-serif; }}
        td {{ padding: 8px; }}
        tr.dkim-fail, tr.spf-fail {{ background-color: #ffcccc; }}
    </style>
</head>
<body>
    <h1>Consolidated DMARC Report</h1>
    {all_html}
</body>
</html>
"""

    # Save the consolidated report
    with open(output_file, "w") as f:
        f.write(complete_html)

def start_gui():
    root = tk.Tk()
    root.title("DMARC Report Processor")
    root.geometry("400x200")

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
            return  # User cancelled

        status_label.config(text="Processing...")
        root.update()

        try:
            process_files(selected_files, output_file)
            status_label.config(text=f"Done! Report saved as {os.path.basename(output_file)}")
            messagebox.showinfo("Success", f"Consolidated report generated successfully.\nSaved to: {output_file}")
        except Exception as e:
            status_label.config(text="Error occurred.")
            messagebox.showerror("Error", f"An error occurred during processing:\n{str(e)}")

    btn_select = tk.Button(root, text="Select DMARC Files (*.xml, *.zip)", command=select_files, pady=10)
    btn_select.pack(pady=20)

    btn_process = tk.Button(root, text="Process Files", command=process, pady=10)
    btn_process.pack(pady=10)

    status_label = tk.Label(root, text="Ready", fg="blue")
    status_label.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
