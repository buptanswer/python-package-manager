"""
测试本地模块检测和处理功能
覆盖: check_local_module_exists, 本地模块在安装流程中的处理,
     本地模块在requirements.txt中的处理, 参数验证
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from package_installer_yulibupt import (
    PackageTracker,
    ImportInfo,
    check_local_module_exists,
    generate_enhanced_requirements,
    enhanced_process_installation,
    scan_python_files,
    read_file_safely,
    extract_imports_with_details,
    check_package_installed,
    check_package_installed_via_pip,
    diagnose_import_failure,
    get_installed_package_info,
    install_package
)


class TestLocalModuleInRequirements(unittest.TestCase):
    """测试本地模块在requirements.txt中的处理"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)
        self.requirements_file = self.test_dir / "requirements.txt"
        self.tracker = PackageTracker()

    def _add_import(self, package_name, pip_package=None, file_path=None, line_number=1):
        """辅助方法：添加导入到追踪器"""
        if pip_package is None:
            pip_package = package_name
        if file_path is None:
            file_path = self.test_dir / "test.py"
        import_info = ImportInfo(
            package_name=package_name,
            import_type="import",
            import_statement=f"import {package_name}",
            line_number=line_number,
            file_path=file_path,
            pip_package=pip_package
        )
        self.tracker.add_import(import_info)

    def test_local_modules_in_separate_section(self):
        """测试本地模块出现在单独的LOCAL MODULES部分"""
        # 添加第三方包和本地模块
        self._add_import("requests")
        self._add_import("LocalModule")
        
        # 生成requirements，标记LocalModule为本地模块
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project",
            failed_packages=set(),
            failed_pip_packages=set(),
            local_packages={"LocalModule"}
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        
        # 应该包含第三方包
        self.assertIn("requests", content)
        
        # 应该包含LOCAL MODULES部分
        self.assertIn("LOCAL MODULES", content)
        self.assertIn("LocalModule", content)
        self.assertIn("Local module", content)
        
        # 本地模块不应该出现在实际的包列表中（作为pip包）
        # 检查DETAILED PACKAGE INFORMATION部分（实际的包列表）
        if "DETAILED PACKAGE INFORMATION" in content:
            package_section = content.split("DETAILED PACKAGE INFORMATION")[1].split("FILE USAGE STATISTICS")[0]
            # LocalModule不应该作为独立的包行出现（不是注释）
            lines = package_section.split('\n')
            package_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
            self.assertNotIn("LocalModule", package_lines)

    def test_local_modules_excluded_from_package_list(self):
        """测试本地模块不包含在实际的包列表中"""
        self._add_import("requests")
        self._add_import("LocalModule")
        
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project",
            failed_packages=set(),
            failed_pip_packages=set(),
            local_packages={"LocalModule"}
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        
        # 找到包列表部分（在LOCAL MODULES之前）
        if "LOCAL MODULES" in content:
            package_section = content.split("LOCAL MODULES")[0]
        else:
            package_section = content
        
        # LocalModule不应该在包列表中（作为pip包）
        # 检查是否作为独立的包行出现（不是注释）
        lines = package_section.split('\n')
        package_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        self.assertNotIn("LocalModule", package_lines)

    def test_local_and_failed_packages_separated(self):
        """测试本地模块和安装失败的包分开处理"""
        self._add_import("requests")
        self._add_import("LocalModule")
        self._add_import("FailedPackage")
        
        generate_enhanced_requirements(
            self.tracker,
            str(self.requirements_file),
            "test_project",
            failed_packages={"FailedPackage"},
            failed_pip_packages=set(),
            local_packages={"LocalModule"}
        )
        
        content = self.requirements_file.read_text(encoding='utf-8')
        
        # 应该有LOCAL MODULES部分
        self.assertIn("LOCAL MODULES", content)
        self.assertIn("LocalModule", content)
        
        # 应该有INSTALLATION FAILED部分
        self.assertIn("INSTALLATION FAILED", content)
        self.assertIn("FailedPackage", content)
        
        # 两个部分应该分开
        local_section_start = content.find("LOCAL MODULES")
        failed_section_start = content.find("INSTALLATION FAILED")
        self.assertLess(local_section_start, failed_section_start)


