"""
Unit tests for work item comments functionality.

This module contains comprehensive tests for the comments.py module,
including tests for retrieving and adding work item comments.
"""

from unittest.mock import MagicMock

from azure.devops.v7_1.work_item_tracking.models import WorkItem

from mcp_azure_devops.features.work_items.tools.comments import (
    _add_work_item_comment_impl,
    _format_comment,
    _get_project_for_work_item,
    _get_work_item_comments_impl,
)


# Tests for _format_comment
def test_format_comment_with_all_fields():
    """Test formatting a comment with all fields present."""
    mock_comment = MagicMock()
    mock_comment.text = "This is a test comment"
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Test User"
    mock_comment.created_by = mock_created_by
    mock_comment.created_date = "2023-01-15"

    result = _format_comment(mock_comment)

    assert "## Comment by Test User on 2023-01-15" in result
    assert "This is a test comment" in result


def test_format_comment_without_date():
    """Test formatting a comment without a created date."""
    mock_comment = MagicMock()
    mock_comment.text = "Comment without date"
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Another User"
    mock_comment.created_by = mock_created_by
    mock_comment.created_date = None

    result = _format_comment(mock_comment)

    assert "## Comment by Another User:" in result
    assert "on" not in result.split("\n")[0]  # No date in header
    assert "Comment without date" in result


def test_format_comment_without_author():
    """Test formatting a comment without author information."""
    mock_comment = MagicMock()
    mock_comment.text = "Anonymous comment"
    mock_comment.created_by = None
    mock_comment.created_date = "2023-01-20"

    result = _format_comment(mock_comment)

    assert "## Comment by Unknown on 2023-01-20" in result
    assert "Anonymous comment" in result


def test_format_comment_without_text():
    """Test formatting a comment without text."""
    mock_comment = MagicMock()
    mock_comment.text = None
    mock_created_by = MagicMock()
    mock_created_by.display_name = "User Name"
    mock_comment.created_by = mock_created_by
    mock_comment.created_date = "2023-01-25"

    result = _format_comment(mock_comment)

    assert "## Comment by User Name on 2023-01-25" in result
    assert "No text" in result


def test_format_comment_minimal():
    """Test formatting a minimal comment with no optional fields."""
    mock_comment = MagicMock()
    mock_comment.text = None
    mock_comment.created_by = None
    mock_comment.created_date = None

    result = _format_comment(mock_comment)

    assert "## Comment by Unknown:" in result
    assert "No text" in result


# Tests for _get_project_for_work_item
def test_get_project_for_work_item_success():
    """Test successfully retrieving project from work item."""
    mock_client = MagicMock()
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = {"System.TeamProject": "MyProject"}
    mock_client.get_work_item.return_value = mock_work_item

    result = _get_project_for_work_item(123, mock_client)

    assert result == "MyProject"
    mock_client.get_work_item.assert_called_once_with(123)


def test_get_project_for_work_item_no_project_field():
    """Test when work item has no project field."""
    mock_client = MagicMock()
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = {}
    mock_client.get_work_item.return_value = mock_work_item

    result = _get_project_for_work_item(123, mock_client)

    assert result is None


def test_get_project_for_work_item_exception():
    """Test when exception occurs during work item retrieval."""
    mock_client = MagicMock()
    mock_client.get_work_item.side_effect = Exception("Network error")

    result = _get_project_for_work_item(123, mock_client)

    assert result is None


def test_get_project_for_work_item_no_fields():
    """Test when work item has no fields attribute."""
    mock_client = MagicMock()
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = None
    mock_client.get_work_item.return_value = mock_work_item

    result = _get_project_for_work_item(123, mock_client)

    assert result is None


