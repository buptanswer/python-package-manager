"""
测试包追踪器功能
覆盖: PackageTracker类
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

    def _create_import_info(self, package_name, line_number=1, file_path=None, 
                           pip_package=None, import_type="import"):
        """辅助方法：创建ImportInfo对象"""
        if file_path is None:
            file_path = self.test_file
        if pip_package is None:
            pip_package = package_name
        return ImportInfo(
            package_name=package_name,
            import_type=import_type,
            import_statement=f"{import_type} {package_name}",
            line_number=line_number,
            file_path=file_path,
            pip_package=pip_package
        )

    # ==================== add_import测试 ====================

    def test_add_single_import(self):
        """测试添加单个导入"""
        import_info = self._create_import_info("requests")
        self.tracker.add_import(import_info)
        
        self.assertIn("requests", self.tracker.all_packages)
        self.assertIn("requests", self.tracker.package_imports)
        self.assertIn(self.test_file, self.tracker.file_imports)

    def test_add_multiple_imports_same_package(self):
        """测试添加同一包的多个导入"""
        for i in range(3):
            import_info = self._create_import_info("requests", line_number=i+1)
            self.tracker.add_import(import_info)
        
        self.assertEqual(len(self.tracker.package_imports["requests"]), 3)

    def test_add_multiple_imports_different_packages(self):
        """测试添加不同包的导入"""
        packages = ["requests", "pandas", "numpy"]
        for pkg in packages:
            import_info = self._create_import_info(pkg)
            self.tracker.add_import(import_info)
        
        for pkg in packages:
            self.assertIn(pkg, self.tracker.all_packages)

    def test_add_imports_from_multiple_files(self):
        """测试从多个文件添加导入"""
        files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]
        for file in files:
            import_info = self._create_import_info("requests", file_path=file)
            self.tracker.add_import(import_info)
        
        self.assertEqual(len(self.tracker.file_imports), 3)
        self.assertEqual(len(self.tracker.package_imports["requests"]), 3)

    # ==================== get_third_party_packages测试 ====================

    def test_get_third_party_packages_filters_stdlib(self):
        """测试过滤标准库"""
        # 添加标准库
        for stdlib in ["os", "sys", "json", "collections"]:
            import_info = self._create_import_info(stdlib)
            self.tracker.add_import(import_info)
        
        # 添加第三方包
        for third_party in ["requests", "pandas"]:
            import_info = self._create_import_info(third_party)
            self.tracker.add_import(import_info)
        
        third_party = self.tracker.get_third_party_packages()
        self.assertIn("requests", third_party)
        self.assertIn("pandas", third_party)
        self.assertNotIn("os", third_party)
        self.assertNotIn("sys", third_party)

    def test_get_third_party_packages_returns_set(self):
        """测试返回Set类型"""
        import_info = self._create_import_info("requests")
        self.tracker.add_import(import_info)
        
        third_party = self.tracker.get_third_party_packages()
        self.assertIsInstance(third_party, set)

    def test_get_third_party_packages_empty(self):
        """测试空追踪器"""
        third_party = self.tracker.get_third_party_packages()
        self.assertEqual(len(third_party), 0)

    def test_get_third_party_packages_only_stdlib(self):
        """测试只有标准库时"""
        for stdlib in ["os", "sys", "json"]:
            import_info = self._create_import_info(stdlib)
            self.tracker.add_import(import_info)
        
        third_party = self.tracker.get_third_party_packages()
        self.assertEqual(len(third_party), 0)

    # ==================== get_package_stats测试 ====================

    def test_get_package_stats_single_import(self):
        """测试单个导入的统计"""
        import_info = self._create_import_info("requests")
        self.tracker.add_import(import_info)
        
        stats = self.tracker.get_package_stats()
        self.assertIn("requests", stats)
        self.assertEqual(stats["requests"]["imports_count"], 1)
        self.assertEqual(stats["requests"]["files_count"], 1)

    def test_get_package_stats_multiple_imports_same_file(self):
        """测试同一文件多次导入的统计"""
        for i in range(5):
            import_info = self._create_import_info("requests", line_number=i+1)
            self.tracker.add_import(import_info)
        
        stats = self.tracker.get_package_stats()
        self.assertEqual(stats["requests"]["imports_count"], 5)
        self.assertEqual(stats["requests"]["files_count"], 1)

    def test_get_package_stats_multiple_files(self):
        """测试多个文件导入的统计"""
        files = [Path(f"file{i}.py") for i in range(3)]
        for file in files:
            import_info = self._create_import_info("requests", file_path=file)
            self.tracker.add_import(import_info)
        
        stats = self.tracker.get_package_stats()
        self.assertEqual(stats["requests"]["imports_count"], 3)
        self.assertEqual(stats["requests"]["files_count"], 3)

    def test_get_package_stats_pip_package(self):
        """测试pip包名统计"""
        import_info = self._create_import_info("PIL", pip_package="pillow")
        self.tracker.add_import(import_info)
        
        stats = self.tracker.get_package_stats()
        self.assertEqual(stats["PIL"]["pip_package"], "pillow")

    def test_get_package_stats_excludes_stdlib(self):
        """测试统计排除标准库"""
        self.tracker.add_import(self._create_import_info("os"))
        self.tracker.add_import(self._create_import_info("requests"))
        
        stats = self.tracker.get_package_stats()
        self.assertNotIn("os", stats)
        self.assertIn("requests", stats)

    def test_get_package_stats_empty(self):
        """测试空追踪器的统计"""
        stats = self.tracker.get_package_stats()
        self.assertEqual(stats, {})

    # ==================== 数据完整性测试 ====================

    def test_all_packages_consistency(self):
        """测试all_packages与package_imports一致性"""
        packages = ["requests", "pandas", "numpy"]
        for pkg in packages:
            self.tracker.add_import(self._create_import_info(pkg))
        
        self.assertEqual(self.tracker.all_packages, set(packages))
        self.assertEqual(set(self.tracker.package_imports.keys()), set(packages))

    def test_file_imports_consistency(self):
        """测试file_imports数据完整性"""
        file1 = Path("file1.py")
        file2 = Path("file2.py")
        
        self.tracker.add_import(self._create_import_info("requests", file_path=file1))
        self.tracker.add_import(self._create_import_info("pandas", file_path=file1))
        self.tracker.add_import(self._create_import_info("numpy", file_path=file2))
        
        self.assertEqual(len(self.tracker.file_imports[file1]), 2)
        self.assertEqual(len(self.tracker.file_imports[file2]), 1)

    # ==================== 边界情况测试 ====================

    def test_same_import_multiple_times(self):
        """测试重复添加相同导入"""
        for _ in range(3):
            self.tracker.add_import(self._create_import_info("requests", line_number=1))
        
        # 应该都被添加（不去重）
        self.assertEqual(len(self.tracker.package_imports["requests"]), 3)

    def test_package_imports_list_order(self):
        """测试导入顺序保持"""
        for i in range(5):
            self.tracker.add_import(self._create_import_info("requests", line_number=i+1))
        
        line_numbers = [imp.line_number for imp in self.tracker.package_imports["requests"]]
        self.assertEqual(line_numbers, [1, 2, 3, 4, 5])


if __name__ == '__main__':
    unittest.main()
