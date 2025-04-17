"""
Work item tools for Azure DevOps.

This module provides MCP tools for working with Azure DevOps work items.
"""
import os
from typing import Optional, List
from azure.devops.v7_1.work_item_tracking.models import Wiql, WorkItem
from azure.devops.v7_1.work_item_tracking import WorkItemTrackingClient
from mcp_azure_devops.utils.azure_client import get_connection
from mcp_azure_devops.features.work_items.common import get_work_item_client, AzureDevOpsClientError


def _format_work_item_basic(work_item: WorkItem) -> str:
    """
    Format basic work item information.
    
    Args:
        work_item: Work item object to format
        
    Returns:
        String with basic work item details
    """
    fields = work_item.fields or {}
    title = fields.get("System.Title", "Untitled")
    item_type = fields.get("System.WorkItemType", "Unknown")
    state = fields.get("System.State", "Unknown")
    project = fields.get("System.TeamProject", "Unknown")
    
    # Add link to the work item (if available)
    url_part = ""
    # Safely handle the _links attribute which is a ReferenceLinks object, not a dictionary
    try:
        if hasattr(work_item, '_links') and work_item._links:
            if hasattr(work_item._links, 'self') and hasattr(work_item._links.html, 'href'):
                url_part = f"\nWeb URL: {work_item._links.html.href}"
    except Exception:
        # If any error occurs, just skip adding the URL
        pass
    
    return f"# Work Item {work_item.id}: {title}\nType: {item_type}\nState: {state}\nProject: {project}{url_part}"


def _format_work_item_detailed(work_item: WorkItem, basic_info: str) -> str:
    """
    Add detailed information to basic work item information.
    
    Args:
        work_item: Work item object to format
        basic_info: Already formatted basic information
        
    Returns:
        String with comprehensive work item details
    """
    details = [basic_info]  # Start with basic info already provided
    
    fields = work_item.fields or {}
    if "System.Description" in fields:
        details.append("\n## Description")
        # 將描述中的換行符號轉換為 Markdown 換行格式 (雙空格加換行符)
        description = fields["System.Description"].replace('\n', '  \n')
        details.append(description)
    
    # 新增 Tags 資訊
    if "System.Tags" in fields and fields["System.Tags"]:
        details.append("\n## Tags")
        details.append(fields["System.Tags"])
    
    # 新增 Remaining Work 資訊
    if "Microsoft.VSTS.Scheduling.RemainingWork" in fields:
        details.append("\n## Remaining Work")
        details.append(f"{fields['Microsoft.VSTS.Scheduling.RemainingWork']} hours")
    
    # Add acceptance criteria if available
    if "Microsoft.VSTS.Common.AcceptanceCriteria" in fields:
        details.append("\n## Acceptance Criteria")
        details.append(fields["Microsoft.VSTS.Common.AcceptanceCriteria"])
    
    # Add repro steps if available
    if "Microsoft.VSTS.TCM.ReproSteps" in fields:
        details.append("\n## Repro Steps")
        details.append(fields["Microsoft.VSTS.TCM.ReproSteps"])
    
    # Add additional details section
    details.append("\n## Additional Details")
    
    if "System.AssignedTo" in fields:
        assigned_to = fields['System.AssignedTo']
        # Handle the AssignedTo object which could be a dict or dictionary-like object
        if hasattr(assigned_to, 'display_name') and hasattr(assigned_to, 'unique_name'):
            # If it's an object with directly accessible properties
            details.append(f"Assigned To: {assigned_to.display_name} ({assigned_to.unique_name})")
        elif isinstance(assigned_to, dict):
            # If it's a dictionary
            display_name = assigned_to.get('displayName', '')
            unique_name = assigned_to.get('uniqueName', '')
            details.append(f"Assigned To: {display_name} ({unique_name})")
        else:
            # Fallback to display the raw value if we can't parse it
            details.append(f"Assigned To: {assigned_to}")
    
    # Add created by information
    if "System.CreatedBy" in fields:
        created_by = fields['System.CreatedBy']
        if hasattr(created_by, 'display_name'):
            details.append(f"Created By: {created_by.display_name}")
        elif isinstance(created_by, dict) and 'displayName' in created_by:
            details.append(f"Created By: {created_by['displayName']}")
        else:
            details.append(f"Created By: {created_by}")
    
    # Add created date
    if "System.CreatedDate" in fields:
        details.append(f"Created Date: {fields['System.CreatedDate']}")
    
    # Add last updated information
    if "System.ChangedDate" in fields:
        changed_date = fields['System.ChangedDate']
        
        # Add the changed by information if available
        if "System.ChangedBy" in fields:
            changed_by = fields['System.ChangedBy']
            if hasattr(changed_by, 'display_name'):
                details.append(f"Last updated {changed_date} by {changed_by.display_name}")
            elif isinstance(changed_by, dict) and 'displayName' in changed_by:
                details.append(f"Last updated {changed_date} by {changed_by['displayName']}")
            else:
                details.append(f"Last updated {changed_date} by {changed_by}")
        else:
            details.append(f"Last updated: {changed_date}")
    
    if "System.IterationPath" in fields:
        details.append(f"Iteration: {fields['System.IterationPath']}")
    
    if "System.AreaPath" in fields:
        details.append(f"Area: {fields['System.AreaPath']}")
    
    # Add tags
    if "System.Tags" in fields and fields["System.Tags"]:
        details.append(f"Tags: {fields['System.Tags']}")
    
    # Add priority
    if "Microsoft.VSTS.Common.Priority" in fields:
        details.append(f"Priority: {fields['Microsoft.VSTS.Common.Priority']}")
    
    # Add effort/story points (could be in different fields depending on process template)
    if "Microsoft.VSTS.Scheduling.Effort" in fields:
        details.append(f"Effort: {fields['Microsoft.VSTS.Scheduling.Effort']}")
    if "Microsoft.VSTS.Scheduling.StoryPoints" in fields:
        details.append(f"Story Points: {fields['Microsoft.VSTS.Scheduling.StoryPoints']}")
    
    # Add related items section if available
    if hasattr(work_item, 'relations') and work_item.relations:
        details.append("\n## Related Items")
        
        for relation in work_item.relations:
            # Get the relation type (use getattr to safely handle missing attributes)
            rel_type = getattr(relation, 'rel', "Unknown relation")
            
            # Get the target URL
            target_url = getattr(relation, 'url', "Unknown URL")
            
            # Format the link based on what type it is
            link_text = target_url
            if "workitem" in target_url.lower():
                # It's a work item link - try to extract the ID
                try:
                    work_item_id = target_url.split('/')[-1]
                    if work_item_id.isdigit():
                        link_text = f"Work Item #{work_item_id}"
                except:
                    pass  # Keep the original URL if parsing fails
            
            # Check for comments in attributes
            comment = ""
            if hasattr(relation, 'attributes') and relation.attributes:
                attrs = relation.attributes
                if isinstance(attrs, dict) and 'comment' in attrs and attrs['comment']:
                    comment = f" - Comment: {attrs['comment']}"
            
            details.append(f"- {rel_type}: {link_text}{comment}")
    
    return "\n".join(details)


