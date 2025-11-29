"""
🚀 增强版Python项目智能包管理工具
==========================================
功能:
- 自动扫描整个项目文件夹的所有.py文件
- 智能提取所有import语句（包含行号和详细信息）
- 自动去重、过滤标准库
- 安装并验证
- 生成详细的日志式requirements.txt
- 包来源追踪和依赖分析

新增功能:
- 📋 详细的包来源日志记录
- 🔍 精确的行号和文件路径追踪
- 📊 项目依赖使用统计
- 🔄 智能覆盖和备份策略
- 👥 版本控制友好的格式

使用方法:
方式1 - 扫描整个项目:
    python package_installer_yulibupt.py

方式2 - 扫描指定文件夹:
    python package_installer_yulibupt.py path/to/project

方式3 - 手动指定import(像之前一样):
    修改 YOUR_IMPORTS 变量,设置 SCAN_MODE = False
"""

import subprocess
import sys
import importlib.util
import re
import os
import shutil
import json
import urllib.request
import urllib.error
from typing import Set, Dict, Tuple, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# ==================== 配置区 ====================

# 扫描模式: True=自动扫描项目, False=使用YOUR_IMPORTS
SCAN_MODE = True

# 扫描路径 (None=当前目录, 或指定路径如 "./src")
SCAN_PATH = None

# 是否扫描子文件夹
SCAN_SUBDIRS = True

# 排除的文件夹 (不扫描这些文件夹)
EXCLUDE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.idea', '.vscode', 'build', 'dist',
    '.egg-info', '.pytest_cache', '.mypy_cache'
}

# 排除的文件 (不扫描这些文件)
# 支持精确匹配和模糊匹配
EXCLUDE_FILES = {
    'package_installer_yulibupt.py',
}

# 排除文件名包含这些关键词的文件 (不区分大小写)
EXCLUDE_FILE_PATTERNS = [
    'install_packages',  # 排除任何包含install_packages的文件
    'package_installer', # 排除任何包含package_installer的文件
    'test_',            # 排除测试文件
]

# 是否生成 requirements.txt
GENERATE_REQUIREMENTS = True

# 手动模式下的import语句
YOUR_IMPORTS = """
"""

# ==================== 新增数据结构 ====================

@dataclass
class ImportInfo:
    """单个导入语句的详细信息"""
    package_name: str          # 包名 (如: requests)
    import_type: str          # 导入类型: 'import' 或 'from_import'
    import_statement: str     # 完整导入语句
    line_number: int          # 行号
    file_path: Path          # 文件路径
    pip_package: str         # pip包名 (如: requests)

class PackageTracker:
    """包依赖追踪器 - 核心改进类"""
    def __init__(self):
        self.package_imports: Dict[str, List[ImportInfo]] = {}  # 包名 -> 导入信息列表
        self.file_imports: Dict[Path, List[ImportInfo]] = {}    # 文件 -> 导入信息列表
        self.all_packages: Set[str] = set()                    # 所有发现的包名
    
    def add_import(self, import_info: ImportInfo):
        """添加导入信息到追踪器"""
        # 添加到包映射
        if import_info.package_name not in self.package_imports:
            self.package_imports[import_info.package_name] = []
        self.package_imports[import_info.package_name].append(import_info)
        
        # 添加到文件映射
        if import_info.file_path not in self.file_imports:
            self.file_imports[import_info.file_path] = []
        self.file_imports[import_info.file_path].append(import_info)
        
        # 添加到包集合
        self.all_packages.add(import_info.package_name)
    
    def get_third_party_packages(self) -> Set[str]:
        """获取第三方包（排除标准库）"""
        return self.all_packages - STDLIB
    
    def get_package_stats(self) -> Dict[str, Dict[str, int]]:
        """获取包使用统计"""
        stats = {}
        for package in self.get_third_party_packages():
            if package in self.package_imports:
                imports = self.package_imports[package]
                if not imports:  # 安全检查：防止空列表
                    continue
                files_count = len(set(imp.file_path for imp in imports))
                stats[package] = {
                    'files_count': files_count,
                    'imports_count': len(imports),
                    'pip_package': imports[0].pip_package
                }
        return stats

# ==================== 核心代码 ====================

# 特殊包名映射
PACKAGE_MAPPING = {
    'PIL': 'pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4',
    'dotenv': 'python-dotenv',
    'yaml': 'pyyaml',
    'OpenSSL': 'pyopenssl',
    'Crypto': 'pycryptodome',
    'dateutil': 'python-dateutil',
    'MySQLdb': 'mysqlclient',
    '_mysql': 'mysqlclient',
    'pkg_resources': 'setuptools',
    # Windows特定模块（pywin32包）
    'win32clipboard': 'pywin32',
    'win32con': 'pywin32',
    'win32api': 'pywin32',
    'win32gui': 'pywin32',
    'win32file': 'pywin32',
    'win32process': 'pywin32',
    'win32service': 'pywin32',
    'win32event': 'pywin32',
    'win32security': 'pywin32',
    'win32pipe': 'pywin32',
    'win32com': 'pywin32',
    'pythoncom': 'pywin32',
    'pywintypes': 'pywin32',
}

# 包名模式匹配规则（用于自动识别常见模式）
# 当遇到匹配的模块名时，自动使用对应的pip包名
# 格式: (正则表达式模式, pip包名)
PACKAGE_PATTERNS = [
    # Windows模块模式：所有win32开头的模块 -> pywin32
    (r'^win32', 'pywin32'),
    # 其他常见模式可以在这里添加，例如：
    # (r'^some_pattern', 'some-package'),
    # (r'^another_pattern', 'another-package'),
]