class TestLocalModuleInWorkflow(unittest.TestCase):
    """测试本地模块在完整工作流程中的处理"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_local_module_detected_in_scan(self):
        """测试扫描时检测到本地模块"""
        # 创建本地模块文件
        local_module = self.test_dir / "LocalModule.py"
        local_module.write_text("# local module", encoding='utf-8')
        
        # 创建使用本地模块的文件
        main_file = self.test_dir / "main.py"
        main_file.write_text("import LocalModule\nimport requests", encoding='utf-8')
        
        # 扫描文件
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        self.assertEqual(len(files), 2)  # main.py 和 LocalModule.py
        
        # 提取导入
        tracker = PackageTracker()
        for py_file in files:
            if py_file.name == "main.py":  # 只处理main.py
                content = read_file_safely(py_file)
                imports = extract_imports_with_details(content, py_file)
                for import_info in imports:
                    tracker.add_import(import_info)
        
        # 验证
        all_packages = tracker.all_packages
        self.assertIn("LocalModule", all_packages)
        self.assertIn("requests", all_packages)
        
        # 检查本地模块是否存在
        search_paths = [self.test_dir]
        local_path = check_local_module_exists("LocalModule", [Path(p) for p in search_paths])
        self.assertIsNotNone(local_path)
        self.assertEqual(local_path, local_module)

    def test_local_module_package_directory(self):
        """测试包目录形式的本地模块"""
        # 创建包目录
        pkg_dir = self.test_dir / "MyPackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("# package", encoding='utf-8')
        
        # 创建使用该包的文件
        main_file = self.test_dir / "main.py"
        main_file.write_text("import MyPackage\nimport requests", encoding='utf-8')
        
        # 检查本地模块
        local_path = check_local_module_exists("MyPackage", [self.test_dir])
        self.assertIsNotNone(local_path)
        self.assertEqual(local_path, pkg_dir)

    def test_mixed_local_and_third_party(self):
        """测试本地模块和第三方包混合的场景"""
        # 创建本地模块
        local_module = self.test_dir / "Utils.py"
        local_module.write_text("# utils", encoding='utf-8')
        
        # 创建使用两者的文件
        main_file = self.test_dir / "app.py"
        main_file.write_text(
            "import Utils\nimport requests\nfrom bs4 import BeautifulSoup",
            encoding='utf-8'
        )
        
        # 完整流程
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        tracker = PackageTracker()
        for py_file in files:
            if py_file.name == "app.py":
                content = read_file_safely(py_file)
                imports = extract_imports_with_details(content, py_file)
                for import_info in imports:
                    tracker.add_import(import_info)
        
        # 验证
        third_party = tracker.get_third_party_packages()
        self.assertIn("requests", third_party)
        self.assertIn("bs4", third_party)
        self.assertIn("Utils", third_party)  # Utils也会被识别为第三方包（需要后续过滤）
        
        # 检查本地模块
        local_path = check_local_module_exists("Utils", [self.test_dir])
        self.assertIsNotNone(local_path)


class TestParameterValidation(unittest.TestCase):
    """测试参数验证功能"""

    def test_check_package_installed_empty_string(self):
        """测试check_package_installed处理空字符串"""
        self.assertFalse(check_package_installed(""))
        self.assertFalse(check_package_installed("   "))

    def test_check_package_installed_via_pip_empty_string(self):
        """测试check_package_installed_via_pip处理空字符串"""
        self.assertFalse(check_package_installed_via_pip(""))
        self.assertFalse(check_package_installed_via_pip("   "))

    def test_check_local_module_exists_empty_string(self):
        """测试check_local_module_exists处理空字符串"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_local_module_exists("", [Path(tmpdir)])
            self.assertIsNone(result)
            
            result = check_local_module_exists("   ", [Path(tmpdir)])
            self.assertIsNone(result)

    def test_diagnose_import_failure_empty_string(self):
        """测试diagnose_import_failure处理空字符串"""
        msg, actual = diagnose_import_failure("", "somepackage")
        self.assertIn("不能为空", msg)
        
        msg, actual = diagnose_import_failure("module", "")
        self.assertIn("无效", msg)

    def test_get_installed_package_info_empty_string(self):
        """测试get_installed_package_info处理空字符串"""
        result = get_installed_package_info("")
        self.assertIsNone(result)

    def test_install_package_empty_string(self):
        """测试install_package处理空字符串（只测试参数验证，不实际安装）"""
        # 测试空模块名
        success, msg, actual = install_package("", "somepackage")
        self.assertFalse(success)
        self.assertIn("不能为空", msg)
        self.assertIsNone(actual)
        
        # 测试空pip包名
        success, msg, actual = install_package("module", "")
        self.assertFalse(success)
        self.assertIn("不能为空", msg)
        self.assertIsNone(actual)
        
        # 测试空白字符串
        success, msg, actual = install_package("   ", "somepackage")
        self.assertFalse(success)
        self.assertIn("不能为空", msg)


