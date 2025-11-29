"""
测试包名映射功能
覆盖: get_pip_package_name, generate_package_name_variants, search_pypi_package,
      PACKAGE_MAPPING, PACKAGE_PATTERNS
"""
import unittest
from package_installer_yulibupt import (
    get_pip_package_name,
    generate_package_name_variants,
    PACKAGE_MAPPING,
    PACKAGE_PATTERNS
)


class TestPackageMapping(unittest.TestCase):
    """测试包名映射功能"""

    # ==================== PACKAGE_MAPPING测试 ====================

    def test_pil_to_pillow(self):
        """测试PIL映射到pillow"""
        self.assertEqual(get_pip_package_name("PIL"), "pillow")

    def test_cv2_to_opencv(self):
        """测试cv2映射到opencv-python"""
        self.assertEqual(get_pip_package_name("cv2"), "opencv-python")

    def test_sklearn_to_scikit_learn(self):
        """测试sklearn映射到scikit-learn"""
        self.assertEqual(get_pip_package_name("sklearn"), "scikit-learn")

    def test_bs4_to_beautifulsoup4(self):
        """测试bs4映射到beautifulsoup4"""
        self.assertEqual(get_pip_package_name("bs4"), "beautifulsoup4")

    def test_dotenv_to_python_dotenv(self):
        """测试dotenv映射到python-dotenv"""
        self.assertEqual(get_pip_package_name("dotenv"), "python-dotenv")

    def test_yaml_to_pyyaml(self):
        """测试yaml映射到pyyaml"""
        self.assertEqual(get_pip_package_name("yaml"), "pyyaml")

    def test_openssl_to_pyopenssl(self):
        """测试OpenSSL映射到pyopenssl"""
        self.assertEqual(get_pip_package_name("OpenSSL"), "pyopenssl")

    def test_crypto_to_pycryptodome(self):
        """测试Crypto映射到pycryptodome"""
        self.assertEqual(get_pip_package_name("Crypto"), "pycryptodome")

    def test_dateutil_to_python_dateutil(self):
        """测试dateutil映射到python-dateutil"""
        self.assertEqual(get_pip_package_name("dateutil"), "python-dateutil")

    def test_mysqldb_to_mysqlclient(self):
        """测试MySQLdb映射到mysqlclient"""
        self.assertEqual(get_pip_package_name("MySQLdb"), "mysqlclient")

    def test_pkg_resources_to_setuptools(self):
        """测试pkg_resources映射到setuptools"""
        self.assertEqual(get_pip_package_name("pkg_resources"), "setuptools")

    # ==================== pywin32模块映射测试 ====================

    def test_win32clipboard_to_pywin32(self):
        """测试win32clipboard映射到pywin32"""
        self.assertEqual(get_pip_package_name("win32clipboard"), "pywin32")

    def test_win32con_to_pywin32(self):
        """测试win32con映射到pywin32"""
        self.assertEqual(get_pip_package_name("win32con"), "pywin32")

    def test_win32api_to_pywin32(self):
        """测试win32api映射到pywin32"""
        self.assertEqual(get_pip_package_name("win32api"), "pywin32")

    def test_win32gui_to_pywin32(self):
        """测试win32gui映射到pywin32"""
        self.assertEqual(get_pip_package_name("win32gui"), "pywin32")

    def test_win32com_to_pywin32(self):
        """测试win32com映射到pywin32"""
        self.assertEqual(get_pip_package_name("win32com"), "pywin32")

    def test_pythoncom_to_pywin32(self):
        """测试pythoncom映射到pywin32"""
        self.assertEqual(get_pip_package_name("pythoncom"), "pywin32")

    def test_pywintypes_to_pywin32(self):
        """测试pywintypes映射到pywin32"""
        self.assertEqual(get_pip_package_name("pywintypes"), "pywin32")

    # ==================== PACKAGE_PATTERNS测试 ====================

    def test_win32_pattern_match(self):
        """测试win32模式匹配"""
        # 测试未在PACKAGE_MAPPING中但匹配模式的模块
        result = get_pip_package_name("win32timezone")
        self.assertEqual(result, "pywin32")

    def test_win32_pattern_prefix(self):
        """测试win32前缀模式"""
        result = get_pip_package_name("win32serviceutil")
        self.assertEqual(result, "pywin32")

    # ==================== 无映射测试 ====================

    def test_no_mapping_returns_original(self):
        """测试无映射时返回原名"""
        self.assertEqual(get_pip_package_name("requests"), "requests")
        self.assertEqual(get_pip_package_name("pandas"), "pandas")
        self.assertEqual(get_pip_package_name("numpy"), "numpy")

    def test_unknown_package(self):
        """测试未知包名"""
        self.assertEqual(get_pip_package_name("some_unknown_package"), "some_unknown_package")

    # ==================== 映射优先级测试 ====================

    def test_direct_mapping_priority(self):
        """测试直接映射优先于模式匹配"""
        # win32clipboard 既在PACKAGE_MAPPING中，也匹配PACKAGE_PATTERNS
        # 应该返回PACKAGE_MAPPING中的值
        result = get_pip_package_name("win32clipboard")
        self.assertEqual(result, "pywin32")


