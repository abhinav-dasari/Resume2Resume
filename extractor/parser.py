"""
Information Extraction Module — The Brain of the Resume Template Builder.

This module takes raw PDF text and converts it into structured JSON data
for resume documents. It extracts:
    - Name, email, phone, address
    - LinkedIn, GitHub
    - Skills, programming languages
    - Education (PG, UG, 12th, 10th)
    - Experience, projects, certifications

Uses regex patterns and heuristic rules for field extraction.
Structured for easy extension with LLM-based extraction in the future.
"""

import re
import json


# ─────────────────────────────────────────────
# Regex Patterns
# ─────────────────────────────────────────────

PATTERNS = {
    'email': re.compile(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    ),
    'phone': re.compile(
        r'(?:\+91[\s\-]?)?(?:\(?0?\d{2,4}\)?[\s\-]?)?\d{5}[\s\-]?\d{5}'
    ),
    'phone_simple': re.compile(r'\b\d{10}\b'),
    'url_linkedin': re.compile(
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?',
        re.IGNORECASE
    ),
    'url_github': re.compile(
        r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?',
        re.IGNORECASE
    ),
    'date': re.compile(
        r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b'
    ),
    'date_written': re.compile(
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
        r'\s+\d{4}\b',
        re.IGNORECASE
    ),
    'pin_code': re.compile(r'\b\d{6}\b'),
    'aadhaar_number': re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b'),
    'pan_number': re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b'),
    'cgpa': re.compile(r'\b(?:CGPA|GPA|SGPA)\s*[:\-]?\s*(\d+\.?\d*)', re.IGNORECASE),
    'percentage': re.compile(r'\b(\d{1,3}\.?\d*)\s*%'),
}

# ─────────────────────────────────────────────
# Common skills list for resume parsing
# ─────────────────────────────────────────────

COMMON_SKILLS = [
    'python', 'java', 'javascript', 'c\\+\\+', 'c#', 'ruby', 'php', 'swift',
    'kotlin', 'go', 'golang', 'rust', 'typescript', 'scala', 'r\\b',
    'html', 'css', 'react', 'angular', 'vue', 'node\\.?js', 'express',
    'django', 'flask', 'spring', 'laravel', 'rails', 'next\\.?js',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle',
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
    'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'devops',
    'machine learning', 'deep learning', 'artificial intelligence',
    'nlp', 'natural language processing', 'computer vision',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
    'data science', 'data analysis', 'data engineering', 'big data',
    'hadoop', 'spark', 'kafka', 'airflow',
    'rest api', 'graphql', 'microservices', 'api',
    'linux', 'unix', 'windows', 'macos',
    'agile', 'scrum', 'jira', 'confluence',
    'figma', 'photoshop', 'illustrator', 'ui/ux',
    'excel', 'power bi', 'tableau',
    'blockchain', 'cybersecurity', 'networking',
    'opencv', 'selenium', 'junit', 'pytest',
]

SKILLS_PATTERN = re.compile(
    r'\b(' + '|'.join(COMMON_SKILLS) + r')\b',
    re.IGNORECASE
)

# Map of programming languages and their standard display format
PROG_LANG_MAP = {
    'python': 'Python',
    'c': 'C',
    'c++': 'C++',
    'cpp': 'C++',
    'c plus plus': 'C++',
    'c#': 'C#',
    'csharp': 'C#',
    'java': 'Java',
    'javascript': 'JavaScript',
    'js': 'JavaScript',
    'typescript': 'TypeScript',
    'ts': 'TypeScript',
    'html': 'HTML',
    'css': 'CSS',
    'sql': 'SQL',
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL',
    'sqlite': 'SQLite',
    'oracle sql': 'SQL',
    'pl/sql': 'PL/SQL',
    'ruby': 'Ruby',
    'php': 'PHP',
    'swift': 'Swift',
    'kotlin': 'Kotlin',
    'go': 'Go',
    'golang': 'Go',
    'rust': 'Rust',
    'scala': 'Scala',
    'r': 'R',
    'perl': 'Perl',
    'matlab': 'MATLAB',
    'dart': 'Dart',
    'lua': 'Lua',
    'haskell': 'Haskell',
    'elixir': 'Elixir',
    'bash': 'Bash',
    'shell': 'Shell',
    'powershell': 'PowerShell',
    'assembly': 'Assembly',
    'solidity': 'Solidity',
}