# 包的特殊处理配置
# 定义需要特殊处理的包（后处理步骤、验证方式等）
# 
# 通用问题类型：
# 1. 后处理步骤：某些包安装后需要运行脚本或执行命令（如pywin32需要运行post-install脚本）
# 2. 多模块验证：某些包包含多个子模块，需要验证所有或任一模块
# 3. 延迟验证：某些包安装后需要等待一段时间才能导入
# 4. 特殊验证逻辑：某些包的验证方式不同（如需要所有模块都能导入，或只要一个能导入）
#
# 格式: {
#   'pip_package_name': {
#       'post_install': Optional[Callable],  # 后处理函数（自定义函数，接收pip_package参数）
#       'post_install_script': Optional[str],  # 后处理脚本模块名（如'pywin32_postinstall'）
#       'post_install_args': Optional[List[str]],  # 脚本参数（如['-install']）
#       'verify_modules': Optional[List[str]],  # 需要验证的模块列表（默认使用package_name和additional_modules）
#       'verify_delay': Optional[float],  # 验证前等待时间（秒），用于需要时间初始化的包
#       'verify_any': Optional[bool],  # 是否只要有一个模块能导入就算成功（默认True）
#                                      # False表示所有模块都必须能导入
#       'skip_import_verify': Optional[bool],  # 跳过导入验证，改用pip show验证（某些包如pywin32需要重启进程才能导入）
#   }
# }
PACKAGE_SPECIAL_HANDLING = {
    'pywin32': {
        'post_install_script': 'pywin32_postinstall',
        'post_install_args': ['-install'],
        'skip_import_verify': True,  # pywin32需要重启Python进程才能导入，使用pip show验证
    },
    # 其他需要特殊处理的包可以在这里添加，例如：
    # 'some-package': {
    #     'post_install_script': 'some_package.setup',
    #     'post_install_args': ['configure'],
    #     'verify_delay': 2.0,  # 安装后等待2秒再验证
    #     'verify_modules': ['module1', 'module2'],  # 指定要验证的模块
    #     'verify_any': False,  # 所有模块都必须能导入
    # },
    # 'another-package': {
    #     'post_install': lambda pkg: some_custom_function(pkg),  # 使用自定义函数
    #     'verify_delay': 1.5,
    # },
}

def get_pip_package_name(import_name: str) -> str:
    """
    获取pip包名，支持多种查找方式：
    1. 直接映射（PACKAGE_MAPPING）
    2. 模式匹配（PACKAGE_PATTERNS）
    3. 默认返回原名称
    """
    # 首先检查直接映射
    if import_name in PACKAGE_MAPPING:
        return PACKAGE_MAPPING[import_name]
    
    # 检查模式匹配
    for pattern, pip_name in PACKAGE_PATTERNS:
        if re.match(pattern, import_name):
            return pip_name
    
    # 默认返回原名称
    return import_name


def generate_package_name_variants(package_name: str) -> List[str]:
    """
    生成包名的常见变体，用于智能查找
    例如：win32clipboard -> ['pywin32', 'win32', 'win32clipboard', 'py-win32']
    """
    variants = [package_name]
    
    # 添加py-前缀变体
    if not package_name.startswith('py'):
        variants.append(f'py-{package_name}')
        variants.append(f'python-{package_name}')
    
    # 下划线转连字符
    if '_' in package_name:
        variants.append(package_name.replace('_', '-'))
    
    # 连字符转下划线
    if '-' in package_name:
        variants.append(package_name.replace('-', '_'))
    
    # 移除数字前缀（如 2to3 -> to3）
    if re.match(r'^\d+', package_name):
        variants.append(re.sub(r'^\d+', '', package_name))
    
    # 添加常见后缀
    for suffix in ['-python', '-py', '']:
        if not package_name.endswith(suffix):
            base = package_name
            variants.append(f'{base}{suffix}')
    
    # 去重并保持顺序
    seen = set()
    result = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            result.append(v)
    
    return result


def search_pypi_package(module_name: str) -> Optional[str]:
    """
    在PyPI上搜索包名，尝试找到正确的pip包名
    使用PyPI JSON API: https://pypi.org/pypi/{package_name}/json
    """
    # 尝试直接搜索模块名
    variants = generate_package_name_variants(module_name)
    
    for variant in variants[:5]:  # 限制尝试次数
        try:
            url = f"https://pypi.org/pypi/{variant}/json"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
                # 如果找到了包，返回包名
                if 'info' in data and 'name' in data['info']:
                    return data['info']['name']
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            continue
    
    return None


def try_install_with_variants(package_name: str, original_pip_name: str) -> Tuple[bool, str, Optional[str]]:
    """
    尝试使用变体名称安装包
    返回: (是否成功, 消息, 实际使用的pip包名)
    """
    # 如果原始名称就是映射后的名称，先尝试模式匹配
    suggested_name = get_pip_package_name(package_name)
    if suggested_name != original_pip_name:
        is_success, msg, actual_name = install_package(package_name, suggested_name, auto_retry=False)
        if is_success:
            return True, f"安装成功（使用映射: {suggested_name}）", actual_name or suggested_name
    
    # 生成变体并尝试
    variants = generate_package_name_variants(package_name)
    
    for variant in variants[:3]:  # 限制尝试次数，避免太慢
        if variant == original_pip_name:
            continue  # 已经尝试过了
        
        is_success, msg, actual_name = install_package(package_name, variant, auto_retry=False)
        if is_success:
            return True, f"安装成功（尝试变体: {variant}）", actual_name or variant
    
    # 尝试PyPI搜索
    pypi_name = search_pypi_package(package_name)
    if pypi_name and pypi_name != original_pip_name:
        is_success, msg, actual_name = install_package(package_name, pypi_name, auto_retry=False)
        if is_success:
            return True, f"安装成功（PyPI找到: {pypi_name}）", actual_name or pypi_name
    
    return False, f"安装失败: 未找到匹配的包（已尝试: {original_pip_name}）", None


# Python标准库 - 优先使用运行时检测（Python 3.10+），否则使用硬编码列表
def _get_stdlib():
    """获取Python标准库模块集合"""
    try:
        # Python 3.10+ 支持
        if hasattr(sys, 'stdlib_module_names'):
            return set(sys.stdlib_module_names)
    except AttributeError:
        pass
    
    # 回退到硬编码列表（兼容旧版本）
    return {
        '__future__', '_thread', 'abc', 'aifc', 'argparse', 'array', 'ast',
        'asynchat', 'asyncio', 'asyncore', 'atexit', 'audioop', 'base64',
        'bdb', 'binascii', 'binhex', 'bisect', 'builtins', 'bz2', 'calendar',
        'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop',
        'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
        'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt',
        'csv', 'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
        'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum',
        'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch',
        'formatter', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
        'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac',
        'html', 'http', 'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib',
        'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3',
        'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal',
        'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt', 'multiprocessing',
        'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
        'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
        'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile',
        'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri',
        'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy',
        'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
        'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver',
        'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep',
        'struct', 'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig',
        'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test',
        'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize',
        'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types',
        'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv',
        'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
        'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib',
        'zoneinfo',
    }

STDLIB = _get_stdlib()


