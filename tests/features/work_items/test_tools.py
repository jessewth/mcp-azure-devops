"""
Work item tools tests.
"""
from unittest.mock import MagicMock, patch
import pytest
from mcp_azure_devops.features.work_items.tools import (
    _create_work_item_impl,
    _format_work_item_basic
)

# Tests for _query_work_items_impl
def test_query_work_items_impl_no_results():
    """Test query with no results."""
    mock_client = MagicMock()
    mock_query_result = MagicMock()
    mock_query_result.work_items = []
    mock_client.query_by_wiql.return_value = mock_query_result
    
    result = _query_work_items_impl("SELECT * FROM WorkItems", 10, mock_client)
    assert result == "No work items found matching the query."

def test_query_work_items_impl_with_results():
    """Test query with results."""
    mock_client = MagicMock()
    
    # Mock query result
    mock_query_result = MagicMock()
    mock_work_item_ref1 = MagicMock(spec=WorkItemReference)
    mock_work_item_ref1.id = "123"
    mock_work_item_ref2 = MagicMock(spec=WorkItemReference)
    mock_work_item_ref2.id = "456"
    mock_query_result.work_items = [mock_work_item_ref1, mock_work_item_ref2]
    mock_client.query_by_wiql.return_value = mock_query_result
    
    # Mock work items
    mock_work_item1 = MagicMock(spec=WorkItem)
    mock_work_item1.id = 123
    mock_work_item1.fields = {
        "System.WorkItemType": "Bug",
        "System.Title": "Test Bug",
        "System.State": "Active"
    }
    
    mock_work_item2 = MagicMock(spec=WorkItem)
    mock_work_item2.id = 456
    mock_work_item2.fields = {
        "System.WorkItemType": "Task",
        "System.Title": "Test Task",
        "System.State": "Closed"
    }
    
    mock_client.get_work_items.return_value = [mock_work_item1, mock_work_item2]
    
    result = _query_work_items_impl("SELECT * FROM WorkItems", 10, mock_client)
    
    # Check that the result contains the expected basic info formatting
    assert "# Work Item 123: Test Bug" in result
    assert "Type: Bug" in result
    assert "State: Active" in result
    assert "# Work Item 456: Test Task" in result
    assert "Type: Task" in result
    assert "State: Closed" in result


# Tests for _get_work_item_impl
def test_get_work_item_impl_basic():
    """Test retrieving basic work item info."""
    mock_client = MagicMock()
    
    # Mock work item
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.id = 123
    mock_work_item.fields = {
        "System.WorkItemType": "Bug",
        "System.Title": "Test Bug",
        "System.State": "Active",
        "System.TeamProject": "Test Project"
    }
    mock_client.get_work_item.return_value = mock_work_item
    
    result = _get_work_item_impl(123, mock_client, detailed=False)
    
    # Check that the result contains expected basic info
    assert "# Work Item 123: Test Bug" in result
    assert "Type: Bug" in result
    assert "State: Active" in result
    assert "Project: Test Project" in result

def test_get_work_item_impl_detailed():
    """Test retrieving detailed work item info."""
    mock_client = MagicMock()
    
    # Mock work item with more fields for detailed view
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.id = 123
    mock_work_item.fields = {
        "System.WorkItemType": "Bug",
        "System.Title": "Test Bug",
        "System.State": "Active",
        "System.TeamProject": "Test Project",
        "System.Description": "This is a description",
        "System.AssignedTo": {"displayName": "Test User", "uniqueName": "test@example.com"},
        "System.CreatedBy": {"displayName": "Creator User"},
        "System.CreatedDate": "2023-01-01",
        "System.IterationPath": "Project\\Sprint 1",
        "System.AreaPath": "Project\\Area",
        "System.Tags": "tag1; tag2",
    }
    mock_client.get_work_item.return_value = mock_work_item
    
    result = _get_work_item_impl(123, mock_client, detailed=True)
    
    # Check that the result contains both basic and detailed info
    assert "# Work Item 123: Test Bug" in result
    assert "Type: Bug" in result
    assert "Description" in result
    assert "This is a description" in result
    assert "Assigned To: Test User (test@example.com)" in result
    assert "Created By: Creator User" in result
    assert "Iteration: Project\\Sprint 1" in result

