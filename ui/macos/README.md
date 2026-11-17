# Anki macOS 学习空间

使用 shadcn-svelte 的 macOS 界面层。Svelte 源码在此目录，生成资源在 `qt/aqt/data/web/modern`，由构建系统复制到 `_aqt/data/web/modern`。

```sh
npm ci
npm run check
npm run build
```

生成文件随源码提交，常规 Anki 构建不需要额外运行此目录的 npm；修改本目录后需重新生成资源。Python 接口位于 `qt/aqt/modern_ui.py`，仅在 macOS 且资源存在时启用，其他平台保留上游入口。

首页显示调度器的牌组树和数量；父牌组包含子牌组，不应将所有行再次相加。学习记录使用 revlog 的真实作答次数，采用调度器切日时间。卡片列表使用 Anki 搜索语法，每次显示前 100 条。字段仅以转义后的纯文本摘要展示；完整字段、媒体、模板、删除和批量管理通过原生编辑器完成，避免将复杂笔记当成两字段文本覆盖。

复习、评分、同步、导入、牌组选项、设置和统计均调用 Anki 原有入口，不实现另一套调度或同步。偏好设置的七个分类通过 `modern_preferences.py` 映射原生控件，保留原有值、信号、动作和保存流程；实验功能页仍打开上游页面。其他窗口沿用现有 macOS 控件主题。牌组首页布局类插件需要单独验证兼容性。

shadcn-svelte 组件保留 MIT 授权，见 `LICENSES/shadcn-svelte-MIT.txt`；项目整体沿用 Anki 的 AGPL-3.0-or-later。
