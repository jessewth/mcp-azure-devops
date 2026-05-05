# 下載 Attachments 功能規劃分析

## 1. 背景與目標

### 現有功能

目前 `attachments.py` 模組提供兩個 MCP 工具：

| 工具名稱 | 功能 |
|---------|------|
| `add_work_item_attachment` | 上傳本地檔案並附加到 Work Item |
| `get_work_item_attachments` | 取得 Work Item 的附件清單（僅回傳 URL 和 metadata） |

### 缺失功能

目前 **沒有** 下載附件的功能。`get_work_item_attachments` 只回傳附件的 URL、名稱、類型等 metadata，無法將附件內容實際下載到本地檔案系統。

### 目標

新增 `download_work_item_attachment` MCP 工具，允許 AI 助手從 Azure DevOps Work Item 下載附件到本地。

---

## 2. Azure DevOps SDK API 分析

### 可用 API 方法

Azure DevOps Python SDK (`azure-devops>=7.1.0b4`) 的 `WorkItemTrackingClient` 提供：

```python
def get_attachment_content(self, id, file_name=None, download=None):
    """
    下載附件內容。

    :param str id: 附件的唯一識別碼 (GUID)
    :param str file_name: (可選) 檔案名稱
    :param bool download: (可選) 是否觸發下載
    :return: 附件的二進位內容 (stream)
    """
```

### 附件 ID 取得方式

附件 URL 格式通常為：
```
https://dev.azure.com/{org}/{project}/_apis/wit/attachments/{attachment-id}?fileName={name}
```

可從 `_get_work_item_attachments_impl` 回傳的 `url` 欄位中解析出 attachment ID。

---

## 3. 功能設計

### 3.1 新增工具：`download_work_item_attachment`

**用途：** 根據 Work Item ID 和附件資訊，下載一個或多個附件到指定的本地目錄。

**參數設計：**

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `id` | `int` | ✅ | Work Item ID |
| `download_path` | `str` | ✅ | 本地下載目標目錄 |
| `attachment_name` | `Optional[str]` | ❌ | 指定下載特定名稱的附件，為 None 時下載全部 |
| `project` | `Optional[str]` | ❌ | 專案名稱 |
| `include_embedded` | `Optional[bool]` | ❌ | 是否包含嵌入式圖片，預設 False |

**回傳格式：** Markdown 格式的下載結果報告，包含成功/失敗清單及本地路徑。

### 3.2 新增實作函式

```python
def _download_attachment_impl(
    attachment_url: str,
    attachment_name: str,
    download_path: str,
    wit_client: WorkItemTrackingClient,
) -> str:
    """下載單一附件到本地。"""
    pass

def _download_work_item_attachments_impl(
    item_id: int,
    download_path: str,
    wit_client: WorkItemTrackingClient,
    attachment_name: Optional[str] = None,
    project: Optional[str] = None,
    include_embedded: bool = False,
) -> str:
    """下載 Work Item 的附件到本地目錄。"""
    pass
```

---

## 4. 實作步驟

### Step 1: 解析附件 ID 的工具函式

從附件 URL 中提取 GUID 格式的 attachment ID：

```python
import re
from urllib.parse import urlparse, parse_qs

def _extract_attachment_id(url: str) -> Optional[str]:
    """從附件 URL 中提取 attachment ID。"""
    # URL 格式: .../wit/attachments/{guid}?fileName=...
    match = re.search(
        r'/attachments/([0-9a-f-]{36})', url
    )
    return match.group(1) if match else None
```

### Step 2: 單一附件下載實作

```python
def _download_attachment_impl(
    attachment_url: str,
    attachment_name: str,
    download_path: str,
    wit_client: WorkItemTrackingClient,
) -> Tuple[bool, str]:
    """
    下載單一附件到本地。

    Returns:
        Tuple[bool, str]: (成功與否, 本地檔案路徑或錯誤訊息)
    """
    attachment_id = _extract_attachment_id(attachment_url)
    if not attachment_id:
        return (False, f"無法解析附件 ID: {attachment_url}")

    # 確保目標目錄存在
    os.makedirs(download_path, exist_ok=True)

    # 下載附件內容
    content = wit_client.get_attachment_content(
        id=attachment_id,
        file_name=attachment_name,
        download=True
    )

    # 寫入本地檔案
    local_path = os.path.join(download_path, attachment_name)
    with open(local_path, "wb") as f:
        for chunk in content:
            f.write(chunk)

    return (True, local_path)
```

### Step 3: 批次下載實作

