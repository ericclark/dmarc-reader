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