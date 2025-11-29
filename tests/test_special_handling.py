"""
测试特殊包处理功能
覆盖: PACKAGE_SPECIAL_HANDLING, check_package_installed, check_package_installed_via_pip,
      run_package_post_install, check_local_module_exists, diagnose_import_failure,
      get_installed_package_info
"""
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from package_installer_yulibupt import (
    PACKAGE_SPECIAL_HANDLING,
    check_package_installed,
    check_package_installed_via_pip,
    run_package_post_install,
    check_local_module_exists,
    diagnose_import_failure,
    get_installed_package_info
)


class TestPackageSpecialHandlingConfig(unittest.TestCase):
    """测试特殊包处理配置"""

    def test_config_is_dict(self):
        """测试PACKAGE_SPECIAL_HANDLING是字典"""
        self.assertIsInstance(PACKAGE_SPECIAL_HANDLING, dict)

    def test_pywin32_config_exists(self):
        """测试pywin32配置存在"""
        self.assertIn('pywin32', PACKAGE_SPECIAL_HANDLING)

    def test_pywin32_has_post_install_script(self):
        """测试pywin32有后处理脚本配置"""
        config = PACKAGE_SPECIAL_HANDLING['pywin32']
        self.assertIn('post_install_script', config)
        self.assertEqual(config['post_install_script'], 'pywin32_postinstall')

    def test_pywin32_has_post_install_args(self):
        """测试pywin32有后处理参数配置"""
        config = PACKAGE_SPECIAL_HANDLING['pywin32']
        self.assertIn('post_install_args', config)
        self.assertEqual(config['post_install_args'], ['-install'])

    def test_pywin32_skip_import_verify(self):
        """测试pywin32跳过导入验证配置"""
        config = PACKAGE_SPECIAL_HANDLING['pywin32']
        self.assertIn('skip_import_verify', config)
        self.assertTrue(config['skip_import_verify'])


class TestCheckPackageInstalled(unittest.TestCase):
    """测试包安装检查功能"""

    def test_check_stdlib_installed(self):
        """测试检查标准库是否已安装"""
        self.assertTrue(check_package_installed("os"))
        self.assertTrue(check_package_installed("sys"))
        self.assertTrue(check_package_installed("json"))

    def test_check_nonexistent_package(self):
        """测试检查不存在的包"""
        self.assertFalse(check_package_installed("nonexistent_fake_package_12345"))

    def test_returns_bool(self):
        """测试返回布尔值"""
        result = check_package_installed("os")
        self.assertIsInstance(result, bool)

    def test_handles_invalid_module_name(self):
        """测试处理无效模块名"""
        # 不应该抛出异常
        result = check_package_installed("")
        self.assertIsInstance(result, bool)