```python
def _download_work_item_attachments_impl(
    item_id: int,
    download_path: str,
    wit_client: WorkItemTrackingClient,
    attachment_name: Optional[str] = None,
    project: Optional[str] = None,
    include_embedded: bool = False,
) -> str:
    """下載 Work Item 的附件。"""
    # 1. 取得附件清單
    attachments = _get_work_item_attachments_impl(
        item_id, wit_client, project
    )

    # 2. 篩選附件
    if attachment_name:
        attachments = [a for a in attachments if a["name"] == attachment_name]

    if not include_embedded:
        attachments = [
            a for a in attachments
            if a.get("type") != "embedded_image"
        ]

    # 3. 逐一下載並收集結果
    results = []
    for attachment in attachments:
        success, path_or_error = _download_attachment_impl(
            attachment["url"],
            attachment["name"],
            download_path,
            wit_client,
        )
        results.append({
            "name": attachment["name"],
            "success": success,
            "detail": path_or_error,
        })

    # 4. 格式化結果
    return _format_download_results(item_id, results)
```

### Step 4: MCP Tool 註冊

在 `register_tools()` 中新增：

```python
@mcp.tool()
def download_work_item_attachment(
    id: int,
    download_path: str,
    attachment_name: Optional[str] = None,
    project: Optional[str] = None,
    include_embedded: bool = False,
) -> str:
    """
    Downloads attachments from a work item to local filesystem.

    Use this tool when you need to:
    - Download files attached to work items for local processing
    - Save screenshots or diagrams from work items locally
    - Extract embedded images from work item descriptions
    - Get local copies of requirement documents or specifications

    IMPORTANT: Files will be saved to the specified download_path
    directory. The directory will be created if it doesn't exist.
    Existing files with the same name will be overwritten.

    Args:
        id: The work item ID (integer). Example: 502199
        download_path: Local directory path to save downloaded files
        attachment_name: Optional specific attachment name to download.
            If not provided, downloads all attachments.
        project: Optional project name
        include_embedded: Whether to include embedded images from
            HTML fields (default: False)

    Returns:
        Formatted string containing download results including
        success/failure status and local file paths
    """
    try:
        wit_client = get_work_item_client()
        return _download_work_item_attachments_impl(
            id, download_path, wit_client,
            attachment_name, project, include_embedded,
        )
    except AzureDevOpsClientError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error downloading attachments: {str(e)}"
```

---

## 5. 測試計畫

### 單元測試 (`tests/features/work_items/test_attachments.py` 擴充)

| 測試案例 | 描述 |
|---------|------|
| `test_extract_attachment_id_valid` | 測試從有效 URL 中提取 GUID |
| `test_extract_attachment_id_invalid` | 測試無效 URL 回傳 None |
| `test_download_single_attachment` | Mock SDK 呼叫，驗證檔案寫入 |
| `test_download_all_attachments` | 測試批次下載所有附件 |
| `test_download_by_name_filter` | 測試以名稱篩選下載 |
| `test_download_exclude_embedded` | 測試預設排除嵌入式圖片 |
| `test_download_include_embedded` | 測試 include_embedded=True |
| `test_download_path_creation` | 測試目錄不存在時自動建立 |
| `test_download_error_handling` | 測試 SDK 錯誤時的錯誤處理 |
| `test_download_invalid_url` | 測試無法解析 ID 時的處理 |

---

## 6. 檔案變更清單

| 檔案路徑 | 變更類型 | 說明 |
|---------|---------|------|
| `src/mcp_azure_devops/features/work_items/tools/attachments.py` | 修改 | 新增下載相關函式和 MCP 工具 |
| `tests/features/work_items/test_attachments.py` | 修改 | 新增下載功能的單元測試 |

---

## 7. 安全性考量

1. **路徑穿越防護**：驗證 `download_path` 和 `attachment_name` 不包含 `..` 或絕對路徑注入
2. **檔案大小限制**：考慮加入最大下載大小限制避免記憶體溢出
3. **檔名消毒**：清理附件名稱中的特殊字元，避免檔案系統問題
4. **權限驗證**：依賴 PAT Token 的權限控制，不做額外授權

---

## 8. 相依性

- 不需要新增額外 Python 套件
- 使用 `azure-devops>=7.1.0b4` 現有的 `get_attachment_content` API
- 使用標準庫 `os`, `re`, `urllib.parse`

---

## 9. 風險與注意事項

| 風險 | 緩解措施 |
|------|---------|
| `get_attachment_content` 回傳格式可能是 stream 而非 bytes | 使用迭代方式讀取，相容 stream 和 bytes |
| 附件檔案可能很大 | 使用 chunk 方式寫入，不一次載入記憶體 |
| 同名檔案覆蓋問題 | 文件中明確說明會覆蓋，或加入編號機制 |
| 嵌入式圖片 URL 可能需要認證 | 透過 SDK client 的認證 session 下載 |

---

## 10. MCP Tool 使用方式

### 工具總覽

本模組共提供三個 MCP 工具：

| 工具名稱 | 用途 |
|---------|------|
| `add_work_item_attachment` | 上傳本地檔案到 Azure DevOps 並附加到 Work Item |
| `get_work_item_attachments` | 查詢 Work Item 附件清單（回傳 URL 和 metadata） |
| `download_work_item_attachment` | 從 Azure DevOps 下載附件到本地檔案系統 |

