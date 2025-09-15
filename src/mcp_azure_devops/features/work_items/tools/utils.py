"""
Utility functions for Azure DevOps work item tools.

This module provides shared utility functions used across work item tools.
"""

import re
from typing import Optional

try:
    from markdown_it import MarkdownIt
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


def _is_html_content(text: str) -> bool:
    """
    Check if text contains HTML elements.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to contain HTML elements
    """
    # Check for well-formed HTML tags
    # Tag name must start with letter, can contain letters, numbers, hyphens
    # Must have proper opening/closing structure
    html_pattern = re.compile(r'<\s*([a-zA-Z][a-zA-Z0-9\-]*)\b[^>]*>', re.IGNORECASE)
    matches = html_pattern.findall(text)
    
    # Verify these are actual HTML tag names (not just < and >)
    if matches:
        common_html_tags = {
            'a', 'abbr', 'address', 'area', 'article', 'aside', 'audio',
            'b', 'base', 'bdi', 'bdo', 'blockquote', 'body', 'br', 'button',
            'canvas', 'caption', 'cite', 'code', 'col', 'colgroup',
            'data', 'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 'div', 'dl', 'dt',
            'em', 'embed',
            'fieldset', 'figcaption', 'figure', 'footer', 'form',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header', 'hr', 'html',
            'i', 'iframe', 'img', 'input', 'ins',
            'kbd',
            'label', 'legend', 'li', 'link',
            'main', 'map', 'mark', 'meta', 'meter',
            'nav', 'noscript',
            'object', 'ol', 'optgroup', 'option', 'output',
            'p', 'param', 'picture', 'pre', 'progress',
            'q',
            'rb', 'rp', 'rt', 'ruby',
            's', 'samp', 'script', 'section', 'select', 'small', 'source', 'span', 'strong', 'style', 'sub', 'summary', 'sup',
            'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'track',
            'u', 'ul',
            'var', 'video',
            'wbr'
        }
        
        # Check if any of the found tags are known HTML tags
        for tag in matches:
            if tag.lower() in common_html_tags:
                return True
    
    return False


def _is_markdown_content(text: str) -> bool:
    """
    Check if text contains Markdown formatting.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to contain Markdown formatting
    """
    # Common Markdown patterns
    markdown_patterns = [
        r'^#{1,6}\s',  # Headers
        r'^\s*[\*\-\+]\s',  # Unordered lists  
        r'^\s*\d+\.\s',  # Ordered lists
        r'\*\*.*?\*\*',  # Bold
        r'__.*?__',  # Bold alternative
        r'\*.*?\*',  # Italic
        r'_.*?_',  # Italic alternative
        r'`.*?`',  # Inline code
        r'```',  # Code blocks
        r'^\s*>',  # Blockquotes
        r'\[.*?\]\(.*?\)',  # Links
        r'!\[.*?\]\(.*?\)',  # Images
        r'^\s*\|.*\|',  # Tables
        r'^\s*---+\s*$',  # Horizontal rules
    ]
    
    for pattern in markdown_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    return False


def sanitize_description_html(description: Optional[str]) -> Optional[str]:
    """
    Check and automatically convert description text to HTML format, supporting both HTML and Markdown input.

    This function detects the format of the input text and handles it appropriately:
    - HTML content is returned as-is
    - Markdown content is converted to HTML
    - Plain text is converted to HTML with line breaks preserved

    Args:
        description: Original description text, can be plain text, HTML, or Markdown

    Returns:
        Processed HTML text suitable for Azure DevOps
    """
    if not description:
        return description

    desc_stripped = description.strip()
    
    # Return early for empty content after stripping
    if not desc_stripped:
        return description
    
    # Check if it's already HTML content
    if _is_html_content(desc_stripped):
        return description
    
    # Check if it's Markdown content and convert to HTML
    if MARKDOWN_AVAILABLE and _is_markdown_content(desc_stripped):
        from markdown_it import MarkdownIt
        md = MarkdownIt()
        html_content = md.render(desc_stripped)
        # Remove trailing newline that markdown-it adds
        return html_content.rstrip('\n')
    
    # For plain text, convert line breaks to HTML break tags
    description_html = description.replace("\n", "<br>")
    return f"<div>{description_html}</div>"
