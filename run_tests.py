"""
运行所有测试

使用方法:
    python run_tests.py           # 运行所有测试
    python run_tests.py -v        # 详细输出
    python run_tests.py -q        # 简洁输出
"""
import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_all_tests(verbosity=2):
    """运行所有测试
    
    Args:
        verbosity: 输出详细程度 (0=安静, 1=正常, 2=详细)
    
    Returns:
        bool: 测试是否全部通过
    """
    # 发现并加载所有测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 所有测试模块
    test_modules = [
        'tests.test_import_extraction',      # Import提取测试
        'tests.test_file_operations',        # 文件操作测试
        'tests.test_package_tracker',        # 包追踪器测试
        'tests.test_package_mapping',        # 包名映射测试
        'tests.test_special_handling',       # 特殊包处理测试
        'tests.test_requirements_generation', # Requirements生成测试
        'tests.test_integration',            # 集成测试
    ]
    
    # 统计信息
    loaded_modules = 0
    failed_modules = []
    
    for module_name in test_modules:
        try:
            tests = loader.loadTestsFromName(module_name)
            suite.addTests(tests)
            loaded_modules += 1
        except ImportError as e:
            failed_modules.append((module_name, str(e)))
            print(f"警告: 无法加载测试模块 {module_name}: {e}")
    
    # 打印加载信息
    if verbosity > 0:
        print(f"\n{'='*70}")
        print(f"加载了 {loaded_modules}/{len(test_modules)} 个测试模块")
        if failed_modules:
            print(f"失败模块: {len(failed_modules)}")
            for module, error in failed_modules:
                print(f"  - {module}: {error}")
        print(f"{'='*70}\n")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # 打印摘要
    if verbosity > 0:
        print(f"\n{'='*70}")
        print("测试摘要")
        print(f"{'='*70}")
        print(f"运行: {result.testsRun}")
        print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"失败: {len(result.failures)}")
        print(f"错误: {len(result.errors)}")
        print(f"跳过: {len(result.skipped)}")
        print(f"{'='*70}\n")
    
    # 返回测试结果
    return result.wasSuccessful()


def run_specific_tests(module_name, verbosity=2):
    """运行特定测试模块
    
    Args:
        module_name: 测试模块名（如 'test_import_extraction'）
        verbosity: 输出详细程度
    
    Returns:
        bool: 测试是否通过
    """
    loader = unittest.TestLoader()
    
    # 支持简短名称
    if not module_name.startswith('tests.'):
        module_name = f'tests.{module_name}'
    
    try:
        suite = loader.loadTestsFromName(module_name)
    except ImportError as e:
        print(f"错误: 无法加载测试模块 {module_name}: {e}")
        return False
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # 解析命令行参数
    verbosity = 2  # 默认详细输出
    
    if '-v' in sys.argv or '--verbose' in sys.argv:
        verbosity = 2
    elif '-q' in sys.argv or '--quiet' in sys.argv:
        verbosity = 0
    
    # 检查是否指定了特定模块
    specific_module = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            specific_module = arg
            break
    
    if specific_module:
        success = run_specific_tests(specific_module, verbosity)
    else:
        success = run_all_tests(verbosity)
    
    sys.exit(0 if success else 1)
