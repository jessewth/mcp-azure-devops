"""Comprehensive unit tests for work_items query operations."""

from unittest.mock import MagicMock

from azure.devops.v7_1.work_item_tracking.models import (
    WorkItem,
    WorkItemReference,
)

from mcp_azure_devops.features.work_items.tools.query import (
    _query_work_items_impl,
)


class TestQueryWorkItemsImpl:
    """Test suite for _query_work_items_impl function."""

    def test_query_with_no_results(self):
        """Test query that returns no work items."""
        mock_client = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.work_items = []
        mock_client.query_by_wiql.return_value = mock_query_result

        result = _query_work_items_impl(
            "SELECT * FROM WorkItems", 10, mock_client
        )

        assert result == "No work items found matching the query."
        mock_client.query_by_wiql.assert_called_once()

    def test_query_with_single_result(self):
        """Test query that returns a single work item."""
        mock_client = MagicMock()

        # Mock query result with single work item reference
        mock_query_result = MagicMock()
        mock_work_item_ref = MagicMock(spec=WorkItemReference)
        mock_work_item_ref.id = "123"
        mock_query_result.work_items = [mock_work_item_ref]
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock work item
        mock_work_item = MagicMock(spec=WorkItem)
        mock_work_item.id = 123
        mock_work_item.fields = {
            "System.WorkItemType": "Bug",
            "System.Title": "Test Bug",
            "System.State": "Active",
        }
        mock_client.get_work_items.return_value = [mock_work_item]

        result = _query_work_items_impl(
            "SELECT * FROM WorkItems WHERE [System.Id] = 123",
            10,
            mock_client,
        )

        # Verify the result contains expected work item data
        assert "# Work Item 123" in result
        assert "- **System.WorkItemType**: Bug" in result
        assert "- **System.Title**: Test Bug" in result
        assert "- **System.State**: Active" in result

    def test_query_with_multiple_results(self):
        """Test query that returns multiple work items."""
        mock_client = MagicMock()

        # Mock query result with multiple work item references
        mock_query_result = MagicMock()
        mock_work_item_ref1 = MagicMock(spec=WorkItemReference)
        mock_work_item_ref1.id = "123"
        mock_work_item_ref2 = MagicMock(spec=WorkItemReference)
        mock_work_item_ref2.id = "456"
        mock_work_item_ref3 = MagicMock(spec=WorkItemReference)
        mock_work_item_ref3.id = "789"
        mock_query_result.work_items = [
            mock_work_item_ref1,
            mock_work_item_ref2,
            mock_work_item_ref3,
        ]
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock work items
        mock_work_item1 = MagicMock(spec=WorkItem)
        mock_work_item1.id = 123
        mock_work_item1.fields = {
            "System.WorkItemType": "Bug",
            "System.Title": "First Bug",
            "System.State": "Active",
        }

        mock_work_item2 = MagicMock(spec=WorkItem)
        mock_work_item2.id = 456
        mock_work_item2.fields = {
            "System.WorkItemType": "Task",
            "System.Title": "Second Task",
            "System.State": "In Progress",
        }

        mock_work_item3 = MagicMock(spec=WorkItem)
        mock_work_item3.id = 789
        mock_work_item3.fields = {
            "System.WorkItemType": "User Story",
            "System.Title": "Third Story",
            "System.State": "Closed",
        }

        mock_client.get_work_items.return_value = [
            mock_work_item1,
            mock_work_item2,
            mock_work_item3,
        ]

        result = _query_work_items_impl(
            "SELECT * FROM WorkItems", 10, mock_client
        )

        # Verify all work items are included in the result
        assert "# Work Item 123" in result
        assert "First Bug" in result
        assert "# Work Item 456" in result
        assert "Second Task" in result
        assert "# Work Item 789" in result
        assert "Third Story" in result

    def test_query_with_top_parameter(self):
        """Test that the top parameter limits results correctly."""
        mock_client = MagicMock()

        # Mock query result
        mock_query_result = MagicMock()
        mock_work_item_ref = MagicMock(spec=WorkItemReference)
        mock_work_item_ref.id = "123"
        mock_query_result.work_items = [mock_work_item_ref]
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock work item
        mock_work_item = MagicMock(spec=WorkItem)
        mock_work_item.id = 123
        mock_work_item.fields = {
            "System.WorkItemType": "Bug",
            "System.Title": "Test Bug",
            "System.State": "Active",
        }
        mock_client.get_work_items.return_value = [mock_work_item]

        # Execute with specific top value
        _query_work_items_impl("SELECT * FROM WorkItems", 5, mock_client)

        # Verify that query_by_wiql was called with the correct top value
        call_args = mock_client.query_by_wiql.call_args
        assert call_args[1]["top"] == 5

    def test_query_handles_none_work_items(self):
        """Test that None work items are filtered out."""
        mock_client = MagicMock()

        # Mock query result
        mock_query_result = MagicMock()
        mock_work_item_ref1 = MagicMock(spec=WorkItemReference)
        mock_work_item_ref1.id = "123"
        mock_work_item_ref2 = MagicMock(spec=WorkItemReference)
        mock_work_item_ref2.id = "456"
        mock_query_result.work_items = [
            mock_work_item_ref1,
            mock_work_item_ref2,
        ]
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock work items with one None (simulating error_policy="omit")
        mock_work_item1 = MagicMock(spec=WorkItem)
        mock_work_item1.id = 123
        mock_work_item1.fields = {
            "System.WorkItemType": "Bug",
            "System.Title": "Valid Bug",
            "System.State": "Active",
        }

        mock_client.get_work_items.return_value = [mock_work_item1, None]

        result = _query_work_items_impl(
            "SELECT * FROM WorkItems", 10, mock_client
        )

        # Verify only the valid work item is in the result
        assert "# Work Item 123" in result
        assert "Valid Bug" in result
        # Ensure the result doesn't have any None-related errors
        assert "None" not in result

    def test_query_with_complex_wiql(self):
        """Test query with complex WIQL syntax."""
        mock_client = MagicMock()

        # Mock query result
        mock_query_result = MagicMock()
        mock_work_item_ref = MagicMock(spec=WorkItemReference)
        mock_work_item_ref.id = "123"
        mock_query_result.work_items = [mock_work_item_ref]
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock work item
        mock_work_item = MagicMock(spec=WorkItem)
        mock_work_item.id = 123
        mock_work_item.fields = {
            "System.WorkItemType": "Bug",
            "System.Title": "High Priority Bug",
            "System.State": "Active",
            "Microsoft.VSTS.Common.Priority": "1",
        }
        mock_client.get_work_items.return_value = [mock_work_item]

        complex_query = """
        SELECT * FROM WorkItems
        WHERE [System.WorkItemType] = 'Bug'
        AND [System.State] = 'Active'
        AND [Microsoft.VSTS.Common.Priority] = 1
        ORDER BY [System.CreatedDate] DESC
        """

        result = _query_work_items_impl(complex_query, 10, mock_client)

        # Verify the query was executed
        assert "# Work Item 123" in result
        assert "High Priority Bug" in result
        mock_client.query_by_wiql.assert_called_once()

    def test_query_with_different_work_item_types(self):
        """Test query returning different work item types."""
        mock_client = MagicMock()

        # Mock query result
        mock_query_result = MagicMock()
        mock_refs = [
            MagicMock(spec=WorkItemReference, id="1"),
            MagicMock(spec=WorkItemReference, id="2"),
            MagicMock(spec=WorkItemReference, id="3"),
            MagicMock(spec=WorkItemReference, id="4"),
        ]
        mock_query_result.work_items = mock_refs
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock different work item types
        work_item_types = [
            ("Bug", "1", "Bug Item"),
            ("Task", "2", "Task Item"),
            ("User Story", "3", "Story Item"),
            ("Epic", "4", "Epic Item"),
        ]

        mock_work_items = []
        for work_type, item_id, title in work_item_types:
            mock_item = MagicMock(spec=WorkItem)
            mock_item.id = int(item_id)
            mock_item.fields = {
                "System.WorkItemType": work_type,
                "System.Title": title,
                "System.State": "Active",
            }
            mock_work_items.append(mock_item)

        mock_client.get_work_items.return_value = mock_work_items

        result = _query_work_items_impl(
            "SELECT * FROM WorkItems", 10, mock_client
        )

        # Verify all work item types are represented
        for work_type, item_id, title in work_item_types:
            assert f"# Work Item {item_id}" in result
            assert title in result
            assert work_type in result

    def test_query_verifies_get_work_items_parameters(self):
        """Test that get_work_items is called with correct parameters."""
        mock_client = MagicMock()

        # Mock query result
        mock_query_result = MagicMock()
        mock_work_item_ref = MagicMock(spec=WorkItemReference)
        mock_work_item_ref.id = "123"
        mock_query_result.work_items = [mock_work_item_ref]
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock work item
        mock_work_item = MagicMock(spec=WorkItem)
        mock_work_item.id = 123
        mock_work_item.fields = {
            "System.WorkItemType": "Bug",
            "System.Title": "Test",
        }
        mock_client.get_work_items.return_value = [mock_work_item]

        _query_work_items_impl("SELECT * FROM WorkItems", 10, mock_client)

        # Verify get_work_items was called with correct parameters
        call_args = mock_client.get_work_items.call_args
        assert call_args[1]["ids"] == [123]
        assert call_args[1]["expand"] == "all"
        assert call_args[1]["error_policy"] == "omit"

    def test_query_formats_output_correctly(self):
        """Test that query output is formatted with double newlines."""
        mock_client = MagicMock()

        # Mock query result with two work items
        mock_query_result = MagicMock()
        mock_refs = [
            MagicMock(spec=WorkItemReference, id="1"),
            MagicMock(spec=WorkItemReference, id="2"),
        ]
        mock_query_result.work_items = mock_refs
        mock_client.query_by_wiql.return_value = mock_query_result

        # Mock work items
        mock_work_items = []
        for i in range(1, 3):
            mock_item = MagicMock(spec=WorkItem)
            mock_item.id = i
            mock_item.fields = {
                "System.WorkItemType": "Bug",
                "System.Title": f"Bug {i}",
            }
            mock_work_items.append(mock_item)

        mock_client.get_work_items.return_value = mock_work_items

        result = _query_work_items_impl(
            "SELECT * FROM WorkItems", 10, mock_client
        )

        # Verify output is separated by double newlines
        assert "\n\n" in result
        parts = result.split("\n\n")
        # Should have 2 work items
        assert len(parts) == 2
