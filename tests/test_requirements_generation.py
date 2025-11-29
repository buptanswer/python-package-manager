"""
测试requirements.txt生成功能
覆盖: generate_enhanced_requirements, backup_existing_requirements,
      write_file_header, write_dependency_overview, write_detailed_package_info, write_file_usage_stats
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from package_installer_yulibupt import (
    PackageTracker,
    ImportInfo,
    generate_enhanced_requirements,
    backup_existing_requirements
)


class TestGenerateEnhancedRequirements(unittest.TestCase):
    """测试增强版requirements.txt生成功能"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)
        self.requirements_file = self.test_dir / "requirements.txt"
        self.tracker = PackageTracker()
        self.test_file = Path("test.py")

    def _add_import(self, package_name, pip_package=None, file_path=None, line_number=1):
        """辅助方法：添加导入到追踪器"""
        if pip_package is None:
            pip_package = package_name
        if file_path is None:
            file_path = self.test_file
        import_info = ImportInfo(
            package_name=package_name,
            import_type="import",
            import_statement=f"import {package_name}",
            line_number=line_number,
            file_path=file_path,
            pip_package=pip_package
        )
        self.tracker.add_import(import_info)

    # ==================== 基础生成测试 ====================

    def test_generate_creates_file(self):
        """测试生成文件"""
        self._add_import("requests")
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        self.assertTrue(self.requirements_file.exists())

    def test_generate_returns_dict(self):
        """测试返回字典"""
        self._add_import("requests")
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        self.assertIsInstance(result, dict)

    def test_generate_includes_package(self):
        """测试包含包名"""
        self._add_import("requests")
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        self.assertIn("requests", result)

    def test_generate_multiple_packages(self):
        """测试生成多个包"""
        packages = ["requests", "pandas", "numpy"]
        for pkg in packages:
            self._add_import(pkg)
        
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        for pkg in packages:
            self.assertIn(pkg, result)

    # ==================== 文件内容测试 ====================

    def test_file_contains_project_name(self):
        """测试文件包含项目名"""
        self._add_import("requests")
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "my_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("my_project", content)

    def test_file_contains_timestamp(self):
        """测试文件包含时间戳"""
        self._add_import("requests")
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("Generated:", content)

    def test_file_contains_package_name(self):
        """测试文件包含包名"""
        self._add_import("requests")
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("requests", content)

    def test_file_contains_dependency_overview(self):
        """测试文件包含依赖概览"""
        self._add_import("requests")
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("DEPENDENCY OVERVIEW", content)

    def test_file_contains_detailed_info(self):
        """测试文件包含详细信息"""
        self._add_import("requests")
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("DETAILED PACKAGE INFORMATION", content)

    def test_file_contains_usage_stats(self):
        """测试文件包含使用统计"""
        self._add_import("requests")
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("FILE USAGE STATISTICS", content)

    # ==================== 包名映射测试 ====================

    def test_pip_package_mapping(self):
        """测试pip包名映射"""
        self._add_import("PIL", pip_package="pillow")
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        # 应该使用映射后的pip包名
        self.assertIn("pillow", result.values())

    def test_multiple_modules_same_pip_package(self):
        """测试多个模块映射到同一pip包"""
        self._add_import("win32clipboard", pip_package="pywin32")
        self._add_import("win32con", pip_package="pywin32")
        
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        # requirements.txt中应该只有一个pywin32
        content = self.requirements_file.read_text(encoding='utf-8')
        # 统计非注释行中pywin32出现的次数
        lines = [line for line in content.split('\n') if not line.startswith('#') and line.strip()]
        pywin32_count = sum(1 for line in lines if line.strip() == 'pywin32')
        self.assertEqual(pywin32_count, 1)

    # ==================== 失败包处理测试 ====================

    def test_exclude_failed_packages(self):
        """测试排除失败的包"""
        self._add_import("requests")
        self._add_import("failed_pkg")
        
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project",
            failed_packages={"failed_pkg"},
            failed_pip_packages=set()
        )
        
        self.assertIn("requests", result)
        self.assertNotIn("failed_pkg", result)

    def test_failed_packages_in_comments(self):
        """测试失败包出现在注释中"""
        self._add_import("requests")
        self._add_import("failed_pkg")
        
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project",
            failed_packages={"failed_pkg"},
            failed_pip_packages=set()
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("INSTALLATION FAILED PACKAGES", content)

    # ==================== 统计信息测试 ====================

    def test_file_count_stats(self):
        """测试文件计数统计"""
        file1 = Path("file1.py")
        file2 = Path("file2.py")
        self._add_import("requests", file_path=file1)
        self._add_import("requests", file_path=file2)
        
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        # 应该显示文件统计
        self.assertIn("file(s)", content)

    def test_import_count_stats(self):
        """测试导入计数统计"""
        self._add_import("requests", line_number=1)
        self._add_import("requests", line_number=5)
        self._add_import("requests", line_number=10)
        
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("import(s)", content)


