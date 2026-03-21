import xml.etree.ElementTree as ET
import os
from html import escape  # For safe HTML output

def process_dmarc_report(xml_file):
    """Parses a DMARC XML report and generates an HTML report."""

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Metadata Extraction
    org_name = root.find('report_metadata/org_name').text
    email = root.find('report_metadata/email').text
    report_id = root.find('report_metadata/report_id').text
    date_start = root.find('report_metadata/date_range/begin').text
    date_end = root.find('report_metadata/date_range/end').text

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

    # Generate HTML
    html_str = f"""
    <!DOCTYPE html>
    <html>
    <head><title>DMARC Report - {report_id}</title></head>
    <body>
        <h1>DMARC Report</h1>
        <h2>Organization: {org_name}</h2>
        <p>Email: {email}</p>
        <p>Report ID: {report_id}</p>
        <p>Date Range: {date_start} to {date_end}</p>

        <h2>Domain Policy</h2>
        <p>Domain: {domain}</p>
        <p>Policy: {p_policy}</p>

        <h2>Records</h2>
        <table>
            <thead>
                <tr>
                    <th>Source IP</th>
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
                    f'<tr><td>{r["source_ip"]}</td><td>{r["count"]}</td><td>{r["disposition"]}</td><td>{r["dkim"]}</td><td>{r["spf"]}</td><td>{escape(r["header_from"])}</td><td>{r["spf_domain"]}</td><td>{r["spf_result"]}</td></tr>' 
                     for r in records) 
                }
            </tbody>
        </table>
    </body>
    </html>
    """

    return html_str, report_id  # Return both the HTML content and the report_id
    

# Script Execution
report_directory = "/home/eric/dmarc/raw"  # Replace with your report directory

for filename in os.listdir(report_directory):
    if filename.endswith(".xml"):
        filepath = os.path.join(report_directory, filename)
        html_report, report_id = process_dmarc_report(filepath)  # Get report_id

        # Save HTML report
        html_filename = f"{report_id}.html"  
        with open(html_filename, "w") as f:
            f.write(html_report)