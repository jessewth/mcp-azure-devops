# MCP Azure DevOps 環境設定指令碼
# 此指令碼可幫助您一鍵設定 MCP Azure DevOps 專案所需的所有環境

# 顯示歡迎訊息
Write-Host "歡迎使用 MCP Azure DevOps 環境設定指令碼" -ForegroundColor Green
Write-Host "此指令碼將幫助您設定所需的環境和相依套件" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# 檢查 Python 安裝
Write-Host "正在檢查 Python 安裝..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version
    Write-Host "已安裝的 Python 版本: $pythonVersion" -ForegroundColor Green
    
    $pythonVersionNumber = $pythonVersion -replace "Python ", ""
    $versionParts = $pythonVersionNumber.Split(".")
    $majorVersion = [int]$versionParts[0]
    $minorVersion = [int]$versionParts[1]
    
    if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 9)) {
        Write-Host "警告: 需要 Python 3.9+ 版本" -ForegroundColor Yellow
        Write-Host "請安裝更新版本的 Python 後再執行此指令碼" -ForegroundColor Yellow
        exit
    }
} catch {
    Write-Host "錯誤: 未找到 Python。請安裝 Python 3.9+ 後再執行此指令碼" -ForegroundColor Red
    exit
}

# 安裝專案相依套件
Write-Host "正在安裝專案相依套件..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

# 設定 .env 檔案
Write-Host "正在設定環境變數..." -ForegroundColor Cyan
$pat = Read-Host -Prompt "請輸入您的 Azure DevOps Personal Access Token (PAT)"
$orgUrl = Read-Host -Prompt "請輸入您的 Azure DevOps 組織 URL (例如 https://dev.azure.com/your-organisation)"

# 檢查輸入是否有效
if ([string]::IsNullOrWhiteSpace($pat) -or [string]::IsNullOrWhiteSpace($orgUrl)) {
    Write-Host "錯誤: PAT 和組織 URL 不能為空" -ForegroundColor Red
    exit
}

# 建立 .env 檔案
$envContent = @"
AZURE_DEVOPS_PAT=$pat
AZURE_DEVOPS_ORGANIZATION_URL=$orgUrl
"@

Set-Content -Path ".\.env" -Value $envContent

Write-Host "成功建立 .env 檔案!" -ForegroundColor Green

# 將伺服器設定添加到 Claude Desktop 設定檔
Write-Host "正在設定 Claude Desktop..." -ForegroundColor Cyan

# 取得專案絕對路徑
$projectPath = Resolve-Path "."
$srcPath = Join-Path -Path $projectPath -ChildPath "src\mcp_azure_devops"

# 檢查是否安裝了 uv
$uvPath = ""
try {
    # 嘗試找出 uv 執行檔的路徑
    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCmd) {
        $uvPath = $uvCmd.Path
        Write-Host "找到 uv 路徑: $uvPath" -ForegroundColor Green
    } else {
        # 嘗試從常見位置找 uv
        $possiblePaths = @(
            "C:\Python311\Scripts\uv.exe",
            "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts\uv.exe"
        )
        
        foreach ($path in $possiblePaths) {
            if (Test-Path $path) {
                $uvPath = $path
                Write-Host "找到 uv 路徑: $uvPath" -ForegroundColor Green
                break
            }
        }
        
        if (-not $uvPath) {
            Write-Host "警告: 無法找到 uv 執行檔。將使用預設的 mcp 命令安裝" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "警告: 無法找到 uv 執行檔。將使用預設的 mcp 命令安裝" -ForegroundColor Yellow
}

# Claude Desktop 設定檔路徑
$claudeConfigPath = "$env:APPDATA\Claude\claude_desktop_config.json"

# 確認設定檔目錄存在
$claudeConfigDir = Split-Path -Path $claudeConfigPath -Parent
if (-not (Test-Path -Path $claudeConfigDir)) {
    Write-Host "建立 Claude 設定目錄: $claudeConfigDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $claudeConfigDir -Force | Out-Null
}

# 讀取現有的設定或建立新的設定
if (Test-Path -Path $claudeConfigPath) {
    try {
        $claudeConfig = Get-Content -Path $claudeConfigPath -Raw | ConvertFrom-Json
        Write-Host "已讀取現有的 Claude Desktop 設定檔" -ForegroundColor Green
    } catch {
        Write-Host "警告: 無法解析現有的 Claude Desktop 設定檔，將建立新的設定" -ForegroundColor Yellow
        $claudeConfig = @{
            mcpServers = @{}
        }
    }
} else {
    Write-Host "未找到 Claude Desktop 設定檔，將建立新的設定" -ForegroundColor Yellow
    $claudeConfig = @{
        mcpServers = @{}
    }
}

# 確保 mcpServers 屬性存在
if (-not $claudeConfig.mcpServers) {
    $claudeConfig | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue @{}
}

# 建立 Azure DevOps Assistant 設定
if ($uvPath) {
    # 使用找到的 uv 路徑
    $azureDevOpsConfig = @{
        command = $uvPath
        args = @(
            "--directory"
            $srcPath
            "run"
            "--with"
            "mcp[cli]"
            "mcp"
            "run"
            "$srcPath\server.py"
        )
    }
} else {
    # 使用一般的 Python 命令
    $azureDevOpsConfig = @{
        command = "python"
        args = @(
            "-m"
            "mcp"
            "run"
            "$srcPath\server.py"
        )
    }
}

# 更新設定檔
$claudeConfig.mcpServers."Azure DevOps Assistant" = $azureDevOpsConfig

# 儲存設定檔
$claudeConfig | ConvertTo-Json -Depth 10 | Set-Content -Path $claudeConfigPath

Write-Host "已成功更新 Claude Desktop 設定檔，並加入 Azure DevOps Assistant" -ForegroundColor Green

# 完成安裝
Write-Host "===============================================" -ForegroundColor Green
Write-Host "環境設定完成！" -ForegroundColor Green
Write-Host "您現在可以使用以下命令來執行伺服器:" -ForegroundColor Green
Write-Host "開發模式 (使用 MCP Inspector): mcp dev src/mcp_azure_devops/server.py" -ForegroundColor Cyan
Write-Host "已自動安裝在 Claude Desktop，服務名稱: 'Azure DevOps Assistant'" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Green