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
}

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
            
            pip_package = PACKAGE_MAPPING.get(package_name, package_name)
            
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
                
                pip_package = PACKAGE_MAPPING.get(package_name, package_name)
                
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


def generate_requirements(packages: Dict[str, str], user_packages: Set[str], output_file: str = "requirements.txt"):
    """
    生成requirements.txt（保持向后兼容）
    只包含用户直接导入的包,不包含自动安装的依赖包
    """
    # 只保留用户实际导入的包
    user_requirements = {pkg: pip_name for pkg, pip_name in packages.items() if pkg in user_packages}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Auto-generated by install_packages.py\n")
        f.write(f"# Generated at: {datetime.now()}\n")
        f.write("# Only includes directly imported packages (not transitive dependencies)\n")
        f.write("# pip will automatically install dependencies like numpy for wordcloud\n\n")
        for pip_pkg in sorted(user_requirements.values()):
            f.write(f"{pip_pkg}\n")
    
    return user_requirements


def backup_existing_requirements(requirements_file: str, max_backups: int = 5):
    """
    备份现有的requirements.txt文件
    只保留最近max_backups个备份，删除旧的备份文件
    """
    req_path = Path(requirements_file)
    if not req_path.exists():
        return
    
    # 创建备份
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{requirements_file}.backup_{timestamp}"
    shutil.copy2(requirements_file, backup_name)
    print_colored(f"   📋 已备份现有文件: {backup_name}", "cyan")
    
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
                                 project_name: Optional[str] = None) -> Dict[str, str]:
    """
    生成增强版requirements.txt，包含详细的来源信息
    """
    # 备份现有文件
    backup_existing_requirements(output_file)
    
    # 获取第三方包
    third_party_packages = tracker.get_third_party_packages()
    package_stats = tracker.get_package_stats()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # === 文件头部 ===
        write_file_header(f, project_name, len(third_party_packages), tracker)
        
        # === 包依赖概览 ===
        write_dependency_overview(f, third_party_packages, package_stats)
        
        # === 详细包信息 ===
        write_detailed_package_info(f, third_party_packages, tracker)
        
        # === 文件使用统计 ===
        write_file_usage_stats(f, tracker)
    
    return {pkg: str(package_stats[pkg]['pip_package'])
            for pkg in third_party_packages if pkg in package_stats}


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


def write_dependency_overview(f, packages: Set[str], package_stats: Dict[str, Dict[str, int]]):
    """写入依赖概览"""
    f.write("# 📋 DEPENDENCY OVERVIEW\n")
    f.write("# " + "-" * 78 + "\n")
    
    for package in sorted(packages):
        if package in package_stats:
            stats = package_stats[package]
            pip_package = stats['pip_package']
            files_count = stats['files_count']
            imports_count = stats['imports_count']
            f.write(f"# {pip_package:<20} → {files_count} file(s), {imports_count} import(s)\n")
    
    f.write("# " + "-" * 78 + "\n\n")


