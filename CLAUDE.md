# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A DMARC (Domain-based Message Authentication, Reporting & Conformance) XML report processor that parses reports from mail providers (Google, Outlook, etc.), performs IP geolocation, and generates consolidated HTML reports with failure highlighting.

**Primary script**: `dmarcjules.py` — the most complete version with CLI and GUI support, batch processing, and ZIP file handling. The other scripts (`dmarc.py`, `dmarc-a.py`, `dmarc-b.py`) are earlier/partial versions.

## Setup & Running

```bash
# Install dependencies (virtual environment already at .venv/)
pip install -r requirements.txt

# CLI mode: process all XMLs in a directory
python dmarcjules.py --dir raw --out consolidated_report.html

# GUI mode (Tkinter file picker)
python dmarcjules.py --gui

# Basic version (hardcoded to ./raw, no geolocation)
python dmarc.py
```

Input files go in `./raw/` — accepts `.xml` files directly or `.zip` archives containing XMLs.

## Architecture

**Data flow**: XML files → `parse_report_xml()` → `get_country()` for each IP → `generate_html_fragment()` → combined HTML output.

### Key functions in `dmarcjules.py`

- **`get_country(ip)`** — IP geolocation via `ip2geotools` free API (1000 req/day limit). A local `IP2LOCATION-LITE-DB1.CSV` is present in the repo but not currently used by the code.
- **`parse_report_xml(tree)`** — Parses an `xml.etree.ElementTree` into a dict with metadata and records (source_ip, count, disposition, dkim, spf results).
- **`generate_html_fragment(data)`** — Produces a styled HTML table for one report; rows with DKIM/SPF failures get CSS class `"fail"` (highlighted red).
- **`process_files(filepaths, output_file)`** — Orchestrates ZIP extraction, XML parsing, and HTML assembly into a single output file.

### DMARC XML structure expected

```
<feedback>
  <report_metadata> → org_name, report_id, date_range (Unix timestamps)
  <policy_published> → domain, policy (p)
  <record>           → source_ip, count, disposition, dkim/spf evaluated + auth results
```

## Dependencies

- `ip2geotools` — only non-stdlib dependency (see `requirements.txt`)
- `tkinter`, `xml.etree.ElementTree`, `zipfile` — stdlib