def _get_work_item_impl(
    item_id: int,
    wit_client: WorkItemTrackingClient,
    detailed: bool = False
) -> str:
    """
    Implementation of work item retrieval.
    
    Args:
        item_id: The work item ID
        wit_client: Work item tracking client
        detailed: Whether to return detailed information
            
    Returns:
        Formatted string containing work item information
    """
    try:
        work_item = wit_client.get_work_item(item_id, expand="all")
        
        # Always format basic info first
        basic_info = _format_work_item_basic(work_item)
        
        # If detailed is requested, add more information
        if detailed:
            return _format_work_item_detailed(work_item, basic_info)
        else:
            return basic_info
            
    except Exception as e:
        return f"Error retrieving work item {item_id}: {str(e)}"




def _get_work_item_comments_impl(
    item_id: int,
    wit_client: WorkItemTrackingClient,
    project: Optional[str] = None
) -> str:
    """
    Implementation of work item comments retrieval.
    
    Args:
        item_id: The work item ID
        wit_client: Work item tracking client
        project: Optional project name
            
    Returns:
        Formatted string containing work item comments
    """
    # If project is not provided, try to get it from the work item
    if not project:
        try:
            work_item = wit_client.get_work_item(item_id)
            if work_item and work_item.fields:
                project = work_item.fields.get("System.TeamProject")
        except Exception as e:
            return f"Error retrieving work item {item_id} to determine project: {str(e)}"
    
    # Get comments using the project if available
    comments = wit_client.get_comments(project=project, work_item_id=item_id)
    
    # Format the comments
    formatted_comments = []
    for comment in comments.comments:
        # Format the date if available
        created_date = ""
        if hasattr(comment, 'created_date') and comment.created_date:
            created_date = f" on {comment.created_date}"
        
        # Format the author if available
        author = "Unknown"
        if hasattr(comment, 'created_by') and comment.created_by:
            if hasattr(comment.created_by, 'display_name') and comment.created_by.display_name:
                author = comment.created_by.display_name
        
        # Format the comment text
        text = "No text"
        if hasattr(comment, 'text') and comment.text:
            text = comment.text
        
        formatted_comments.append(f"## Comment by {author}{created_date}:\n{text}")
    
    if not formatted_comments:
        return "No comments found for this work item."
    
    return "\n\n".join(formatted_comments)