---

### `download_work_item_attachment`

**功能描述：** 將 Work Item 上的附件下載到本地指定目錄。

#### 參數

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `id` | `int` | ✅ | — | Work Item ID，例如 `502199` |
| `download_path` | `str` | ✅ | — | 本地下載目標目錄路徑 |
| `attachment_name` | `str` | ❌ | `None` | 指定下載特定名稱的附件；省略時下載全部 |
| `project` | `str` | ❌ | `None` | Azure DevOps 專案名稱 |
| `include_embedded` | `bool` | ❌ | `False` | 是否包含嵌入在 HTML 欄位中的圖片 |

#### 使用情境

- 需要將附件下載到本地進行處理或分析
- 取得 Work Item 描述中的截圖或設計圖
- 本地備份需求文件或規格書
- 提取嵌入式圖片做進一步處理

#### 使用範例

**範例 1：下載 Work Item 的所有附件**

```json
{
  "tool": "download_work_item_attachment",
  "arguments": {
    "id": 502199,
    "download_path": "/tmp/work-item-attachments"
  }
}
```

**範例 2：下載指定名稱的附件**

```json
{
  "tool": "download_work_item_attachment",
  "arguments": {
    "id": 502199,
    "download_path": "C:\\Users\\dev\\downloads",
    "attachment_name": "requirements.pdf"
  }
}
```

**範例 3：下載所有附件（含嵌入式圖片）**

```json
{
  "tool": "download_work_item_attachment",
  "arguments": {
    "id": 502199,
    "download_path": "/home/user/attachments",
    "include_embedded": true
  }
}
```

**範例 4：指定專案名稱**

```json
{
  "tool": "download_work_item_attachment",
  "arguments": {
    "id": 123456,
    "download_path": "./downloads",
    "project": "MyProject",
    "include_embedded": false
  }
}
```

#### 回傳格式

工具回傳 Markdown 格式的下載結果報告：

```markdown
# Download Results for Work Item 502199

**Total:** 3 | **Success:** 2 | **Failed:** 1

## Successfully Downloaded
- ✅ `requirements.pdf` → `/tmp/work-item-attachments/requirements.pdf`
- ✅ `screenshot.png` → `/tmp/work-item-attachments/screenshot.png`

## Failed Downloads
- ❌ `broken-link.doc`: Cannot parse attachment ID from URL: https://...
```

#### 注意事項

1. **目錄自動建立**：如果 `download_path` 指定的目錄不存在，會自動建立（含巢狀目錄）
2. **檔案覆蓋**：若目標目錄已存在同名檔案，將會被覆蓋
3. **檔名消毒**：附件名稱中的特殊字元（如 `<>:"/\|?*`）會被替換為 `_`
4. **路徑安全**：自動防止路徑穿越攻擊（如 `../../etc/passwd`）
5. **嵌入式圖片**：預設不下載嵌入在 Description 或 Acceptance Criteria 中的圖片，需明確設定 `include_embedded: true`
6. **認證需求**：使用環境變數中設定的 PAT Token 進行認證，需確保 Token 有讀取附件的權限

---

### `get_work_item_attachments`

**功能描述：** 取得 Work Item 的附件清單資訊（不下載檔案內容）。

#### 參數

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `id` | `int` | ✅ | — | Work Item ID |
| `project` | `str` | ❌ | `None` | Azure DevOps 專案名稱 |

#### 使用範例

```json
{
  "tool": "get_work_item_attachments",
  "arguments": {
    "id": 502199
  }
}
```

#### 回傳格式

```markdown
# Attachments for Work Item 502199

## Formal Attachments
### 1. requirements.pdf
- URL: https://dev.azure.com/org/project/_apis/wit/attachments/guid...
- Comment: Updated requirements document

## Embedded Images
### 1. screenshot.png
- URL: https://dev.azure.com/org/...?fileName=screenshot.png
- Located in: System.Description
- Preview: ![Image 1](https://...)
```

---

### `add_work_item_attachment`

**功能描述：** 上傳本地檔案並附加到指定的 Work Item。

#### 參數

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `id` | `int` | ✅ | — | Work Item ID |
| `file_path` | `str` | ✅ | — | 本地檔案完整路徑 |
| `comment` | `str` | ❌ | `None` | 附件的說明註解 |
| `project` | `str` | ❌ | `None` | Azure DevOps 專案名稱 |

#### 使用範例

```json
{
  "tool": "add_work_item_attachment",
  "arguments": {
    "id": 502199,
    "file_path": "/home/user/reports/analysis.pdf",
    "comment": "Sprint review analysis report"
  }
}
```

---

### 典型工作流程

```
1. 使用 get_work_item_attachments 查看附件清單
        ↓
2. 確認需要下載的附件名稱
        ↓
3. 使用 download_work_item_attachment 下載到本地
        ↓
4. 本地處理完成後，使用 add_work_item_attachment 上傳結果
```