def scan_python_files(root_path: str, scan_subdirs: bool = True) -> List[Path]:
    """扫描指定路径下的所有Python文件"""
    try:
        root = Path(root_path)
        if not root.exists():
            print_colored(f"   ⚠️  路径不存在: {root_path}", "yellow")
            return []
        
        if not root.is_dir():
            print_colored(f"   ⚠️  路径不是目录: {root_path}", "yellow")
            return []
        
        py_files = []
        
        if scan_subdirs:
            for path in root.rglob("*.py"):
                try:
                    # 检查是否在排除的目录中（精确匹配路径部分）
                    if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
                        continue
                    # 检查是否是排除的文件(精确匹配)
                    if path.name in EXCLUDE_FILES:
                        continue
                    # 检查是否匹配排除模式(模糊匹配)
                    if any(pattern in path.name.lower() for pattern in EXCLUDE_FILE_PATTERNS):
                        continue
                    py_files.append(path)
                except (PermissionError, OSError):
                    # 跳过无权限访问的文件
                    continue
        else:
            for path in root.glob("*.py"):
                try:
                    if path.name in EXCLUDE_FILES:
                        continue
                    if any(pattern in path.name.lower() for pattern in EXCLUDE_FILE_PATTERNS):
                        continue
                    py_files.append(path)
                except (PermissionError, OSError):
                    continue
        
        return sorted(py_files)
    except Exception as e:
        print_colored(f"   ⚠️  扫描路径时出错: {e}", "yellow")
        return []


def read_file_safely(file_path: Path) -> str:
    """安全读取文件内容"""
    try:
        if not file_path.exists():
            print_colored(f"   ⚠️  文件不存在: {file_path}", "yellow")
            return ""
        
        if not file_path.is_file():
            print_colored(f"   ⚠️  路径不是文件: {file_path}", "yellow")
            return ""
    except (PermissionError, OSError) as e:
        print_colored(f"   ⚠️  无法访问文件: {file_path} ({e})", "yellow")
        return ""
    
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except (PermissionError, OSError) as e:
            print_colored(f"   ⚠️  无法读取文件: {file_path} ({e})", "yellow")
            return ""
    
    # 如果所有编码都失败,返回空字符串
    print_colored(f"   ⚠️  无法读取文件（编码问题）: {file_path}", "yellow")
    return ""


def extract_imports_from_code(code_text: str) -> Set[str]:
    """智能提取代码中的所有import包名（保持向后兼容）"""
    packages = set()
    
    # 移除注释
    lines = []
    for line in code_text.split('\n'):
        # 只移除行末注释，不处理字符串
        line = re.sub(r'#.*$', '', line)
        lines.append(line.strip())
    
    # 使用更精确的正则表达式来匹配import语句，确保它们不在字符串中
    # 参考: https://stackoverflow.com/questions/6883049/regex-to-match-python-import-statements
    
    # from xxx import yyy
    from_pattern = r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+'
    # import xxx
    import_pattern = r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_.]+(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_.]+)*)'
    
    for line in lines:
        if not line:
            continue
            
        # 检查行是否包含有效的import语句（不在字符串中）
        # 简单的检查：如果行中引号数量为奇数，则可能包含未闭合的字符串
        # 这种情况下跳过该行，避免误匹配
        if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
            continue
            
        # 匹配 from xxx import yyy
        from_match = re.match(from_pattern, line)
        if from_match:
            pkg = from_match.group(1).split('.')[0]
            packages.add(pkg)
            continue
        
        # 匹配 import xxx
        import_match = re.match(import_pattern, line)
        if import_match:
            imports_str = import_match.group(1)
            for item in imports_str.split(','):
                item = item.strip()
                pkg = item.split(' as ')[0].strip()
                pkg = pkg.split('.')[0]
                if pkg:
                    packages.add(pkg)
    
    return packages


def extract_imports_with_details(code_text: str, file_path: Path) -> List[ImportInfo]:
    """
    智能提取代码中的所有import语句，包含详细信息
    支持多行import语句（使用括号）
    返回: ImportInfo对象列表
    """
    imports = []
    lines = code_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        original_line = line
        line_num = i + 1
        
        # 移除行末注释但保留字符串中的内容
        line_without_comment = re.sub(r'#.*$', '', line).strip()
        
        if not line_without_comment:
            i += 1
            continue
        
        # 检查行是否包含有效的import语句（不在字符串中）
        # 简单的检查：如果行中引号数量为奇数，则可能包含未闭合的字符串
        # 这种情况下跳过该行，避免误匹配
        if line_without_comment.count('"') % 2 != 0 or line_without_comment.count("'") % 2 != 0:
            i += 1
            continue
        
        # 处理多行import（以括号开始）
        multi_line_import = False
        if '(' in line_without_comment and ('import' in line_without_comment or 'from' in line_without_comment):
            # 检查是否是import语句且包含括号
            if re.match(r'^\s*(from|import)', line_without_comment):
                multi_line_import = True
        
        # 匹配 from xxx import yyy 格式（单行或多行）
        # 先检查是否是from import语句（包括相对导入）
        from_pattern_match = re.match(r'^\s*from\s+([a-zA-Z_.][a-zA-Z0-9_.]*)\s+import', line_without_comment)
        if from_pattern_match:
            package_name_raw = from_pattern_match.group(1)
            
            # 过滤相对导入（以.开头）
            if package_name_raw.startswith('.'):
                i += 1
                continue
            
            # 处理多行from import
            if multi_line_import and '(' in line_without_comment:
                # 收集多行内容，直到找到闭合括号
                import_parts = [line_without_comment]
                j = i + 1
                paren_count = line_without_comment.count('(') - line_without_comment.count(')')
                max_lines = len(lines)  # 防止无限循环
                while j < max_lines and paren_count > 0:
                    next_line = re.sub(r'#.*$', '', lines[j]).strip()
                    import_parts.append(next_line)
                    paren_count += next_line.count('(') - next_line.count(')')
                    j += 1
                    # 安全限制：如果超过1000行还没闭合，可能是语法错误，停止处理
                    if j - i > 1000:
                        break
                full_import = ' '.join(import_parts)
                original_line = '\n'.join(lines[i:j])
                i = j
            else:
                full_import = line_without_comment
                i += 1
            
            # 提取包名（取第一部分）
            package_name = package_name_raw.split('.')[0]
            
            # 检查包名是否为空
            if not package_name or package_name.strip() == '':
                continue
            
            pip_package = get_pip_package_name(package_name)
            
            imports.append(ImportInfo(
                package_name=package_name,
                import_type='from_import',
                import_statement=original_line.strip(),
                line_number=line_num,
                file_path=file_path,
                pip_package=pip_package
            ))
            continue
        
        # 匹配 import xxx 格式（单行或多行）
        import_match = re.match(r'^\s*import\s+(.+)$', line_without_comment)
        if import_match:
            # 处理多行import
            if multi_line_import and '(' in line_without_comment:
                # 收集多行内容，直到找到闭合括号
                import_parts = [line_without_comment]
                j = i + 1
                paren_count = line_without_comment.count('(') - line_without_comment.count(')')
                max_lines = len(lines)  # 防止无限循环
                while j < max_lines and paren_count > 0:
                    next_line = re.sub(r'#.*$', '', lines[j]).strip()
                    import_parts.append(next_line)
                    paren_count += next_line.count('(') - next_line.count(')')
                    j += 1
                    # 安全限制：如果超过1000行还没闭合，可能是语法错误，停止处理
                    if j - i > 1000:
                        break
                full_import = ' '.join(import_parts)
                original_line = '\n'.join(lines[i:j])
                imports_str = re.match(r'^\s*import\s+(.+)$', full_import)
                if imports_str:
                    imports_str = imports_str.group(1)
                else:
                    imports_str = import_match.group(1)
                i = j
            else:
                imports_str = import_match.group(1)
                i += 1
            
            # 清理imports_str（移除括号和换行）
            imports_str = re.sub(r'[()]', '', imports_str)
            for item in imports_str.split(','):
                item = item.strip()
                if not item:
                    continue
                package_name = item.split(' as ')[0].strip().split('.')[0]
                
                # 检查包名是否为空
                if not package_name or package_name.strip() == '':
                    continue
                
                pip_package = get_pip_package_name(package_name)
                
                imports.append(ImportInfo(
                    package_name=package_name,
                    import_type='import',
                    import_statement=original_line.strip(),
                    line_number=line_num,
                    file_path=file_path,
                    pip_package=pip_package
                ))
            continue
        
        i += 1
    
    return imports


