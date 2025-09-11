# 自定义配置目录

这个目录用于存放用户自定义的默认配置文件。

## 使用方法

1. **复制默认配置文件**：从 `config/defaults/` 目录复制需要修改的配置文件到此目录
2. **修改配置**：根据需要修改复制的文件
3. **自动生效**：系统会自动使用自定义配置覆盖默认配置

## 配置优先级

```
用户核心配置 (user_settings.toml) > 自定义默认配置 (custom/) > 系统默认配置 (defaults/)
```

## 示例

假设你想修改浏览器取证的默认查询数量：

```bash
# 1. 复制默认配置
cp config/defaults/browser.toml config/custom/browser.toml

# 2. 修改自定义配置
# 编辑 config/custom/browser.toml，修改 max_history_items = 200

# 3. 配置自动生效，无需重启
```

## 版本升级

- 系统默认配置 (`config/defaults/`) 在升级时会被覆盖
- 自定义配置 (`config/custom/`) 在升级时会保留
- 用户核心配置 (`user_settings.toml`) 在升级时会保留