class TestLocalModuleEdgeCases(unittest.TestCase):
    """测试本地模块的边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_local_module_with_special_characters_in_name(self):
        """测试本地模块名包含特殊字符（虽然Python不允许，但防御性测试）"""
        # Python模块名不能包含特殊字符，但测试防御性
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_local_module_exists("module-name", [Path(tmpdir)])
            # 应该返回None，因为Python模块名不能包含连字符
            # 但函数应该不会崩溃
            self.assertIsInstance(result, (type(None), Path))

    def test_local_module_in_nested_directory(self):
        """测试嵌套目录中的本地模块"""
        # 创建嵌套结构
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        local_module = subdir / "NestedModule.py"
        local_module.write_text("# nested", encoding='utf-8')
        
        # 搜索应该能找到（如果搜索路径包含subdir）
        result = check_local_module_exists("NestedModule", [subdir])
        self.assertIsNotNone(result)
        
        # 如果只搜索父目录，应该找不到
        result = check_local_module_exists("NestedModule", [self.test_dir])
        self.assertIsNone(result)

    def test_multiple_local_modules_same_name_different_paths(self):
        """测试不同路径中有同名本地模块"""
        # 创建两个目录，都有同名模块
        dir1 = self.test_dir / "dir1"
        dir2 = self.test_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        module1 = dir1 / "Common.py"
        module2 = dir2 / "Common.py"
        module1.write_text("# module 1", encoding='utf-8')
        module2.write_text("# module 2", encoding='utf-8')
        
        # 搜索应该找到第一个（按搜索顺序）
        result = check_local_module_exists("Common", [dir1, dir2])
        self.assertIsNotNone(result)
        self.assertEqual(result, module1)


class TestLocalModuleIntegration(unittest.TestCase):
    """测试本地模块的集成场景"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_full_workflow_with_local_module(self):
        """测试包含本地模块的完整工作流程"""
        # 创建本地模块
        utils_file = self.test_dir / "utils.py"
        utils_file.write_text("# utility functions", encoding='utf-8')
        
        # 创建主文件
        main_file = self.test_dir / "main.py"
        main_file.write_text(
            "import utils\nimport requests\nimport os",
            encoding='utf-8'
        )
        
        # 扫描
        files = scan_python_files(str(self.test_dir), scan_subdirs=True)
        tracker = PackageTracker()
        for py_file in files:
            content = read_file_safely(py_file)
            imports = extract_imports_with_details(content, py_file)
            for import_info in imports:
                tracker.add_import(import_info)
        
        # 验证包被检测到
        all_packages = tracker.all_packages
        self.assertIn("utils", all_packages)
        self.assertIn("requests", all_packages)
        
        # 检查本地模块
        local_path = check_local_module_exists("utils", [self.test_dir])
        self.assertIsNotNone(local_path)
        
        # 生成requirements（模拟本地模块被识别）
        req_file = self.test_dir / "requirements.txt"
        generate_enhanced_requirements(
            tracker,
            str(req_file),
            "test_project",
            failed_packages=set(),
            failed_pip_packages=set(),
            local_packages={"utils"}
        )
        
        content = req_file.read_text(encoding='utf-8')
        
        # 应该包含第三方包
        self.assertIn("requests", content)
        
        # 应该包含本地模块部分
        self.assertIn("LOCAL MODULES", content)
        self.assertIn("utils", content)
        
        # 标准库不应该在requirements中
        self.assertNotIn("os", content.split("LOCAL MODULES")[0] if "LOCAL MODULES" in content else content)


if __name__ == '__main__':
    unittest.main()

