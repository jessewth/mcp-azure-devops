"""Tests for work item utilities."""


from mcp_azure_devops.features.work_items.tools.utils import (
    _is_html_content,
    _is_markdown_content,
    sanitize_description_html,
)


class TestIsHtmlContent:
    """Test HTML content detection."""

    def test_recognizes_html_tags(self):
        """Test that HTML tags are recognized."""
        assert _is_html_content("<div>content</div>")
        assert _is_html_content("<p>paragraph</p>")
        assert _is_html_content("<span class='test'>text</span>")
        assert _is_html_content("<br>")
        assert _is_html_content("<br/>")
        assert _is_html_content("Text with <strong>bold</strong> content")

    def test_ignores_plain_text(self):
        """Test that plain text is not recognized as HTML."""
        assert not _is_html_content("This is plain text")
        assert not _is_html_content("Text with < and > symbols but no tags")
        assert not _is_html_content("Mathematical expression: 5 < 10 > 3")

    def test_empty_or_none_input(self):
        """Test handling of empty or None input."""
        assert not _is_html_content("")
        assert not _is_html_content("   ")


class TestIsMarkdownContent:
    """Test Markdown content detection."""

    def test_recognizes_headers(self):
        """Test that Markdown headers are recognized."""
        assert _is_markdown_content("# Header 1")
        assert _is_markdown_content("## Header 2")
        assert _is_markdown_content("### Header 3")
        assert _is_markdown_content("#### Header 4")
        assert _is_markdown_content("##### Header 5")
        assert _is_markdown_content("###### Header 6")

    def test_recognizes_lists(self):
        """Test that Markdown lists are recognized."""
        assert _is_markdown_content("* Item 1")
        assert _is_markdown_content("- Item 1")
        assert _is_markdown_content("+ Item 1")
        assert _is_markdown_content("1. Numbered item")
        assert _is_markdown_content("10. Numbered item")

    def test_recognizes_emphasis(self):
        """Test that Markdown emphasis is recognized."""
        assert _is_markdown_content("Text with **bold** content")
        assert _is_markdown_content("Text with __bold__ content")
        assert _is_markdown_content("Text with *italic* content")
        assert _is_markdown_content("Text with _italic_ content")

    def test_recognizes_code(self):
        """Test that Markdown code is recognized."""
        assert _is_markdown_content("Inline `code` here")
        assert _is_markdown_content("```\ncode block\n```")
        assert _is_markdown_content("```python\nprint('hello')\n```")

    def test_recognizes_links_and_images(self):
        """Test that Markdown links and images are recognized."""
        assert _is_markdown_content("Check out [this link](http://example.com)")
        assert _is_markdown_content("![Alt text](image.png)")

    def test_recognizes_blockquotes(self):
        """Test that Markdown blockquotes are recognized."""
        assert _is_markdown_content("> This is a quote")
        assert _is_markdown_content("  > Indented quote")

    def test_recognizes_tables(self):
        """Test that Markdown tables are recognized."""
        assert _is_markdown_content("| Column 1 | Column 2 |")
        assert _is_markdown_content("| --- | --- |")

    def test_recognizes_horizontal_rules(self):
        """Test that Markdown horizontal rules are recognized."""
        assert _is_markdown_content("---")
        assert _is_markdown_content("----")
        assert _is_markdown_content("-----")

    def test_ignores_plain_text(self):
        """Test that plain text is not recognized as Markdown."""
        assert not _is_markdown_content("This is plain text")
        assert not _is_markdown_content("Text without any markdown formatting")
        assert not _is_markdown_content("Some text with punctuation! And numbers 123.")

    def test_empty_or_none_input(self):
        """Test handling of empty input."""
        assert not _is_markdown_content("")
        assert not _is_markdown_content("   ")


class TestSanitizeDescriptionHtml:
    """Test HTML/Markdown sanitization and conversion."""

    def test_returns_none_for_none_input(self):
        """Test that None input returns None."""
        assert sanitize_description_html(None) is None

    def test_returns_empty_for_empty_input(self):
        """Test that empty input returns empty."""
        assert sanitize_description_html("") == ""
        # Whitespace-only input after stripping becomes empty, so return original
        assert sanitize_description_html("   ") == "   "

    def test_preserves_existing_html(self):
        """Test that existing HTML is preserved."""
        html_content = "<div><p>This is HTML content</p></div>"
        assert sanitize_description_html(html_content) == html_content

        html_with_attributes = '<span class="highlight">Important</span>'
        assert sanitize_description_html(html_with_attributes) == html_with_attributes

    def test_converts_markdown_to_html(self):
        """Test that Markdown is converted to HTML."""
        # Test headers
        result = sanitize_description_html("# Main Header")
        assert "<h1>Main Header</h1>" in result

        # Test emphasis
        result = sanitize_description_html("Text with **bold** and *italic* content")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

        # Test lists
        markdown_list = "- Item 1\n- Item 2\n- Item 3"
        result = sanitize_description_html(markdown_list)
        assert "<ul>" in result
        assert "<li>Item 1</li>" in result

        # Test links
        result = sanitize_description_html("Check out [this link](http://example.com)")
        assert '<a href="http://example.com">this link</a>' in result

        # Test code
        result = sanitize_description_html("Inline `code` here")
        assert "<code>code</code>" in result

    def test_converts_plain_text_to_html(self):
        """Test that plain text is converted to HTML."""
        plain_text = "This is plain text\nWith line breaks"
        result = sanitize_description_html(plain_text)
        assert result == "<div>This is plain text<br>With line breaks</div>"

    def test_complex_markdown_conversion(self):
        """Test conversion of complex Markdown content."""
        complex_markdown = """# Project Requirements

## Overview
This project needs to implement the following features:

1. **User Authentication**
   - Login functionality
   - Password reset

2. **Data Management** 
   - CRUD operations
   - Data validation

### Technical Details
Here's some `inline code` and a code block:

```python
def hello_world():
    print("Hello, World!")
```

> **Note**: This is important information

For more details, see [our documentation](http://docs.example.com).
"""
        result = sanitize_description_html(complex_markdown)
        
        # Verify key elements are converted
        assert "<h1>Project Requirements</h1>" in result
        assert "<h2>Overview</h2>" in result
        assert "<strong>User Authentication</strong>" in result
        assert "<ol>" in result  # Ordered list
        assert "<code>inline code</code>" in result
        assert "<pre><code" in result  # Code block
        assert "<blockquote>" in result
        assert '<a href="http://docs.example.com">our documentation</a>' in result

    def test_edge_cases(self):
        """Test edge cases and mixed content."""
        # Mixed content that could be ambiguous
        mixed_content = "This has *some* markdown but also <strong>HTML</strong>"
        result = sanitize_description_html(mixed_content)
        # Should preserve HTML since HTML detection takes precedence
        assert "<strong>HTML</strong>" in result

        # Markdown-like text that isn't really markdown
        pseudo_markdown = "The price is $5 * 2 = $10"
        result = sanitize_description_html(pseudo_markdown)
        # Should be treated as plain text since * pattern doesn't match markdown italic
        assert result == "<div>The price is $5 * 2 = $10</div>"

    def test_whitespace_handling(self):
        """Test proper handling of whitespace."""
        # Leading/trailing whitespace
        result = sanitize_description_html("  # Header  ")
        assert "<h1>Header</h1>" in result

        # Multiple line breaks
        result = sanitize_description_html("Line 1\n\nLine 2\n\n\nLine 3")
        # Should preserve the structure when treated as plain text
        expected = "<div>Line 1<br><br>Line 2<br><br><br>Line 3</div>"
        assert result == expected