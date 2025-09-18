from django import template

register = template.Library()

@register.filter
def get_grade_count(existing_grade_data, section_id):
    """Get grade count for a specific section and grade"""
    if not existing_grade_data:
        return 0
    
    section_data = existing_grade_data.get(section_id, {})
    return section_data.get('grade', 0)

@register.filter
def get_section_grade_count(existing_grade_data, section_grade_key):
    """Get grade count using section_grade_key format: 'section_id:grade'"""
    if not existing_grade_data:
        return 0
    
    try:
        section_id, grade = section_grade_key.split(':')
        section_id = int(section_id)
        section_data = existing_grade_data.get(section_id, {})
        return section_data.get(grade, 0)
    except (ValueError, AttributeError):
        return 0

@register.filter
def lookup(dictionary, key):
    """Look up a key in a dictionary"""
    if not dictionary:
        return None
    return dictionary.get(key)