# Map of technical skills for standardized capitalization
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


# ─────────────────────────────────────────────
# Education Level Parser Helper
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Education Level Parser Helper
# ─────────────────────────────────────────────

def _format_education_block(lines):
    """
    Format education block lines into clean: Degree, Institution (Year), Marks/CGPA
    """
    if not lines:
        return ''

    degree, inst, years, marks = '', '', '', ''
    year_pattern = re.compile(r'\b(?:19|20)\d{2}\s*(?:[–\-—\to]+\s*(?:Present|(?:19|20)\d{2}))?\b', re.IGNORECASE)
    cgpa_pattern = re.compile(r'\b(?:CGPA|GPA|SGPA)\s*[:\-]?\s*\d+\.?\d*', re.IGNORECASE)
    pct_pattern = re.compile(r'\b(?:Percentage|Pct)?\s*[:\-]?\s*\d{1,3}\.?\d*\s*%', re.IGNORECASE)
    deg_pattern = re.compile(r'\b(?:Bachelor|B\.Tech|BTech|B\.E|B\.Sc|BCA|BBA|Master|M\.Tech|MTech|M\.S|MSc|MBA|MCA|12th|10th|Intermediate|Secondary|HSC|SSC|Class XII|Class X)\b', re.IGNORECASE)
    inst_keywords = ['university', 'college', 'school', 'institute', 'academy', 'tmr', 'lpu', 'iit', 'nit', 'bits', 'high school', 'junior college']

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        # Check CGPA/Marks
        cgpa_m = cgpa_pattern.search(line_clean)
        pct_m = pct_pattern.search(line_clean)
        if cgpa_m and not marks:
            marks = cgpa_m.group()
        elif pct_m and not marks:
            marks = pct_m.group()

        # Check Years
        year_m = year_pattern.search(line_clean)
        if year_m and not years:
            years = year_m.group()

        # Check Degree
        if deg_pattern.search(line_clean) and not degree:
            d = cgpa_pattern.sub('', line_clean)
            d = pct_pattern.sub('', d)
            d = re.sub(r'[\s—\-\:]+$', '', d).strip()
            degree = d
        elif any(kw in line_lower for kw in inst_keywords) and not inst:
            inst = line_clean
        elif not year_m and not cgpa_m and not pct_m and not deg_pattern.search(line_clean) and not inst and len(line_clean) > 3:
            inst = line_clean

    comps = []
    if degree:
        comps.append(degree)
    if inst:
        comps.append(f"{inst} ({years})" if years else inst)
    elif years:
        comps.append(f"({years})")

    if marks and marks not in (degree or ''):
        comps.append(marks)

    return ', '.join(comps) if comps else ', '.join(lines)


