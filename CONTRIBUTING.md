# 贡献指南

欢迎纠正技术错误、改善说明、增加可复现示例，并提出交互实验设计。

## 开发环境

- Node.js 22+，Python 3.10+，C11 编译器。
- 安装依赖：npm install
- 开发服务器：npm run docs:dev
- 内容检查：npm test
- 静态构建：npm run build && npm run check:output
- 浏览器测试：npx playwright install chromium && npm run test:e2e

## 内容规范

- 每个章节唯一来源：docs/chapters/NN-slug.md。不要再编辑或新增根目录的旧 HTML。
- 新增章节时同步更新 courses.json；站点目录和校验工具依赖此文件。
- 旧地址跳转页位于 docs/public/NN.html；更改 slug 前要考虑旧 URL 兼容。
- 理论表述区分语言标准、ABI、编译器实现、CPU 和 Linux 版本差异。
- 可执行示例放在 labs/ 并提供可验证的预期输出；文中的教学伪代码必须清楚标识。
- 性能对比必须包含完整实验环境、工作负载和重复测量记录，示意数据必须显著标注。
- 不提交未获授权的官方教材、实验发行包、第三方图片和其他限制分发的材料。

## Pull Request

请说明目标、变更文件、测试命令、可观测验收结果、内容来源及已知局限。PR 不自动合并，需检查 CI 和 Pages 发布状态。

