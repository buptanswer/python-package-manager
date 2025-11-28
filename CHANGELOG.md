# 更新日志

所有重要的项目变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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

[2.1.0]: https://github.com/buptanswer/python-package-manager/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/buptanswer/python-package-manager/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/buptanswer/python-package-manager/releases/tag/v1.0.0