def parse_education_levels(education_text):
    """
    Parse education section into 4 levels with institution, degree, year, and marks:
    - education_post_graduation (PG)
    - education_under_graduation (UG)
    - education_12th (12th / Intermediate)
    - education_10th (10th / Secondary)
    """
    result = {
        'education_post_graduation': '',
        'education_under_graduation': '',
        'education_12th': '',
        'education_10th': '',
    }

    if not education_text:
        return result

    lines = [line.strip() for line in education_text.split('\n') if line.strip()]

    level_lines = {'pg': [], 'ug': [], '12th': [], '10th': []}
    current_level = None

    for i, line in enumerate(lines):
        l_low = line.lower()
        if any(k in l_low for k in ['master', 'm.tech', 'mtech', 'msc', 'mba', 'mca', 'post graduate', 'm.e']):
            current_level = 'pg'
        elif any(k in l_low for k in ['bachelor', 'b.tech', 'btech', 'bsc', 'bba', 'bca', 'under graduate', 'b.e']):
            current_level = 'ug'
        elif any(k in l_low for k in ['12th', 'intermediate', 'senior secondary', 'class xii', 'hsc']):
            current_level = '12th'
        elif any(k in l_low for k in ['10th', 'secondary', 'ssc', 'class x', 'matriculation']):
            current_level = '10th'

        if current_level:
            level_lines[current_level].append((i, line))

    used_indices = set()
    for level in ['pg', 'ug', '12th', '10th']:
        item_tuples = level_lines[level]
        if not item_tuples:
            continue
        indices = [t[0] for t in item_tuples]
        min_idx = min(indices)
        max_idx = max(indices)

        # Include preceding lines if not used by another level
        start_idx = min_idx
        while start_idx > 0 and (start_idx - 1) not in used_indices:
            prev_line = lines[start_idx - 1].lower()
            if any(k in prev_line for k in ['master', 'bachelor', '12th', '10th', 'intermediate', 'secondary']):
                break
            start_idx -= 1

        for idx in range(start_idx, max_idx + 1):
            used_indices.add(idx)

        all_block_lines = [lines[idx] for idx in range(start_idx, max_idx + 1)]

        deg, inst, years, marks = '', '', '', ''
        cgpa_pattern = re.compile(r'\b(?:CGPA|GPA|SGPA)\s*[:\-]?\s*\d+\.?\d*', re.IGNORECASE)
        pct_pattern = re.compile(r'\b(?:Percentage|Pct)?\s*[:\-]?\s*\d{1,3}\.?\d*\s*%', re.IGNORECASE)
        year_pattern = re.compile(r'\b(?:19|20)\d{2}\s*(?:[–\-—\to]+\s*(?:Present|(?:19|20)\d{2}))?\b', re.IGNORECASE)
        deg_pattern = re.compile(r'\b(?:Bachelor|B\.Tech|BTech|B\.E|B\.Sc|BCA|BBA|Master|M\.Tech|MTech|M\.S|MSc|MBA|MCA|12th|10th|Intermediate|Secondary|HSC|SSC|Class XII|Class X)\b', re.IGNORECASE)
        inst_keywords = ['university', 'college', 'school', 'institute', 'academy', 'tmr', 'lpu', 'iit', 'nit', 'bits', 'high school', 'junior college']

        for l in all_block_lines:
            l_low = l.lower()
            cm = cgpa_pattern.search(l)
            pm = pct_pattern.search(l)
            ym = year_pattern.search(l)
            if cm and not marks:
                marks = cm.group()
            elif pm and not marks:
                marks = pm.group()
            if ym and not years:
                years = ym.group()

            if deg_pattern.search(l) and not deg:
                d = cgpa_pattern.sub('', l)
                d = pct_pattern.sub('', d)
                deg = re.sub(r'[\s—\-\:]+$', '', d).strip()

            if any(kw in l_low for kw in inst_keywords) and not inst:
                inst = l.strip()

        # Fallback for inst if no explicit keyword matched
        if not inst:
            for l in all_block_lines:
                cm = cgpa_pattern.search(l)
                pm = pct_pattern.search(l)
                ym = year_pattern.search(l)
                if not cm and not pm and not ym and not deg_pattern.search(l) and len(l.strip()) > 3:
                    inst = l.strip()
                    break

        comps = []
        if deg:
            comps.append(deg)
        if inst:
            comps.append(f"{inst} ({years})" if years else inst)
        elif years:
            comps.append(f"({years})")
        if marks:
            comps.append(marks)

        key_map = {
            'pg': 'education_post_graduation',
            'ug': 'education_under_graduation',
            '12th': 'education_12th',
            '10th': 'education_10th'
        }
        result[key_map[level]] = ', '.join(comps)

    return result


# ─────────────────────────────────────────────
# Projects and Certifications Parsers Helper
# ─────────────────────────────────────────────

