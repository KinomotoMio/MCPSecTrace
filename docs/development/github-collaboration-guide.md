# GitHub 协作开发维护指南

本指南旨在帮助 MCPSecTrace 项目团队成员掌握 GitHub 协作开发的最佳实践，提高团队协作效率和代码质量。

## 📚 目录

- [基本概念](#基本概念)
- [Commit 规范](#commit-规范)
- [分支管理策略](#分支管理策略)
- [Issue 提交指南](#issue-提交指南)
- [Pull Request 流程](#pull-request-流程)
- [Git 高级操作](#git-高级操作)
- [团队协作最佳实践](#团队协作最佳实践)
- [常见问题解决](#常见问题解决)

## 🔰 基本概念

### 项目协作模式

**对于私有项目（如我们的MCPSecTrace）：**
- ✅ **直接在主仓库中创建分支**：团队成员有写入权限，直接在主仓库创建功能分支
- ❌ **不需要Fork**：Fork主要用于开源项目的外部贡献者

**对于开源项目：**
- ✅ **Fork + Pull Request**：外部贡献者需要先Fork再提交PR
- ✅ **核心维护者直接提交**：有写入权限的核心成员可以直接在主仓库操作

### 基本工作流程

```
主分支(master/main) → 创建功能分支 → 开发 → 测试 → 提交PR → 代码审查 → 合并
```

## 📝 Commit 规范

### Commit 消息格式

使用 **约定式提交（Conventional Commits）** 格式：

```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

### 提交类型（type）

| 类型 | 描述 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(browser): 添加Firefox历史记录提取功能` |
| `fix` | 修复bug | `fix(sysmon): 修复日志解析时的编码错误` |
| `docs` | 文档更新 | `docs: 更新安装指南` |
| `style` | 代码格式化（不影响功能） | `style: 格式化automation模块代码` |
| `refactor` | 重构代码 | `refactor(mcp): 重组MCP服务器目录结构` |
| `test` | 添加或修改测试 | `test(core): 添加浏览器取证单元测试` |
| `chore` | 构建过程或辅助工具的变动 | `chore: 更新依赖包版本` |
| `perf` | 性能优化 | `perf(image): 优化图像识别算法性能` |
| `ci` | CI/CD配置变更 | `ci: 添加自动化测试流水线` |
| `build` | 构建系统变更 | `build: 更新pyproject.toml配置` |

### 作用域（scope）

根据项目模块划分：
- `core` - 核心功能模块
- `automation` - GUI自动化模块
- `mcp` - MCP服务器模块
- `utils` - 工具和实用程序
- `docs` - 文档
- `tests` - 测试
- `config` - 配置文件

### 好的Commit示例

```bash
# ✅ 好的提交消息
feat(automation): 添加Focus Pack自动化支持

实现Focus Pack安全扫描工具的GUI自动化功能，包括：
- 启动扫描流程
- 等待扫描完成检测
- 结果导出功能

Closes #123

# ✅ 简单的修复
fix(core): 修复浏览器数据提取时的路径错误

# ✅ 文档更新
docs(readme): 更新快速开始指南
```

### 不好的Commit示例

```bash
# ❌ 避免这样的提交消息
fix bug
update files
WIP
改了一些东西
修复
```

## 🌳 分支管理策略

### 分支命名规范

```
<类型>/<描述>
```

**分支类型：**
- `feature/` - 新功能开发
- `fix/` - bug修复
- `hotfix/` - 紧急修复
- `refactor/` - 重构
- `docs/` - 文档更新

**示例：**
```bash
feature/add-chrome-extension-support
fix/sysmon-encoding-issue
hotfix/critical-security-patch
refactor/mcp-server-architecture
docs/update-api-documentation
```

### 分支生命周期

```bash
# 1. 从主分支创建功能分支
git checkout master
git pull origin master
git checkout -b feature/new-threat-detection

# 2. 开发并提交
git add .
git commit -m "feat(core): 添加新的威胁检测算法"

# 3. 推送分支
git push -u origin feature/new-threat-detection

# 4. 创建PR，经过审查后合并

# 5. 删除已合并的分支
git checkout master
git pull origin master
git branch -d feature/new-threat-detection
git push origin --delete feature/new-threat-detection
```

## 🐛 Issue 提交指南

### 何时提交Issue

1. **发现Bug**：程序错误、异常行为
2. **功能请求**：新功能需求、改进建议
3. **文档问题**：文档错误、遗漏
4. **性能问题**：性能瓶颈、优化建议
5. **安全问题**：安全漏洞、风险点

### Issue模板

#### Bug报告模板

```markdown
## 🐛 Bug描述
简要描述遇到的问题

## 📋 重现步骤
1. 进入 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## ✅ 期望行为
描述你期望发生的行为

## ❌ 实际行为
描述实际发生的行为

## 🖼️ 截图
如果适用，添加截图来帮助解释你的问题

## 🔧 环境信息
- 操作系统: [例如 Windows 11]
- Python版本: [例如 3.13.0]
- 项目版本: [例如 0.1.0]
- 浏览器 (如果相关): [例如 Chrome 120]

## 📄 错误日志
```
粘贴相关的错误日志
```

## 💡 其他信息
添加关于问题的其他上下文信息
```

#### 功能请求模板

```markdown
## 🚀 功能描述
简要描述你想要的功能

## 💭 动机
解释为什么需要这个功能，它解决了什么问题

## 📝 详细说明
提供功能的详细描述

## 🎯 预期结果
描述实现这个功能后的预期效果

## 🔄 替代方案
描述你考虑过的任何替代解决方案或功能

## 📋 附加信息
添加关于功能请求的其他上下文信息或截图
```

### Issue标签体系

| 标签 | 颜色 | 描述 |
|------|------|------|
| `bug` | 🔴 red | Bug报告 |
| `enhancement` | 🟢 green | 功能增强 |
| `documentation` | 🔵 blue | 文档相关 |
| `help wanted` | 🟡 yellow | 需要帮助 |
| `good first issue` | 🟢 green | 适合新手 |
| `priority:high` | 🔴 red | 高优先级 |
| `priority:medium` | 🟡 yellow | 中优先级 |
| `priority:low` | 🟢 green | 低优先级 |
| `area:core` | 🔵 blue | 核心功能 |
| `area:automation` | 🟣 purple | GUI自动化 |
| `area:mcp` | 🟠 orange | MCP服务器 |

## 🔄 Pull Request 流程

### PR创建最佳实践

#### 1. 准备工作

```bash
# 确保本地master分支是最新的
git checkout master
git pull origin master

# 创建功能分支
git checkout -b feature/your-feature-name

# 进行开发工作
# ... 编码 ...

# 提交更改
git add .
git commit -m "feat(scope): 描述你的更改"

# 推送分支到远程
git push -u origin feature/your-feature-name
```

#### 2. 创建Pull Request

**对于私有项目（我们的情况）：**
- ✅ 直接在GitHub仓库中创建PR
- ✅ 选择 `feature/your-branch` → `master`
- ❌ 不需要Fork，因为团队成员有直接访问权限

**对于开源项目贡献：**
- ✅ 先Fork项目到自己账户
- ✅ 在Fork的仓库中创建分支
- ✅ 创建PR从 `your-fork:feature-branch` → `original:master`

#### 3. PR标题和描述格式

**PR标题格式：**
```
[类型](作用域): 简短描述
```

**PR描述模板：**
```markdown
## 📝 更改描述
简要描述这个PR的主要更改

## 🎯 解决的问题
- 修复 #issue_number
- 实现功能请求 #issue_number

## 📋 更改列表
- [ ] 添加了新功能X
- [ ] 修复了bug Y
- [ ] 更新了文档Z

## 🧪 测试
- [ ] 本地测试通过
- [ ] 添加了单元测试
- [ ] 手动测试场景：
  - 场景1：...
  - 场景2：...

## 📸 截图/演示
如果有UI更改，请提供截图

## ⚠️ 注意事项
- 任何破坏性更改
- 需要额外配置的地方
- 依赖项变更

## 👀 请审查者关注
- 特定的代码段
- 设计决策
- 性能影响
```

### PR审查流程

#### 审查者职责
1. **代码质量检查**
   - 代码风格是否符合项目规范
   - 逻辑是否清晰合理
   - 是否有潜在的bug

2. **功能验证**
   - 功能是否按预期工作
   - 边界情况是否考虑
   - 性能是否可接受

3. **文档和测试**
   - 是否有适当的文档更新
   - 测试覆盖是否充分
   - API文档是否更新

#### 审查反馈格式

```markdown
# ✅ 正面反馈
LGTM! (Looks Good To Me)
代码质量很好，逻辑清晰

# 💬 建议
建议：这里可以使用更简洁的写法
```python
# 原代码
if condition == True:
    return result
    
# 建议改为
if condition:
    return result
```

# ❓ 问题
问题：这个函数在输入为空时会怎么处理？

# 🔧 需要修改
需要修改：请添加错误处理逻辑，防止程序崩溃
```

### 合并策略

我们推荐使用 **Squash and Merge** 策略：

**优点：**
- 保持主分支历史简洁
- 每个功能一个commit
- 便于回滚和查找问题

**操作步骤：**
1. PR审查通过后
2. 点击 "Squash and merge"
3. 编辑合并commit消息
4. 删除功能分支

## ⚡ Git 高级操作

### Rebase 操作

#### 什么是Rebase？
Rebase是将一系列提交"重放"到另一个基准提交上，使提交历史更加线性和清晰。

#### 常用场景1：整理提交历史

```bash
# 场景：你在feature分支上有多个杂乱的提交，想要整理成清晰的提交
git log --oneline
# a1b2c3d fix typo
# e4f5g6h add feature part 2  
# h7i8j9k add feature part 1
# k0l1m2n WIP
# n3o4p5q master分支的最新提交

# 交互式rebase，整理最近4个提交
git rebase -i HEAD~4

# 在编辑器中会看到：
pick h7i8j9k add feature part 1
pick e4f5g6h add feature part 2
pick k0l1m2n WIP
pick a1b2c3d fix typo

# 修改为：
pick h7i8j9k add feature part 1
squash e4f5g6h add feature part 2
squash k0l1m2n WIP  
squash a1b2c3d fix typo

# 保存退出，然后编辑最终的提交消息
feat(automation): 实现Focus Pack自动化功能

实现了Focus Pack安全扫描工具的完整自动化流程，包括：
- 扫描启动和监控
- 结果检测和导出
- 错误处理和日志记录
```

#### 常用场景2：同步主分支最新更改

```bash
# 当前在feature分支，master有新的提交
git checkout feature/my-feature

# 获取最新的master分支
git fetch origin master

# 将feature分支的提交重新应用到最新的master上
git rebase origin/master

# 如果有冲突，解决冲突后继续
git add .
git rebase --continue

# 如果想取消rebase
git rebase --abort
```

#### 常用场景3：修改历史提交

```bash
# 修改最近的第2个提交
git rebase -i HEAD~2

# 在编辑器中将要修改的提交改为edit：
edit abc123d previous commit
pick def456e latest commit

# Git会停在要修改的提交上，进行修改
git add modified_file.py
git commit --amend -m "fix(core): 修正的提交消息"

# 继续rebase
git rebase --continue
```

### Checkout 高级用法

#### 分支和文件checkout

```bash
# 基本分支切换
git checkout master
git checkout feature/new-branch

# 创建并切换到新分支
git checkout -b feature/awesome-feature

# 基于远程分支创建本地分支
git checkout -b feature/local-branch origin/feature/remote-branch

# 从特定提交创建分支
git checkout -b hotfix/critical-fix abc123d

# checkout特定文件到工作目录（丢弃本地修改）
git checkout -- filename.py
git checkout HEAD~1 -- filename.py  # 恢复到上一个提交的版本

# checkout特定文件从其他分支
git checkout master -- config/settings.py  # 从master分支获取文件
```

#### 临时切换和查看

```bash
# 临时切换到特定提交（分离HEAD状态）
git checkout abc123d

# 查看特定提交的状态，然后回到原分支
git checkout abc123d
# ... 查看文件 ...
git checkout feature/my-branch  # 回到原来的分支

# 使用Git 2.23+的新命令（推荐）
git switch master              # 切换分支
git switch -c new-branch       # 创建并切换
git restore filename.py        # 恢复文件
```

### Stash 操作

#### 临时保存工作进度

```bash
# 保存当前工作进度
git stash
git stash push -m "保存GUI自动化开发进度"

# 查看stash列表
git stash list

# 应用最新的stash
git stash pop

# 应用特定的stash
git stash apply stash@{1}

# 查看stash内容
git stash show stash@{0}
git stash show -p stash@{0}  # 显示详细差异

# 删除stash
git stash drop stash@{0}
git stash clear  # 清空所有stash
```

#### 选择性stash

```bash
# 只stash特定文件
git stash push src/automation/huorong.py

# 交互式选择要stash的内容
git stash push -p

# 包含未跟踪的文件
git stash push -u
```

### Reset 和 Revert

#### Reset：修改历史（危险操作）

```bash
# 软重置：保留工作目录和暂存区的更改
git reset --soft HEAD~1

# 混合重置（默认）：保留工作目录更改，清空暂存区
git reset --mixed HEAD~1
git reset HEAD~1  # 等同于上面

# 硬重置：丢弃所有更改（危险！）
git reset --hard HEAD~1

# 重置到特定提交
git reset --hard abc123d

# 重置特定文件
git reset HEAD filename.py  # 从暂存区移除文件
```

#### Revert：安全的撤销

```bash
# 创建新提交来撤销某个提交（安全）
git revert abc123d

# 撤销多个提交
git revert abc123d..def456e

# 撤销merge提交
git revert -m 1 merge_commit_hash
```

### Cherry-pick

#### 选择性应用提交

```bash
# 将其他分支的特定提交应用到当前分支
git cherry-pick abc123d

# 应用多个提交
git cherry-pick abc123d def456e

# 应用提交但不自动提交（先review）
git cherry-pick --no-commit abc123d

# 解决冲突后继续
git add .
git cherry-pick --continue

# 取消cherry-pick
git cherry-pick --abort
```

### 查看和比较

#### 高级log查看

```bash
# 图形化显示分支历史
git log --graph --oneline --all

# 查看特定文件的提交历史
git log --follow src/core/browser_forensics.py

# 查看特定时间范围的提交
git log --since="2 weeks ago" --until="1 week ago"

# 查看特定作者的提交
git log --author="张三"

# 搜索提交消息
git log --grep="fix.*bug"

# 查看提交统计
git log --stat
git log --shortstat
```

#### 比较操作

```bash
# 比较分支
git diff master..feature/new-branch

# 比较特定提交
git diff abc123d def456e

# 只显示文件名
git diff --name-only master..feature/new-branch

# 比较特定文件
git diff master..feature/new-branch -- src/core/

# 查看未提交的更改
git diff  # 工作目录 vs 暂存区
git diff --cached  # 暂存区 vs 上次提交
git diff HEAD  # 工作目录 vs 上次提交
```

## 🤝 团队协作最佳实践

### 工作流程建议

#### 日常开发流程

```bash
# 1. 开始新工作前，同步主分支
git checkout master
git pull origin master

# 2. 创建功能分支
git checkout -b feature/issue-123-add-new-scanner

# 3. 进行开发工作，提交小而频繁的commits
git add src/automation/new_scanner.py
git commit -m "feat(automation): 添加新扫描器基础框架"

git add tests/test_new_scanner.py
git commit -m "test(automation): 添加新扫描器单元测试"

# 4. 推送分支并创建PR
git push -u origin feature/issue-123-add-new-scanner

# 5. 在GitHub上创建Pull Request

# 6. 根据审查反馈进行修改
git add .
git commit -m "fix(automation): 根据审查反馈修复边界条件处理"
git push

# 7. PR合并后，清理本地分支
git checkout master
git pull origin master
git branch -d feature/issue-123-add-new-scanner
```

#### 团队协作规则

1. **永远不要直接推送到master分支**
   ```bash
   # ❌ 禁止直接推送到master
   git push origin master
   
   # ✅ 通过PR流程
   git push origin feature/your-branch
   ```

2. **保持分支最新**
   ```bash
   # 定期同步master分支的更新
   git fetch origin
   git rebase origin/master
   ```

3. **提交前的检查清单**
   - [ ] 代码格式化：`uv run black src/`
   - [ ] 导入排序：`uv run isort src/`
   - [ ] 类型检查：`uv run mypy src/`
   - [ ] 运行测试：`uv run pytest`
   - [ ] 提交消息符合规范

### 冲突解决

#### 合并冲突处理

```bash
# 当出现合并冲突时
git pull origin master
# 或者
git rebase origin/master

# Git会标记冲突文件，编辑文件解决冲突
# 冲突标记如下：
<<<<<<< HEAD
你的更改
=======
别人的更改
>>>>>>> commit_hash

# 解决冲突后，标记为已解决
git add conflicted_file.py

# 完成合并或rebase
git commit  # 对于merge
git rebase --continue  # 对于rebase
```

#### 避免冲突的策略

1. **频繁同步主分支**
2. **小而专注的功能分支**
3. **避免同时修改同一文件的同一部分**
4. **及时沟通重大更改**

### 代码审查指南

#### 审查者指南

**技术层面：**
- 代码逻辑是否正确
- 性能是否有问题
- 安全隐患检查
- 错误处理是否充分

**项目层面：**
- 是否遵循项目架构
- 代码风格是否一致
- 测试覆盖是否充分
- 文档是否更新

**沟通层面：**
- 使用建设性的语言
- 解释"为什么"而不只是"什么"
- 提供具体的改进建议
- 认可好的代码实践

#### 被审查者指南

**提交PR时：**
- 提供清晰的PR描述
- 自己先review一遍代码
- 确保CI测试通过
- 主动解释复杂的设计决策

**响应反馈时：**
- 及时响应审查意见
- 虚心接受建议
- 不确定的地方主动询问
- 解释不同意见的原因

## 🚨 常见问题解决

### 问题1：忘记创建分支就开始开发

```bash
# 现状：在master分支上做了修改但还没提交
git status  # 看到有未提交的更改

# 解决：创建新分支并切换
git checkout -b feature/forgot-to-branch
git add .
git commit -m "feat: 添加忘记创建分支的功能"
```

### 问题2：提交了敏感信息

```bash
# 如果还没推送到远程
git reset --soft HEAD~1  # 撤销最近的提交
# 编辑文件，移除敏感信息
git add .
git commit -m "feat: 添加功能（已移除敏感信息）"

# 如果已经推送到远程（需要谨慎）
# 1. 立即更改泄露的密码/密钥
# 2. 使用git filter-branch或BFG清理历史
```

### 问题3：需要撤销已推送的提交

```bash
# 使用revert（推荐，安全）
git revert abc123d
git push origin master

# 不要使用force push除非确实必要
# git push --force origin master  # 危险操作！
```

### 问题4：分支落后于master太多

```bash
# 方法1：rebase（推荐）
git fetch origin
git rebase origin/master

# 方法2：merge
git fetch origin  
git merge origin/master
```

### 问题5：误删了分支

```bash
# 查找被删除分支的最后一个commit
git reflog

# 根据reflog恢复分支
git checkout -b recovered-branch abc123d
```

## 📋 快速参考

### 常用命令速查

```bash
# 分支操作
git branch                          # 查看本地分支
git branch -r                       # 查看远程分支
git branch -a                       # 查看所有分支
git branch -d branch-name            # 删除分支
git push origin --delete branch     # 删除远程分支

# 状态查看
git status                          # 工作区状态
git log --oneline -10               # 最近10个提交
git log --graph --oneline --all     # 图形化历史

# 临时保存
git stash                           # 保存当前工作
git stash pop                       # 恢复最近保存
git stash list                      # 查看保存列表

# 同步操作
git fetch origin                    # 获取远程更新
git pull origin master             # 拉取并合并
git push origin branch-name         # 推送分支
```

### 紧急情况处理

```bash
# 回滚到上一个提交
git reset --hard HEAD~1

# 回滚到特定提交
git reset --hard abc123d

# 撤销特定提交（安全）
git revert abc123d

# 放弃所有本地修改
git checkout .
git clean -fd
```

---

## 📚 扩展阅读

- [Git官方文档](https://git-scm.com/doc)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [约定式提交规范](https://www.conventionalcommits.org/zh-hans/)
- [语义化版本](https://semver.org/lang/zh-CN/)

## 💡 团队约定

基于这个指南，我们团队约定：

1. **必须通过PR进行代码合并**
2. **使用Squash and Merge策略**
3. **PR必须至少有一人审查通过**
4. **遵循约定式提交格式**
5. **保持分支命名规范**
6. **及时删除已合并的分支**

---

*这份指南是活文档，会根据团队实践不断完善。有任何疑问或建议，请提交Issue讨论。*
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "\u521b\u5efaGitHub\u7ef4\u62a4\u6307\u5357\u6587\u6863\u7ed3\u6784", "status": "completed"}, {"id": "2", "content": "\u7f16\u5199Commit\u89c4\u8303\u548c\u63d0\u4ea4\u4fe1\u606f\u683c\u5f0f", "status": "completed"}, {"id": "3", "content": "\u7f16\u5199Issue\u548cPR\u63d0\u4ea4\u6307\u5357", "status": "in_progress"}, {"id": "4", "content": "\u7f16\u5199Git\u9ad8\u7ea7\u64cd\u4f5c\u6307\u5357", "status": "pending"}, {"id": "5", "content": "\u7f16\u5199\u5206\u652f\u7ba1\u7406\u548c\u534f\u4f5c\u6d41\u7a0b", "status": "pending"}]