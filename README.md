# 🚀 Python智能包管理工具

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-208%20passed-brightgreen.svg)](run_tests.py)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

一个强大的Python项目依赖管理工具，能够自动扫描项目中的所有Python文件，智能提取导入语句，并生成详细的依赖文档。

## ✨ 核心特性

### 🔍 智能扫描
- **自动发现**：递归扫描整个项目目录的所有`.py`文件
- **精确提取**：智能识别`import`和`from...import`语句
- **多行支持**：完整支持多行import语句（使用括号）
- **行号追踪**：记录每个导入语句的精确位置（文件名+行号）
- **智能过滤**：自动排除虚拟环境、缓存目录等无关文件
- **相对导入过滤**：自动过滤相对导入，只识别第三方包
- **本地模块检测**：自动识别项目中的本地模块，避免误安装不相关的PyPI包

### 📦 依赖管理
- **标准库识别**：运行时自动检测标准库（Python 3.10+），兼容旧版本
- **包名映射**：智能处理特殊包名（如`PIL`→`pillow`，`cv2`→`opencv-python`）
- **依赖统计**：分析每个包的使用频率和分布情况
- **自动安装**：一键安装所有缺失的第三方包
- **安装验证**：安装后自动验证包是否可用
- **特殊包处理**：支持pywin32等需要特殊处理的包
- **本地模块保护**：自动检测并跳过本地模块，防止误安装不相关的PyPI包

### 📋 详细文档
- **增强版requirements.txt**：不仅列出包名，还包含：
  - 📊 每个包的使用统计（文件数、导入次数）
  - 📄 详细的来源信息（哪个文件的哪一行）
  - 🔍 完整的导入语句记录
  - 📈 项目级别的依赖概览

### 🛡️ 安全可靠
- **备份机制**：自动备份现有的`requirements.txt`，保留最近5个备份
- **编码兼容**：支持多种文件编码（UTF-8、GBK、GB2312等）
- **错误处理**：完善的异常处理和友好的错误提示
- **跨平台**：兼容Windows、Linux、macOS
- **边界情况处理**：完善的错误处理和边界情况处理

### 🧪 测试覆盖
- **完整测试套件**：208个单元测试，覆盖所有核心功能
- **8个测试模块**：Import提取、文件操作、包追踪、包名映射、特殊处理、Requirements生成、本地模块、集成测试
- **边界测试**：测试各种边界情况和异常处理

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
cd python-package-manager
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

# 排除文件名包含这些关键词的文件
EXCLUDE_FILE_PATTERNS = [
    'test_',           # 排除测试文件
    'install_packages', # 排除安装脚本
]

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
# Generated: 2025-11-29 02:50:00
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

### 示例3：多行import支持
工具完全支持多行import语句：
```python
from package import (
    item1,
    item2,
    item3
)

import (
    pkg1,
    pkg2,
    pkg3
)
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
| `MySQLdb` | `mysqlclient` |
| `pkg_resources` | `setuptools` |
| `win32clipboard` | `pywin32` |
| `win32con` | `pywin32` |
| `win32api` | `pywin32` |

### 2. 特殊包处理
自动处理需要特殊安装流程的包：

```python
PACKAGE_SPECIAL_HANDLING = {
    'pywin32': {
        'post_install_script': 'pywin32_postinstall',
        'post_install_args': ['-install'],
        'skip_import_verify': True,  # 使用pip show验证
    },
}
```

pywin32等包安装后需要重启Python才能导入，工具会自动使用`pip show`验证安装成功。

### 3. 详细的依赖追踪
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

### 4. 项目统计分析
- 📊 包使用频率统计
- 📁 文件级别的导入分析
- 🔗 依赖关系追踪
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
from package_installer_yulibupt import (
    PackageTracker, 
    scan_python_files,
    extract_imports_with_details,
    read_file_safely
)

# 创建追踪器
tracker = PackageTracker()

# 扫描文件
files = scan_python_files('./my_project')

# 分析导入
for file in files:
    content = read_file_safely(file)
    imports = extract_imports_with_details(content, file)
    for imp in imports:
        tracker.add_import(imp)

# 获取统计
stats = tracker.get_package_stats()
third_party = tracker.get_third_party_packages()
```

