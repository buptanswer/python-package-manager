"""
测试文件操作功能
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from package_installer_yulibupt import (
    scan_python_files,
    read_file_safely,
    EXCLUDE_DIRS,
    EXCLUDE_FILES
)


class TestFileOperations(unittest.TestCase):
    """测试文件操作功能"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_scan_python_files_basic(self):
        """测试基本文件扫描"""
        # 创建测试文件
        (self.test_dir / "test1.py").write_text("import os")
        (self.test_dir / "test2.py").write_text("import sys")
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        self.assertEqual(len(files), 2)

    def test_scan_python_files_subdirs(self):
        """测试递归扫描子目录"""
        # 创建子目录和文件
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        (subdir / "test.py").write_text("import os")
        (self.test_dir / "test.py").write_text("import sys")
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 2)

    def test_scan_excludes_dirs(self):
        """测试排除目录"""
        # 创建排除的目录
        for excluded_dir in ['__pycache__', '.git', 'venv']:
            excluded_path = self.test_dir / excluded_dir
            excluded_path.mkdir()
            (excluded_path / "test.py").write_text("import os")
        
        # 创建正常文件
        (self.test_dir / "test.py").write_text("import sys")
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        # 应该只找到正常文件，排除目录中的文件应该被忽略
        self.assertEqual(len(files), 1)

    def test_scan_excludes_files(self):
        """测试排除文件"""
        # 创建排除的文件
        (self.test_dir / "package_installer_yulibupt.py").write_text("import os")
        # 创建正常文件
        (self.test_dir / "test.py").write_text("import sys")
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=False)
        # 排除的文件应该不在结果中
        file_names = {f.name for f in files}
        self.assertNotIn("package_installer_yulibupt.py", file_names)
        self.assertIn("test.py", file_names)

    def test_scan_nonexistent_path(self):
        """测试不存在的路径"""
        files = scan_python_files("/nonexistent/path/12345")
        self.assertEqual(len(files), 0)

    def test_scan_file_instead_of_dir(self):
        """测试文件而不是目录"""
        test_file = self.test_dir / "test.py"
        test_file.write_text("import os")
        
        files = scan_python_files(str(test_file))
        self.assertEqual(len(files), 0)

    def test_read_file_safely_basic(self):
        """测试基本文件读取"""
        test_file = self.test_dir / "test.py"
        content = "import os\nimport sys"
        test_file.write_text(content, encoding='utf-8')
        
        result = read_file_safely(test_file)
        self.assertEqual(result, content)

    def test_read_file_safely_nonexistent(self):
        """测试读取不存在的文件"""
        result = read_file_safely(Path("/nonexistent/file.py"))
        self.assertEqual(result, "")

    def test_read_file_safely_encoding(self):
        """测试不同编码的文件读取"""
        test_file = self.test_dir / "test_gbk.py"
        content = "import os"
        # 尝试写入GBK编码（如果系统支持）
        try:
            test_file.write_text(content, encoding='gbk')
            result = read_file_safely(test_file)
            self.assertEqual(result, content)
        except (UnicodeEncodeError, LookupError):
            # 如果系统不支持GBK，跳过测试
            self.skipTest("系统不支持GBK编码")


if __name__ == '__main__':
    unittest.main()