def backup_existing_requirements(requirements_file: str, max_backups: int = 5):
    """
    备份现有的requirements.txt文件
    只保留最近max_backups个备份，删除旧的备份文件
    """
    req_path = Path(requirements_file)
    if not req_path.exists():
        return
    
    # 创建备份
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{requirements_file}.backup_{timestamp}"
        shutil.copy2(requirements_file, backup_name)
        print_colored(f"   📋 已备份现有文件: {backup_name}", "cyan")
    except (PermissionError, OSError) as e:
        print_colored(f"   ⚠️  备份失败: {e}，将继续生成新文件", "yellow")
    
    # 清理旧备份
    try:
        backup_pattern = f"{Path(requirements_file).name}.backup_*"
        backup_files = sorted(Path(requirements_file).parent.glob(backup_pattern), 
                             key=lambda p: p.stat().st_mtime, reverse=True)
        
        # 删除超出限制的旧备份
        if len(backup_files) > max_backups:
            for old_backup in backup_files[max_backups:]:
                try:
                    old_backup.unlink()
                except Exception:
                    pass  # 忽略删除失败
    except Exception:
        pass  # 忽略清理失败


def generate_enhanced_requirements(tracker: PackageTracker,
                                 output_file: str = "requirements.txt",
                                 project_name: Optional[str] = None,
                                 failed_packages: Optional[Set[str]] = None,
                                 failed_pip_packages: Optional[Set[str]] = None) -> Dict[str, str]:
    """
    生成增强版requirements.txt，包含详细的来源信息
    
    Args:
        tracker: 包追踪器
        output_file: 输出文件路径
        project_name: 项目名称
        failed_packages: 安装失败的包名集合（import名称）
        failed_pip_packages: 安装失败的pip包名集合
    """
    # 备份现有文件
    backup_existing_requirements(output_file)
    
    # 获取第三方包
    third_party_packages = tracker.get_third_party_packages()
    package_stats = tracker.get_package_stats()
    
    # 排除安装失败的包
    if failed_packages is None:
        failed_packages = set()
    if failed_pip_packages is None:
        failed_pip_packages = set()
    
    # 过滤掉失败的包
    successful_packages = set()
    for pkg in third_party_packages:
        if pkg in package_stats:
            pip_pkg = package_stats[pkg]['pip_package']
            # 如果包名或pip包名在失败列表中，则跳过
            if pkg not in failed_packages and pip_pkg not in failed_pip_packages:
                successful_packages.add(pkg)
    
    # 确保输出目录存在
    output_path = Path(output_file)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        raise IOError(f"无法创建输出目录 {output_path.parent}: {e}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # === 文件头部 ===
        write_file_header(f, project_name, len(successful_packages), tracker)
        
        # === 包依赖概览 ===
        write_dependency_overview(f, successful_packages, package_stats, tracker)
        
        # === 详细包信息 ===
        write_detailed_package_info(f, successful_packages, tracker)
        
        # === 文件使用统计 ===
        write_file_usage_stats(f, tracker)
        
        # === 失败的包信息（如果有） ===
        if failed_packages or failed_pip_packages:
            f.write("\n# ⚠️  INSTALLATION FAILED PACKAGES (excluded from requirements)\n")
            f.write("# " + "=" * 78 + "\n")
            f.write("# The following packages were detected but failed to install:\n")
            f.write("# They are NOT included in the requirements.txt above.\n")
            f.write("# " + "-" * 78 + "\n")
            for pkg in sorted(failed_packages):
                if pkg in package_stats:
                    pip_pkg = package_stats[pkg]['pip_package']
                    f.write(f"# {pkg} (pip: {pip_pkg}) - Installation failed\n")
            for pip_pkg in sorted(failed_pip_packages):
                f.write(f"# {pip_pkg} - Installation failed\n")
            f.write("# " + "=" * 78 + "\n")
    
    # 返回去重后的pip包名（多个模块可能映射到同一个pip包）
    pip_packages = {}
    for pkg in successful_packages:
        if pkg in package_stats:
            pip_pkg = package_stats[pkg]['pip_package']
            # 如果多个模块映射到同一个pip包，只保留一个（使用第一个遇到的模块名作为key）
            if pip_pkg not in pip_packages:
                pip_packages[pip_pkg] = pkg
    
    return {pkg: str(package_stats[pkg]['pip_package'])
            for pip_pkg, pkg in pip_packages.items()}


def write_file_header(f, project_name: Optional[str], package_count: int, tracker: PackageTracker):
    """写入文件头部信息"""
    total_imports = sum(len(imports) for imports in tracker.package_imports.values()
                       if imports and imports[0].package_name in tracker.get_third_party_packages())
    total_files = len([fp for fp in tracker.file_imports.keys()
                      if any(imp.package_name in tracker.get_third_party_packages()
                            for imp in tracker.file_imports[fp])])
    
    f.write("# " + "=" * 78 + "\n")
    f.write("# 📦 Enhanced Python Package Requirements\n")
    f.write("# " + "=" * 78 + "\n")
    f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"# Project:   {project_name or 'Unknown'}\n")
    f.write(f"# Files:     {total_files} Python files scanned\n")
    f.write(f"# Packages:  {package_count} third-party packages\n")
    f.write(f"# Imports:   {total_imports} import statements\n")
    f.write("# " + "=" * 78 + "\n\n")