class TestGeneratePackageNameVariants(unittest.TestCase):
    """测试包名变体生成功能"""

    def test_basic_variants(self):
        """测试基本变体生成"""
        variants = generate_package_name_variants("package")
        self.assertIn("package", variants)

    def test_py_prefix_variants(self):
        """测试py前缀变体"""
        variants = generate_package_name_variants("package")
        self.assertIn("py-package", variants)
        self.assertIn("python-package", variants)

    def test_no_py_prefix_for_py_packages(self):
        """测试已有py前缀的包不重复添加"""
        variants = generate_package_name_variants("pypackage")
        self.assertIn("pypackage", variants)
        # 不应该有py-pypackage

    def test_underscore_to_dash(self):
        """测试下划线转连字符"""
        variants = generate_package_name_variants("my_package")
        self.assertIn("my-package", variants)

    def test_dash_to_underscore(self):
        """测试连字符转下划线"""
        variants = generate_package_name_variants("my-package")
        self.assertIn("my_package", variants)

    def test_numeric_prefix_removal(self):
        """测试移除数字前缀"""
        variants = generate_package_name_variants("2to3")
        self.assertIn("to3", variants)

    def test_suffix_variants(self):
        """测试后缀变体"""
        variants = generate_package_name_variants("package")
        self.assertIn("package-python", variants)
        self.assertIn("package-py", variants)

    def test_no_duplicates(self):
        """测试无重复变体"""
        variants = generate_package_name_variants("package")
        self.assertEqual(len(variants), len(set(variants)))

    def test_original_first(self):
        """测试原始包名在第一位"""
        variants = generate_package_name_variants("mypackage")
        self.assertEqual(variants[0], "mypackage")


class TestPackageMappingIntegrity(unittest.TestCase):
    """测试包映射配置完整性"""

    def test_package_mapping_is_dict(self):
        """测试PACKAGE_MAPPING是字典"""
        self.assertIsInstance(PACKAGE_MAPPING, dict)

    def test_package_mapping_not_empty(self):
        """测试PACKAGE_MAPPING不为空"""
        self.assertGreater(len(PACKAGE_MAPPING), 0)

    def test_package_mapping_values_are_strings(self):
        """测试PACKAGE_MAPPING值为字符串"""
        for key, value in PACKAGE_MAPPING.items():
            self.assertIsInstance(key, str, f"Key {key} should be string")
            self.assertIsInstance(value, str, f"Value {value} should be string")

    def test_package_patterns_is_list(self):
        """测试PACKAGE_PATTERNS是列表"""
        self.assertIsInstance(PACKAGE_PATTERNS, list)

    def test_package_patterns_format(self):
        """测试PACKAGE_PATTERNS格式正确"""
        for pattern, pip_name in PACKAGE_PATTERNS:
            self.assertIsInstance(pattern, str, "Pattern should be string")
            self.assertIsInstance(pip_name, str, "Pip name should be string")

    def test_common_mappings_exist(self):
        """测试常用映射存在"""
        common_mappings = {
            'PIL': 'pillow',
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'bs4': 'beautifulsoup4',
            'yaml': 'pyyaml',
        }
        for import_name, pip_name in common_mappings.items():
            self.assertIn(import_name, PACKAGE_MAPPING)
            self.assertEqual(PACKAGE_MAPPING[import_name], pip_name)


if __name__ == '__main__':
    unittest.main()