def _query_work_items_impl(
    query: str, 
    top: int,
    wit_client: WorkItemTrackingClient
) -> str:
    """
    Implementation of query_work_items that operates with a client.
    
    Args:
        query: The WIQL query string
        top: Maximum number of results to return
        wit_client: Work item tracking client
            
    Returns:
        Formatted string containing work item details
    """
    
    # Create the WIQL query
    wiql = Wiql(query=query)
    
    # Execute the query
    wiql_results = wit_client.query_by_wiql(wiql, top=top).work_items
    
    if not wiql_results:
        return "No work items found matching the query."
    
    # Get the work items from the results
    work_item_ids = [int(res.id) for res in wiql_results]
    work_items = wit_client.get_work_items(ids=work_item_ids, error_policy="omit")
    
    # Use the same formatting as get_work_item_basic
    formatted_results = []
    for work_item in work_items:
        if work_item:
            formatted_results.append(_format_work_item_basic(work_item))
    
    return "\n\n".join(formatted_results)


def _create_work_item_impl(
    project: str,
    title: str,
    description: str,
    work_item_type: str,
    wit_client: WorkItemTrackingClient,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None
) -> str:
    """
    建立工作項目的實作。

    Args:
        project: 專案名稱
        title: 工作項目標題
        description: 工作項目描述 (選填，會自動轉換為 HTML 格式)
        work_item_type: 工作項目類型 (例如: Bug, Task, User Story)
        wit_client: 工作項目追蹤客戶端
        area_path: 區域路徑 (選填)
        iteration_path: 迭代路徑 (選填)
            
    Returns:
        已格式化的字串，包含新建立的工作項目資訊
    """
    try:
        # 自動轉換 description 為 HTML 格式，保留換行
        if description and not (description.strip().startswith('<') and ('>' in description) and 
              ('<html' in description.lower() or '<p>' in description.lower() or '<div' in description.lower())):
            description = f"<div>{description.replace('\n', '<br>')}</div>"

        # 建立工作項目的欄位
        document = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": title
            },
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": description
            }
        ]

        # 如果有提供區域路徑，加入設定
        if area_path:
            document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": area_path
            })

        # 如果有提供迭代路徑，加入設定
        if iteration_path:
            document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": iteration_path
            })

        # 建立工作項目
        created_item = wit_client.create_work_item(
            document=document,
            project=project,
            type=work_item_type
        )

        # 回傳基本資訊
        return _format_work_item_basic(created_item)

    except Exception as e:
        return f"建立工作項目時發生錯誤: {str(e)}"


def _upload_attachment_impl(
    file_path: str,
    wit_client: WorkItemTrackingClient,
    project: Optional[str] = None
) -> tuple[str, str]:
    """
    上傳檔案附件到 Azure DevOps。

    Args:
        file_path: 本機檔案路徑
        wit_client: 工作項目追蹤客戶端
        project: 專案名稱 (選填)
            
    Returns:
        tuple[str, str]: (附件 URL, 附件名稱)
    """
    try:
        # 檢查檔案是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到檔案: {file_path}")

        # 取得檔案名稱
        file_name = os.path.basename(file_path)
        # 讀取檔案內容為位元組
        with open(file_path, 'rb') as f:
            file_content = f.read()
        # 建立位元組串流
        from io import BytesIO
        upload_stream = BytesIO(file_content)
        # 上傳附件
        attachment = wit_client.create_attachment(
            upload_stream=upload_stream,
            file_name=file_name,
            project=project
        )
        return attachment.url, file_name
    except FileNotFoundError:
        raise
    except Exception as e:
        raise Exception(f"上傳附件時發生錯誤: {str(e)}")