def test_get_work_item_impl_error():
    """Test error handling in get_work_item_impl."""
    mock_client = MagicMock()
    mock_client.get_work_item.side_effect = Exception("Test error")
    
    result = _get_work_item_impl(123, mock_client, detailed=False)
    
    assert "Error retrieving work item 123: Test error" in result

# Tests for _get_work_item_comments_impl
def test_get_work_item_comments_impl():
    """Test retrieving work item comments."""
    mock_client = MagicMock()
    
    # Mock work item for project lookup
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = {"System.TeamProject": "Test Project"}
    mock_client.get_work_item.return_value = mock_work_item
    
    # Mock comments
    mock_comment1 = MagicMock()
    mock_comment1.text = "This is comment 1"
    mock_created_by = MagicMock()
    mock_created_by.display_name = "Comment User"
    mock_comment1.created_by = mock_created_by
    mock_comment1.created_date = "2023-01-02"
    
    mock_comments = MagicMock()
    mock_comments.comments = [mock_comment1]
    mock_client.get_comments.return_value = mock_comments
    
    result = _get_work_item_comments_impl(123, mock_client)
    
    assert "## Comment by Comment User on 2023-01-02" in result
    assert "This is comment 1" in result

def test_get_work_item_comments_impl_no_comments():
    """Test retrieving work item with no comments."""
    mock_client = MagicMock()
    
    # Mock work item for project lookup
    mock_work_item = MagicMock(spec=WorkItem)
    mock_work_item.fields = {"System.TeamProject": "Test Project"}
    mock_client.get_work_item.return_value = mock_work_item
    
    # Mock empty comments
    mock_comments = MagicMock()
    mock_comments.comments = []
    mock_client.get_comments.return_value = mock_comments
    
    result = _get_work_item_comments_impl(123, mock_client)
    
    assert "No comments found for this work item." in result


# Tests for _create_work_item_impl
def test_create_work_item_impl_success():
    """測試成功建立工作項目的情境"""
    # 準備測試資料
    mock_client = MagicMock()
    mock_work_item = MagicMock()
    mock_work_item.id = 1
    mock_work_item.fields = {
        "System.Title": "測試標題",
        "System.WorkItemType": "Task",
        "System.State": "New",
        "System.TeamProject": "測試專案"
    }
    mock_client.create_work_item.return_value = mock_work_item

    # 執行測試
    result = _create_work_item_impl(
        project="測試專案",
        title="測試標題",
        description="測試描述",
        work_item_type="Task",
        wit_client=mock_client
    )

    # 驗證結果
    assert "Work Item 1: 測試標題" in result
    assert "Type: Task" in result
    assert "State: New" in result
    assert "Project: 測試專案" in result

    # 驗證呼叫
    mock_client.create_work_item.assert_called_once()
    call_args = mock_client.create_work_item.call_args
    assert call_args[1]["project"] == "測試專案"
    assert call_args[1]["type"] == "Task"
    document = call_args[1]["document"]
    assert any(op["path"] == "/fields/System.Title" and op["value"] == "測試標題" for op in document)
    assert any(op["path"] == "/fields/System.Description" and op["value"] == "測試描述" for op in document)

def test_create_work_item_impl_error():
    """測試建立工作項目失敗的情境"""
    # 準備測試資料
    mock_client = MagicMock()
    mock_client.create_work_item.side_effect = Exception("測試錯誤")

    # 執行測試
    result = _create_work_item_impl(
        project="測試專案",
        title="測試標題",
        description="測試描述",
        work_item_type="Task",
        wit_client=mock_client
    )

    # 驗證結果
    assert "建立工作項目時發生錯誤" in result
    assert "測試錯誤" in result

