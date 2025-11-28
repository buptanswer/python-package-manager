"""
集成测试
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from package_installer_yulibupt import (
    scan_python_files,
    read_file_safely,
    extract_imports_with_details,
    PackageTracker
)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_full_workflow(self):
        """测试完整工作流程"""
        # 创建测试项目结构
        (self.test_dir / "main.py").write_text(
            "import requests\nfrom bs4 import BeautifulSoup",
            encoding='utf-8'
        )
        (self.test_dir / "utils.py").write_text(
            "import os\nimport json",
            encoding='utf-8'
        )
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        (subdir / "helper.py").write_text(
            "import pandas as pd",
            encoding='utf-8'
        )
        
        # 扫描文件
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertGreater(len(files), 0)
        
        # 提取导入
        tracker = PackageTracker()
        for py_file in files:
            content = read_file_safely(py_file)
            imports = extract_imports_with_details(content, py_file)
            for import_info in imports:
                tracker.add_import(import_info)
        
        # 检查结果
        third_party = tracker.get_third_party_packages()
        self.assertIn("requests", third_party)
        self.assertIn("bs4", third_party)
        self.assertIn("pandas", third_party)
        # 标准库应该被过滤
        self.assertNotIn("os", third_party)
        self.assertNotIn("json", third_party)

    def test_complex_multiline_imports(self):
        """测试复杂多行import场景"""
        code = """import os
from package import (
    item1,
    item2,
    item3
)
import (
    pkg1,
    pkg2
)
from .relative import something"""
        
        test_file = self.test_dir / "test.py"
        test_file.write_text(code, encoding='utf-8')
        
        content = read_file_safely(test_file)
        imports = extract_imports_with_details(content, test_file)
        
        package_names = {imp.package_name for imp in imports}
        self.assertIn("os", package_names)
        self.assertIn("package", package_names)
        self.assertIn("pkg1", package_names)
        self.assertIn("pkg2", package_names)
        # 相对导入应该被过滤
        self.assertNotIn("relative", package_names)


if __name__ == '__main__':
    unittest.main()

