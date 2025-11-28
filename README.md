# 🚀 Python智能包管理工具

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

一个强大的Python项目依赖管理工具，能够自动扫描项目中的所有Python文件，智能提取导入语句，并生成详细的依赖文档。

## ✨ 核心特性

### 🔍 智能扫描
- **自动发现**：递归扫描整个项目目录的所有`.py`文件
- **精确提取**：智能识别`import`和`from...import`语句
- **行号追踪**：记录每个导入语句的精确位置（文件名+行号）
- **智能过滤**：自动排除虚拟环境、缓存目录等无关文件

### 📦 依赖管理
- **标准库识别**：自动区分标准库和第三方包
- **包名映射**：智能处理特殊包名（如`PIL`→`pillow`，`cv2`→`opencv-python`）
- **依赖统计**：分析每个包的使用频率和分布情况
- **自动安装**：一键安装所有缺失的第三方包

### 📋 详细文档
- **增强版requirements.txt**：不仅列出包名，还包含：
  - 📊 每个包的使用统计（文件数、导入次数）
  - 📄 详细的来源信息（哪个文件的哪一行）
  - 🔍 完整的导入语句记录
  - 📈 项目级别的依赖概览

### 🛡️ 安全可靠
- **备份机制**：自动备份现有的`requirements.txt`
- **编码兼容**：支持多种文件编码（UTF-8、GBK、GB2312等）
- **错误处理**：完善的异常处理和友好的错误提示
- **跨平台**：兼容Windows、Linux、macOS

## 📥 安装

### 方式1：直接下载
```bash
# 下载脚本
wget https://raw.githubusercontent.com/buptanswer/python-package-manager/main/package_installer_yulibupt.py

# 或使用curl
curl -O https://raw.githubusercontent.com/buptanswer/python-package-manager/main/package_installer_yulibupt.py
```

### 方式2：克隆仓库
```bash
git clone https://github.com/buptanswer/python-package-manager.git
cd package-installer
```

## 🚀 快速开始

### 基础用法

#### 1. 扫描当前项目
```bash
python package_installer_yulibupt.py
```

#### 2. 扫描指定目录
```bash
python package_installer_yulibupt.py /path/to/your/project
```

#### 3. 手动指定导入
编辑脚本中的配置：
```python
SCAN_MODE = False
YOUR_IMPORTS = """
import requests
from bs4 import BeautifulSoup
import pandas as pd
"""
```

### 配置选项

在脚本顶部的配置区可以自定义行为：

```python
# 扫描模式: True=自动扫描, False=手动指定
SCAN_MODE = True

# 扫描路径 (None=当前目录)
SCAN_PATH = None

# 是否递归扫描子目录
SCAN_SUBDIRS = True

# 排除的目录
EXCLUDE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 
    'node_modules', '.idea', '.vscode'
}

# 排除的文件
EXCLUDE_FILES = {
    'package_installer_yulibupt.py',
}

# 是否生成requirements.txt
GENERATE_REQUIREMENTS = True
```

## 📖 使用示例

### 示例1：分析新项目
```bash
$ python package_installer_yulibupt.py

======================================================================
🚀 增强版Python项目智能包管理工具 - 扫描模式
======================================================================

📁 扫描路径: /home/user/my-project
📋 项目名称: my-project
🔍 扫描模式: 递归扫描子目录

📝 步骤1: 扫描Python文件...
   找到 15 个Python文件

📦 步骤2: 详细分析import语句...
   检测到 23 个不同的包

🔍 步骤3: 过滤标准库...
   标准库: 18 个 | 第三方库: 5 个

   第三方包详情:
     • requests (3 文件, 5 导入)
     • pandas (2 文件, 3 导入)
     • numpy (4 文件, 8 导入)
```