# Tests for _get_work_item_comments_impl
def test_get_work_item_comments_impl_with_project():
    """Test retrieving comments with explicit project parameter."""
    mock_client = MagicMock()

    # Mock comments
    mock_comment1 = MagicMock()
    mock_comment1.text = "First comment"
    mock_created_by1 = MagicMock()
    mock_created_by1.display_name = "User One"
    mock_comment1.created_by = mock_created_by1
    mock_comment1.created_date = "2023-01-10"

    mock_comment2 = MagicMock()
    mock_comment2.text = "Second comment"
    mock_created_by2 = MagicMock()
    mock_created_by2.display_name = "User Two"
    mock_comment2.created_by = mock_created_by2
    mock_comment2.created_date = "2023-01-11"

    mock_comments = MagicMock()
    mock_comments.comments = [mock_comment1, mock_comment2]
    mock_client.get_comments.return_value = mock_comments

    result = _get_work_item_comments_impl(123, mock_client, "TestProject")

    assert "## Comment by User One on 2023-01-10" in result
    assert "First comment" in result
    assert "## Comment by User Two on 2023-01-11" in result
    assert "Second comment" in result
    mock_client.get_comments.assert_called_once_with(
        project="TestProject", work_item_id=123
    )


def test_get_work_item_comments_impl_without_project():
    """Test retrieving comments without explicit project (auto-detect)."""
    mock_client = MagicMock()

    # Mock work item for project lookup
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = {"System.TeamProject": "AutoProject"}
    mock_client.get_work_item.return_value = mock_work_item

    # Mock comments
    mock_comment = MagicMock()
    mock_comment.text = "Auto-detected project comment"
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Test User"
    mock_comment.created_by = mock_created_by
    mock_comment.created_date = "2023-01-12"

    mock_comments = MagicMock()
    mock_comments.comments = [mock_comment]
    mock_client.get_comments.return_value = mock_comments

    result = _get_work_item_comments_impl(123, mock_client)

    assert "## Comment by Test User on 2023-01-12" in result
    assert "Auto-detected project comment" in result
    mock_client.get_work_item.assert_called_once_with(123)
    mock_client.get_comments.assert_called_once_with(
        project="AutoProject", work_item_id=123
    )


def test_get_work_item_comments_impl_no_comments():
    """Test retrieving work item with no comments."""
    mock_client = MagicMock()

    # Mock work item for project lookup
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = {"System.TeamProject": "EmptyProject"}
    mock_client.get_work_item.return_value = mock_work_item

    # Mock empty comments
    mock_comments = MagicMock()
    mock_comments.comments = []
    mock_client.get_comments.return_value = mock_comments

    result = _get_work_item_comments_impl(123, mock_client)

    assert "No comments found for this work item." in result


def test_get_work_item_comments_impl_project_not_found():
    """Test when project cannot be determined from work item."""
    mock_client = MagicMock()
    mock_client.get_work_item.side_effect = Exception("Work item not found")

    result = _get_work_item_comments_impl(123, mock_client)

    assert "Error retrieving work item 123 to determine project" in result


# Tests for _add_work_item_comment_impl
def test_add_work_item_comment_impl_with_project():
    """Test adding a comment with explicit project parameter."""
    mock_client = MagicMock()

    # Mock the added comment response
    mock_new_comment = MagicMock()
    mock_new_comment.text = "New comment added"
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Current User"
    mock_new_comment.created_by = mock_created_by
    mock_new_comment.created_date = "2023-01-30"

    mock_client.add_comment.return_value = mock_new_comment

    result = _add_work_item_comment_impl(
        123, "New comment added", mock_client, "TestProject"
    )

    assert "Comment added successfully." in result
    assert "## Comment by Current User on 2023-01-30" in result
    assert "New comment added" in result
    mock_client.add_comment.assert_called_once()


