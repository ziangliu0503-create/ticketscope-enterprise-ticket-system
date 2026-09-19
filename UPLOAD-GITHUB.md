# GitHub 更新与 Render 部署

1. 解压下载的 ZIP。
2. 打开解压后的 `enterprise-ticket-system` 文件夹。
3. 在 GitHub 仓库首页选择 **Add file → Upload files**。
4. 将该文件夹里面的所有文件和子文件夹拖入上传区域。不要只上传 ZIP 文件。
5. 等待文件列表加载完成，在提交说明中填写 `Improve role-based workspaces`。
6. 点击 **Commit changes**。
7. Render Blueprint 默认会检测 GitHub 的新提交并自动部署；进入 Render 的 `ticketscope-demo` 查看部署日志。
8. 如果几分钟后没有开始部署，在 Blueprint 页面点击 **Manual sync**。

部署完成后建议打开一个无痕窗口，分别登录三个演示账号检查角色差异。不同标签页现在使用独立登录会话，不会再被最后登录的账号覆盖。
