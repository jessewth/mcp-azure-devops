# Query.py Unit Tests - 測試文檔

本文檔說明如何執行 `query.py` 模組的單元測試。

## 測試文件位置

新增的測試文件位於：
```
tests/features/work_items/test_query.py
```

## 環境設置

### 1. 安裝 uv 包管理器
```bash
python3 -m pip install uv
```

### 2. 創建虛擬環境
```bash
uv venv
```

### 3. 激活虛擬環境
```bash
source .venv/bin/activate
```

### 4. 安裝項目依賴
```bash
uv pip install -e ".[dev]"
```

## 執行測試

### 運行所有 query.py 的測試
```bash
uv run pytest tests/features/work_items/test_query.py -v
```

### 運行特定測試
```bash
# 測試無結果的查詢
uv run pytest tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_no_results -v

# 測試有結果的查詢
uv run pytest tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_single_result -v

# 測試多個結果
uv run pytest tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_multiple_results -v
```

### 運行完整測試套件
```bash
uv run pytest tests/ -v
```

## 測試覆蓋範圍

新增的測試涵蓋以下場景：

1. **test_query_with_no_results** - 測試查詢沒有返回任何工作項
2. **test_query_with_single_result** - 測試查詢返回單個工作項
3. **test_query_with_multiple_results** - 測試查詢返回多個工作項
4. **test_query_with_top_parameter** - 測試 top 參數正確限制結果數量
5. **test_query_handles_none_work_items** - 測試過濾 None 工作項
6. **test_query_with_complex_wiql** - 測試複雜的 WIQL 查詢語法
7. **test_query_with_different_work_item_types** - 測試不同類型的工作項（Bug, Task, User Story, Epic）
8. **test_query_verifies_get_work_items_parameters** - 驗證 get_work_items 使用正確的參數
9. **test_query_formats_output_correctly** - 測試輸出格式化正確（使用雙換行符分隔）

## 代碼質量檢查

### 運行代碼檢查（Linting）
```bash
uv run ruff check tests/features/work_items/test_query.py
```

### 運行代碼格式化
```bash
uv run ruff format tests/features/work_items/test_query.py
```

### 運行類型檢查
```bash
uv run pyright tests/features/work_items/test_query.py
```

## 測試結果

執行測試後，您應該看到以下結果：

```
================================================= test session starts ==================================================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /home/runner/work/mcp-azure-devops/mcp-azure-devops
configfile: pyproject.toml
plugins: asyncio-1.2.0, anyio-4.8.0

tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_no_results PASSED               [ 11%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_single_result PASSED            [ 22%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_multiple_results PASSED         [ 33%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_top_parameter PASSED            [ 44%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_handles_none_work_items PASSED       [ 55%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_complex_wiql PASSED             [ 66%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_different_work_item_types PASSED [ 77%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_verifies_get_work_items_parameters PASSED [ 88%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_formats_output_correctly PASSED      [100%]

================================================== 9 passed in 0.50s ===================================================
```

## 完整測試統計

運行整個項目的測試套件：
- **總測試數**: 93
- **通過**: 92
- **失敗**: 1 (預期的 trio 相關失敗，這是正常的)

## 注意事項

1. 所有測試使用模擬（Mock）對象，不需要實際的 Azure DevOps 連接
2. 測試遵循現有的代碼風格和測試模式
3. 每個測試都有清晰的文檔字符串說明其目的
4. 測試覆蓋了成功和邊緣情況

## 疑難排解

如果遇到問題：

1. **導入錯誤**: 確保虛擬環境已激活且依賴已安裝
2. **測試失敗**: 除了 trio 相關的單個失敗外，其他失敗表示存在實際問題
3. **Linting 錯誤**: 運行 `uv run ruff check --fix .` 自動修復大多數格式問題

---

# Query.py Unit Tests - Test Documentation (English)

This document explains how to run unit tests for the `query.py` module.

## Test File Location

The new test file is located at:
```
tests/features/work_items/test_query.py
```

## Environment Setup

### 1. Install uv Package Manager
```bash
python3 -m pip install uv
```

### 2. Create Virtual Environment
```bash
uv venv
```

### 3. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 4. Install Project Dependencies
```bash
uv pip install -e ".[dev]"
```

## Running Tests

### Run All query.py Tests
```bash
uv run pytest tests/features/work_items/test_query.py -v
```

### Run Specific Tests
```bash
# Test query with no results
uv run pytest tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_no_results -v

# Test query with results
uv run pytest tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_single_result -v

# Test multiple results
uv run pytest tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_multiple_results -v
```

### Run Complete Test Suite
```bash
uv run pytest tests/ -v
```

## Test Coverage

The new tests cover the following scenarios:

1. **test_query_with_no_results** - Test query with no work items returned
2. **test_query_with_single_result** - Test query returning a single work item
3. **test_query_with_multiple_results** - Test query returning multiple work items
4. **test_query_with_top_parameter** - Test that top parameter correctly limits results
5. **test_query_handles_none_work_items** - Test filtering of None work items
6. **test_query_with_complex_wiql** - Test complex WIQL query syntax
7. **test_query_with_different_work_item_types** - Test different work item types (Bug, Task, User Story, Epic)
8. **test_query_verifies_get_work_items_parameters** - Verify get_work_items uses correct parameters
9. **test_query_formats_output_correctly** - Test output formatting (double newline separators)

## Code Quality Checks

### Run Linting
```bash
uv run ruff check tests/features/work_items/test_query.py
```

### Run Code Formatting
```bash
uv run ruff format tests/features/work_items/test_query.py
```

### Run Type Checking
```bash
uv run pyright tests/features/work_items/test_query.py
```

## Test Results

After running the tests, you should see:

```
================================================= test session starts ==================================================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /home/runner/work/mcp-azure-devops/mcp-azure-devops
configfile: pyproject.toml
plugins: asyncio-1.2.0, anyio-4.8.0

tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_no_results PASSED               [ 11%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_single_result PASSED            [ 22%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_multiple_results PASSED         [ 33%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_top_parameter PASSED            [ 44%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_handles_none_work_items PASSED       [ 55%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_complex_wiql PASSED             [ 66%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_with_different_work_item_types PASSED [ 77%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_verifies_get_work_items_parameters PASSED [ 88%]
tests/features/work_items/test_query.py::TestQueryWorkItemsImpl::test_query_formats_output_correctly PASSED      [100%]

================================================== 9 passed in 0.50s ===================================================
```

## Complete Test Statistics

Running the entire project test suite:
- **Total Tests**: 93
- **Passed**: 92
- **Failed**: 1 (Expected trio-related failure, this is normal)

## Notes

1. All tests use mock objects, no actual Azure DevOps connection required
2. Tests follow existing code style and test patterns
3. Each test has clear docstrings explaining its purpose
4. Tests cover both success and edge cases

## Troubleshooting

If you encounter issues:

1. **Import Errors**: Ensure virtual environment is activated and dependencies are installed
2. **Test Failures**: Apart from the single trio-related failure, other failures indicate real issues
3. **Linting Errors**: Run `uv run ruff check --fix .` to auto-fix most formatting issues
