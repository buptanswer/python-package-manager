"""
测试文件操作功能
覆盖: scan_python_files, read_file_safely
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from package_installer_yulibupt import (
    scan_python_files,
    read_file_safely,
    EXCLUDE_DIRS,
    EXCLUDE_FILES,
    EXCLUDE_FILE_PATTERNS
)


class TestScanPythonFiles(unittest.TestCase):
    """测试Python文件扫描功能"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    # ==================== 基础扫描测试 ====================

    def test_scan_single_file(self):
        """测试扫描单个文件"""
        (self.test_dir / "test.py").write_text("import os", encoding='utf-8')
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "test.py")

    def test_scan_multiple_files(self):
        """测试扫描多个文件"""
        for i in range(5):
            (self.test_dir / f"test{i}.py").write_text("import os", encoding='utf-8')
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        self.assertEqual(len(files), 5)

    def test_scan_no_py_files(self):
        """测试没有.py文件的目录"""
        (self.test_dir / "test.txt").write_text("hello", encoding='utf-8')
        (self.test_dir / "test.js").write_text("console.log('hi')", encoding='utf-8')
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        self.assertEqual(len(files), 0)

    def test_scan_empty_directory(self):
        """测试空目录"""
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        self.assertEqual(len(files), 0)

    # ==================== 子目录扫描测试 ====================

    def test_scan_subdirs_enabled(self):
        """测试启用子目录扫描"""
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        (self.test_dir / "root.py").write_text("import os", encoding='utf-8')
        (subdir / "sub.py").write_text("import sys", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 2)

    def test_scan_subdirs_disabled(self):
        """测试禁用子目录扫描"""
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        (self.test_dir / "root.py").write_text("import os", encoding='utf-8')
        (subdir / "sub.py").write_text("import sys", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "root.py")

    def test_scan_nested_subdirs(self):
        """测试嵌套子目录扫描"""
        level1 = self.test_dir / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)
        
        (self.test_dir / "root.py").write_text("import os", encoding='utf-8')
        (level1 / "l1.py").write_text("import os", encoding='utf-8')
        (level2 / "l2.py").write_text("import os", encoding='utf-8')
        (level3 / "l3.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 4)

    # ==================== 排除目录测试 ====================

    def test_exclude_pycache(self):
        """测试排除__pycache__目录"""
        pycache = self.test_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "test.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "main.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        file_names = {f.name for f in files}
        self.assertIn("main.py", file_names)
        self.assertNotIn("test.py", file_names)

    def test_exclude_git(self):
        """测试排除.git目录"""
        git_dir = self.test_dir / ".git"
        git_dir.mkdir()
        (git_dir / "hook.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "main.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 1)

    def test_exclude_venv(self):
        """测试排除venv目录"""
        for venv_name in ['venv', '.venv', 'env']:
            venv_dir = self.test_dir / venv_name
            venv_dir.mkdir()
            (venv_dir / "activate.py").write_text("import os", encoding='utf-8')
        
        (self.test_dir / "main.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 1)

    def test_exclude_multiple_dirs(self):
        """测试排除多个目录"""
        for dir_name in ['__pycache__', '.git', 'venv', 'node_modules', '.idea', 'build']:
            excluded_dir = self.test_dir / dir_name
            excluded_dir.mkdir()
            (excluded_dir / "test.py").write_text("import os", encoding='utf-8')
        
        (self.test_dir / "main.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 1)

    # ==================== 排除文件测试 ====================

    def test_exclude_installer_file(self):
        """测试排除安装脚本文件"""
        (self.test_dir / "package_installer_yulibupt.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "main.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        file_names = {f.name for f in files}
        self.assertNotIn("package_installer_yulibupt.py", file_names)
        self.assertIn("main.py", file_names)

    def test_exclude_test_files(self):
        """测试排除测试文件（test_前缀）"""
        (self.test_dir / "test_something.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "main.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        file_names = {f.name for f in files}
        self.assertNotIn("test_something.py", file_names)
        self.assertIn("main.py", file_names)

    def test_exclude_pattern_case_insensitive(self):
        """测试排除模式不区分大小写"""
        (self.test_dir / "TEST_file.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "Test_File.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "main.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        file_names = {f.name for f in files}
        self.assertEqual(len(file_names), 1)
        self.assertIn("main.py", file_names)

    # ==================== 错误处理测试 ====================

    def test_scan_nonexistent_path(self):
        """测试不存在的路径"""
        files = scan_python_files("/nonexistent/path/12345")
        self.assertEqual(len(files), 0)

    def test_scan_file_instead_of_dir(self):
        """测试传入文件而不是目录"""
        test_file = self.test_dir / "test.py"
        test_file.write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(test_file))
        self.assertEqual(len(files), 0)

    def test_scan_returns_sorted(self):
        """测试返回结果已排序"""
        (self.test_dir / "z_file.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "a_file.py").write_text("import os", encoding='utf-8')
        (self.test_dir / "m_file.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        file_names = [f.name for f in files]
        self.assertEqual(file_names, sorted(file_names))


class TestReadFileSafely(unittest.TestCase):
    """测试安全文件读取功能"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    # ==================== 基础读取测试 ====================

    def test_read_utf8_file(self):
        """测试读取UTF-8编码文件"""
        test_file = self.test_dir / "test.py"
        content = "import os\n# 中文注释"
        test_file.write_text(content, encoding='utf-8')
        
        result = read_file_safely(test_file)
        self.assertEqual(result, content)

    def test_read_empty_file(self):
        """测试读取空文件"""
        test_file = self.test_dir / "empty.py"
        test_file.write_text("", encoding='utf-8')
        
        result = read_file_safely(test_file)
        self.assertEqual(result, "")

    def test_read_large_file(self):
        """测试读取大文件"""
        test_file = self.test_dir / "large.py"
        content = "import os\n" * 10000
        test_file.write_text(content, encoding='utf-8')
        
        result = read_file_safely(test_file)
        self.assertEqual(result, content)

    # ==================== 编码测试 ====================

    def test_read_gbk_file(self):
        """测试读取GBK编码文件"""
        test_file = self.test_dir / "gbk.py"
        content = "import os"
        try:
            test_file.write_text(content, encoding='gbk')
            result = read_file_safely(test_file)
            self.assertEqual(result, content)
        except (UnicodeEncodeError, LookupError):
            self.skipTest("系统不支持GBK编码")

    def test_read_latin1_file(self):
        """测试读取Latin-1编码文件"""
        test_file = self.test_dir / "latin1.py"
        content = "import os"
        test_file.write_text(content, encoding='latin-1')
        
        result = read_file_safely(test_file)
        self.assertEqual(result, content)

    # ==================== 错误处理测试 ====================

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        result = read_file_safely(Path("/nonexistent/file.py"))
        self.assertEqual(result, "")

    def test_read_directory(self):
        """测试读取目录（而非文件）"""
        result = read_file_safely(self.test_dir)
        self.assertEqual(result, "")

    def test_read_returns_string(self):
        """测试返回类型为字符串"""
        test_file = self.test_dir / "test.py"
        test_file.write_text("import os", encoding='utf-8')
        
        result = read_file_safely(test_file)
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    unittest.main()
