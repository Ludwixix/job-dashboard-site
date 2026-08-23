from pathlib import Path
import re
from fpdf import FPDF

ROOT = Path(r"C:\Users\samlu\.openclaw\workspace")
APP = ROOT / "applications"

NAVY = (31, 45, 61)
BLUE = (37, 105, 170)
TEAL = (37, 105, 170)
CORAL = (37, 105, 170)
GOLD = (37, 105, 170)
TEXT = (43, 48, 54)
MUTED = (92, 103, 114)
RULE = (207, 216, 225)
PAPER = (255, 255, 255)


def clean(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`]+", "", text)
    text = text.replace("–", "-").replace("—", "-").replace("·", ", ")
    # Turn Markdown-style skill separators into natural, readable prose.
    # Remove Markdown hard-break artifacts that were leaking into PDFs.
    text = re.sub(r"\\+\s*$", "", text)
    text = re.sub(r"\s*\|\s*", ", ", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" ,")
    text = text.replace("’", "'").replace("“", '"').replace("”", '"').replace("•", "-")
    # FPDF cannot wrap an unbroken URL or slug. Add harmless visual break points
    # for PDF rendering; the Markdown source retains the original value.
    # Preserve recognised product and professional names when source text
    # arrives with inconsistent casing.
    for source, replacement in {
        'microsoft 365': 'Microsoft 365', 'microsoft graph': 'Microsoft Graph',
        'azure': 'Azure', 'entra id': 'Entra ID', 'intune': 'Intune',
        'autopilot': 'Autopilot', 'powershell': 'PowerShell', 'servicenow': 'ServiceNow',
        'sharepoint': 'SharePoint', 'exchange online': 'Exchange Online',
        'windows 10/11': 'Windows 10/11', 'windows 11': 'Windows 11',
        'active directory': 'Active Directory', 'itil 4': 'ITIL 4',
        'sla': 'SLA', 'rca': 'RCA', 'euc': 'EUC', 'soe': 'SOE',
    }.items():
        text = re.sub(rf'(?i)\b{re.escape(source)}\b', replacement, text)
    text = re.sub(r"(\S{55})(?=\S)", r"\1 ", text)
    return text.encode("latin-1", "replace").decode("latin-1")


def natural_skill_line(text):
    """Turn a keyword list into readable, ATS-visible language."""
    value = clean(text)
    parts = [part.strip(' ,') for part in value.split(',') if part.strip(' ,')]
    if len(parts) < 3:
        return value
    return ', '.join(parts[:-1]) + ', and ' + parts[-1]


class ApplicationPDF(FPDF):
    def header(self):
        # Minimal template chrome: one accent colour and a thin rule.
        self.set_fill_color(*BLUE)
        self.rect(0, 0, 210, 3, "F")

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"Sam Ludwig  |  Infrastructure, cloud, and endpoint systems  |  Page {self.page_no()}", align="C")


def add_page(pdf):
    pdf.add_page()
    pdf.set_left_margin(18)
    pdf.set_right_margin(18)
    pdf.set_top_margin(16)
    pdf.set_auto_page_break(auto=True, margin=18)


def render(md_path):
    pdf = ApplicationPDF("P", "mm", "A4")
    pdf.set_title(md_path.stem.replace("_", " "))
    add_page(pdf)

    source_lines = md_path.read_text(encoding="utf-8").splitlines()
    # Consume the Markdown identity header because the PDF draws a single,
    # richer identity block below. Rendering both headers caused duplication,
    # broken rhythm, and the impression of double spacing.
    lines = []
    index = 0
    while index < len(source_lines) and not source_lines[index].strip():
        index += 1
    if index < len(source_lines) and source_lines[index].startswith('# '):
        index += 1
        contact = []
        while index < len(source_lines) and source_lines[index].strip() and not source_lines[index].startswith('#'):
            contact.append(clean(source_lines[index].strip()))
            index += 1
        if contact:
            lines.append('__CONTACT__' + '  |  '.join(contact))
    lines.extend(source_lines[index:])
    # Add a visual identity block before the Markdown content. All identity
    # information remains real text, rather than an embedded image.
    # ATS-safe header: plain text in the document body, one accent rule, and
    # no photo, icon, table, text box, or image-based content.
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(18, 17)
    pdf.cell(174, 9, "Sam Ludwig")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*BLUE)
    pdf.set_xy(18, 28)
    pdf.cell(174, 6, "Infrastructure | Cloud | Modern Workplace")
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.5)
    pdf.line(18, 38, 192, 38)
    pdf.set_y(44)

    is_letter = "cover_letter" in md_path.stem
    if is_letter:
        # Cover letters need letter rhythm, not résumé section treatment.
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*TEXT)
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith('__CONTACT__'):
                if line.startswith('__CONTACT__'):
                    pdf.set_text_color(*MUTED)
                    pdf.multi_cell(174, 4.5, clean(line.replace('__CONTACT__', '')), align='L')
                    pdf.ln(3)
                continue
            if line.startswith('**') and line.endswith('**'):
                pdf.set_font("Helvetica", "B", 10.5)
                pdf.set_text_color(*NAVY)
                pdf.multi_cell(174, 5, clean(line), align='L')
                pdf.ln(1)
            else:
                pdf.set_font("Helvetica", "", 9.5)
                pdf.set_text_color(*TEXT)
                pdf.set_x(18)
                pdf.multi_cell(174, 5.2, clean(line), align='L')
                pdf.ln(2.2)
    else:
        # Résumé blocks: headings stay with following content, bullets use a
        # real glyph and hanging indent, and no page starts with a continuation.
        in_skills = False
        for pos, raw in enumerate(lines):
            line = raw.strip()
            if not line or line.startswith('__CONTACT__'):
                if line.startswith('__CONTACT__'):
                    pdf.set_font("Helvetica", "", 8.5); pdf.set_text_color(*MUTED); pdf.set_x(18)
                    pdf.multi_cell(174, 4.8, clean(line.replace('__CONTACT__', '')), align='L'); pdf.ln(1.6)
                continue
            next_line = lines[pos + 1].strip() if pos + 1 < len(lines) else ''
            if line.startswith('### ') and pdf.get_y() > 250:
                pdf.add_page(); pdf.set_y(16)
            if line.startswith('## ') or line.startswith('### '):
                raw_heading = clean(line[3:] if line.startswith('## ') else line[4:])
                section_map = {'Core Skills': 'Skills', 'Qualifications': 'Certifications and Education', 'Work Rights': 'Additional Information', 'Professional Summary': 'Professional Summary', 'Professional Experience': 'Professional Experience'}
                is_section = raw_heading in section_map
                heading = section_map.get(raw_heading, raw_heading)
                if is_section:
                    in_skills = heading == 'Skills'
                    pdf.ln(3); pdf.set_fill_color(*BLUE); pdf.rect(18, pdf.get_y()+1, 2, 4.6, 'F')
                    pdf.set_font('Helvetica','B',14); pdf.set_text_color(*NAVY); pdf.set_x(22.5); pdf.multi_cell(169.5,6.2,heading, align='L')
                    pdf.ln(2.2); pdf.set_draw_color(*RULE); pdf.line(18,pdf.get_y(),192,pdf.get_y()); pdf.ln(1.6)
                else:
                    in_skills = False
                    if pdf.get_y() > 260: pdf.add_page(); pdf.set_y(16)
                    # Role headings stay distinct from section headings.
                    pdf.set_font('Helvetica','B',10.3); pdf.set_text_color(*BLUE); pdf.set_x(18); pdf.multi_cell(174,5.2,heading, align='L'); pdf.ln(.8)
            elif line.startswith('- '):
                pdf.set_font('Helvetica','',10.0); pdf.set_text_color(*TEXT); pdf.set_x(22)
                pdf.cell(4,5.0,'-'); pdf.multi_cell(166,5.0,clean(line[2:]), align='L'); pdf.ln(1.2)
            elif line.startswith('**') and line.endswith('**'):
                pdf.set_font('Helvetica','B',9.2); pdf.set_text_color(*TEXT); pdf.set_x(18); pdf.multi_cell(174,4.8,clean(line), align='L'); pdf.ln(.6)
            else:
                pdf.set_font('Helvetica','',10.0); pdf.set_text_color(*TEXT); pdf.set_x(18)
                value = natural_skill_line(line) if in_skills else clean(line)
                pdf.multi_cell(174,5.2,value, align='L'); pdf.ln(.8)

    pdf.output(str(md_path.with_suffix('.pdf')))


for markdown_file in sorted(APP.glob("*.md")):
    if markdown_file.name.startswith("2026-"):
        render(markdown_file)
        print(markdown_file.with_suffix(".pdf").name)