@pytest.mark.asyncio
async def test_create_work_item_tool():
    """測試建立工作項目工具函式"""
    from mcp_azure_devops.features.work_items.tools import register_tools
    
    # 建立模擬的 MCP 伺服器
    mock_mcp = MagicMock()
    tool_registry = {}
    
    def mock_tool():
        def decorator(f):
            tool_registry[f.__name__] = f
            return f
        return decorator
    
    mock_mcp.tool = mock_tool
    
    # 註冊工具
    register_tools(mock_mcp)
    
    # 驗證工具是否已註冊
    assert "create_work_item" in tool_registry
    
    # 準備測試資料
    with patch("mcp_azure_devops.features.work_items.tools.get_work_item_client") as mock_get_client:
        mock_client = MagicMock()
        mock_work_item = MagicMock()
        mock_work_item.id = 1
        mock_work_item.fields = {
            "System.Title": "測試標題",
            "System.WorkItemType": "Task",
            "System.State": "New",
            "System.TeamProject": "測試專案"
        }
        mock_client.create_work_item.return_value = mock_work_item
        mock_get_client.return_value = mock_client
        
        # 執行測試
        result = tool_registry["create_work_item"](
            project="測試專案",
            title="測試標題",
            description="測試描述"
        )
        
        # 驗證結果
        assert "Work Item 1: 測試標題" in result
        assert "Type: Task" in result
        assert "State: New" in result
        assert "Project: 測試專案" in result

def test_create_work_item_impl_with_area_and_iteration():
    """測試建立工作項目時包含區域路徑和迭代路徑的情境"""
    # 準備測試資料
    mock_client = MagicMock()
    mock_work_item = MagicMock()
    mock_work_item.id = 1
    mock_work_item.fields = {
        "System.Title": "測試標題",
        "System.WorkItemType": "Task",
        "System.State": "New",
        "System.TeamProject": "測試專案",
        "System.AreaPath": "G11n\\OKR",
        "System.IterationPath": "G11n\\Sprint 189"
    }
    mock_client.create_work_item.return_value = mock_work_item

    # 執行測試
    result = _create_work_item_impl(
        project="測試專案",
        title="測試標題",
        description="測試描述",
        work_item_type="Task",
        wit_client=mock_client,
        area_path="G11n\\OKR",
        iteration_path="G11n\\Sprint 189"
    )

    # 驗證結果
    assert "Work Item 1: 測試標題" in result
    assert "Type: Task" in result
    assert "State: New" in result
    assert "Project: 測試專案" in result

    # 驗證呼叫
    mock_client.create_work_item.assert_called_once()
    call_args = mock_client.create_work_item.call_args
    assert call_args[1]["project"] == "測試專案"
    assert call_args[1]["type"] == "Task"
    document = call_args[1]["document"]
    assert any(op["path"] == "/fields/System.Title" and op["value"] == "測試標題" for op in document)
    assert any(op["path"] == "/fields/System.Description" and op["value"] == "測試描述" for op in document)
    assert any(op["path"] == "/fields/System.AreaPath" and op["value"] == "G11n\\OKR" for op in document)
    assert any(op["path"] == "/fields/System.IterationPath" and op["value"] == "G11n\\Sprint 189" for op in document)

@pytest.mark.asyncio
async def test_create_work_item_tool_with_area_and_iteration():
    """測試建立工作項目工具函式，包含區域路徑和迭代路徑"""
    from mcp_azure_devops.features.work_items.tools import register_tools
    
    # 建立模擬的 MCP 伺服器
    mock_mcp = MagicMock()
    tool_registry = {}
    
    def mock_tool():
        def decorator(f):
            tool_registry[f.__name__] = f
            return f
        return decorator
    
    mock_mcp.tool = mock_tool
    
    # 註冊工具
    register_tools(mock_mcp)
    
    # 驗證工具是否已註冊
    assert "create_work_item" in tool_registry
    
    # 準備測試資料
    with patch("mcp_azure_devops.features.work_items.tools.get_work_item_client") as mock_get_client:
        mock_client = MagicMock()
        mock_work_item = MagicMock()
        mock_work_item.id = 1
        mock_work_item.fields = {
            "System.Title": "測試標題",
            "System.WorkItemType": "Task",
            "System.State": "New",
            "System.TeamProject": "測試專案",
            "System.AreaPath": "G11n\\OKR",
            "System.IterationPath": "G11n\\Sprint 189"
        }
        mock_client.create_work_item.return_value = mock_work_item
        mock_get_client.return_value = mock_client
        
        # 執行測試
        result = tool_registry["create_work_item"](
            project="測試專案",
            title="測試標題",
            description="測試描述",
            work_item_type="Task",
            area_path="G11n\\OKR",
            iteration_path="G11n\\Sprint 189"
        )
        
        # 驗證結果
        assert "Work Item 1: 測試標題" in result
        assert "Type: Task" in result
        assert "State: New" in result
        assert "Project: 測試專案" in result