def _update_work_item_impl(
    item_id: int,
    wit_client: WorkItemTrackingClient,
    title: Optional[str] = None,
    description: Optional[str] = None,
    state: Optional[str] = None,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    assigned_to: Optional[str] = None,
    tags: Optional[str] = None
) -> str:
    """
    更新工作項目的實作。

    Args:
        item_id: 工作項目 ID
        wit_client: 工作項目追蹤客戶端
        title: 工作項目標題 (選填)
        description: 工作項目描述 (選填，會自動轉換為 HTML 格式)
        state: 工作項目狀態 (選填)
        area_path: 區域路徑 (選填)
        iteration_path: 迭代路徑 (選填)
        assigned_to: 指派給 (選填)
        tags: 標籤，多個標籤用分號分隔 (選填，例如: "tag1; tag2")
            
    Returns:
        已格式化的字串，包含更新後的工作項目資訊
    """
    try:
        # 建立更新文件
        document = []
        
        # 只更新有提供的欄位
        if title:
            document.append({
                "op": "add",
                "path": "/fields/System.Title",
                "value": title
            })
            
        if description:
            # 檢查是否已是 HTML 格式
            if not (description.strip().startswith('<') and ('>' in description) and 
                  ('<html' in description.lower() or '<p>' in description.lower() or '<div' in description.lower())):
                # 自動轉換為 HTML 格式，保留換行
                description = f"<div>{description.replace('\n', '<br>')}</div>"
            
            document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": description
            })
            
        if state:
            document.append({
                "op": "add",
                "path": "/fields/System.State",
                "value": state
            })
            
        if area_path:
            document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": area_path
            })
            
        if iteration_path:
            document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": iteration_path
            })
            
        if assigned_to:
            document.append({
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "value": assigned_to
            })

        # 新增 tags 的處理
        if tags is not None:  # 使用 is not None 來允許空字串作為清除標籤的方式
            document.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": tags
            })

        if not document:
            return "沒有提供任何要更新的欄位"

        # 更新工作項目
        updated_item = wit_client.update_work_item(
            document=document,
            id=item_id
        )

        # 回傳更新後的基本資訊
        return _format_work_item_basic(updated_item)

    except Exception as e:
        return f"更新工作項目時發生錯誤: {str(e)}"


def _update_work_item_with_attachment_impl(
    item_id: int,
    attachment_url: str,
    attachment_name: str,
    comment: Optional[str],
    wit_client: WorkItemTrackingClient
) -> str:
    """
    更新工作項目並加入附件。

    Args:
        item_id: 工作項目 ID
        attachment_url: 附件 URL
        attachment_name: 附件名稱
        comment: 附件說明 (選填)
        wit_client: 工作項目追蹤客戶端
            
    Returns:
        str: 更新後的工作項目資訊
    """
    try:
        # 建立更新文件
        document = [{
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "AttachedFile",
                "url": attachment_url,
                "attributes": {
                    "comment": comment or f"已上傳附件: {attachment_name}"
                }
            }
        }]

        # 更新工作項目
        updated_item = wit_client.update_work_item(
            document=document,
            id=item_id
        )

        return _format_work_item_basic(updated_item)

    except Exception as e:
        return f"更新工作項目時發生錯誤: {str(e)}"


def _add_work_item_comment_impl(
    item_id: int,
    comment: str,
    wit_client: WorkItemTrackingClient,
    project: Optional[str] = None
) -> str:
    """
    替工作項目新增評論的實作。

    Args:
        item_id: 工作項目 ID
        comment: 評論內容
        wit_client: 工作項目追蹤客戶端
        project: 專案名稱 (選填)
            
    Returns:
        已格式化的字串，包含新增評論後的工作項目資訊
    """
    try:
        # 如果沒有提供專案名稱，從工作項目取得
        if not project:
            work_item = wit_client.get_work_item(item_id)
            if work_item and work_item.fields:
                project = work_item.fields.get("System.TeamProject")
                if not project:
                    raise ValueError("無法確定專案名稱")
        # 新增評論
        wit_client.add_comment(
            project=project,
            work_item_id=item_id,
            request={"text": comment}
        )
        # 取得更新後的工作項目資訊
        return _get_work_item_impl(item_id, wit_client, detailed=True)
    except Exception as e:
        return f"新增評論時發生錯誤: {str(e)}"