def parse_projects(projects_text):
    """
    Parse projects text into structured project_1, project_2, project_3, project_4, project_5.
    """
    result = {
        'project_1': '',
        'project_2': '',
        'project_3': '',
        'project_4': '',
        'project_5': '',
    }
    if not projects_text:
        return result

    raw_blocks = re.split(r'\n\s*\n', projects_text.strip())
    if len(raw_blocks) == 1:
        lines = [l.strip() for l in projects_text.split('\n') if l.strip()]
        blocks = []
        curr = []
        date_pattern = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b|\b(?:19|20)\d{2}\s*[\-–—\to]+', re.IGNORECASE)
        for l in lines:
            if curr and ('|' in l or date_pattern.search(l)) and not l.startswith('•') and not l.startswith('-'):
                curr_text = ' '.join(curr)
                if '|' in curr_text or date_pattern.search(curr_text):
                    blocks.append(curr)
                    curr = [l]
                    continue
            curr.append(l)
        if curr:
            blocks.append(curr)
        raw_blocks = ['\n'.join(b) for b in blocks]

    for idx, block in enumerate(raw_blocks[:5], 1):
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
        clean_str = ' — '.join(lines)
        clean_str = clean_str.replace('• ', '- ')
        result[f'project_{idx}'] = clean_str

    return result


def parse_certifications(certs_text):
    """
    Parse certifications text into structured certification_1, certification_2, certification_3, certification_4, certification_5.
    """
    result = {
        'certification_1': '',
        'certification_2': '',
        'certification_3': '',
        'certification_4': '',
        'certification_5': '',
    }
    if not certs_text:
        return result

    raw_blocks = re.split(r'\n\s*\n', certs_text.strip())
    if len(raw_blocks) == 1:
        lines = [l.strip() for l in certs_text.split('\n') if l.strip()]
        blocks = []
        curr = []
        date_pattern = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b|\b(?:19|20)\d{2}\s*[\-–—\to]+', re.IGNORECASE)
        for l in lines:
            if curr and ('|' in l or date_pattern.search(l)) and not l.startswith('•') and not l.startswith('-'):
                curr_text = ' '.join(curr)
                if '|' in curr_text or date_pattern.search(curr_text):
                    blocks.append(curr)
                    curr = [l]
                    continue
            curr.append(l)
        if curr:
            blocks.append(curr)
        raw_blocks = ['\n'.join(b) for b in blocks]

    for idx, block in enumerate(raw_blocks[:5], 1):
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
        clean_str = ' — '.join(lines)
        clean_str = clean_str.replace('• ', '- ')
        result[f'certification_{idx}'] = clean_str

    return result


# ─────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────

def extract_info(text, doc_type=None):
    """
    Main extraction function. Always extracts as a resume.

    Args:
        text (str): The raw PDF text.
        doc_type (str, optional): Ignored — always treated as 'resume'.

    Returns:
        dict: {
            'document_type': 'resume',
            'fields': dict (extracted structured data),
        }
    """
    if not text or not text.strip():
        return {
            'document_type': 'resume',
            'fields': {},
        }

    fields = extract_resume(text)

    return {
        'document_type': 'resume',
        'fields': fields,
    }


