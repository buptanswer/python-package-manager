"""
测试import提取功能
覆盖: extract_imports_with_details, extract_imports_from_code
"""
import unittest
from pathlib import Path
from package_installer_yulibupt import (
    extract_imports_with_details,
    extract_imports_from_code,
    ImportInfo
)


class TestImportExtraction(unittest.TestCase):
    """测试import提取功能"""

    def setUp(self):
        """设置测试环境"""
        self.test_file = Path("test_temp.py")

    # ==================== 基础导入测试 ====================
    
    def test_single_import(self):
        """测试单个import语句"""
        code = "import requests"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "requests")
        self.assertEqual(imports[0].import_type, "import")

    def test_multiple_imports(self):
        """测试多个import语句"""
        code = "import requests\nimport os\nimport json"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertEqual(len(imports), 3)
        self.assertIn("requests", package_names)
        self.assertIn("os", package_names)
        self.assertIn("json", package_names)

    def test_from_import(self):
        """测试from import语句"""
        code = "from bs4 import BeautifulSoup"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "bs4")
        self.assertEqual(imports[0].import_type, "from_import")

    def test_from_import_multiple_items(self):
        """测试from import多个项目"""
        code = "from collections import Counter, OrderedDict, defaultdict"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "collections")

    def test_import_as_alias(self):
        """测试import as别名"""
        code = "import pandas as pd\nimport numpy as np"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("pandas", package_names)
        self.assertIn("numpy", package_names)

    def test_from_import_as_alias(self):
        """测试from import as别名"""
        code = "from PIL import Image as img"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "PIL")

    def test_comma_separated_imports(self):
        """测试逗号分隔的import"""
        code = "import os, sys, json"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("os", package_names)
        self.assertIn("sys", package_names)
        self.assertIn("json", package_names)

    # ==================== 多行导入测试 ====================

    def test_multiline_from_import_parentheses(self):
        """测试多行from import（括号）"""
        code = """from package import (
    item1,
    item2,
    item3
)"""
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "package")

    def test_multiline_import_parentheses(self):
        """测试多行import（括号）"""
        code = """import (
    package1,
    package2,
    package3
)"""
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("package1", package_names)
        self.assertIn("package2", package_names)
        self.assertIn("package3", package_names)

    def test_nested_parentheses(self):
        """测试嵌套括号"""
        code = """from package import (
    item1,
    (item2, item3),
    item4
)"""
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "package")

    def test_unclosed_parentheses(self):
        """测试未闭合的括号（应该能处理，不会无限循环）"""
        code = """from package import (
    item1,
    item2
    # 缺少闭合括号"""
        # 应该能处理，不会抛出异常或无限循环
        imports = extract_imports_with_details(code, self.test_file)
        # 至少应该能提取到包名
        self.assertGreaterEqual(len(imports), 0)

    def test_very_long_multiline_import(self):
        """测试超长多行import（应该有1000行安全限制）"""
        code = "from package import (\n"
        for i in range(1500):  # 超过1000行限制
            code += f"    item{i},\n"
        code += "    final_item\n)"
        # 应该能处理，不会无限循环
        imports = extract_imports_with_details(code, self.test_file)
        self.assertGreaterEqual(len(imports), 0)

    # ==================== 相对导入测试 ====================

    def test_relative_import_single_dot(self):
        """测试单点相对导入"""
        code = "from .module import something"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0, "单点相对导入应该被过滤")

    def test_relative_import_double_dot(self):
        """测试双点相对导入"""
        code = "from ..parent import other"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0, "双点相对导入应该被过滤")

    def test_relative_import_triple_dot(self):
        """测试三点相对导入"""
        code = "from ...grandparent import something"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0, "三点相对导入应该被过滤")

    def test_mixed_relative_and_absolute(self):
        """测试混合相对和绝对导入"""
        code = """from .local import local_func
from ..parent import parent_func
import requests
from bs4 import BeautifulSoup"""
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("requests", package_names)
        self.assertIn("bs4", package_names)
        self.assertNotIn("local", package_names)
        self.assertNotIn("parent", package_names)

    # ==================== 注释处理测试 ====================

    def test_import_with_inline_comment(self):
        """测试带行内注释的import"""
        code = "import requests  # HTTP库"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "requests")

    def test_commented_out_import(self):
        """测试被注释掉的import"""
        code = "# import fake_package"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0)

    def test_only_comments(self):
        """测试只有注释的文件"""
        code = """# 这是一个注释
# import fake_package
# from fake import something"""
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0)

    # ==================== 字符串处理测试 ====================

    def test_import_in_string_double_quotes(self):
        """测试双引号字符串中的import"""
        code = 'code = "import fake_package"\nimport real_package'
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("real_package", package_names)
        self.assertNotIn("fake_package", package_names)

    def test_import_in_string_single_quotes(self):
        """测试单引号字符串中的import"""
        code = "code = 'import fake_package'\nimport real_package"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("real_package", package_names)

    def test_import_in_docstring(self):
        """测试docstring中的import示例"""
        code = '''"""
示例:
    import example_package
"""
import real_package'''
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("real_package", package_names)

    # ==================== 边界情况测试 ====================

    def test_empty_file(self):
        """测试空文件"""
        code = ""
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0)

    def test_whitespace_only(self):
        """测试只有空白的文件"""
        code = "   \n\n   \t\n"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0)

    def test_empty_package_name(self):
        """测试空包名（不应该发生但应该处理）"""
        # 这是一个畸形的import，不应该产生结果
        code = "from  import something"  # 空包名
        imports = extract_imports_with_details(code, self.test_file)
        # 应该不崩溃
        self.assertIsInstance(imports, list)

    def test_submodule_import(self):
        """测试子模块导入"""
        code = "import urllib.request\nfrom xml.etree import ElementTree"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("urllib", package_names)
        self.assertIn("xml", package_names)

    # ==================== ImportInfo结构测试 ====================

    def test_import_info_structure(self):
        """测试ImportInfo结构完整性"""
        code = "import requests"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        imp = imports[0]
        
        self.assertIsInstance(imp, ImportInfo)
        self.assertEqual(imp.package_name, "requests")
        self.assertEqual(imp.import_type, "import")
        self.assertEqual(imp.import_statement, "import requests")
        self.assertEqual(imp.line_number, 1)
        self.assertEqual(imp.file_path, self.test_file)
        self.assertEqual(imp.pip_package, "requests")

    def test_import_info_line_numbers(self):
        """测试行号正确性"""
        code = """# comment
import os
import sys
import json"""
        imports = extract_imports_with_details(code, self.test_file)
        line_numbers = {imp.line_number for imp in imports}
        self.assertIn(2, line_numbers)
        self.assertIn(3, line_numbers)
        self.assertIn(4, line_numbers)

    def test_import_info_pip_package_mapping(self):
        """测试pip包名映射"""
        code = "import PIL\nimport cv2\nimport sklearn"
        imports = extract_imports_with_details(code, self.test_file)
        pip_packages = {imp.pip_package for imp in imports}
        self.assertIn("pillow", pip_packages)
        self.assertIn("opencv-python", pip_packages)
        self.assertIn("scikit-learn", pip_packages)

    # ==================== 向后兼容性测试 ====================

    def test_backward_compatibility(self):
        """测试向后兼容函数 extract_imports_from_code"""
        code = "import requests\nfrom bs4 import BeautifulSoup"
        packages = extract_imports_from_code(code)
        self.assertIn("requests", packages)
        self.assertIn("bs4", packages)

    def test_backward_compatibility_returns_set(self):
        """测试向后兼容函数返回Set类型"""
        code = "import requests"
        packages = extract_imports_from_code(code)
        self.assertIsInstance(packages, set)

    # ==================== 混合场景测试 ====================

    def test_mixed_imports_complex(self):
        """测试复杂混合import场景"""
        code = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
模块文档
\"\"\"

import os
import sys
from collections import Counter
import pandas as pd
from bs4 import BeautifulSoup as BS
from .local import func  # 相对导入
import (
    pkg1,
    pkg2
)
from package import (
    item1,
    item2,
    item3
)
# import commented

def main():
    code = "import fake"
    pass
"""
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        
        # 应该包含
        self.assertIn("os", package_names)
        self.assertIn("sys", package_names)
        self.assertIn("collections", package_names)
        self.assertIn("pandas", package_names)
        self.assertIn("bs4", package_names)
        self.assertIn("pkg1", package_names)
        self.assertIn("pkg2", package_names)
        self.assertIn("package", package_names)
        
        # 不应该包含
        self.assertNotIn("local", package_names)  # 相对导入
        self.assertNotIn("commented", package_names)  # 注释
        self.assertNotIn("fake", package_names)  # 字符串


if __name__ == '__main__':
    unittest.main()
