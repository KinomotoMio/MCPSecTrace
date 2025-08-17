# 开发文档

本目录包含MCPSecTrace项目的开发相关文档。

## 📖 文档列表

### [GitHub 协作开发维护指南](github-collaboration-guide.md)
详细的GitHub协作开发指南，包括：
- ✅ Commit规范和提交信息格式
- ✅ 分支管理策略和命名规范  
- ✅ Issue和Pull Request最佳实践
- ✅ Git高级操作（rebase、stash、cherry-pick等）
- ✅ 团队协作流程和代码审查指南
- ✅ 常见问题解决方案和快速参考

**适用对象：** 所有项目贡献者，特别是GitHub协作经验不足的团队成员

### [重构后代码测试指南](post-refactor-testing-guide.md)
项目重构后的系统性测试方法，包括：
- ✅ 快速验证清单和环境配置测试
- ✅ 模块导入和循环依赖检查
- ✅ 核心功能和MCP服务器测试
- ✅ GUI自动化和集成测试
- ✅ 性能测试和文档验证
- ✅ 自动化测试脚本和故障排除

**适用对象：** 开发者在重构后验证代码正常性，QA测试人员

## 🧪 测试脚本

### 自动化测试脚本
- `tests/integration/test_imports.py` - 模块导入测试
- `tests/unit/test_utils.py` - 工具功能测试  
- `scripts/test_all.sh` - 综合测试脚本

**运行方式：**
```bash
# 运行单个测试
uv run python tests/integration/test_imports.py
uv run python tests/unit/test_utils.py

# 运行完整测试套件
bash scripts/test_all.sh
```

## 🎯 快速开始

如果你是新成员，建议按以下顺序阅读：

1. **先读** [GitHub协作指南](github-collaboration-guide.md) 了解基本流程
2. **实践** 创建一个测试分支熟悉流程
3. **参考** 日常开发中遇到问题时查阅相应章节

## 💡 文档维护

这些文档是活文档，会根据团队实践不断更新。如有改进建议：

1. 提交Issue讨论
2. 或者直接提交PR修改文档
3. 在团队会议中提出

---

*欢迎为文档完善贡献力量！*