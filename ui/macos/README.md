# Anki macOS 学习空间

使用 shadcn-svelte 的 macOS 界面层。Svelte 源码在此目录，生成资源在 `qt/aqt/data/web/modern`，由构建系统复制到 `_aqt/data/web/modern`。

```sh
npm ci
npm run check
npm run build
```

生成文件随源码提交，常规 Anki 构建不需要额外运行此目录的 npm；修改本目录后需重新生成资源。Python 接口位于 `qt/aqt/modern_ui.py`，仅在 macOS 且资源存在时启用，其他平台保留上游入口。

首页保留待学摘要、当前牌组学习入口和精简牌组列表，界面正文 16px、导航和主按钮 15px、辅助信息至少 14px；卡片模板字体不受影响。首页显示调度器的牌组树和数量；父牌组包含子牌组，不应将所有行再次相加。学习记录使用 revlog 的真实作答次数，采用调度器切日时间。卡片列表使用 Anki 搜索语法，每次显示前 100 条。字段仅以转义后的纯文本摘要展示；完整字段、媒体、模板、删除和批量管理通过原生编辑器完成，避免将复杂笔记当成两字段文本覆盖。

牌组详情与完成页共用首页外壳；复习页使用新的顶部导航和评分控件，所有显示答案、评分、计时及按键逻辑仍交给 Anki 原有入口。同步、导入、牌组选项和统计也沿用上游业务，不实现另一套调度或同步。偏好设置的七个分类通过 `modern_preferences.py` 映射原生控件，保留原有值、信号、动作和保存流程；实验功能页仍打开上游页面。其他窗口沿用现有 macOS 控件主题。旧牌组页/概览页的 HTML 扩展钩子存在时自动使用原生兼容布局，完整保留插件正文、脚本、渲染时序和底栏处理器；没有这类扩展时继续使用新版布局。未逐一验证所有第三方插件。

shadcn-svelte 组件保留 MIT 授权，见 `LICENSES/shadcn-svelte-MIT.txt`；项目整体沿用 Anki 的 AGPL-3.0-or-later。


## 回归检查

用已构建的 Anki Python/runtime 包运行 `qt/tools/check_modern_ui_regressions.py`，从仓库根目录执行：

```sh
PYTHONPATH=<built-runtime> python qt/tools/check_modern_ui_regressions.py \
  --fixture-base <synthetic-profile-base> --profile '<profile-name>' \
  --artifacts <output-directory>
```

必须使用人工测试资料库。检查器复制到临时目录，移除复制资料的同步凭据并以安全模式启动；不打开原资料库。覆盖设置文字/数字切页后的显示与保存、含特殊字符的父牌组及子/孙牌组查询、400px 原生窗口中各按钮的真实边界、三种队列名称与颜色、原调度器评分、桌面宽度恢复，以及模拟扩展的正文、脚本、渲染顺序和底栏按钮。结果和截图写入指定输出目录。

同样的参数可用于 `qt/tools/check_readability.py`，检查三种窗口大小下的字号、精简首页、首屏学习入口与按钮边界，并保存截图。

## macOS 应用图标

已确认的主图为 `assets/app-icon.png`，透明画布上的蓝色圆角底、白色卡片和蓝色星形。运行 `python3 ui/macos/scripts/export-app-icon.py`（仓库根目录、macOS）使用系统工具导出 16–1024 像素的 ICNS，写入 `qt/installer/app/resources/anki.icns`。其他平台的图标保持原样。