def extract_resume(text):
    """
    Extract structured fields from resume text.

    Returns:
        dict: Extracted fields including name, email, phone, skills, etc.
    """
    data = {
        'name': '',
        'email': '',
        'phone': '',
        'address': '',
        'linkedin': '',
        'github': '',
        'skills': [],
        'languages': [],
        'education': '',
        'education_post_graduation': '',
        'education_under_graduation': '',
        'education_12th': '',
        'education_10th': '',
        'experience': '',
        'projects': '',
        'project_1': '',
        'project_2': '',
        'project_3': '',
        'project_4': '',
        'project_5': '',
        'certifications': '',
        'certification_1': '',
        'certification_2': '',
        'certification_3': '',
        'certification_4': '',
        'certification_5': '',
    }

    lines = text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]

    # --- Email ---
    email_match = PATTERNS['email'].search(text)
    if email_match:
        data['email'] = email_match.group()

    # --- Phone ---
    phone_match = PATTERNS['phone'].search(text)
    if phone_match:
        data['phone'] = phone_match.group().strip()
    else:
        phone_simple = PATTERNS['phone_simple'].search(text)
        if phone_simple:
            data['phone'] = phone_simple.group()

    # --- LinkedIn ---
    linkedin_match = PATTERNS['url_linkedin'].search(text)
    if linkedin_match:
        data['linkedin'] = linkedin_match.group()

    # --- GitHub ---
    github_match = PATTERNS['url_github'].search(text)
    if github_match:
        data['github'] = github_match.group()

    # --- Name ---
    # Heuristic: The name is usually the first non-empty line that is NOT
    # an email, phone, URL, or section header
    for line in lines[:5]:
        line_clean = line.strip()
        # Skip if it looks like a section header
        if any(kw in line_clean.lower() for kw in [
            'resume', 'curriculum', 'cv', 'objective', 'summary',
            'contact', 'personal'
        ]):
            continue
        # Skip if it's an email, phone, or URL
        if PATTERNS['email'].search(line_clean):
            continue
        if PATTERNS['phone'].search(line_clean) or PATTERNS['phone_simple'].search(line_clean):
            continue
        if 'linkedin.com' in line_clean.lower() or 'github.com' in line_clean.lower():
            continue
        # Skip very long lines (probably descriptions)
        if len(line_clean) > 60:
            continue
        # Skip lines with mostly numbers
        if sum(c.isdigit() for c in line_clean) > len(line_clean) // 2:
            continue
        # This is likely the name
        if line_clean and any(c.isalpha() for c in line_clean):
            data['name'] = line_clean
            break

    # --- Skills & Programming Languages ---
    raw_skills = set()
    skill_matches = SKILLS_PATTERN.findall(text)
    for skill in skill_matches:
        raw_skills.add(skill.strip())

    # Also look for skills section
    skills_section = _extract_section(text, [
        'skills', 'technical skills', 'technologies', 'tech stack',
        'tools', 'competencies'
    ])
    if skills_section:
        items = re.split(r'[,|•·●▪►\n]', skills_section)
        for item in items:
            item = re.sub(r'^[A-Za-z0-9\s/&\-]+:\s*', '', item).strip()
            item = item.strip('-').strip('•').strip()
            if item and len(item) < 40 and len(item) > 1:
                raw_skills.add(item)

    # Check programming languages / languages section
    languages_section = _extract_section(text, [
        'programming languages', 'programming language', 'languages', 'language proficiency'
    ])
    if languages_section:
        items = re.split(r'[,|•·●▪►\n]', languages_section)
        for item in items:
            item = re.sub(r'^[A-Za-z0-9\s/&\-]+:\s*', '', item).strip()
            item = item.strip('-').strip('•').strip()
            if item and len(item) < 40 and len(item) > 1:
                raw_skills.add(item)

    # Separate programming languages from general skills
    general_skills = set()
    prog_languages = set()
    seen_skills_low = set()
    seen_langs_low = set()

    for item in raw_skills:
        item_clean = re.sub(r'^[A-Za-z0-9\s/&\-]+:\s*', '', item).strip()
        if not item_clean:
            continue
        item_lower = item_clean.lower()
        if item_lower in PROG_LANG_MAP:
            lang = PROG_LANG_MAP[item_lower]
            if lang.lower() not in seen_langs_low:
                seen_langs_low.add(lang.lower())
                prog_languages.add(lang)
        elif item_lower == 'html':
            if 'html' not in seen_langs_low:
                seen_langs_low.add('html')
                prog_languages.add('HTML')
        elif item_lower == 'css':
            if 'css' not in seen_langs_low:
                seen_langs_low.add('css')
                prog_languages.add('CSS')
        elif item_lower == 'sql':
            if 'sql' not in seen_langs_low:
                seen_langs_low.add('sql')
                prog_languages.add('SQL')
        elif item_lower in SKILL_CAPS:
            sk = SKILL_CAPS[item_lower]
            if sk.lower() not in seen_skills_low:
                seen_skills_low.add(sk.lower())
                general_skills.add(sk)
        else:
            sk = item_clean.title()
            if sk.lower() not in seen_skills_low:
                seen_skills_low.add(sk.lower())
                general_skills.add(sk)

    data['skills'] = sorted(list(general_skills))
    data['languages'] = sorted(list(prog_languages))

    # --- Education ---
    education_section = _extract_section(text, [
        'education', 'academic', 'qualification', 'academics'
    ])
    if education_section:
        data['education'] = education_section.strip()
        edu_levels = parse_education_levels(education_section)
        data.update(edu_levels)
    else:
        data['education_post_graduation'] = ''
        data['education_under_graduation'] = ''
        data['education_12th'] = ''
        data['education_10th'] = ''

    # --- Experience ---
    experience_section = _extract_section(text, [
        'experience', 'work experience', 'professional experience',
        'employment', 'work history', 'internship'
    ])
    if experience_section:
        data['experience'] = experience_section.strip()

    # --- Projects ---
    projects_section = _extract_section(text, [
        'projects', 'personal projects', 'academic projects', 'key projects'
    ])
    if projects_section:
        data['projects'] = projects_section.strip()
        parsed_projs = parse_projects(projects_section)
        data.update(parsed_projs)

    # --- Certifications ---
    certs_section = _extract_section(text, [
        'certifications', 'certificates', 'certification',
        'courses', 'training'
    ])
    if certs_section:
        data['certifications'] = certs_section.strip()
        parsed_certs = parse_certifications(certs_section)
        data.update(parsed_certs)

    # --- Address ---
    address_section = _extract_section(text, ['address', 'location', 'city'])
    if address_section:
        data['address'] = address_section.strip()

    return data


