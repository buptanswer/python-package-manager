"""
集成测试
覆盖: 完整工作流程、复杂场景
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from package_installer_yulibupt import (
    scan_python_files,
    read_file_safely,
    extract_imports_with_details,
    PackageTracker,
    generate_enhanced_requirements,
    get_pip_package_name,
    PACKAGE_MAPPING,
    STDLIB
)


class TestFullWorkflow(unittest.TestCase):
    """测试完整工作流程"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_basic_workflow(self):
        """测试基本工作流程"""
        # 1. 创建测试项目
        (self.test_dir / "main.py").write_text(
            "import requests\nfrom bs4 import BeautifulSoup",
            encoding='utf-8'
        )
        
        # 2. 扫描文件
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 1)
        
        # 3. 提取导入
        tracker = PackageTracker()
        for py_file in files:
            content = read_file_safely(py_file)
            imports = extract_imports_with_details(content, py_file)
            for import_info in imports:
                tracker.add_import(import_info)
        
        # 4. 验证结果
        third_party = tracker.get_third_party_packages()
        self.assertIn("requests", third_party)
        self.assertIn("bs4", third_party)

    def test_multifile_project(self):
        """测试多文件项目"""
        # 创建项目结构
        (self.test_dir / "main.py").write_text(
            "import requests\nimport json",
            encoding='utf-8'
        )
        (self.test_dir / "utils.py").write_text(
            "import pandas as pd\nimport os",
            encoding='utf-8'
        )
        subdir = self.test_dir / "lib"
        subdir.mkdir()
        (subdir / "helper.py").write_text(
            "from PIL import Image\nimport numpy as np",
            encoding='utf-8'
        )
        
        # 扫描并分析
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 3)
        
        tracker = PackageTracker()
        for py_file in files:
            content = read_file_safely(py_file)
            imports = extract_imports_with_details(content, py_file)
            for import_info in imports:
                tracker.add_import(import_info)
        
        # 验证
        third_party = tracker.get_third_party_packages()
        self.assertIn("requests", third_party)
        self.assertIn("pandas", third_party)
        self.assertIn("PIL", third_party)
        self.assertIn("numpy", third_party)
        
        # 标准库不应该在第三方包中
        self.assertNotIn("os", third_party)
        self.assertNotIn("json", third_party)

    def test_workflow_with_requirements_generation(self):
        """测试包含requirements生成的工作流程"""
        # 创建项目
        (self.test_dir / "app.py").write_text(
            "import requests\nimport pandas\nfrom bs4 import BeautifulSoup",
            encoding='utf-8'
        )
        
        # 完整流程
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        tracker = PackageTracker()
        for py_file in files:
            content = read_file_safely(py_file)
            imports = extract_imports_with_details(content, py_file)
            for import_info in imports:
                tracker.add_import(import_info)
        
        # 生成requirements
        req_file = self.test_dir / "requirements.txt"
        result = generate_enhanced_requirements(
            tracker,
            str(req_file),
            "test_project"
        )
        
        # 验证
        self.assertTrue(req_file.exists())
        content = req_file.read_text(encoding='utf-8')
        self.assertIn("requests", content)
        self.assertIn("pandas", content)
        self.assertIn("beautifulsoup4", content)  # 映射后的包名


class TestComplexImportScenarios(unittest.TestCase):
    """测试复杂导入场景"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_multiline_imports(self):
        """测试多行导入"""
        code = """from package import (
    item1,
    item2,
    item3
)

import (
    pkg1,
    pkg2,
    pkg3
)"""
        test_file = self.test_dir / "test.py"
        test_file.write_text(code, encoding='utf-8')
        
        content = read_file_safely(test_file)
        imports = extract_imports_with_details(content, test_file)
        
        package_names = {imp.package_name for imp in imports}
        self.assertIn("package", package_names)
        self.assertIn("pkg1", package_names)
        self.assertIn("pkg2", package_names)
        self.assertIn("pkg3", package_names)

    def test_mixed_import_styles(self):
        """测试混合导入风格"""
        code = """import os
