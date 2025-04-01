"""
Work item tools tests.
"""
from unittest.mock import MagicMock, patch
import pytest
from mcp_azure_devops.features.work_items.tools import (
    _create_work_item_impl,
    _format_work_item_basic,
    _query_work_items_impl,
    _get_work_item_impl,
    _get_work_item_comments_impl,
    _upload_attachment_impl,
    _update_work_item_impl,
    _update_work_item_with_attachment_impl
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

def test_upload_attachment_impl_success(tmp_path):
    """測試成功上傳附件的情境"""
    # 準備測試檔案
    test_file = tmp_path / "test.txt"
    test_file.write_text("測試內容")
    
    # 準備測試資料
    mock_client = MagicMock()
    mock_attachment = MagicMock()
    mock_attachment.url = "https://dev.azure.com/test/attachment"
    mock_client.create_attachment.return_value = mock_attachment

    # 執行測試
    url, name = _upload_attachment_impl(
        str(test_file),
        mock_client
    )

    # 驗證結果
    assert url == "https://dev.azure.com/test/attachment"
    assert name == "test.txt"
    mock_client.create_attachment.assert_called_once()

def test_upload_attachment_impl_file_not_found():
    """測試上傳不存在檔案的情境"""
    mock_client = MagicMock()
    
    # 執行測試並驗證例外
    with pytest.raises(FileNotFoundError):
        _upload_attachment_impl(
            "不存在的檔案.txt",
            mock_client
        )

def test_update_work_item_impl_success():
    """測試成功更新工作項目的情境"""
    # 準備測試資料
    mock_client = MagicMock()
    mock_work_item = MagicMock()
    mock_work_item.id = 1
    mock_work_item.fields = {
        "System.Title": "更新後的標題",
        "System.State": "Active",
        "System.TeamProject": "測試專案",
        "System.AreaPath": "測試區域",
        "System.IterationPath": "Sprint 1",
        "System.AssignedTo": {"displayName": "測試使用者"}
    }
    mock_client.update_work_item.return_value = mock_work_item

    # 執行測試
    result = _update_work_item_impl(
        1,
        mock_client,
        title="更新後的標題",
        state="Active",
        area_path="測試區域",
        iteration_path="Sprint 1",
        assigned_to="測試使用者"
    )

    # 驗證結果
    assert "Work Item 1: 更新後的標題" in result
    assert "State: Active" in result

    # 驗證呼叫
    mock_client.update_work_item.assert_called_once()
    call_args = mock_client.update_work_item.call_args
    assert call_args[1]["id"] == 1
    document = call_args[1]["document"]
    assert any(op["path"] == "/fields/System.Title" and op["value"] == "更新後的標題" for op in document)
    assert any(op["path"] == "/fields/System.State" and op["value"] == "Active" for op in document)

def test_update_work_item_impl_no_changes():
    """測試沒有提供任何更新欄位的情境"""
    mock_client = MagicMock()
    
    result = _update_work_item_impl(
        1,
        mock_client
    )
    
    assert "沒有提供任何要更新的欄位" in result
    mock_client.update_work_item.assert_not_called()

def test_update_work_item_impl_error():
    """測試更新工作項目失敗的情境"""
    mock_client = MagicMock()
    mock_client.update_work_item.side_effect = Exception("測試錯誤")

    result = _update_work_item_impl(
        1,
        mock_client,
        title="測試標題"
    )

    assert "更新工作項目時發生錯誤" in result
    assert "測試錯誤" in result

def test_update_work_item_with_attachment_impl_success():
    """測試成功更新工作項目附件的情境"""
    # 準備測試資料
    mock_client = MagicMock()
    mock_work_item = MagicMock()
    mock_work_item.id = 1
    mock_work_item.fields = {
        "System.Title": "測試標題",
        "System.WorkItemType": "Task",
        "System.State": "Active",
        "System.TeamProject": "測試專案"
    }
    mock_client.update_work_item.return_value = mock_work_item

    # 執行測試
    result = _update_work_item_with_attachment_impl(
        1,
        "https://dev.azure.com/test/attachment",
        "test.txt",
        "測試附件",
        mock_client
    )

    # 驗證結果
    assert "Work Item 1: 測試標題" in result
    assert "Type: Task" in result
    
    # 驗證呼叫
    mock_client.update_work_item.assert_called_once()
    call_args = mock_client.update_work_item.call_args
    assert call_args[1]["id"] == 1
    document = call_args[1]["document"]
    assert document[0]["op"] == "add"
    assert document[0]["path"] == "/relations/-"
    assert document[0]["value"]["rel"] == "AttachedFile"
    assert document[0]["value"]["url"] == "https://dev.azure.com/test/attachment"
    assert document[0]["value"]["attributes"]["comment"] == "測試附件"

@pytest.mark.asyncio
async def test_update_work_item_tool():
    """測試更新工作項目工具函式"""
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
    assert "update_work_item" in tool_registry
    
    # 準備測試資料
    with patch("mcp_azure_devops.features.work_items.tools.get_work_item_client") as mock_get_client:
        mock_client = MagicMock()
        mock_work_item = MagicMock()
        mock_work_item.id = 1
        mock_work_item.fields = {
            "System.Title": "更新後的標題",
            "System.State": "Active",
            "System.TeamProject": "測試專案"
        }
        mock_client.update_work_item.return_value = mock_work_item
        mock_get_client.return_value = mock_client
        
        # 執行測試
        result = tool_registry["update_work_item"](
            id=1,
            title="更新後的標題",
            state="Active"
        )
        
        # 驗證結果
        assert "Work Item 1: 更新後的標題" in result
        assert "State: Active" in result
        assert "Project: 測試專案" in result

@pytest.mark.asyncio
async def test_add_work_item_attachment_tool():
    """測試新增工作項目附件工具函式"""
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
    assert "add_work_item_attachment" in tool_registry
    
    # 準備測試檔案
    test_file = "test.txt"
    mock_file = MagicMock(spec=open)
    mock_file.read.return_value = "測試內容"
    
    # 準備測試資料
    with patch("mcp_azure_devops.features.work_items.tools.get_work_item_client") as mock_get_client, \
         patch("builtins.open", return_value=mock_file), \
         patch("os.path.exists", return_value=True):
        mock_client = MagicMock()
        
        # 模擬附件上傳
        mock_attachment = MagicMock()
        mock_attachment.url = "https://dev.azure.com/test/attachment"
        mock_client.create_attachment.return_value = mock_attachment
        
        # 模擬工作項目更新
        mock_work_item = MagicMock()
        mock_work_item.id = 1
        mock_work_item.fields = {
            "System.Title": "測試標題",
            "System.WorkItemType": "Task",
            "System.State": "Active",
            "System.TeamProject": "測試專案"
        }
        mock_client.update_work_item.return_value = mock_work_item
        mock_get_client.return_value = mock_client
        
        # 執行測試
        result = tool_registry["add_work_item_attachment"](
            id=1,
            file_path=test_file,
            comment="測試附件"
        )
        
        # 驗證結果
        assert "Work Item 1: 測試標題" in result
        assert "Type: Task" in result
        assert "Project: 測試專案" in result

        # 驗證檔案上傳
        mock_client.create_attachment.assert_called_once()
        
        # 驗證工作項目更新
        mock_client.update_work_item.assert_called_once()
        call_args = mock_client.update_work_item.call_args
        document = call_args[1]["document"]
        assert document[0]["value"]["rel"] == "AttachedFile"
        assert document[0]["value"]["url"] == "https://dev.azure.com/test/attachment"
        assert document[0]["value"]["attributes"]["comment"] == "測試附件"