class TestBackupExistingRequirements(unittest.TestCase):
    """测试备份功能"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)
        self.requirements_file = self.test_dir / "requirements.txt"

    def test_backup_creates_file(self):
        """测试创建备份文件"""
        self.requirements_file.write_text("old content", encoding='utf-8')
        backup_existing_requirements(str(self.requirements_file))
        
        backup_files = list(self.requirements_file.parent.glob("requirements.txt.backup_*"))
        self.assertGreater(len(backup_files), 0)

    def test_backup_preserves_content(self):
        """测试备份保留内容"""
        original_content = "original requirements content"
        self.requirements_file.write_text(original_content, encoding='utf-8')
        backup_existing_requirements(str(self.requirements_file))
        
        backup_files = list(self.requirements_file.parent.glob("requirements.txt.backup_*"))
        self.assertGreater(len(backup_files), 0)
        
        backup_content = backup_files[0].read_text(encoding='utf-8')
        self.assertEqual(backup_content, original_content)

    def test_no_backup_for_nonexistent(self):
        """测试不存在的文件不创建备份"""
        backup_existing_requirements(str(self.requirements_file))
        
        backup_files = list(self.requirements_file.parent.glob("requirements.txt.backup_*"))
        self.assertEqual(len(backup_files), 0)

    def test_backup_limit(self):
        """测试备份数量限制"""
        self.requirements_file.write_text("content", encoding='utf-8')
        
        # 创建多个备份
        for i in range(10):
            backup_existing_requirements(str(self.requirements_file), max_backups=3)
        
        backup_files = list(self.requirements_file.parent.glob("requirements.txt.backup_*"))
        self.assertLessEqual(len(backup_files), 3)

    def test_backup_timestamp_format(self):
        """测试备份时间戳格式"""
        self.requirements_file.write_text("content", encoding='utf-8')
        backup_existing_requirements(str(self.requirements_file))
        
        backup_files = list(self.requirements_file.parent.glob("requirements.txt.backup_*"))
        self.assertGreater(len(backup_files), 0)
        
        # 检查时间戳格式
        backup_name = backup_files[0].name
        self.assertRegex(backup_name, r"requirements\.txt\.backup_\d{8}_\d{6}")


class TestEmptyRequirements(unittest.TestCase):
    """测试空requirements情况"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)
        self.requirements_file = self.test_dir / "requirements.txt"
        self.tracker = PackageTracker()

    def test_empty_tracker(self):
        """测试空追踪器"""
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        self.assertEqual(result, {})
        self.assertTrue(self.requirements_file.exists())

    def test_only_stdlib(self):
        """测试只有标准库"""
        import_info = ImportInfo(
            package_name="os",
            import_type="import",
            import_statement="import os",
            line_number=1,
            file_path=Path("test.py"),
            pip_package="os"
        )
        self.tracker.add_import(import_info)
        
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        # 标准库不应该出现在结果中
        self.assertNotIn("os", result)


if __name__ == '__main__':
    unittest.main()
