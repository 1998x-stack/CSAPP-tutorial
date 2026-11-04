# Playwright 浏览器端到端验收

本目录包含正式的站点回归测试，覆盖首页、28 个章节路由、历史链接兼容和移动端阅读。

运行：先 npm install && npm run build，再执行 npx playwright install chromium && npm run test:e2e。
CI 使用独立 Chromium Job 验证；开发者本机可以用 PLAYWRIGHT_BROWSERS_PATH 指定浏览器缓存。

