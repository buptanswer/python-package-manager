"""
测试requirements.txt生成功能
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from package_installer_yulibupt import (
    PackageTracker,
    ImportInfo,
    generate_enhanced_requirements,
    backup_existing_requirements
)


class TestRequirementsGeneration(unittest.TestCase):
    """测试requirements.txt生成功能"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)
        self.requirements_file = self.test_dir / "requirements.txt"
        self.tracker = PackageTracker()
        self.test_file = Path("test.py")

    def test_generate_enhanced_requirements_basic(self):
        """测试基本requirements生成"""
        # 添加导入
        import_info = ImportInfo(
            package_name="requests",
            import_type="import",
            import_statement="import requests",
            line_number=1,
            file_path=self.test_file,
            pip_package="requests"
        )
        self.tracker.add_import(import_info)
        
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        self.assertIn("requests", result)
        self.assertTrue(self.requirements_file.exists())
        
        # 检查文件内容
        content = self.requirements_file.read_text(encoding='utf-8')
        self.assertIn("requests", content)
        self.assertIn("test_project", content)

    def test_backup_existing_requirements(self):
        """测试备份现有requirements"""
        # 创建现有文件
        self.requirements_file.write_text("old content", encoding='utf-8')
        
        backup_existing_requirements(str(self.requirements_file))
        
        # 检查备份文件是否存在
        backup_files = list(self.requirements_file.parent.glob("requirements.txt.backup_*"))
        self.assertGreater(len(backup_files), 0)


    def test_generate_with_package_mapping(self):
        """测试包名映射"""
        # 添加需要映射的包
        import_info = ImportInfo(
            package_name="PIL",
            import_type="import",
            import_statement="import PIL",
            line_number=1,
            file_path=self.test_file,
            pip_package="pillow"
        )
        self.tracker.add_import(import_info)
        
        result = generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project"
        )
        
        # 应该使用映射后的包名
        self.assertIn("pillow", result.values())


if __name__ == '__main__':
    unittest.main()