def write_dependency_overview(f, packages: Set[str], package_stats: Dict[str, Dict[str, int]], 
                              tracker: Optional['PackageTracker'] = None):
    """写入依赖概览
    按pip包名分组，聚合统计信息（如多个win32模块都映射到pywin32）
    """
    f.write("# 📋 DEPENDENCY OVERVIEW\n")
    f.write("# " + "-" * 78 + "\n")
    
    # 按pip包名分组并聚合统计
    pip_package_stats = {}
    for package in sorted(packages):
        if package in package_stats:
            stats = package_stats[package]
            pip_package = stats['pip_package']
            imports_count = stats['imports_count']
            
            if pip_package not in pip_package_stats:
                pip_package_stats[pip_package] = {'files': set(), 'imports': 0}
            
            # 聚合文件路径（使用set去重）和导入数
            # 从tracker获取该模块的真实文件路径
            if tracker and package in tracker.package_imports:
                for imp in tracker.package_imports[package]:
                    pip_package_stats[pip_package]['files'].add(imp.file_path)
            
            pip_package_stats[pip_package]['imports'] += imports_count
    
    # 写入聚合后的统计信息
    for pip_package in sorted(pip_package_stats.keys()):
        stats = pip_package_stats[pip_package]
        files_count = len(stats['files'])
        imports_count = stats['imports']
        f.write(f"# {pip_package:<20} → {files_count} file(s), {imports_count} import(s)\n")
    
    f.write("# " + "-" * 78 + "\n\n")


def write_detailed_package_info(f, packages: Set[str], tracker: PackageTracker):
    """写入详细包信息
    按pip包名分组，确保同一个pip包只写入一次（如多个win32模块都映射到pywin32）
    """
    f.write("# 📦 DETAILED PACKAGE INFORMATION\n")
    f.write("# " + "=" * 78 + "\n\n")
    
    # 按pip包名分组
    pip_package_groups = {}
    for package in sorted(packages):
        if package not in tracker.package_imports:
            continue
            
        imports = tracker.package_imports[package]
        if not imports:  # 安全检查：防止空列表
            continue
        pip_package = imports[0].pip_package
        
        if pip_package not in pip_package_groups:
            pip_package_groups[pip_package] = []
        pip_package_groups[pip_package].extend(imports)
    
    # 按pip包名排序，每个pip包只写入一次
    for pip_package in sorted(pip_package_groups.keys()):
        all_imports = pip_package_groups[pip_package]
        
        # 包标题
        f.write(f"# {pip_package}\n")
        f.write("# " + "-" * len(pip_package) + "\n")
        
        # 实际的pip包名（这是pip install时需要的）
        f.write(f"{pip_package}\n")
        
        # 使用详情（包含所有映射到这个pip包的模块）
        file_groups = {}
        for imp in all_imports:
            file_name = imp.file_path.name
            if file_name not in file_groups:
                file_groups[file_name] = []
            file_groups[file_name].append(imp)
        
        for file_name in sorted(file_groups.keys()):
            file_imports = sorted(file_groups[file_name], key=lambda x: x.line_number)
            f.write(f"#   📄 {file_name}:\n")
            for imp in file_imports:
                f.write(f"#     L{imp.line_number:3d}: {imp.import_statement}\n")
        
        f.write("\n")


def write_file_usage_stats(f, tracker: PackageTracker):
    """写入文件使用统计"""
    f.write("# 📊 FILE USAGE STATISTICS\n")
    f.write("# " + "=" * 78 + "\n")
    
    third_party_packages = tracker.get_third_party_packages()
    
    for file_path in sorted(tracker.file_imports.keys()):
        imports = tracker.file_imports[file_path]
        third_party_imports = [imp for imp in imports if imp.package_name in third_party_packages]
        
        if third_party_imports:
            f.write(f"# 📄 {file_path.name}: {len(third_party_imports)} third-party imports\n")
            for imp in sorted(third_party_imports, key=lambda x: x.line_number):
                f.write(f"#     L{imp.line_number:3d}: {imp.package_name} ({imp.pip_package})\n")
            f.write("#\n")
    
    f.write("# " + "=" * 78 + "\n")
    f.write("# End of requirements.txt\n")


def check_package_installed(package_name: str) -> bool:
    """
    检查包是否已安装
    使用更严格的验证：不仅检查模块是否存在，还尝试实际导入
    """
    try:
        # 首先检查模块规范是否存在
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            return False
        
        # 尝试实际导入模块以确认它真的可用
        # 这可以避免一些边缘情况（如模块存在但无法导入）
        try:
            importlib.import_module(package_name)
            return True
        except (ImportError, ModuleNotFoundError, ValueError, AttributeError, TypeError):
            return False
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError, TypeError):
        return False


