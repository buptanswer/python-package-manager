# 更新日志

所有重要的项目变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.2.0] - 2025-11-29

### 新增
- ✨ 特殊包处理机制（`PACKAGE_SPECIAL_HANDLING`配置）
- ✨ pywin32安装后验证支持（使用`pip show`验证，无需重启进程）
- ✨ `check_package_installed_via_pip`函数：通过pip命令验证包安装
- ✨ `skip_import_verify`选项：跳过导入验证的特殊包配置
- ✨ 全新测试套件：168个单元测试，覆盖所有核心功能
  - Import提取测试（32个测试）
  - 文件操作测试（22个测试）
  - 包追踪器测试（17个测试）
  - 包名映射测试（36个测试）
  - 特殊包处理测试（20个测试）
  - Requirements生成测试（24个测试）
  - 集成测试（17个测试）

### 修复
- 🐛 修复pywin32安装后验证失败问题（需重启进程才能导入）
- 🐛 修复`write_dependency_overview`文件数统计不准确问题
- 🐛 修复`generate_package_name_variants`注释示例错误
- 🐛 修复`enhanced_process_installation`统计不一致问题

### 移除
- 🗑️ 移除未使用的`process_installation`函数
- 🗑️ 移除未使用的`generate_requirements`函数
- 🗑️ 移除冗余变量`packages_to_install`和`successful_pip_packages`

### 改进
- ⚡ 改进安装统计准确性（模块名计数而非包名）
- 📝 改进代码注释和文档
- 🧪 大幅增强测试覆盖率（从35个测试增至168个）

## [2.1.0] - 2025-11-29

### 新增
- ✨ 完整支持多行import语句（使用括号）
- ✨ 自动过滤相对导入（以`.`开头的导入）
- ✨ 运行时标准库检测（Python 3.10+），兼容旧版本
- ✨ 备份文件自动清理机制（保留最近5个备份）
- ✨ 完整测试套件（35个单元测试）
- ✨ 改进的错误处理和边界情况处理
- ✨ 更详细的错误信息提取

### 修复
- 🐛 修复Windows编码问题
- 🐛 修复文件路径处理异常（relative_to错误）
- 🐛 修复索引越界问题（空列表检查）
- 🐛 修复无限循环防护（多行import长度限制）
- 🐛 修复权限错误处理
- 🐛 改进备份清理逻辑

### 改进
- ⚡ 改进文件扫描性能（异常处理优化）
- 📝 改进代码注释和文档
- 🧪 添加完整的测试覆盖

## [2.0.0] - 2025-11-26

### 新增
- ✨ 详细的包来源日志记录
- 🔍 精确的行号和文件路径追踪
- 📊 项目依赖使用统计
- 🔄 智能覆盖和备份策略
- 👥 版本控制友好的格式

### 改进
- 📋 增强版requirements.txt生成
- 🎨 改进控制台输出格式
- 📝 更详细的包使用统计

## [1.0.0] - 2025-11-XX

### 新增
- 🎉 初始版本发布
- 📦 基础的包扫描和安装功能
- 📋 简单的requirements.txt生成
- 🔍 基本的import语句提取

---

[2.2.0]: https://github.com/buptanswer/python-package-manager/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/buptanswer/python-package-manager/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/buptanswer/python-package-manager/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/buptanswer/python-package-manager/releases/tag/v1.0.0
