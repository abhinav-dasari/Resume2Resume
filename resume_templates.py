"""
Resume Templates Registry

Defines 4 pre-built resume templates with different styles and section layouts.
Each template specifies the order and positioning of resume sections.
"""

RESUME_TEMPLATES = {
    'modern-minimal': {
        'id': 'modern-minimal',
        'name': 'Modern Minimal',
        'description': 'Clean single-column layout with subtle accent borders and generous whitespace.',
        'icon': '✨',
        'color_accent': '#6366f1',
        'layout_type': 'single-column',
        'sections_order': [
            'header',        # Name, email, phone, links
            'skills',        # Skills tags
            'experience',    # Work experience
            'projects',      # Projects breakdown
            'education',     # Education levels
            'certifications', # Certs & trainings
            'languages',     # Programming languages
        ],
    },
    'professional-classic': {
        'id': 'professional-classic',
        'name': 'Professional Classic',
        'description': 'Traditional two-column layout with a sidebar for skills, education, and links.',
        'icon': '📋',
        'color_accent': '#0ea5e9',
        'layout_type': 'two-column',
        'sections_order': [
            'header',
            'experience',
            'projects',
            'certifications',
        ],
        'sidebar_sections': [
            'skills',
            'languages',
            'education',
        ],
    },
    'creative-bold': {
        'id': 'creative-bold',
        'name': 'Creative Bold',
        'description': 'Vibrant design with gradient accents, bold headings, and creative section dividers.',
        'icon': '🎨',
        'color_accent': '#f43f5e',
        'layout_type': 'single-column',
        'sections_order': [
            'header',
            'skills',
            'projects',
            'experience',
            'education',
            'certifications',
            'languages',
        ],
    },
    'corporate-clean': {
        'id': 'corporate-clean',
        'name': 'Corporate Clean',
        'description': 'Formal, ATS-friendly layout with structured sections and clean typography.',
        'icon': '🏢',
        'color_accent': '#10b981',
        'layout_type': 'single-column',
        'sections_order': [
            'header',
            'experience',
            'education',
            'skills',
            'projects',
            'certifications',
            'languages',
        ],
    },
}


def get_template(template_id):
    """
    Get a template by its ID.

    Args:
        template_id (str): The template identifier.

    Returns:
        dict or None: The template configuration, or None if not found.
    """
    return RESUME_TEMPLATES.get(template_id)


def get_all_templates():
    """
    Get all available templates as a list.

    Returns:
        list: List of template configuration dictionaries.
    """
    return list(RESUME_TEMPLATES.values())
