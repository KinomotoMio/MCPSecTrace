# GitHub 分支保护设置指南

为了确保PR协作流程，需要在GitHub仓库设置中配置分支保护规则。

## 设置步骤

1. 进入仓库设置页面：`Settings` → `Branches`

2. 点击 `Add branch protection rule`

3. 配置以下规则：

### 基本设置
- **Branch name pattern**: `master` (或 `main`)
- **Restrict pushes that create matching branches**: ✅ 勾选

### 必需的状态检查
- **Require status checks to pass before merging**: ✅ 勾选
- **Require branches to be up to date before merging**: ✅ 勾选
- **Status checks that are required**:
  - `检查PR审查状态`
  - `代码质量检查` (可选)

### 必需的审查
- **Require pull request reviews before merging**: ✅ 勾选
- **Required number of reviewers before merging**: `1`
- **Dismiss stale reviews when new commits are pushed**: ✅ 勾选
- **Require review from code owners**: 如果有CODEOWNERS文件则勾选
- **Restrict reviews to users with push access**: ✅ 勾选

### 其他限制
- **Require conversation resolution before merging**: ✅ 勾选（确保讨论得到解决）
- **Require signed commits**: 根据需要选择
- **Require linear history**: ✅ 勾选（保持提交历史整洁）
- **Do not allow bypassing the above settings**: ✅ 勾选

### 管理员权限
- **Allow administrators to bypass these requirements**: ❌ 不勾选（确保管理员也遵守规则）

## 效果

设置完成后：
- ✅ 禁止直接推送到master分支
- ✅ 所有更改必须通过PR
- ✅ PR必须有至少1个其他人的审查批准
- ✅ 必须通过CI检查才能合并
- ✅ 确保审查讨论得到解决

## 两人协作流程

1. **开发者A** 创建Issue描述要做的工作
2. **开发者A** 创建分支，完成开发，提交PR并关联Issue
3. **开发者B** 审查代码，提出意见或批准
4. CI检查通过 + 审查批准后，**开发者B** 合并PR
5. Issue自动关闭

这样确保每个更改都经过双人检查，提高代码质量。