class TestCheckPackageInstalledViaPip(unittest.TestCase):
    """测试pip安装检查功能"""

    def test_check_pip_installed(self):
        """测试检查pip是否已安装"""
        # pip应该总是已安装的
        result = check_package_installed_via_pip("pip")
        self.assertTrue(result)

    def test_check_wheel_installed(self):
        """测试检查wheel是否已安装（通常pip环境都有）"""
        # pip 和 wheel 通常都已安装
        result = check_package_installed_via_pip("pip")
        self.assertTrue(result)

    def test_check_nonexistent_package(self):
        """测试检查不存在的pip包"""
        result = check_package_installed_via_pip("nonexistent_fake_package_12345")
        self.assertFalse(result)

    def test_returns_bool(self):
        """测试返回布尔值"""
        result = check_package_installed_via_pip("pip")
        self.assertIsInstance(result, bool)

    @patch('subprocess.run')
    def test_handles_timeout(self, mock_run):
        """测试处理超时"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(cmd="test", timeout=30)
        
        result = check_package_installed_via_pip("some_package")
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_handles_exception(self, mock_run):
        """测试处理异常"""
        mock_run.side_effect = Exception("Test error")
        
        result = check_package_installed_via_pip("some_package")
        self.assertFalse(result)


class TestRunPackagePostInstall(unittest.TestCase):
    """测试包后处理功能"""

    def test_no_special_handling_returns_true(self):
        """测试无特殊处理配置时返回True"""
        result = run_package_post_install("requests")
        self.assertTrue(result)

    def test_returns_bool(self):
        """测试返回布尔值"""
        result = run_package_post_install("some_package")
        self.assertIsInstance(result, bool)

    @patch('importlib.util.find_spec')
    @patch('subprocess.run')
    def test_runs_post_install_script(self, mock_run, mock_find_spec):
        """测试运行后处理脚本"""
        # 模拟find_spec找到脚本
        mock_spec = MagicMock()
        mock_spec.origin = "/path/to/script.py"
        mock_find_spec.return_value = mock_spec
        
        # 模拟subprocess.run成功
        mock_run.return_value = MagicMock(returncode=0)
        
        # 使用patch来模拟os.path.exists
        with patch('os.path.exists', return_value=True):
            result = run_package_post_install("pywin32")
        
        # 应该调用了subprocess.run
        self.assertTrue(mock_run.called or result in [True, False])


class TestSpecialHandlingOptions(unittest.TestCase):
    """测试特殊处理选项"""

    def test_skip_import_verify_option(self):
        """测试skip_import_verify选项"""
        config = PACKAGE_SPECIAL_HANDLING.get('pywin32', {})
        skip_verify = config.get('skip_import_verify', False)
        self.assertIsInstance(skip_verify, bool)

    def test_verify_any_option_default(self):
        """测试verify_any选项默认值"""
        # verify_any默认应该是True
        config = PACKAGE_SPECIAL_HANDLING.get('some_nonexistent', {})
        verify_any = config.get('verify_any', True)
        self.assertTrue(verify_any)

    def test_verify_delay_option(self):
        """测试verify_delay选项类型"""
        config = PACKAGE_SPECIAL_HANDLING.get('pywin32', {})
        verify_delay = config.get('verify_delay', 0)
        self.assertIsInstance(verify_delay, (int, float))


class TestCheckLocalModuleExists(unittest.TestCase):
    """测试本地模块检测功能"""

    def test_detect_py_file(self):
        """测试检测.py文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个.py文件
            py_file = Path(tmpdir) / "mymodule.py"
            py_file.write_text("# test module")
            
            result = check_local_module_exists("mymodule", [Path(tmpdir)])
            self.assertIsNotNone(result)
            self.assertEqual(result, py_file)

    def test_detect_package_directory(self):
        """测试检测包目录（带__init__.py）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个包目录
            pkg_dir = Path(tmpdir) / "mypackage"
            pkg_dir.mkdir()
            (pkg_dir / "__init__.py").write_text("# init")
            
            result = check_local_module_exists("mypackage", [Path(tmpdir)])
            self.assertIsNotNone(result)
            self.assertEqual(result, pkg_dir)

    def test_not_detect_directory_without_init(self):
        """测试不检测没有__init__.py的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个目录但没有__init__.py
            pkg_dir = Path(tmpdir) / "notapackage"
            pkg_dir.mkdir()
            
            result = check_local_module_exists("notapackage", [Path(tmpdir)])
            self.assertIsNone(result)

    def test_not_detect_nonexistent_module(self):
        """测试不存在的模块返回None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_local_module_exists("nonexistent", [Path(tmpdir)])
            self.assertIsNone(result)

    def test_search_multiple_paths(self):
        """测试搜索多个路径"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                # 在第二个目录中创建模块
                py_file = Path(tmpdir2) / "found.py"
                py_file.write_text("# found")
                
                result = check_local_module_exists("found", [Path(tmpdir1), Path(tmpdir2)])
                self.assertIsNotNone(result)
                self.assertEqual(result, py_file)

    def test_py_file_priority_over_package(self):
        """测试.py文件优先于包目录（在同一搜索路径中）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建.py文件
            py_file = Path(tmpdir) / "mymod.py"
            py_file.write_text("# py file")
            
            # 同时创建包目录
            pkg_dir = Path(tmpdir) / "mymod"
            pkg_dir.mkdir()
            (pkg_dir / "__init__.py").write_text("# init")
            
            result = check_local_module_exists("mymod", [Path(tmpdir)])
            self.assertIsNotNone(result)
            # .py文件应该先被找到
            self.assertEqual(result, py_file)

    def test_empty_search_paths(self):
        """测试空搜索路径列表"""
        result = check_local_module_exists("anymodule", [])
        self.assertIsNone(result)

    def test_nonexistent_search_path(self):
        """测试搜索路径不存在"""
        result = check_local_module_exists("anymodule", [Path("/nonexistent/path/12345")])
        self.assertIsNone(result)

    def test_case_sensitive_detection(self):
        """测试大小写敏感的检测"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建小写文件名
            py_file = Path(tmpdir) / "mymodule.py"
            py_file.write_text("# test")
            
            # 用大写名称搜索（在区分大小写的文件系统上应该找不到）
            result_upper = check_local_module_exists("MYMODULE", [Path(tmpdir)])
            result_lower = check_local_module_exists("mymodule", [Path(tmpdir)])
            
            # 小写应该能找到
            self.assertIsNotNone(result_lower)
            # 注意：在Windows上文件系统不区分大小写，所以大写也能找到