def test_add_work_item_comment_impl_without_project():
    """Test adding a comment without explicit project (auto-detect)."""
    mock_client = MagicMock()

    # Mock work item for project lookup
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = {"System.TeamProject": "AutoProject"}
    mock_client.get_work_item.return_value = mock_work_item

    # Mock the added comment response
    mock_new_comment = MagicMock()
    mock_new_comment.text = "Auto-detected comment"
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Current User"
    mock_new_comment.created_by = mock_created_by
    mock_new_comment.created_date = "2023-02-01"

    mock_client.add_comment.return_value = mock_new_comment

    result = _add_work_item_comment_impl(
        123, "Auto-detected comment", mock_client
    )

    assert "Comment added successfully." in result
    assert "## Comment by Current User on 2023-02-01" in result
    mock_client.get_work_item.assert_called_once_with(123)


def test_add_work_item_comment_impl_project_not_found():
    """Test error when project cannot be determined."""
    mock_client = MagicMock()
    mock_client.get_work_item.side_effect = Exception("Work item not found")

    result = _add_work_item_comment_impl(123, "Some comment", mock_client)

    assert "Error retrieving work item 123 to determine project" in result


def test_add_work_item_comment_impl_plain_text():
    """Test adding a plain text comment (should be converted to HTML)."""
    mock_client = MagicMock()

    # Mock the added comment response
    mock_new_comment = MagicMock()
    mock_new_comment.text = "<div>Plain text<br>with line break</div>"
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Test User"
    mock_new_comment.created_by = mock_created_by
    mock_new_comment.created_date = "2023-02-05"

    mock_client.add_comment.return_value = mock_new_comment

    result = _add_work_item_comment_impl(
        123, "Plain text\nwith line break", mock_client, "TestProject"
    )

    assert "Comment added successfully." in result
    # Verify that add_comment was called with a CommentCreate object
    mock_client.add_comment.assert_called_once()
    call_args = mock_client.add_comment.call_args
    assert call_args[1]["project"] == "TestProject"
    assert call_args[1]["work_item_id"] == 123


def test_add_work_item_comment_impl_html_content():
    """Test adding HTML content (should be preserved as-is)."""
    mock_client = MagicMock()

    html_content = "<p>This is <strong>HTML</strong> content</p>"

    # Mock the added comment response
    mock_new_comment = MagicMock()
    mock_new_comment.text = html_content
    mock_created_by = MagicMock()
    mock_created_by.display_name = "HTML User"
    mock_new_comment.created_by = mock_created_by
    mock_new_comment.created_date = "2023-02-10"

    mock_client.add_comment.return_value = mock_new_comment

    result = _add_work_item_comment_impl(
        123, html_content, mock_client, "TestProject"
    )

    assert "Comment added successfully." in result
    mock_client.add_comment.assert_called_once()


def test_add_work_item_comment_impl_markdown_content():
    """Test adding Markdown content (should be converted to HTML)."""
    mock_client = MagicMock()

    markdown_content = "# Header\n\nThis is **bold** text"

    # Mock the added comment response
    mock_new_comment = MagicMock()
    # Markdown would be converted to HTML by sanitize_description_html
    mock_new_comment.text = (
        "<h1>Header</h1>\n<p>This is <strong>bold</strong> text</p>"
    )
    mock_created_by = MagicMock()
    mock_created_by.display_name = "MD User"
    mock_new_comment.created_by = mock_created_by
    mock_new_comment.created_date = "2023-02-15"

    mock_client.add_comment.return_value = mock_new_comment

    result = _add_work_item_comment_impl(
        123, markdown_content, mock_client, "TestProject"
    )

    assert "Comment added successfully." in result
    mock_client.add_comment.assert_called_once()


def test_add_work_item_comment_impl_empty_text():
    """Test adding an empty comment."""
    mock_client = MagicMock()

    # Mock the added comment response
    mock_new_comment = MagicMock()
    mock_new_comment.text = ""
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Empty User"
    mock_new_comment.created_by = mock_created_by
    mock_new_comment.created_date = "2023-02-20"

    mock_client.add_comment.return_value = mock_new_comment

    result = _add_work_item_comment_impl(123, "", mock_client, "TestProject")

    assert "Comment added successfully." in result
    mock_client.add_comment.assert_called_once()