### 运行测试
```bash
# 运行所有测试
python run_tests.py

# 运行特定测试模块
python run_tests.py test_import_extraction

# 详细输出
python run_tests.py -v
```

## 📊 输出格式

### 控制台输出
- ✅ 彩色输出，清晰易读
- 📊 进度指示和状态信息
- 🔍 详细的错误信息
- 💡 智能提示和建议

### requirements.txt格式
- 📋 标准pip格式兼容
- 📝 详细的注释说明
- 🔍 完整的来源追踪
- 📊 使用统计信息

## 🧪 测试

项目包含完整的测试套件：

- **208个单元测试**：覆盖所有核心功能
- **测试模块**：
  - `test_import_extraction.py` - Import提取测试（32个测试）
  - `test_file_operations.py` - 文件操作测试（22个测试）
  - `test_package_tracker.py` - 包追踪器测试（17个测试）
  - `test_package_mapping.py` - 包名映射测试（36个测试）
  - `test_special_handling.py` - 特殊包处理测试（43个测试）
  - `test_requirements_generation.py` - Requirements生成测试（26个测试）
  - `test_local_modules.py` - 本地模块测试（18个测试）
  - `test_integration.py` - 集成测试（17个测试）

运行测试：
```bash
python run_tests.py
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📝 更新日志

### v2.3.0 (2025-11-30)
- ✨ **重要安全修复**：新增本地模块检测功能，防止误安装不相关的PyPI包
- ✨ 本地模块在requirements.txt中单独列出，不标记为安装失败
- ✨ 新增导入失败诊断功能，智能检测大小写不匹配等问题
- ✨ 新增参数验证，提高代码健壮性
- 🐛 修复本地模块被错误标记为"安装失败"的问题
- 🐛 修复安装统计数字不准确的问题
- 🐛 修复备份文件排序时的异常处理
- 🐛 修复`get_installed_package_info`的stdout空值检查
- 🧪 新增18个测试，测试套件从168个增至208个测试

### v2.2.0 (2025-11-29)
- ✨ 新增特殊包处理机制（支持pywin32等）
- ✨ 新增`pip show`验证方式
- ✨ 全新测试套件（168个测试）
- 🐛 修复pywin32安装验证失败问题
- 🐛 修复文件数统计不准确问题
- 🗑️ 移除未使用的冗余代码

### v2.1.0 (2025-11-29)
- ✨ 新增多行import语句完整支持（使用括号）
- ✨ 新增相对导入自动过滤
- ✨ 改进标准库检测（运行时检测，兼容旧版本）
- ✨ 新增备份文件自动清理机制
- ✨ 改进错误处理和边界情况处理
- ✨ 新增完整测试套件（35个测试）
- 🐛 修复Windows编码问题
- 🐛 修复文件路径处理异常
- 🐛 修复索引越界问题
- 🐛 修复无限循环防护

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
A: 可能是动态导入（如`__import__()`或`importlib.import_module()`）或条件导入。建议使用手动模式补充。

### Q: 如何处理私有包？
A: 在`PACKAGE_MAPPING`中添加映射关系。

### Q: 支持虚拟环境吗？
A: 是的，自动检测并使用当前激活的虚拟环境。

### Q: 可以用于CI/CD吗？
A: 完全可以！支持命令行参数和自动化脚本。

### Q: 多行import语句支持吗？
A: 完全支持！工具可以正确处理使用括号的多行import语句。

### Q: 相对导入会被识别吗？
A: 不会。工具会自动过滤相对导入（以`.`开头的导入），只识别第三方包。

### Q: pywin32安装后显示"需重启Python后可导入"是什么意思？
A: pywin32是特殊包，安装后需要重启Python进程才能导入使用。工具会自动使用`pip show`验证安装成功，您只需重启Python即可正常使用。

### Q: 工具会误安装本地模块对应的PyPI包吗？
A: 不会。v2.3.0版本新增了本地模块检测功能，工具会自动识别项目目录中的`.py`文件或包目录，跳过安装并单独列出。这避免了误安装不相关的PyPI包污染环境。

### Q: 如果遇到"安装成功但验证失败"怎么办？
A: 工具现在会提供详细的诊断信息，包括：
- 是否是大小写不匹配问题
- 是否是本地模块
- 是否需要添加包名映射
根据提示信息进行相应处理即可。

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
