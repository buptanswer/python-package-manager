"""
测试包追踪器功能
"""
import unittest
from pathlib import Path
from package_installer_yulibupt import (
    PackageTracker,
    ImportInfo,
    STDLIB
)


class TestPackageTracker(unittest.TestCase):
    """测试包追踪器功能"""

    def setUp(self):
        """设置测试环境"""
        self.tracker = PackageTracker()
        self.test_file = Path("test.py")

    def test_add_import(self):
        """测试添加导入"""
        import_info = ImportInfo(
            package_name="requests",
            import_type="import",
            import_statement="import requests",
            line_number=1,
            file_path=self.test_file,
            pip_package="requests"
        )
        self.tracker.add_import(import_info)
        
        self.assertIn("requests", self.tracker.all_packages)
        self.assertIn("requests", self.tracker.package_imports)
        self.assertIn(self.test_file, self.tracker.file_imports)

    def test_get_third_party_packages(self):
        """测试获取第三方包"""
        # 添加标准库
        stdlib_import = ImportInfo(
            package_name="os",
            import_type="import",
            import_statement="import os",
            line_number=1,
            file_path=self.test_file,
            pip_package="os"
        )
        self.tracker.add_import(stdlib_import)
        
        # 添加第三方包
        third_party_import = ImportInfo(
            package_name="requests",
            import_type="import",
            import_statement="import requests",
            line_number=2,
            file_path=self.test_file,
            pip_package="requests"
        )
        self.tracker.add_import(third_party_import)
        
        third_party = self.tracker.get_third_party_packages()
        self.assertIn("requests", third_party)
        self.assertNotIn("os", third_party)

    def test_get_package_stats(self):
        """测试获取包统计"""
        # 添加多个导入
        for i in range(3):
            import_info = ImportInfo(
                package_name="requests",
                import_type="import",
                import_statement="import requests",
                line_number=i+1,
                file_path=self.test_file,
                pip_package="requests"
            )
            self.tracker.add_import(import_info)
        
        stats = self.tracker.get_package_stats()
        self.assertIn("requests", stats)
        self.assertEqual(stats["requests"]["imports_count"], 3)
        self.assertEqual(stats["requests"]["files_count"], 1)

    def test_get_package_stats_empty(self):
        """测试空包统计"""
        stats = self.tracker.get_package_stats()
        self.assertEqual(stats, {})

    def test_multiple_files(self):
        """测试多个文件的导入"""
        file1 = Path("file1.py")
        file2 = Path("file2.py")
        
        import1 = ImportInfo(
            package_name="requests",
            import_type="import",
            import_statement="import requests",
            line_number=1,
            file_path=file1,
            pip_package="requests"
        )
        import2 = ImportInfo(
            package_name="requests",
            import_type="import",
            import_statement="import requests",
            line_number=1,
            file_path=file2,
            pip_package="requests"
        )
        
        self.tracker.add_import(import1)
        self.tracker.add_import(import2)
        
        stats = self.tracker.get_package_stats()
        self.assertEqual(stats["requests"]["files_count"], 2)
        self.assertEqual(stats["requests"]["imports_count"], 2)


if __name__ == '__main__':
    unittest.main()

