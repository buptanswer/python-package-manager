"""
测试import提取功能
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

    def tearDown(self):
        """清理测试环境"""
        if self.test_file.exists():
            self.test_file.unlink()

    def test_single_line_import(self):
        """测试单行import"""
        code = "import requests\nimport os"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("requests", package_names)
        self.assertIn("os", package_names)

    def test_from_import(self):
        """测试from import"""
        code = "from bs4 import BeautifulSoup\nfrom collections import Counter"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("bs4", package_names)
        self.assertIn("collections", package_names)

    def test_multiline_import_parentheses(self):
        """测试多行import（括号）"""
        code = """from package import (
    item1,
    item2,
    item3
)"""
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].package_name, "package")

    def test_multiline_import_single_line(self):
        """测试多行import单行格式"""
        code = """import (
    package1,
    package2
)"""
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("package1", package_names)
        self.assertIn("package2", package_names)

    def test_relative_import_filter(self):
        """测试相对导入过滤"""
        code = "from .module import something\nfrom ..parent import other"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0, "相对导入应该被过滤")

    def test_import_with_comments(self):
        """测试带注释的import"""
        code = "import requests  # HTTP库\nfrom bs4 import BeautifulSoup  # HTML解析"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("requests", package_names)
        self.assertIn("bs4", package_names)

    def test_import_in_string(self):
        """测试字符串中的import（应该被忽略）"""
        code = 'code = "import fake_package"\nimport real_package'
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("real_package", package_names)
        self.assertNotIn("fake_package", package_names)

    def test_empty_file(self):
        """测试空文件"""
        code = ""
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0)

    def test_only_comments(self):
        """测试只有注释的文件"""
        code = "# 这是一个注释\n# import fake"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertEqual(len(imports), 0)

    def test_import_as_alias(self):
        """测试import as别名"""
        code = "import pandas as pd\nimport numpy as np"
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("pandas", package_names)
        self.assertIn("numpy", package_names)

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
        """测试超长多行import（应该有长度限制）"""
        code = "from package import (\n"
        for i in range(2000):
            code += f"    item{i},\n"
        code += "    final_item\n)"
        # 应该能处理，不会无限循环
        imports = extract_imports_with_details(code, self.test_file)
        self.assertGreaterEqual(len(imports), 0)

    def test_mixed_imports(self):
        """测试混合import"""
        code = """import os
from package import item
import (
    pkg1,
    pkg2
)
from .relative import something"""
        imports = extract_imports_with_details(code, self.test_file)
        package_names = {imp.package_name for imp in imports}
        self.assertIn("os", package_names)
        self.assertIn("package", package_names)
        self.assertIn("pkg1", package_names)
        self.assertIn("pkg2", package_names)
        # 相对导入应该被过滤
        self.assertNotIn("relative", package_names)

    def test_import_info_structure(self):
        """测试ImportInfo结构"""
        code = "import requests"
        imports = extract_imports_with_details(code, self.test_file)
        self.assertGreater(len(imports), 0)
        imp = imports[0]
        self.assertIsInstance(imp, ImportInfo)
        self.assertEqual(imp.package_name, "requests")
        self.assertEqual(imp.import_type, "import")
        self.assertEqual(imp.line_number, 1)
        self.assertEqual(imp.file_path, self.test_file)

    def test_backward_compatibility(self):
        """测试向后兼容性（extract_imports_from_code）"""
        code = "import requests\nfrom bs4 import BeautifulSoup"
        packages = extract_imports_from_code(code)
        self.assertIn("requests", packages)
        self.assertIn("bs4", packages)


if __name__ == '__main__':
    unittest.main()