# ─────────────────────────────────────────────
# Section Extraction Helper
# ─────────────────────────────────────────────

def _extract_section(text, section_keywords):
    """
    Extract the content of a named section from the text.
    Sections are assumed to be delimited by headers (lines in ALL CAPS,
    lines followed by dashes, or lines matching known section names).

    Args:
        text (str): The full text to search.
        section_keywords (list): Possible names for the section header.

    Returns:
        str or None: The content of the section, or None if not found.
    """
    lines = text.split('\n')
    section_start = None

    # Known section headers that would end the current section
    all_section_headers = [
        'education', 'experience', 'skills', 'technical skills',
        'projects', 'certifications', 'certificates', 'achievements',
        'awards', 'languages', 'interests', 'hobbies', 'references',
        'objective', 'summary', 'professional summary', 'contact',
        'personal', 'work experience', 'professional experience',
        'employment', 'work history', 'internship', 'training',
        'courses', 'publications', 'activities', 'volunteer',
        'address', 'location', 'declaration', 'academic',
        'qualification', 'competencies', 'tools', 'technologies',
    ]

    for i, line in enumerate(lines):
        line_stripped = line.strip().lower().rstrip(':').rstrip('-').strip()

        # Check if this line is our target section header
        if section_start is None:
            for keyword in section_keywords:
                if line_stripped == keyword or \
                   line_stripped.startswith(keyword + ':') or \
                   line_stripped.startswith(keyword + ' '):
                    section_start = i + 1
                    break
        else:
            # Check if this line is a different section header (end marker)
            for header in all_section_headers:
                if header in section_keywords:
                    continue
                if line_stripped == header or \
                   line_stripped.startswith(header + ':') or \
                   line_stripped.startswith(header + ' '):
                    # Return the content between section_start and here
                    section_content = '\n'.join(lines[section_start:i])
                    return section_content.strip() if section_content.strip() else None

    # If we found the section but no end marker, return everything after it
    if section_start is not None:
        section_content = '\n'.join(lines[section_start:])
        return section_content.strip() if section_content.strip() else None

    return None