def write_detailed_package_info(f, packages: Set[str], tracker: PackageTracker):
    """写入详细包信息"""
    f.write("# 📦 DETAILED PACKAGE INFORMATION\n")
    f.write("# " + "=" * 78 + "\n\n")
    
    for package in sorted(packages):
        if package not in tracker.package_imports:
            continue
            
        imports = tracker.package_imports[package]
        if not imports:  # 安全检查：防止空列表
            continue
        pip_package = imports[0].pip_package
        
        # 包标题
        f.write(f"# {pip_package}\n")
        f.write("# " + "-" * len(pip_package) + "\n")
        
        # 实际的pip包名（这是pip install时需要的）
        f.write(f"{pip_package}\n")
        
        # 使用详情
        file_groups = {}
        for imp in imports:
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
    """检查包是否已安装"""
    try:
        return importlib.util.find_spec(package_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def install_package(package_name: str, pip_package: str) -> Tuple[bool, str]:
    """安装单个包并验证"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_package],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            if check_package_installed(package_name):
                return True, "安装并验证成功"
            else:
                return False, "安装成功但验证失败"
        else:
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
            return False, f"安装失败: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return False, "安装超时(>5分钟)"
    except Exception as e:
        return False, f"异常: {str(e)}"


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
        except:
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
            generate_enhanced_requirements(tracker, "requirements.txt", project_name)
            print_colored("   📄 已生成空的requirements.txt文件", "cyan")
        return
    
    # 显示检测到的第三方包统计
    safe_print(f"\n   第三方包详情:")
    package_stats = tracker.get_package_stats()
    for pkg in sorted(third_party):
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


def process_installation(third_party: Set[str], generate_req: bool):
    """处理安装流程"""
    
    # 保存用户实际导入的包(用于生成requirements.txt)
    user_imported_packages = third_party.copy()
    
    print_colored(f"\n📦 步骤4: 准备安装 {len(third_party)} 个第三方包...", "blue")
    
    packages_to_install = {}
    already_installed = []
    need_install = []
    
    for pkg in sorted(third_party):
        pip_pkg = PACKAGE_MAPPING.get(pkg, pkg)
        packages_to_install[pkg] = pip_pkg
        
        if check_package_installed(pkg):
            already_installed.append(pkg)
        else:
            need_install.append((pkg, pip_pkg))
    
    if already_installed:
        print_colored(f"\n   ✓ 已安装 ({len(already_installed)}):", "green")
        for pkg in already_installed[:5]:
            print(f"     • {pkg}")
        if len(already_installed) > 5:
            print(f"     ... 还有 {len(already_installed) - 5} 个")
    
    if not need_install:
        print_colored("\n🎉 所有包都已安装!", "green")
    else:
        print_colored(f"\n⚙️  步骤5: 安装 {len(need_install)} 个缺失的包...", "blue")
        print_colored("   💡 提示: pip会自动安装依赖包(如numpy被wordcloud依赖)", "cyan")
        print_colored("-" * 70, "cyan")
        
        success = []
        failed = []
        
        for i, (import_name, pip_name) in enumerate(need_install, 1):
            print(f"\n[{i}/{len(need_install)}] {pip_name}")
            is_success, msg = install_package(import_name, pip_name)
            
            if is_success:
                print_colored(f"   ✅ {msg}", "green")
                success.append(pip_name)
            else:
                print_colored(f"   ❌ {msg}", "red")
                failed.append((pip_name, msg))
        
        # 总结
        print_colored("\n" + "=" * 70, "cyan")
        print_colored("📊 安装总结", "bold")
        print_colored("=" * 70, "cyan")
        
        total = len(third_party)
        installed = len(already_installed) + len(success)
        
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
    
    # 生成requirements.txt - 只包含用户直接导入的包
    if generate_req:
        print_colored("\n📄 步骤6: 生成requirements.txt...", "blue")
        try:
            user_requirements = generate_requirements(packages_to_install, user_imported_packages)
            
            print_colored(f"   ✅ 已生成 requirements.txt ({len(user_requirements)} 个直接依赖)", "green")
            print_colored("   💡 只包含你代码中import的包,不含间接依赖", "cyan")
            
            # 显示示例
            if len(user_requirements) <= 10:
                print("\n   内容预览:")
                for pip_pkg in sorted(user_requirements.values()):
                    print(f"     • {pip_pkg}")
                    
        except Exception as e:
            print_colored(f"   ⚠️  生成失败: {e}", "yellow")
    
    print_colored("\n" + "=" * 70, "cyan")
    print_colored("✨ 完成!", "bold")
    print_colored("=" * 70 + "\n", "cyan")


def enhanced_process_installation(tracker: PackageTracker, generate_req: bool, project_name: str):
    """处理增强版安装流程"""
    
    third_party_packages = tracker.get_third_party_packages()
    package_stats = tracker.get_package_stats()
    
    print_colored(f"\n📦 步骤4: 准备安装 {len(third_party_packages)} 个第三方包...", "blue")
    
    packages_to_install = {}
    already_installed = []
    need_install = []
    
    for pkg in sorted(third_party_packages):
        stats = package_stats[pkg]
        pip_pkg = stats['pip_package']
        packages_to_install[pkg] = pip_pkg
        
        if check_package_installed(pkg):
            already_installed.append(pkg)
        else:
            need_install.append((pkg, pip_pkg))
    
    if already_installed:
        print_colored(f"\n   ✓ 已安装 ({len(already_installed)}):", "green")
        for pkg in already_installed[:5]:
            safe_print(f"     • {pkg}")
        if len(already_installed) > 5:
            safe_print(f"     ... 还有 {len(already_installed) - 5} 个")
    
    if not need_install:
        print_colored("\n🎉 所有包都已安装!", "green")
    else:
        print_colored(f"\n⚙️  步骤5: 安装 {len(need_install)} 个缺失的包...", "blue")
        print_colored("   💡 提示: pip会自动安装依赖包(如numpy被wordcloud依赖)", "cyan")
        print_colored("-" * 70, "cyan")
        
        success = []
        failed = []
        
        for i, (import_name, pip_name) in enumerate(need_install, 1):
            print(f"\n[{i}/{len(need_install)}] {pip_name}")
            is_success, msg = install_package(import_name, pip_name)
            
            if is_success:
                print_colored(f"   ✅ {msg}", "green")
                success.append(pip_name)
            else:
                print_colored(f"   ❌ {msg}", "red")
                failed.append((pip_name, msg))
        
        # 总结
        print_colored("\n" + "=" * 70, "cyan")
        print_colored("📊 安装总结", "bold")
        print_colored("=" * 70, "cyan")
        
        total = len(third_party_packages)
        installed = len(already_installed) + len(success)
        
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
            enhanced_requirements = generate_enhanced_requirements(tracker, "requirements.txt", project_name)
            
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