def register_tools(mcp) -> None:
    """
    向 MCP 伺服器註冊工作項目工具。
    
    Args:
        mcp: FastMCP 伺服器實例
    """
    
    @mcp.tool()
    def query_work_items(
        query: str, 
        top: Optional[int]
    ) -> str:
        """
        Query work items using WIQL.
        
        Args:
            query: The WIQL query string
            top: Maximum number of results to return (default: 30)
                
        Returns:
            Formatted string containing work item details
        """
        try:
            wit_client = get_work_item_client()
            # Ensure top is not None before passing to implementation
            return _query_work_items_impl(query, top or 30, wit_client)
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    def get_work_item_basic(
        id: int
    ) -> str:
        """
        Get basic information about a work item.
        
        Args:
            id: The work item ID
            
        Returns:
            Formatted string containing basic work item information
        """
        try:
            wit_client = get_work_item_client()
            return _get_work_item_impl(id, wit_client, detailed=False)
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    def get_work_item_details(
        id: int
    ) -> str:
        """
        Get detailed information about a work item.
        
        Args:
            id: The work item ID
            
        Returns:
            Formatted string containing comprehensive work item information
        """
        try:
            wit_client = get_work_item_client()
            return _get_work_item_impl(id, wit_client, detailed=True)
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    def get_work_item_comments(
        id: int,
        project: Optional[str] = None
    ) -> str:
        """
        Get all comments for a work item.
    
        Args:
            id: The work item ID
            project: Optional project name. If not provided, will be determined from the work item.
            
        Returns:
            Formatted string containing all comments on the work item
        """
        try:
            wit_client = get_work_item_client()
            return _get_work_item_comments_impl(id, wit_client, project)
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    def create_work_item(
        project: str,
        title: str,
        description: str,
        work_item_type: str = "Task",
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None
    ) -> str:
        r"""
        建立新的工作項目。

        Args:
            project: 專案名稱
            title: 工作項目標題
            description: 工作項目描述 (選填，會自動轉換為 HTML 格式)
            work_item_type: 工作項目類型 (預設: Task)
            area_path: 區域路徑 (選填，例如: G11n\OKR)
            iteration_path: 迭代路徑 (選填，例如: G11n\Sprint 189)
            
        Returns:
            已格式化的字串，包含新建立的工作項目資訊
        """
        try:
            wit_client = get_work_item_client()
            return _create_work_item_impl(
                project,
                title,
                description,
                work_item_type,
                wit_client,
                area_path,
                iteration_path
            )
        except AzureDevOpsClientError as e:
            return f"錯誤: {str(e)}"

    @mcp.tool()
    def update_work_item(
        id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        state: Optional[str] = None,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[str] = None  # 新增 tags 參數
    ) -> str:
        """
        更新工作項目。

        Args:
            id: 工作項目 ID
            title: 工作項目標題 (選填)
            description: 工作項目描述 (選填，會自動轉換為 HTML 格式) (選填)
            state: 工作項目狀態 (選填)
            area_path: 區域路徑 (選填)
            iteration_path: 迭代路徑 (選填)
            assigned_to: 指派給 (選填)
            
        Returns:
            已格式化的字串，包含更新後的工作項目資訊
        """
        try:
            wit_client = get_work_item_client()
            return _update_work_item_impl(
                id,
                wit_client,
                title,
                description,
                state,
                area_path,
                iteration_path,
                assigned_to,
                tags  # 加入 tags 參數
            )
        except AzureDevOpsClientError as e:
            return f"錯誤: {str(e)}"

    @mcp.tool()
    def add_work_item_attachment(
        id: int,
        file_path: str,
        comment: Optional[str] = None,
        project: Optional[str] = None
    ) -> str:
        """
        替工作項目新增附件。

        Args:
            id: 工作項目 ID
            file_path: 本機檔案路徑
            comment: 附件說明 (選填)
            project: 專案名稱 (選填)
            
        Returns:
            更新後的工作項目資訊
        """
        try:
            wit_client = get_work_item_client()
            
            # 上傳附件
            attachment_url, attachment_name = _upload_attachment_impl(
                file_path,
                wit_client,
                project
            )
            
            # 更新工作項目
            return _update_work_item_with_attachment_impl(
                id,
                attachment_url,
                attachment_name,
                comment,
                wit_client
            )
            
        except AzureDevOpsClientError as e:
            return f"錯誤: {str(e)}"
    
    @mcp.tool()
    def add_work_item_comment(
        id: int,
        comment: str,
        project: Optional[str] = None
    ) -> str:
        """
        替工作項目新增評論。

        Args:
            id: 工作項目 ID
            comment: 評論內容
            project: 專案名稱 (選填)
            
        Returns:
            更新後的工作項目資訊
        """
        try:
            wit_client = get_work_item_client()
            return _add_work_item_comment_impl(id, comment, wit_client, project)
        except AzureDevOpsClientError as e:
            return f"錯誤: {str(e)}"