def check_package_installed_via_pip(pip_package: str) -> bool:
    """
    通过pip show命令检查包是否已安装
    用于无法通过import验证的包（如pywin32需要重启进程才能导入）
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pip_package],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


def run_package_post_install(pip_package: str) -> bool:
    """
    运行包的后处理步骤（通用函数）
    
    Args:
        pip_package: pip包名
    
    Returns:
        是否成功执行后处理步骤
    """
    if pip_package not in PACKAGE_SPECIAL_HANDLING:
        return True  # 没有特殊处理，视为成功
    
    config = PACKAGE_SPECIAL_HANDLING[pip_package]
    
    # 执行后处理脚本
    if 'post_install_script' in config:
        script_name = config['post_install_script']
        script_args = config.get('post_install_args', [])
        
        try:
            # 方法1: 通过importlib查找脚本
            script_spec = importlib.util.find_spec(script_name)
            script_path = None
            
            if script_spec and script_spec.origin:
                script_path = script_spec.origin
            
            # 方法2: 如果方法1失败，尝试在site-packages中查找
            if not script_path or not os.path.exists(script_path):
                import site
                for site_packages in site.getsitepackages():
                    candidate = os.path.join(site_packages, f'{script_name}.py')
                    if os.path.exists(candidate):
                        script_path = candidate
                        break
            
            # 如果找到了脚本，运行它
            if script_path and os.path.exists(script_path):
                result = subprocess.run(
                    [sys.executable, script_path] + script_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60
                )
                return result.returncode == 0
        except Exception:
            return False  # 后处理失败，但不影响安装
    
    # 执行后处理函数（如果提供）
    if 'post_install' in config:
        try:
            post_install_func = config['post_install']
            if callable(post_install_func):
                return post_install_func(pip_package)
        except Exception:
            return False
    
    return True  # 没有后处理步骤或执行成功


def install_package(package_name: str, pip_package: str, auto_retry: bool = True, 
                   additional_modules: Optional[List[str]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    安装单个包并验证
    
    Args:
        package_name: 导入时使用的模块名
        pip_package: pip包名
        auto_retry: 是否在失败时自动尝试变体
        additional_modules: 额外的模块名列表（用于验证，如pywin32的多个子模块）
    
    Returns:
        (是否成功, 消息, 实际使用的pip包名)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_package],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            # 执行后处理步骤（如果有配置）
            run_package_post_install(pip_package)
            
            # 获取特殊处理配置
            special_config = PACKAGE_SPECIAL_HANDLING.get(pip_package, {})
            
            # 检查是否跳过导入验证（某些包如pywin32需要重启进程才能导入）
            if special_config.get('skip_import_verify', False):
                # 使用pip show验证安装是否成功
                if check_package_installed_via_pip(pip_package):
                    return True, "安装成功（需重启Python后可导入）", pip_package
                else:
                    return False, "安装失败（pip验证未通过）", pip_package
            
            # 延迟验证（如果需要）
            verify_delay = special_config.get('verify_delay', 0)
            if verify_delay > 0:
                import time
                time.sleep(verify_delay)
            
            # 确定需要验证的模块列表
            modules_to_check = [package_name]
            
            # 如果有配置的验证模块列表，使用它
            if 'verify_modules' in special_config:
                modules_to_check = special_config['verify_modules']
                # 如果配置的模块列表为空，回退到使用package_name
                if not modules_to_check:
                    modules_to_check = [package_name]
            # 否则，如果有额外模块列表，也验证它们
            elif additional_modules:
                modules_to_check.extend(additional_modules)
            
            # 确保至少有一个模块需要验证
            if not modules_to_check:
                modules_to_check = [package_name]
            
            # 验证模式：verify_any=True表示只要有一个模块能导入就算成功
            verify_any = special_config.get('verify_any', True)
            
            if verify_any:
                # 只要有一个模块能导入就算成功
                for module in modules_to_check:
                    if check_package_installed(module):
                        return True, "安装并验证成功", pip_package
                # 如果所有模块都验证失败
                return False, "安装成功但验证失败", pip_package
            else:
                # 所有模块都必须能导入才算成功
                failed_modules = []
                for module in modules_to_check:
                    if not check_package_installed(module):
                        failed_modules.append(module)
                
                if failed_modules:
                    return False, f"安装成功但验证失败（无法导入: {', '.join(failed_modules)}）", pip_package
                else:
                    return True, "安装并验证成功", pip_package
        else:
            # 检查是否是"No matching distribution found"错误
            error_text = result.stderr.lower() if result.stderr else ""
            is_no_distribution = "no matching distribution found" in error_text
            
            # 如果启用自动重试且是找不到包的错误，尝试变体
            if auto_retry and is_no_distribution:
                print_colored(f"   🔍 未找到包 {pip_package}，尝试智能查找...", "yellow")
                success, msg, actual_pip_name = try_install_with_variants(package_name, pip_package)
                if success:
                    return True, msg, actual_pip_name
            
            # 改进错误处理：提取关键错误信息，保留更多上下文
            error_lines = result.stderr.strip().split('\n') if result.stderr else []
            if error_lines:
                # 优先查找ERROR/WARNING等关键词所在的行
                error_msg = None
                for line in reversed(error_lines):
                    if any(keyword in line.upper() for keyword in ['ERROR', 'FAILED', 'EXCEPTION', 'WARNING']):
                        error_msg = line.strip()
                        break
                # 如果没有找到关键词，使用最后几行
                if not error_msg:
                    error_msg = '\n'.join(error_lines[-3:]).strip()
            else:
                error_msg = "未知错误（无错误输出）"
            
            # 提供添加映射的建议
            suggestion = ""
            if is_no_distribution:
                suggestion = f"\n   💡 提示: 如果 {package_name} 是某个包的子模块，请在 PACKAGE_MAPPING 中添加映射：\n      '{package_name}': '正确的pip包名'"
            
            return False, f"安装失败: {error_msg}{suggestion}", None
            
    except subprocess.TimeoutExpired:
        return False, "安装超时(>5分钟)", None
    except Exception as e:
        return False, f"异常: {str(e)}", None


def replace_emojis(text: str) -> str:
    """替换文本中的emoji为ASCII安全的替代字符"""
    if os.name == 'nt':
        emoji_map = {
            '🚀': '[*]', '📁': '[DIR]', '📋': '[INFO]', '🔍': '[SCAN]',
            '📝': '[FILE]', '📦': '[PKG]', '✨': '[OK]', '⚠️': '[WARN]',
            '✅': '[SUCCESS]', '❌': '[FAIL]', '📄': '[DOC]', '📊': '[STATS]',
            '⚙️': '[WORK]', '💡': '[TIP]', '🎉': '[DONE]'
        }
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
    return text


def safe_print(text: str):
    """安全打印函数，处理编码问题"""
    text = replace_emojis(text)
    
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果仍然有编码问题，使用ASCII安全版本
        safe_text = text.encode('ascii', 'ignore').decode('ascii')
        print(safe_text)


def print_colored(text: str, color: str = ""):
    """打印彩色文本（兼容Windows编码）"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'reset': '\033[0m',
        'bold': '\033[1m',
    }
    
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    
    # 处理Windows编码问题，将emoji替换为简单字符
    text = replace_emojis(text)
    
    try:
        if color and color in colors:
            print(f"{colors[color]}{text}{colors['reset']}")
        else:
            print(text)
    except UnicodeEncodeError:
        # 如果仍然有编码问题，使用ASCII安全版本
        safe_text = text.encode('ascii', 'ignore').decode('ascii')
        if color and color in colors:
            print(f"{colors[color]}{safe_text}{colors['reset']}")
        else:
            print(safe_text)


