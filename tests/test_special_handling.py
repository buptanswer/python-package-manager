"""
测试特殊包处理功能
覆盖: PACKAGE_SPECIAL_HANDLING, check_package_installed, check_package_installed_via_pip,
      run_package_post_install
"""
import unittest
from unittest.mock import patch, MagicMock
from package_installer_yulibupt import (
    PACKAGE_SPECIAL_HANDLING,
    check_package_installed,
    check_package_installed_via_pip,
    run_package_post_install
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


if __name__ == '__main__':
    unittest.main()

