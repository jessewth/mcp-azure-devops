"""
Unit tests for the work item attachments tools.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from mcp_azure_devops.features.work_items.tools.attachments import (
    _download_attachment_impl,
    _download_work_item_attachments_impl,
    _extract_attachment_id,
    _format_download_results,
    _get_work_item_attachments_impl,
    _sanitize_filename,
)


class TestWorkItemAttachments(unittest.TestCase):
    """Tests for the work item attachments functions."""

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments.get_work_item_client"
    )
    def test_get_attachments_formal(self, mock_get_client):
        """Test getting formal attachments."""
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Create a mock work item with formal attachments
        mock_work_item = MagicMock()
        mock_relation = MagicMock()
        mock_relation.rel = "AttachedFile"
        mock_relation.url = "https://example.com/attachment1"
        mock_relation.attributes = {
            "name": "test_file.txt",
            "comment": "Test comment",
        }
        mock_work_item.relations = [mock_relation]
        mock_work_item.fields = {}

        mock_client.get_work_item.return_value = mock_work_item

        # Call the function
        result = _get_work_item_attachments_impl(123, mock_client)

        # Assertions
        mock_client.get_work_item.assert_called_once_with(123, expand="all")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["url"], "https://example.com/attachment1")
        self.assertEqual(result[0]["name"], "test_file.txt")
        self.assertEqual(result[0]["comment"], "Test comment")
        self.assertEqual(result[0]["type"], "formal_attachment")

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments.get_work_item_client"
    )
    def test_get_attachments_embedded(self, mock_get_client):
        """Test getting embedded images from HTML fields."""
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Create a mock work item with HTML content containing image
        mock_work_item = MagicMock()
        mock_work_item.relations = []
        mock_work_item.fields = {
            "System.Description": '<div><img src="https://91appinc.visualstudio.com/attachment?fileName=image.png" alt="Image"></div>',
            "Microsoft.VSTS.Common.AcceptanceCriteria": '<div><img src="https://91appinc.visualstudio.com/attachment2?fileName=diagram.png" alt="Diagram"></div>',
        }

        mock_client.get_work_item.return_value = mock_work_item

        # Call the function
        result = _get_work_item_attachments_impl(123, mock_client)

        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "embedded_image")
        self.assertEqual(result[0]["name"], "image.png")
        self.assertEqual(result[0]["field"], "System.Description")
        self.assertEqual(result[1]["name"], "diagram.png")
        self.assertEqual(
            result[1]["field"], "Microsoft.VSTS.Common.AcceptanceCriteria"
        )

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments.get_work_item_client"
    )
    def test_get_attachments_none(self, mock_get_client):
        """Test when there are no attachments."""
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Create a mock work item with no attachments
        mock_work_item = MagicMock()
        mock_work_item.relations = []
        mock_work_item.fields = {
            "System.Description": "Just text, no images",
            "Microsoft.VSTS.Common.AcceptanceCriteria": "More text",
        }

        mock_client.get_work_item.return_value = mock_work_item

        # Call the function
        result = _get_work_item_attachments_impl(123, mock_client)

        # Assertions
        self.assertEqual(len(result), 0)

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments.get_work_item_client"
    )
    def test_get_attachments_error(self, mock_get_client):
        """Test error handling."""
        # Setup mock to raise an exception
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_work_item.side_effect = Exception("Test error")

        # Call the function and verify exception is raised
        with self.assertRaises(Exception) as context:
            _get_work_item_attachments_impl(123, mock_client)

        self.assertIn(
            "Error retrieving work item attachments", str(context.exception)
        )


class TestExtractAttachmentId(unittest.TestCase):
    """Tests for _extract_attachment_id."""

    def test_valid_url(self):
        """Test extracting ID from a valid attachment URL."""
        url = (
            "https://dev.azure.com/myorg/myproject/_apis/wit/attachments/"
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890?fileName=test.txt"
        )
        result = _extract_attachment_id(url)
        self.assertEqual(result, "a1b2c3d4-e5f6-7890-abcd-ef1234567890")

    def test_url_without_query_params(self):
        """Test extracting ID from URL without query parameters."""
        url = (
            "https://dev.azure.com/org/_apis/wit/attachments/"
            "12345678-1234-1234-1234-123456789012"
        )
        result = _extract_attachment_id(url)
        self.assertEqual(result, "12345678-1234-1234-1234-123456789012")

    def test_invalid_url_no_guid(self):
        """Test with URL that has no GUID."""
        url = "https://dev.azure.com/org/_apis/wit/attachments/not-a-guid"
        result = _extract_attachment_id(url)
        self.assertIsNone(result)

    def test_invalid_url_completely_different(self):
        """Test with a completely unrelated URL."""
        url = "https://example.com/somefile.txt"
        result = _extract_attachment_id(url)
        self.assertIsNone(result)

    def test_empty_url(self):
        """Test with empty string."""
        result = _extract_attachment_id("")
        self.assertIsNone(result)


class TestSanitizeFilename(unittest.TestCase):
    """Tests for _sanitize_filename."""

    def test_normal_filename(self):
        """Test normal filename passes through."""
        self.assertEqual(_sanitize_filename("report.pdf"), "report.pdf")

    def test_path_traversal(self):
        """Test path traversal is stripped."""
        self.assertEqual(_sanitize_filename("../../etc/passwd"), "passwd")

    def test_special_characters(self):
        """Test special characters are replaced."""
        result = _sanitize_filename('file<>:"/\\|?*.txt')
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)

    def test_empty_filename(self):
        """Test empty filename gets default."""
        self.assertEqual(_sanitize_filename(""), "unnamed_attachment")

    def test_dots_only(self):
        """Test dots-only filename gets default."""
        self.assertEqual(_sanitize_filename("..."), "unnamed_attachment")


class TestDownloadAttachmentImpl(unittest.TestCase):
    """Tests for _download_attachment_impl."""

    def test_download_success_bytes(self):
        """Test successful download with bytes response."""
        mock_client = MagicMock()
        mock_client.get_attachment_content.return_value = iter(
            [b"file content"]
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            url = (
                "https://dev.azure.com/org/_apis/wit/attachments/"
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
                "?fileName=test.txt"
            )
            success, path = _download_attachment_impl(
                url, "test.txt", tmp_dir, mock_client
            )

            self.assertTrue(success)
            self.assertTrue(os.path.exists(path))
            with open(path, "rb") as f:
                self.assertEqual(f.read(), b"file content")

    def test_download_success_iterable(self):
        """Test successful download with iterable response."""
        mock_client = MagicMock()
        mock_client.get_attachment_content.return_value = [
            b"chunk1",
            b"chunk2",
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            url = (
                "https://dev.azure.com/org/_apis/wit/attachments/"
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            )
            success, path = _download_attachment_impl(
                url, "test.bin", tmp_dir, mock_client
            )

            self.assertTrue(success)
            with open(path, "rb") as f:
                self.assertEqual(f.read(), b"chunk1chunk2")

    def test_download_invalid_url(self):
        """Test download with invalid URL (no attachment ID)."""
        mock_client = MagicMock()

        with tempfile.TemporaryDirectory() as tmp_dir:
            success, detail = _download_attachment_impl(
                "https://example.com/no-id",
                "test.txt",
                tmp_dir,
                mock_client,
            )

            self.assertFalse(success)
            self.assertIn("Cannot parse attachment ID", detail)

    def test_download_sdk_error(self):
        """Test download when SDK raises an exception."""
        mock_client = MagicMock()
        mock_client.get_attachment_content.side_effect = Exception(
            "Network error"
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            url = (
                "https://dev.azure.com/org/_apis/wit/attachments/"
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            )
            success, detail = _download_attachment_impl(
                url, "test.txt", tmp_dir, mock_client
            )

            self.assertFalse(success)
            self.assertIn("Download failed", detail)

    def test_download_creates_directory(self):
        """Test that download creates target directory."""
        mock_client = MagicMock()
        mock_client.get_attachment_content.return_value = iter([b"data"])

        with tempfile.TemporaryDirectory() as tmp_dir:
            nested_dir = os.path.join(tmp_dir, "sub", "dir")
            url = (
                "https://dev.azure.com/org/_apis/wit/attachments/"
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            )
            success, path = _download_attachment_impl(
                url, "file.txt", nested_dir, mock_client
            )

            self.assertTrue(success)
            self.assertTrue(os.path.exists(nested_dir))


class TestFormatDownloadResults(unittest.TestCase):
    """Tests for _format_download_results."""

    def test_all_success(self):
        """Test formatting when all downloads succeed."""
        results = [
            {"name": "a.txt", "success": True, "detail": "/tmp/a.txt"},
            {"name": "b.pdf", "success": True, "detail": "/tmp/b.pdf"},
        ]
        output = _format_download_results(123, results)
        self.assertIn("Work Item 123", output)
        self.assertIn("Success:** 2", output)
        self.assertIn("Failed:** 0", output)
        self.assertIn("✅", output)

    def test_all_failed(self):
        """Test formatting when all downloads fail."""
        results = [
            {"name": "a.txt", "success": False, "detail": "Error msg"},
        ]
        output = _format_download_results(456, results)
        self.assertIn("Failed:** 1", output)
        self.assertIn("❌", output)
        self.assertIn("Error msg", output)

    def test_mixed_results(self):
        """Test formatting with mixed success/failure."""
        results = [
            {"name": "ok.txt", "success": True, "detail": "/tmp/ok.txt"},
            {"name": "bad.txt", "success": False, "detail": "Failed"},
        ]
        output = _format_download_results(789, results)
        self.assertIn("Success:** 1", output)
        self.assertIn("Failed:** 1", output)


class TestDownloadWorkItemAttachmentsImpl(unittest.TestCase):
    """Tests for _download_work_item_attachments_impl."""

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._get_work_item_attachments_impl"
    )
    def test_no_attachments(self, mock_get_attachments):
        """Test when work item has no attachments."""
        mock_get_attachments.return_value = []
        mock_client = MagicMock()

        result = _download_work_item_attachments_impl(
            123, "/tmp/dl", mock_client
        )
        self.assertIn("No attachments found", result)

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._get_work_item_attachments_impl"
    )
    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._download_attachment_impl"
    )
    def test_download_all_formal(self, mock_download, mock_get_attachments):
        """Test downloading all formal attachments."""
        mock_get_attachments.return_value = [
            {
                "url": "https://dev.azure.com/attachments/id1",
                "name": "doc.pdf",
                "type": "formal_attachment",
            },
            {
                "url": "https://dev.azure.com/attachments/id2",
                "name": "img.png",
                "type": "embedded_image",
                "field": "System.Description",
            },
        ]
        mock_download.return_value = (True, "/tmp/dl/doc.pdf")
        mock_client = MagicMock()

        result = _download_work_item_attachments_impl(
            123, "/tmp/dl", mock_client
        )

        # Only formal attachment should be downloaded (embedded excluded)
        mock_download.assert_called_once()
        self.assertIn("doc.pdf", result)

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._get_work_item_attachments_impl"
    )
    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._download_attachment_impl"
    )
    def test_download_include_embedded(
        self, mock_download, mock_get_attachments
    ):
        """Test downloading with embedded images included."""
        mock_get_attachments.return_value = [
            {
                "url": "https://dev.azure.com/attachments/id1",
                "name": "doc.pdf",
                "type": "formal_attachment",
            },
            {
                "url": "https://dev.azure.com/attachments/id2",
                "name": "img.png",
                "type": "embedded_image",
                "field": "System.Description",
            },
        ]
        mock_download.return_value = (True, "/tmp/dl/file")
        mock_client = MagicMock()

        result = _download_work_item_attachments_impl(
            123, "/tmp/dl", mock_client, include_embedded=True
        )

        # Both should be downloaded
        self.assertEqual(mock_download.call_count, 2)

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._get_work_item_attachments_impl"
    )
    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._download_attachment_impl"
    )
    def test_download_filter_by_name(
        self, mock_download, mock_get_attachments
    ):
        """Test downloading a specific attachment by name."""
        mock_get_attachments.return_value = [
            {
                "url": "https://dev.azure.com/attachments/id1",
                "name": "doc.pdf",
                "type": "formal_attachment",
            },
            {
                "url": "https://dev.azure.com/attachments/id2",
                "name": "spec.docx",
                "type": "formal_attachment",
            },
        ]
        mock_download.return_value = (True, "/tmp/dl/spec.docx")
        mock_client = MagicMock()

        result = _download_work_item_attachments_impl(
            123, "/tmp/dl", mock_client, attachment_name="spec.docx"
        )

        mock_download.assert_called_once()
        call_args = mock_download.call_args
        self.assertEqual(call_args[0][1], "spec.docx")

    @patch(
        "mcp_azure_devops.features.work_items.tools.attachments"
        "._get_work_item_attachments_impl"
    )
    def test_no_matching_name(self, mock_get_attachments):
        """Test when name filter matches nothing."""
        mock_get_attachments.return_value = [
            {
                "url": "https://dev.azure.com/attachments/id1",
                "name": "doc.pdf",
                "type": "formal_attachment",
            },
        ]
        mock_client = MagicMock()

        result = _download_work_item_attachments_impl(
            123, "/tmp/dl", mock_client, attachment_name="nonexist.txt"
        )
        self.assertIn("No matching attachments", result)


if __name__ == "__main__":
    unittest.main()