def scan_and_install(scan_path: Optional[str] = None, scan_subdirs: bool = True, generate_req: bool = True):
    """扫描项目并安装所有依赖（增强版）"""
    
    print_colored("\n" + "=" * 70, "cyan")
    print_colored("🚀 增强版Python项目智能包管理工具 - 扫描模式", "bold")
    print_colored("=" * 70, "cyan")
    
    # 确定扫描路径
    if scan_path is None:
        scan_path = os.getcwd()
    
    scan_path = os.path.abspath(scan_path)
    project_name = Path(scan_path).name
    safe_print(f"\n📁 扫描路径: {scan_path}")
    safe_print(f"📋 项目名称: {project_name}")
    safe_print(f"🔍 扫描模式: {'递归扫描子目录' if scan_subdirs else '仅当前目录'}")
    
    # 步骤1: 扫描文件
    print_colored("\n📝 步骤1: 扫描Python文件...", "blue")
    py_files = scan_python_files(scan_path, scan_subdirs)
    
    if not py_files:
        print_colored("   ⚠️  未找到任何Python文件!", "yellow")
        return
    
    safe_print(f"   找到 {len(py_files)} 个Python文件")
    
    # 显示扫描的文件列表(排除了安装脚本自己)
    if len(py_files) <= 10:
        safe_print("\n   扫描文件:")
        for f in py_files:
            safe_print(f"     • {f.name}")
    
    # 步骤2: 详细分析import语句
    print_colored("\n📦 步骤2: 详细分析import语句...", "blue")
    tracker = PackageTracker()
    
    for py_file in py_files:
        content = read_file_safely(py_file)
        imports = extract_imports_with_details(content, py_file)
        
        # 更新追踪器
        for import_info in imports:
            tracker.add_import(import_info)
    
    if not tracker.all_packages:
        print_colored("   ⚠️  未检测到任何import语句", "yellow")
        return
    
    safe_print(f"   检测到 {len(tracker.all_packages)} 个不同的包")
    
    # 显示详细信息
    if len(py_files) <= 10:
        safe_print("\n   文件详情:")
        for file_path in sorted(tracker.file_imports.keys()):
            imports = tracker.file_imports[file_path]
            try:
                rel_path = file_path.relative_to(scan_path)
            except ValueError:
                # 如果文件不在扫描路径下，使用绝对路径
                rel_path = file_path
            safe_print(f"     • {rel_path}: {len(imports)} 个导入语句")
    
    # 步骤3: 过滤标准库
    print_colored("\n🔍 步骤3: 过滤标准库...", "blue")
    third_party = tracker.get_third_party_packages()
    stdlib_count = len(tracker.all_packages) - len(third_party)
    safe_print(f"   标准库: {stdlib_count} 个 | 第三方库: {len(third_party)} 个")
    
    if not third_party:
        print_colored("\n✨ 所有包都是标准库,无需安装!", "green")
        if generate_req:
            # 即使没有第三方包，也生成一个空的requirements.txt
            generate_enhanced_requirements(tracker, "requirements.txt", project_name, 
                                          failed_packages=set(), failed_pip_packages=set())
            print_colored("   📄 已生成空的requirements.txt文件", "cyan")
        return
    
    # 显示检测到的第三方包统计
    safe_print(f"\n   第三方包详情:")
    package_stats = tracker.get_package_stats()
    for pkg in sorted(third_party):
        if pkg not in package_stats:
            continue  # 跳过没有统计信息的包（理论上不应该发生）
        stats = package_stats[pkg]
        pip_pkg = stats['pip_package']
        files_count = stats['files_count']
        imports_count = stats['imports_count']
        
        if pkg != pip_pkg:
            safe_print(f"     • {pkg} → {pip_pkg} ({files_count} 文件, {imports_count} 导入)")
        else:
            safe_print(f"     • {pkg} ({files_count} 文件, {imports_count} 导入)")
    
    # 继续安装流程...
    enhanced_process_installation(tracker, generate_req, project_name)