### 示例2：生成的requirements.txt
```txt
# ==============================================================================
# 📦 Enhanced Python Package Requirements
# ==============================================================================
# Generated: 2025-11-26 20:17:27
# Project:   my-project
# Files:     15 Python files scanned
# Packages:  5 third-party packages
# Imports:   16 import statements
# ==============================================================================

# 📋 DEPENDENCY OVERVIEW
# ------------------------------------------------------------------------------
# requests             → 3 file(s), 5 import(s)
# pandas               → 2 file(s), 3 import(s)
# numpy                → 4 file(s), 8 import(s)
# ------------------------------------------------------------------------------

# 📦 DETAILED PACKAGE INFORMATION
# ==============================================================================

# requests
# --------
requests
#   📄 api_client.py:
#     L  5: import requests
#   📄 data_fetcher.py:
#     L 12: import requests
#     L 45: from requests.exceptions import RequestException
```

## 🎯 主要功能

### 1. 智能包名映射
自动处理常见的包名差异：

| 导入名称 | pip包名 |
|---------|---------|
| `PIL` | `pillow` |
| `cv2` | `opencv-python` |
| `sklearn` | `scikit-learn` |
| `bs4` | `beautifulsoup4` |
| `yaml` | `pyyaml` |

### 2. 详细的依赖追踪
```python
@dataclass
class ImportInfo:
    package_name: str      # 包名
    import_type: str       # 导入类型
    import_statement: str  # 完整语句
    line_number: int       # 行号
    file_path: Path        # 文件路径
    pip_package: str       # pip包名
```

### 3. 项目统计分析
- 📊 包使用频率统计
- 📁 文件级别的导入分析
- 🔗 依赖关系可视化
- 📈 项目健康度评估

## 🔧 高级用法

### 自定义排除规则
```python
# 排除特定文件模式
EXCLUDE_FILE_PATTERNS = [
    'test_',           # 排除测试文件
    'install_packages', # 排除安装脚本
    '_backup',         # 排除备份文件
]
```

### 编程方式使用
```python
from package_installer_yulibupt import PackageTracker, scan_python_files

# 创建追踪器
tracker = PackageTracker()

# 扫描文件
files = scan_python_files('./my_project')

# 分析导入
for file in files:
    imports = extract_imports_with_details(content, file)
    for imp in imports:
        tracker.add_import(imp)

# 获取统计
stats = tracker.get_package_stats()
```

## 📊 输出格式

### 控制台输出
- ✅ 彩色输出，清晰易读
- 📊 进度条和状态指示
- 🔍 详细的错误信息
- 💡 智能提示和建议

### requirements.txt格式
- 📋 标准pip格式兼容
- 📝 详细的注释说明
- 🔍 完整的来源追踪
- 📊 使用统计信息

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📝 更新日志

### v2.0.0 (2025-11-26)
- ✨ 新增详细的包来源日志记录
- 🔍 精确的行号和文件路径追踪
- 📊 项目依赖使用统计
- 🔄 智能覆盖和备份策略
- 👥 版本控制友好的格式

### v1.0.0
- 🎉 初始版本发布
- 📦 基础的包扫描和安装功能
- 📋 简单的requirements.txt生成

## ❓ 常见问题

### Q: 为什么某些包没有被检测到？
A: 可能是动态导入或条件导入。建议使用手动模式补充。

### Q: 如何处理私有包？
A: 在`PACKAGE_MAPPING`中添加映射关系。

### Q: 支持虚拟环境吗？
A: 是的，自动检测并使用当前激活的虚拟环境。

### Q: 可以用于CI/CD吗？
A: 完全可以！支持命令行参数和自动化脚本。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢所有贡献者的支持
- 灵感来源于pip-tools和pipreqs
- 使用了Python标准库的强大功能

## 📧 联系方式

- 作者：YuliBUPT
- 邮箱：1404498804@qq.com
- 项目主页：https://github.com/buptanswer/python-package-manager

---

⭐ 如果这个项目对你有帮助，请给个Star！

🐛 发现Bug？[提交Issue](https://github.com/buptanswer/python-package-manager/issues)

💡 有想法？[参与讨论](https://github.com/buptanswer/python-package-manager/discussions)
