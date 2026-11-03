# 中文启动说明

> 个人演示项目。所有数据都是合成数据，不是客户案例。

下面的命令都在 Windows PowerShell 里运行。

## 1. 需要的软件

| 软件 | 用途 | 说明 |
|---|---|---|
| Python 3.10 或更高 | 运行程序 | 测试时用的是 3.11.9 |
| Git | 下载代码 | 也可以在 GitHub 页面点 Code → Download ZIP，解压后进入文件夹 |
| Microsoft Edge | 真实浏览器检查 | 只有 `scripts\ui_check.py` 需要 |

## 2. 安装（只做一次）

```powershell
git clone https://github.com/ALTRIAMERLIN/csv-cleaning-tool.git
cd csv-cleaning-tool
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -e .
```

之后的命令都在 `csv-cleaning-tool` 文件夹里运行。命令直接调用 `.venv` 里的 Python，所以不用激活虚拟环境。

## 3. 打开网页界面

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

看到 `URL: http://127.0.0.1:8501` 后，用浏览器打开这个地址。程序只在本机运行，别的电脑访问不到。要停止，就在这个 PowerShell 窗口按 `Ctrl+C`。

页面上有五步：

1. **Upload CSV**：上传 CSV 文件，或点 **Use bundled synthetic sample** 用自带的示例数据。
2. **Preview**：看行数、列数、列数不对的行，以及前 20 行。
3. **Rules**：选择要去首尾空格的列、必填列、邮箱列、去重用的列，以及重复时保留第一条还是最后一条，然后点 **Run cleaning**。
4. **Results**：看统计数字和对账结果。四个标签页分别是干净数据、问题记录、变更日志和汇总。
5. **Download**：下载四个文件。页面列出每个文件的大小和 SHA-256（文件指纹），用来核对下载的文件。

## 4. 用命令行处理

```powershell
.\.venv\Scripts\python -m csvclean data\demo_customers.csv --out out\demo --rules data\demo_rules.json
```

正常会看到：

```
input=191 clean=165 issues=26 (field_count=2 invalid=16 duplicate=8) changed_cells=25 accounting_ok=True
outputs written to: out\demo
```

结果在 `out\demo` 文件夹里：

| 文件 | 内容 |
|---|---|
| `clean.csv` | 通过所有规则的行 |
| `issues.csv` | 其余的行，每行写明原因 |
| `changes.csv` | 每个去掉了首尾空格的格子，改前和改后的值 |
| `summary.json` | 版本、输入文件指纹、规则、统计数字和对账结果 |

对同一个文件夹再运行一次，程序会拒绝覆盖。要覆盖，就在命令最后加 `--force`，或者换一个 `--out` 文件夹。原始输入文件永远不会被改动。

核对下载的文件，例如：

```powershell
Get-FileHash .\clean.csv -Algorithm SHA256
```

结果应和页面上列出的 SHA-256 相同。`Get-FileHash` 显示大写字母，页面显示小写字母，这不影响比对。

## 5. 运行测试

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts\run_tests.py
.\.venv\Scripts\python scripts\run_tests.py --check
.\.venv\Scripts\python scripts\ui_check.py out\ui_check --start-app
```

| 命令 | 作用 |
|---|---|
| `pytest -q` | 运行全部自动测试 |
| `run_tests.py` | 运行测试，把结果存进 `test-results\` |
| `run_tests.py --check` | 检查保存的测试结果是否还对应当前代码 |
| `ui_check.py ... --start-app` | 自动启动界面，在 Edge 里走一遍上传、设规则、运行、下载，并逐字节核对四个下载文件 |

## 6. 常见问题

| 现象 | 解决办法 |
|---|---|
| 提示 `python` 不是内部或外部命令 | 重新安装 Python 并勾选 “Add python.exe to PATH”，或把第 2 步里的 `python` 换成 `py` |
| 页面提示文件不是 UTF-8 | 在 Excel 里用“另存为 → CSV UTF-8（逗号分隔）”重新保存 |
| 提示 `Output files already exist` | 换一个 `--out` 文件夹，或在命令最后加 `--force` |
| 端口 8501 被占用 | 在启动命令最后加 `--server.port 8502`，再打开 http://127.0.0.1:8502 |

更多说明见英文 [README.md](../README.md)。