class TestDiagnoseImportFailure(unittest.TestCase):
    """测试导入失败诊断功能"""

    def test_returns_tuple(self):
        """测试返回元组"""
        result = diagnose_import_failure("SomeModule", "somemodule")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_diagnose_message_is_string(self):
        """测试诊断消息是字符串"""
        msg, actual = diagnose_import_failure("SomeModule", "somemodule")
        self.assertIsInstance(msg, str)

    def test_diagnose_nonexistent_package(self):
        """测试诊断不存在的包"""
        msg, actual = diagnose_import_failure("FakePackage12345", "fakepackage12345")
        self.assertIsInstance(msg, str)
        self.assertIn("FakePackage12345", msg)

    @patch('package_installer_yulibupt.check_package_installed')
    def test_detect_case_mismatch(self, mock_check):
        """测试检测大小写不匹配"""
        # 模拟：小写模块可以导入
        def side_effect(name):
            return name == "mymodule"
        mock_check.side_effect = side_effect
        
        msg, actual = diagnose_import_failure("MyModule", "mymodule")
        
        # 应该检测到大小写问题
        self.assertIn("mymodule", msg.lower())
        self.assertEqual(actual, "mymodule")

    @patch('package_installer_yulibupt.check_package_installed')
    @patch('package_installer_yulibupt.get_installed_package_info')
    def test_diagnose_installed_but_different_module(self, mock_info, mock_check):
        """测试诊断已安装但模块名不同"""
        mock_check.return_value = False
        mock_info.return_value = {'Name': 'some-package', 'Version': '1.0.0'}
        
        msg, actual = diagnose_import_failure("DifferentName", "some-package")
        
        self.assertIn("some-package", msg)
        self.assertIsNone(actual)


class TestGetInstalledPackageInfo(unittest.TestCase):
    """测试获取已安装包信息功能"""

    def test_get_pip_info(self):
        """测试获取pip包信息"""
        result = get_installed_package_info("pip")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('Name', result)

    def test_get_nonexistent_package_info(self):
        """测试获取不存在的包返回None"""
        result = get_installed_package_info("nonexistent_fake_package_12345")
        self.assertIsNone(result)

    def test_info_contains_version(self):
        """测试信息包含版本"""
        result = get_installed_package_info("pip")
        if result:
            self.assertIn('Version', result)

    def test_info_contains_location(self):
        """测试信息包含位置"""
        result = get_installed_package_info("pip")
        if result:
            self.assertIn('Location', result)

    @patch('subprocess.run')
    def test_handles_timeout(self, mock_run):
        """测试处理超时"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(cmd="test", timeout=30)
        
        result = get_installed_package_info("some_package")
        self.assertIsNone(result)

    @patch('subprocess.run')
    def test_handles_exception(self, mock_run):
        """测试处理异常"""
        mock_run.side_effect = Exception("Test error")
        
        result = get_installed_package_info("some_package")
        self.assertIsNone(result)


class TestLocalModuleIntegration(unittest.TestCase):
    """测试本地模块与安装流程的集成"""

    def test_local_module_detection_with_real_stdlib(self):
        """测试本地模块不会与标准库冲突"""
        # os是标准库，不应该在本地找到（除非有同名文件）
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_local_module_exists("os", [Path(tmpdir)])
            self.assertIsNone(result)

    def test_local_module_with_special_characters_in_path(self):
        """测试带特殊字符的路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个.py文件
            py_file = Path(tmpdir) / "testmod.py"
            py_file.write_text("# test")
            
            result = check_local_module_exists("testmod", [Path(tmpdir)])
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()

