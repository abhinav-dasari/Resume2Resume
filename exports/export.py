"""
Export Module for the ResumeForge AI application.

Handles exporting extracted & edited resume data to:
- JSON format
- CSV format
- PDF format (styled according to selected resume template)
"""

import json
import csv
import io
import re
from flask import Response
from xhtml2pdf import pisa


# ─────────────────────────────────────────────
# JSON Export
# ─────────────────────────────────────────────

def export_json(data, filename='extracted_data.json'):
    """
    Export extracted data as a downloadable JSON file.

    Args:
        data (dict): The extracted structured data.
        filename (str): The download filename.

    Returns:
        Flask Response: A response object with JSON content for download.
    """
    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    return Response(
        json_str,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


# ─────────────────────────────────────────────
# Helper Functions for CSV & PDF Export
# ─────────────────────────────────────────────

def _get_val(data, key):
    """Safely get string value from data dict."""
    val = data.get(key, '')
    if isinstance(val, list):
        return ', '.join(str(x).strip() for x in val if str(x).strip())
    return str(val).strip() if val else ''


def _get_list(data, key):
    """Safely get list value from data dict."""
    val = data.get(key, [])
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str) and val.strip():
        return [x.strip() for x in val.split(',') if x.strip()]
    return []


def _flatten_value(value):
    """
    Flatten a value for CSV representation.
    Lists become comma-separated strings, dicts become JSON strings.
    Multi-line strings are collapsed to a single line.
    """
    if isinstance(value, list):
        return ', '.join(str(item).strip() for item in value if str(item).strip())
    elif isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    elif value is None:
        return ''
    else:
        text = str(value)
        text = re.sub(r'[\r\n]+', ', ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = text.replace('• ', '- ')
        return text.strip()


# Known programming languages for filtering
PROGRAMMING_LANGUAGES = {
    'python', 'java', 'javascript', 'js', 'typescript', 'ts',
    'c', 'c++', 'cpp', 'c#', 'csharp', 'ruby', 'php',
    'swift', 'kotlin', 'go', 'golang', 'rust', 'scala',
    'r', 'perl', 'matlab', 'dart', 'lua', 'haskell', 'elixir',
    'objective-c', 'assembly', 'shell', 'bash', 'powershell',
    'sql', 'mysql', 'postgresql', 'sqlite', 'html', 'css', 'sass', 'less',
    'groovy', 'clojure', 'fortran', 'cobol', 'visual basic',
    'vb.net', 'f#', 'julia', 'zig', 'nim', 'solidity',
}

LANG_ALIASES = {
    'cpp': 'C++',
    'c++': 'C++',
    'c plus plus': 'C++',
    'c#': 'C#',
    'csharp': 'C#',
    'js': 'JavaScript',
    'ts': 'TypeScript',
    'golang': 'Go',
    'html': 'HTML',
    'css': 'CSS',
    'sql': 'SQL',
    'python': 'Python',
    'java': 'Java',
    'c': 'C',
    'r': 'R',
    'ruby': 'Ruby',
    'php': 'PHP',
}

SKILL_CAPS = {
    'cnn': 'CNN',
    'rnn': 'RNN',
    'lstm': 'LSTM',
    'ann': 'ANN',
    'nlp': 'NLP',
    'ai': 'AI',
    'ml': 'ML',
    'ai/ml': 'AI/ML',
    'generative ai': 'Generative AI',
    'gen ai': 'Gen AI',
    'opencv': 'OpenCV',
    'pytorch': 'PyTorch',
    'tensorflow': 'TensorFlow',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'scikit-learn': 'Scikit-Learn',
    'rest api': 'REST API',
    'ci/cd': 'CI/CD',
    'ui/ux': 'UI/UX',
    'postgresql': 'PostgreSQL',
    'mysql': 'MySQL',
    'mongodb': 'MongoDB',
    'graphql': 'GraphQL',
    'aws': 'AWS',
    'gcp': 'GCP',
    'numpy': 'NumPy',
    'pandas': 'Pandas',
    'docker': 'Docker',
    'kubernetes': 'Kubernetes',
    'linux': 'Linux',
    'django': 'Django',
    'flask': 'Flask',
    'react': 'React',
    'angular': 'Angular',
    'vue': 'Vue',
    'node.js': 'Node.js',
    'nodejs': 'Node.js',
    'express': 'Express',
    'next.js': 'Next.js',
    'nextjs': 'Next.js',
}


def _format_skill(s):
    """Clean category prefixes and format tech skill capitalization."""
    s_clean = re.sub(r'^[A-Za-z0-9\s/&\-]+:\s*', '', str(s)).strip()
    s_clean = s_clean.strip('-').strip('•').strip()
    low = s_clean.lower()
    if low in SKILL_CAPS:
        return SKILL_CAPS[low]
    if low in LANG_ALIASES:
        return LANG_ALIASES[low]
    return s_clean.title()


def _filter_programming_languages(values_source):
    """Filter a value or list of values to keep only actual programming languages."""
    if isinstance(values_source, list):
        items = []
        for val in values_source:
            if isinstance(val, list):
                items.extend([str(v).strip() for v in val])
            elif isinstance(val, str):
                items.extend([i.strip().strip('-').strip('•').strip() for i in re.split(r'[,|;]', val)])
    elif isinstance(values_source, str):
        items = [i.strip().strip('-').strip('•').strip() for i in re.split(r'[,|;]', values_source)]
    else:
        return ''

    languages = []
    seen = set()
    for item in items:
        if not item:
            continue
        low = item.lower().strip()
        if low in LANG_ALIASES:
            normalized = LANG_ALIASES[low]
        elif low in PROGRAMMING_LANGUAGES:
            normalized = item.title() if low not in ('html', 'css', 'sql') else low.upper()
        else:
            continue
        if normalized.lower() not in seen:
            seen.add(normalized.lower())
            languages.append(normalized)

    return ', '.join(languages)


def _filter_non_programming_skills(value):
    """Filter a skills value (list or str) to remove programming languages."""
    if isinstance(value, list):
        items = [str(v).strip() for v in value]
    elif isinstance(value, str):
        items = [i.strip().strip('-').strip('•').strip() for i in re.split(r'[,|;]', value)]
    else:
        return ''

    clean_skills = []
    seen = set()
    for item in items:
        if not item:
            continue
        low = item.lower().strip()
        if low in LANG_ALIASES or low in PROGRAMMING_LANGUAGES:
            continue
        if low not in seen:
            seen.add(low)
            clean_skills.append(_format_skill(item))

    return ', '.join(clean_skills)


# ─────────────────────────────────────────────
# CSV Export
# ─────────────────────────────────────────────

def export_csv(data, filename='extracted_data.csv'):
    """
    Export extracted data as a downloadable CSV file.
    """
    CSV_COLUMNS = [
        'Name',
        'LinkedIn',
        'GitHub',
        'Email',
        'Experience',
        'Summary',
        'Skills',
        'Project 1',
        'Project 2',
        'Project 3',
        'Projects',
        'Program Language',
        'Post Graduate',
        'Under Graduate',
        '12th',
        '10th',
        'Education',
        'Certification 1',
        'Certification 2',
        'Certification 3',
        'Certifications',
        'Address',
        'Document Type',
    ]

    FIELD_MAP = {
        'Name': ['name', 'student_name'],
        'LinkedIn': ['linkedin'],
        'GitHub': ['github'],
        'Email': ['email'],
        'Experience': ['experience'],
        'Summary': ['summary', 'objective'],
        'Skills': ['skills'],
        'Project 1': ['project_1'],
        'Project 2': ['project_2'],
        'Project 3': ['project_3'],
        'Projects': ['projects'],
        'Program Language': ['languages'],
        'Post Graduate': ['education_post_graduation'],
        'Under Graduate': ['education_under_graduation'],
        '12th': ['education_12th'],
        '10th': ['education_10th'],
        'Education': ['education'],
        'Certification 1': ['certification_1'],
        'Certification 2': ['certification_2'],
        'Certification 3': ['certification_3'],
        'Certifications': ['certifications', 'certificates'],
        'Address': ['address'],
        'Document Type': ['document_type'],
    }

    row = []
    for col in CSV_COLUMNS:
        if col == 'Program Language':
            sources = []
            if 'languages' in data and data['languages']:
                sources.append(data['languages'])
            if 'skills' in data and data['skills']:
                sources.append(data['skills'])
            row.append(_filter_programming_languages(sources))
        elif col == 'Skills':
            val = data.get('skills', '')
            row.append(_filter_non_programming_skills(val))
        else:
            value = ''
            possible_keys = FIELD_MAP.get(col, [])
            for key in possible_keys:
                if key in data and data[key]:
                    value = data[key]
                    break
            row.append(_flatten_value(value))

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(CSV_COLUMNS)
    writer.writerow(row)

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


# ─────────────────────────────────────────────
# PDF Export
# ─────────────────────────────────────────────

def export_pdf(data, template_id='modern-minimal', filename='resume.pdf'):
    """
    Export extracted/edited resume data as a downloadable PDF file.
    Uses xhtml2pdf to render styled PDF matching the selected template layout.

    Args:
        data (dict): Structured resume fields.
        template_id (str): Template ID ('modern-minimal', 'professional-classic', 'creative-bold', 'corporate-clean').
        filename (str): The output filename.

    Returns:
        Flask Response: PDF document attachment.
    """
    html_content = _generate_resume_html(data, template_id)
    pdf_buffer = io.BytesIO()

    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
    if pisa_status.err:
        print(f"xhtml2pdf error: {pisa_status.err}")

    pdf_buffer.seek(0)

    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


def _generate_resume_html(data, template_id='modern-minimal'):
    """
    Generate clean, printable HTML string for xhtml2pdf PDF rendering.
    Tailors styles according to template_id.
    """
    name = _get_val(data, 'name') or 'Resume'
    email = _get_val(data, 'email')
    phone = _get_val(data, 'phone')
    address = _get_val(data, 'address')
    linkedin = _get_val(data, 'linkedin')
    github = _get_val(data, 'github')

    # Skills parsing (handle list or comma-separated string)
    skills_raw = data.get('skills', [])
    if isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split(',') if s.strip()]
    elif isinstance(skills_raw, list):
        skills = [str(s).strip() for s in skills_raw if str(s).strip()]
    else:
        skills = []

    # Languages parsing (handle list or comma-separated string)
    languages_raw = data.get('languages', [])
    if isinstance(languages_raw, str):
        languages = [l.strip() for l in languages_raw.split(',') if l.strip()]
    elif isinstance(languages_raw, list):
        languages = [str(l).strip() for l in languages_raw if str(l).strip()]
    else:
        languages = []

    experience = _get_val(data, 'experience')

    edu_pg = _get_val(data, 'education_post_graduation')
    edu_ug = _get_val(data, 'education_under_graduation')
    edu_12 = _get_val(data, 'education_12th')
    edu_10 = _get_val(data, 'education_10th')
    edu_full = _get_val(data, 'education')

    projects = []
    for i in range(1, 6):
        p = _get_val(data, f'project_{i}')
        if p:
            projects.append((f"Project {i}", p))
    proj_summary = _get_val(data, 'projects')

    certs = []
    for i in range(1, 6):
        c = _get_val(data, f'certification_{i}')
        if c:
            certs.append(c)
    cert_summary = _get_val(data, 'certifications')

    # Color themes per template
    themes = {
        'modern-minimal': {
            'primary': '#4338ca',
            'accent': '#6366f1',
            'bg': '#ffffff',
            'text': '#1e293b',
            'badge_bg': '#e0e7ff',
            'badge_text': '#3730a3',
            'border': '#cbd5e1',
        },
        'professional-classic': {
            'primary': '#0369a1',
            'accent': '#0ea5e9',
            'bg': '#f8fafc',
            'text': '#0f172a',
            'badge_bg': '#e0f2fe',
            'badge_text': '#075985',
            'border': '#bae6fd',
        },
        'creative-bold': {
            'primary': '#be123c',
            'accent': '#f43f5e',
            'bg': '#ffffff',
            'text': '#111827',
            'badge_bg': '#ffe4e6',
            'badge_text': '#9f1239',
            'border': '#fecdd3',
        },
        'corporate-clean': {
            'primary': '#047857',
            'accent': '#10b981',
            'bg': '#ffffff',
            'text': '#064e3b',
            'badge_bg': '#d1fae5',
            'badge_text': '#065f46',
            'border': '#a7f3d0',
        },
    }

    theme = themes.get(template_id, themes['modern-minimal'])

    # Contact line
    contact_parts = []
    if email: contact_parts.append(email)
    if phone: contact_parts.append(phone)
    if address: contact_parts.append(address)
    contact_str = " &bull; ".join(contact_parts)

    link_parts = []
    if linkedin: link_parts.append(f"LinkedIn: {linkedin}")
    if github: link_parts.append(f"GitHub: {github}")
    link_str = " &bull; ".join(link_parts)

    # Convert text to HTML paragraphs / lines
    def _to_html_p(text):
        if not text:
            return ''
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return ''.join(f'<p class="entry-text">{l}</p>' for l in lines)

    # Skills badges (space-separated span tags for clean xhtml2pdf text wrapping)
    skills_html = ''
    if skills:
        formatted_skills = []
        seen_sk = set()
        for s in skills:
            fs = _format_skill(s)
            if fs and fs.lower() not in seen_sk:
                seen_sk.add(fs.lower())
                formatted_skills.append(fs)
        badges = ' &nbsp; '.join(f'<span class="badge">{s}</span>' for s in formatted_skills)
        skills_html = f'<div class="badge-container">{badges}</div>'

    # Languages badges
    langs_html = ''
    if languages:
        formatted_langs = []
        seen_lg = set()
        for l in languages:
            fl = _format_skill(l)
            if fl and fl.lower() not in seen_lg:
                seen_lg.add(fl.lower())
                formatted_langs.append(fl)
        badges = ' &nbsp; '.join(f'<span class="badge">{l}</span>' for l in formatted_langs)
        langs_html = f'<div class="badge-container">{badges}</div>'

    # Education HTML
    edu_html = ''
    if edu_pg:
        edu_html += f'<p class="edu-item"><b>Post Graduate:</b> {edu_pg}</p>'
    if edu_ug:
        edu_html += f'<p class="edu-item"><b>Under Graduate:</b> {edu_ug}</p>'
    if edu_12:
        edu_html += f'<p class="edu-item"><b>12th / Intermediate:</b> {edu_12}</p>'
    if edu_10:
        edu_html += f'<p class="edu-item"><b>10th / Secondary:</b> {edu_10}</p>'
    if edu_full and not edu_html:
        edu_html += _to_html_p(edu_full)

    # Projects HTML
    proj_html = ''
    if projects:
        for title, desc in projects:
            proj_html += f'<div class="proj-block"><b>{title}:</b> <span class="entry-text">{desc}</span></div>'
    elif proj_summary:
        proj_html += _to_html_p(proj_summary)

    # Certifications HTML
    cert_html = ''
    if certs:
        for c in certs:
            cert_html += f'<p class="cert-item">&bull; {c}</p>'
    elif cert_summary:
        cert_html += _to_html_p(cert_summary)

    # Layout HTML: Professional Classic uses table columns
    if template_id == 'professional-classic':
        body_content = f'''
        <table class="layout-table">
            <tr>
                <td class="sidebar-col">
                    <div class="side-title">Contact</div>
                    <p class="side-text">{email}</p>
                    <p class="side-text">{phone}</p>
                    <p class="side-text">{address}</p>
                    <p class="side-text">{linkedin}</p>
                    <p class="side-text">{github}</p>

                    {f'<div class="side-title">Skills</div>{skills_html}' if skills_html else ''}
                    {f'<div class="side-title">Languages</div>{langs_html}' if langs_html else ''}
                    {f'<div class="side-title">Education</div>{edu_html}' if edu_html else ''}
                </td>
                <td class="main-col">
                    <div class="header-name">{name}</div>

                    {f'<div class="sec-title">Experience</div>{_to_html_p(experience)}' if experience else ''}
                    {f'<div class="sec-title">Projects</div>{proj_html}' if proj_html else ''}
                    {f'<div class="sec-title">Certifications</div>{cert_html}' if cert_html else ''}
                </td>
            </tr>
        </table>
        '''
    else:
        # Single column layout for modern-minimal, creative-bold, corporate-clean
        body_content = f'''
        <div class="header-block">
            <div class="header-name">{name}</div>
            <div class="contact-info">{contact_str}</div>
            {f'<div class="contact-info">{link_str}</div>' if link_str else ''}
        </div>

        {f'<div class="sec-title">Technical Skills</div>{skills_html}' if skills_html else ''}
        {f'<div class="sec-title">Programming Languages</div>{langs_html}' if langs_html else ''}
        {f'<div class="sec-title">Experience</div>{_to_html_p(experience)}' if experience else ''}
        {f'<div class="sec-title">Education</div>{edu_html}' if edu_html else ''}
        {f'<div class="sec-title">Projects</div>{proj_html}' if proj_html else ''}
        {f'<div class="sec-title">Certifications & Trainings</div>{cert_html}' if cert_html else ''}
        '''

    full_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: a4 portrait;
        margin: 1.2cm;
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        color: {theme['text']};
        background: #ffffff;
        font-size: 9.5pt;
        line-height: 1.45;
    }}
    .header-block {{
        border-bottom: 2px solid {theme['accent']};
        padding-bottom: 10px;
        margin-bottom: 14px;
    }}
    .header-name {{
        font-size: 22pt;
        font-weight: bold;
        color: {theme['primary']};
        margin-bottom: 4px;
    }}
    .contact-info {{
        font-size: 8.5pt;
        color: #475569;
        margin-top: 2px;
    }}
    .sec-title {{
        font-size: 11pt;
        font-weight: bold;
        color: {theme['primary']};
        border-bottom: 1px solid {theme['border']};
        padding-bottom: 2px;
        margin-top: 14px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .badge-container {{
        margin-bottom: 6px;
    }}
    .badge {{
        display: inline-block;
        background-color: {theme['badge_bg']};
        color: {theme['badge_text']};
        border: 1px solid {theme['border']};
        padding: 3px 8px;
        margin-right: 6px;
        margin-bottom: 6px;
        border-radius: 4px;
        font-size: 8.5pt;
        font-weight: bold;
    }}
    .entry-text {{
        margin: 2px 0 4px 0;
        color: #1e293b;
    }}
    .edu-item {{
        margin: 3px 0;
        color: #1e293b;
    }}
    .proj-block {{
        margin-bottom: 6px;
    }}
    .cert-item {{
        margin: 3px 0;
        color: #1e293b;
    }}
    /* Two column table layout */
    .layout-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .sidebar-col {{
        width: 32%;
        vertical-align: top;
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
        padding-right: 12px;
    }}
    .main-col {{
        width: 68%;
        vertical-align: top;
        padding-left: 14px;
    }}
    .side-title {{
        font-size: 9.5pt;
        font-weight: bold;
        color: {theme['primary']};
        border-bottom: 1px solid {theme['border']};
        margin-top: 10px;
        margin-bottom: 6px;
        padding-bottom: 2px;
        text-transform: uppercase;
    }}
    .side-text {{
        font-size: 8pt;
        color: #334155;
        margin: 2px 0;
        word-break: break-all;
    }}
</style>
</head>
<body>
    {body_content}
</body>
</html>
'''
    return full_html
