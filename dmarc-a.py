import os
from xml.etree import ElementTree as ET
from html import escape

def read_dmarc_report(filename):
  """
  Reads DMARC report XML file and extracts relevant information.

  Args:
    filename: Path to the XML file.

  Returns:
    A dictionary with extracted data or None if parsing fails.
  """
  try:
    tree = ET.parse(filename)
    root = tree.getroot()

    # Extract relevant data (modify these paths as needed)
    domain = root.findtext("policy_published/domain")
    received = int(root.findtext("policy_succeeded/ rua_reports/rua_formatted/identified_senders"))
    rejected = int(root.findtext("policy_failed/ rua_reports/rua_formatted/policy_rejects"))

    return {
      "domain": domain,
      "received": received,
      "rejected": rejected
    }
  except Exception as e:
    print(f"Error parsing XML: {e}")
    return None

def generate_html_report(reports):
  """
  Generates HTML report from a list of report dictionaries.

  Args:
    reports: List of dictionaries containing report data.

  Returns:
    A string containing the HTML report content.
  """

  html_content = """
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>DMARC Report</title>
    <style>
      table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
        padding: 5px;
      }
    </style>
  </head>
  <body>
    <h1>DMARC Report</h1>
    <table>
      <tr>
        <th>Domain</th>
        <th>Received Emails</th>
        <th>Rejected Emails</th>
      </tr>
  """

  for report in reports:
    html_content += f"""
      <tr>
        <td>{escape(report['domain'])}</td>
        <td>{report['received']}</td>
        <td>{report['rejected']}</td>
      </tr>
    """

  html_content += """
    </table>
  </body>
  </html>
  """

  return html_content

def main():
  # Input directory for extracted XML files
  input_dir = "/home/eric/dmarc/raw/"

  # Output filename for HTML report
  output_file = "dmarc_report.html"

  # Initialize empty list for reports
  reports = []

  for filename in os.listdir(input_dir):
    if filename.endswith(".xml"):
      filepath = os.path.join(input_dir, filename)
      data = read_dmarc_report(filepath)

      if data:
        reports.append(data)

  if reports:
    html_report = generate_html_report(reports)

    with open(output_file, "w") as f:
      f.write(html_report)
      print(f"DMARC report generated: {output_file}")
  else:
    print("No DMARC reports found.")

if __name__ == "__main__":
  main()