import sys
from collections import Counter
import pandas as pd
from bs4 import BeautifulSoup as BS
import numpy, scipy, matplotlib
from .local import something
from ..parent import other"""
        
        test_file = self.test_dir / "test.py"
        test_file.write_text(code, encoding='utf-8')
        
        content = read_file_safely(test_file)
        imports = extract_imports_with_details(content, test_file)
        
        package_names = {imp.package_name for imp in imports}
        
        # 应该包含
        self.assertIn("os", package_names)
        self.assertIn("sys", package_names)
        self.assertIn("collections", package_names)
        self.assertIn("pandas", package_names)
        self.assertIn("bs4", package_names)
        self.assertIn("numpy", package_names)
        self.assertIn("scipy", package_names)
        self.assertIn("matplotlib", package_names)
        
        # 不应该包含相对导入
        self.assertNotIn("local", package_names)
        self.assertNotIn("parent", package_names)

    def test_real_world_file(self):
        """测试真实世界文件"""
        code = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A real world Python module
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from PIL import Image

# Local imports
from .utils import helper
from ..config import settings


def main():
    """Main function"""
    # Some code with string containing import (single line - should be ignored)
    code = "import fake_package"
    pass


if __name__ == "__main__":
    main()
'''
        test_file = self.test_dir / "real_world.py"
        test_file.write_text(code, encoding='utf-8')
        
        content = read_file_safely(test_file)
        imports = extract_imports_with_details(content, test_file)
        
        package_names = {imp.package_name for imp in imports}
        
        # 第三方包
        self.assertIn("requests", package_names)
        self.assertIn("bs4", package_names)
        self.assertIn("pandas", package_names)
        self.assertIn("numpy", package_names)
        self.assertIn("PIL", package_names)
        
        # 标准库
        self.assertIn("os", package_names)
        self.assertIn("sys", package_names)
        self.assertIn("json", package_names)
        
        # 不应该包含相对导入
        self.assertNotIn("utils", package_names)  # 相对导入
        self.assertNotIn("config", package_names)  # 相对导入


class TestPackageMappingIntegration(unittest.TestCase):
    """测试包名映射集成"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_pip_package_in_requirements(self):
        """测试pip包名出现在requirements中"""
        # 使用需要映射的包
        code = """import PIL
import cv2
import sklearn
from bs4 import BeautifulSoup
import yaml"""
        
        test_file = self.test_dir / "app.py"
        test_file.write_text(code, encoding='utf-8')
        
        # 完整流程
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        tracker = PackageTracker()
        for py_file in files:
            content = read_file_safely(py_file)
            imports = extract_imports_with_details(content, py_file)
            for import_info in imports:
                tracker.add_import(import_info)
        
        # 生成requirements
        req_file = self.test_dir / "requirements.txt"
        generate_enhanced_requirements(tracker, str(req_file), "test")
        
        content = req_file.read_text(encoding='utf-8')
        
        # 应该包含映射后的包名
        self.assertIn("pillow", content)
        self.assertIn("opencv-python", content)
        self.assertIn("scikit-learn", content)
        self.assertIn("beautifulsoup4", content)
        self.assertIn("pyyaml", content)


class TestExcludedFilesIntegration(unittest.TestCase):
    """测试排除文件集成"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_excluded_dirs_not_scanned(self):
        """测试排除目录不被扫描"""
        # 创建正常文件
        (self.test_dir / "main.py").write_text("import requests", encoding='utf-8')
        
        # 创建排除目录中的文件
        venv = self.test_dir / "venv"
        venv.mkdir()
        (venv / "lib.py").write_text("import pandas", encoding='utf-8')
        
        pycache = self.test_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "cache.py").write_text("import numpy", encoding='utf-8')
        
        # 扫描
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        
        # 应该只有main.py
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "main.py")

    def test_excluded_files_not_scanned(self):
        """测试排除文件不被扫描"""
        (self.test_dir / "main.py").write_text("import requests", encoding='utf-8')
        (self.test_dir / "test_main.py").write_text("import pytest", encoding='utf-8')
        (self.test_dir / "package_installer_yulibupt.py").write_text("import os", encoding='utf-8')
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        file_names = {f.name for f in files}
        
        self.assertIn("main.py", file_names)
        self.assertNotIn("test_main.py", file_names)
        self.assertNotIn("package_installer_yulibupt.py", file_names)


class TestStatisticsIntegration(unittest.TestCase):
    """测试统计功能集成"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_file_count_accurate(self):
        """测试文件计数准确"""
        # 创建多个使用requests的文件
        for i in range(3):
            (self.test_dir / f"file{i}.py").write_text(
                "import requests",
                encoding='utf-8'
            )
        
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        tracker = PackageTracker()
        for py_file in files:
            content = read_file_safely(py_file)
            imports = extract_imports_with_details(content, py_file)
            for import_info in imports:
                tracker.add_import(import_info)
        
        stats = tracker.get_package_stats()
        self.assertEqual(stats["requests"]["files_count"], 3)

    def test_import_count_accurate(self):
        """测试导入计数准确"""
        code = """import requests
from requests import Session
import requests as req"""
        
        test_file = self.test_dir / "test.py"
        test_file.write_text(code, encoding='utf-8')
        
        tracker = PackageTracker()
        content = read_file_safely(test_file)
        imports = extract_imports_with_details(content, test_file)
        for import_info in imports:
            tracker.add_import(import_info)
        
        stats = tracker.get_package_stats()
        self.assertEqual(stats["requests"]["imports_count"], 3)


if __name__ == '__main__':
    unittest.main()