def enhanced_process_installation(tracker: PackageTracker, generate_req: bool, project_name: str):
    """处理增强版安装流程"""
    
    third_party_packages = tracker.get_third_party_packages()
    package_stats = tracker.get_package_stats()
    
    print_colored(f"\n📦 步骤4: 准备安装 {len(third_party_packages)} 个第三方包...", "blue")
    
    already_installed = []
    need_install = []
    
    # 按pip包名分组，以便处理多模块映射的情况
    pip_package_groups = {}
    for pkg in sorted(third_party_packages):
        if pkg not in package_stats:
            continue  # 跳过没有统计信息的包（理论上不应该发生）
        stats = package_stats[pkg]
        pip_pkg = stats['pip_package']
        
        if pip_pkg not in pip_package_groups:
            pip_package_groups[pip_pkg] = []
        pip_package_groups[pip_pkg].append(pkg)
    
    # 检查每个pip包及其所有映射的模块
    for pip_pkg, module_names in pip_package_groups.items():
        # 安全检查：确保有模块需要处理
        if not module_names:
            continue
        
        # 检查是否需要特殊处理
        special_config = PACKAGE_SPECIAL_HANDLING.get(pip_pkg, {})
        
        # 检查是否跳过导入验证（某些包如pywin32需要重启进程才能导入）
        skip_import_verify = special_config.get('skip_import_verify', False)
        
        # 检查包是否已安装
        is_installed = False
        
        if skip_import_verify:
            # 使用pip show验证
            is_installed = check_package_installed_via_pip(pip_pkg)
        else:
            verify_any = special_config.get('verify_any', True)
            
            # 确定需要检查的模块列表
            modules_to_check = module_names
            if 'verify_modules' in special_config:
                modules_to_check = [m for m in special_config['verify_modules'] if m in module_names]
            
            # 如果模块列表为空，使用原始模块列表
            if not modules_to_check:
                modules_to_check = module_names
            
            if modules_to_check:  # 确保有模块需要检查
                if verify_any:
                    # 只要有一个模块能导入就算已安装
                    for module in modules_to_check:
                        if check_package_installed(module):
                            is_installed = True
                            break
                else:
                    # 所有模块都必须能导入才算已安装
                    is_installed = all(check_package_installed(module) for module in modules_to_check)
        
        if is_installed:
            already_installed.extend(module_names)
        else:
            # 包未安装，添加所有模块名
            for module_name in module_names:
                need_install.append((module_name, pip_pkg))
    
    if already_installed:
        print_colored(f"\n   ✓ 已安装 ({len(already_installed)}):", "green")
        for pkg in already_installed[:5]:
            safe_print(f"     • {pkg}")
        if len(already_installed) > 5:
            safe_print(f"     ... 还有 {len(already_installed) - 5} 个")
    
    if not need_install:
        print_colored("\n🎉 所有包都已安装!", "green")
        failed_packages = set()
        failed_pip_packages = set()
    else:
        print_colored(f"\n⚙️  步骤5: 安装 {len(need_install)} 个缺失的包...", "blue")
        print_colored("   💡 提示: pip会自动安装依赖包(如numpy被wordcloud依赖)", "cyan")
        print_colored("-" * 70, "cyan")
        
        # 去重：多个模块可能映射到同一个pip包（如win32clipboard和win32con都映射到pywin32）
        pip_packages_to_install = {}
        for import_name, pip_name in need_install:
            if pip_name not in pip_packages_to_install:
                pip_packages_to_install[pip_name] = []
            pip_packages_to_install[pip_name].append(import_name)
        
        success_modules = []  # 成功安装的模块名列表（用于统计）
        failed = []
        failed_packages = set()  # 失败的import包名
        failed_pip_packages = set()  # 失败的pip包名
        
        install_index = 0
        for pip_name, import_names in pip_packages_to_install.items():
            if not import_names:  # 安全检查：确保有模块需要安装
                continue
            
            install_index += 1
            # 使用第一个import名称进行验证
            import_name_for_check = import_names[0]
            print(f"\n[{install_index}/{len(pip_packages_to_install)}] {pip_name}")
            if len(import_names) > 1:
                print(f"   (包含模块: {', '.join(import_names)})")
            
            # 对于多个模块映射到同一个pip包的情况，传递所有模块名用于验证
            is_success, msg, actual_pip_name = install_package(
                import_name_for_check, pip_name, 
                additional_modules=import_names[1:] if len(import_names) > 1 else None
            )
            
            if is_success:
                print_colored(f"   ✅ {msg}", "green")
                success_modules.extend(import_names)  # 记录所有模块名（用于统计）
            else:
                print_colored(f"   ❌ {msg}", "red")
                failed.append((pip_name, msg))
                failed_pip_packages.add(pip_name)
                
                # 检查哪些模块实际上能导入（可能部分模块已经可用）
                # 获取特殊处理配置
                special_config = PACKAGE_SPECIAL_HANDLING.get(pip_name, {})
                verify_any = special_config.get('verify_any', True)
                
                # 确定需要检查的模块列表
                modules_to_check = import_names
                if 'verify_modules' in special_config:
                    modules_to_check = [m for m in special_config['verify_modules'] if m in import_names]
                
                # 如果模块列表为空，使用原始模块列表
                if not modules_to_check:
                    modules_to_check = import_names
                
                # 检查哪些模块能导入
                if modules_to_check:  # 确保有模块需要检查
                    if verify_any:
                        # 只要有一个模块能导入，就不标记为完全失败
                        can_import_any = any(check_package_installed(module) for module in modules_to_check)
                        if not can_import_any:
                            # 所有模块都无法导入，标记为失败
                            for imp_name in import_names:
                                failed_packages.add(imp_name)
                        # 如果至少有一个能导入，不添加到failed_packages（可能只是部分失败）
                    else:
                        # 所有模块都必须能导入，检查哪些失败
                        for imp_name in import_names:
                            if not check_package_installed(imp_name):
                                failed_packages.add(imp_name)
                else:
                    # 如果没有模块需要检查，标记所有为失败
                    for imp_name in import_names:
                        failed_packages.add(imp_name)
        
        # 总结
        print_colored("\n" + "=" * 70, "cyan")
        print_colored("📊 安装总结", "bold")
        print_colored("=" * 70, "cyan")
        
        total = len(third_party_packages)
        installed = len(already_installed) + len(success_modules)
        
        print(f"\n你的代码直接使用: {total} 个第三方包")
        print_colored(f"✓ 已就绪: {installed} 个", "green")
        
        if failed:
            print_colored(f"✗ 失败: {len(failed)} 个", "red")
            print("\n失败详情:")
            for pkg, msg in failed:
                print(f"  • {pkg}: {msg}")
            print_colored("\n💡 手动安装: pip install <包名>", "yellow")
        else:
            print_colored("🎉 全部安装成功!", "green")
    
    # 生成增强版requirements.txt
    if generate_req:
        print_colored("\n📄 步骤6: 生成增强版requirements.txt...", "blue")
        try:
            enhanced_requirements = generate_enhanced_requirements(
                tracker, "requirements.txt", project_name,
                failed_packages=failed_packages,
                failed_pip_packages=failed_pip_packages
            )
            
            print_colored(f"   ✅ 已生成增强版 requirements.txt ({len(enhanced_requirements)} 个直接依赖)", "green")
            print_colored("   📋 包含详细的来源信息和使用统计", "cyan")
            print_colored("   🔍 每个包的文件路径和行号都已记录", "cyan")
            
            # 显示示例
            if len(enhanced_requirements) <= 5:
                print("\n   包含的包:")
                for pkg_name, pip_name in sorted(enhanced_requirements.items()):
                    stats = package_stats.get(pkg_name, {})
                    files_count = stats.get('files_count', 0)
                    imports_count = stats.get('imports_count', 0)
                    print(f"     • {pip_name} ({files_count} 文件, {imports_count} 导入)")
                     
        except Exception as e:
            print_colored(f"   ⚠️  生成失败: {e}", "yellow")
    
    print_colored("\n" + "=" * 70, "cyan")
    print_colored("✨ 增强版包管理完成!", "bold")
    print_colored("=" * 70 + "\n", "cyan")


def manual_install(imports_code: str, generate_req: bool = True):
    """手动模式: 使用YOUR_IMPORTS变量"""
    print_colored("\n" + "=" * 70, "cyan")
    print_colored("🚀 Python智能包管理工具 - 手动模式", "bold")
    print_colored("=" * 70, "cyan")
    
    print_colored("\n📝 步骤1: 分析import语句...", "blue")
    
    # 创建一个临时的Path对象表示手动导入
    temp_file_path = Path("manual_imports")
    
    # 使用增强版提取函数获取详细的导入信息
    imports_details = extract_imports_with_details(imports_code, temp_file_path)
    
    if not imports_details:
        print_colored("   ⚠️  未检测到任何import语句", "yellow")
        return
    
    # 创建包追踪器
    tracker = PackageTracker()
    for import_info in imports_details:
        tracker.add_import(import_info)
    
    print(f"   检测到 {len(tracker.all_packages)} 个包")
    
    print_colored("\n🔍 步骤2: 过滤标准库...", "blue")
    third_party = tracker.get_third_party_packages()
    print(f"   标准库: {len(tracker.all_packages) - len(third_party)} 个 | 第三方库: {len(third_party)} 个")
    
    if not third_party:
        print_colored("\n✨ 所有包都是标准库!", "green")
        return
    
    # 使用增强版安装流程
    enhanced_process_installation(tracker, generate_req, "manual_imports")


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        SCAN_PATH = sys.argv[1]
    
    # 执行
    if SCAN_MODE:
        scan_and_install(SCAN_PATH, SCAN_SUBDIRS, GENERATE_REQUIREMENTS)
    else:
        manual_install(YOUR_IMPORTS, GENERATE_REQUIREMENTS)
