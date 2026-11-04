# CSAPP 中文实践教程

[![CI](https://github.com/1998x-stack/CSAPP-tutorial/actions/workflows/ci.yml/badge.svg)](https://github.com/1998x-stack/CSAPP-tutorial/actions/workflows/ci.yml)
[![Pages](https://github.com/1998x-stack/CSAPP-tutorial/actions/workflows/pages.yml/badge.svg)](https://github.com/1998x-stack/CSAPP-tutorial/actions/workflows/pages.yml)

**28 章中文系统教程 · VitePress 文档站 · V0.3 独立 C11/POSIX 系统实验与黄金测试**。

项目定位为独立学习教程，课程划分不等于 CS:APP 第三版原书章节组织，也不代表 Carnegie Mellon University 或教材作者的官方项目。

## 在线阅读

- 项目规划中的 Pages 站点：[https://1998x-stack.github.io/CSAPP-tutorial/](https://1998x-stack.github.io/CSAPP-tutorial/)（是否可访问以实际 Pages 发布状态为准）。
- [课程总览](docs/chapters/index.md) · [学习路线](docs/guides/learning-path.md) · [实验总览](docs/labs/index.md)
- 从旧版网页分享的 `01.html`～`28.html` 地址会跳转至新课程路径。

## 本地运行

需要 Node.js 22+、Python 3.10+ 和 C11 编译器。首次安装开发依赖：

```bash
npm install
npm run docs:dev      # 开发服务器
npm test              # 内容、链接、可执行示例检查
npm run build         # 生成 docs/.vitepress/dist
npm run check:output  # 检查输出和 28 个旧地址跳转页
npm run docs:preview  # 本地查看构建版本

# 实验：需要 CMake 3.20+、GCC/Clang 和 Python
npm run test:labs
```

## 课程目录

| 章节 | 标题 | 核心主题 |
| --- | --- | --- |
| 01 | [计算机系统漫游](docs/chapters/01-introduction.md) | hello程序的一生、硬件组成与存储层次 |
| 02 | [信息的表示与处理——整数](docs/chapters/02-integers.md) | 大小端字节序、补码编码 |
| 03 | [信息的表示与处理——浮点数](docs/chapters/03-floating-point.md) | IEEE 754格式、规格化与非规格化 |
| 04 | [程序的机器级表示——基础](docs/chapters/04-machine-basics.md) | x86-64寄存器全景、数据传送与算术指令 |
| 05 | [程序的机器级表示——控制流](docs/chapters/05-machine-control-flow.md) | 条件码寄存器、条件跳转与CMP/TEST |
| 06 | [程序的机器级表示——过程与栈](docs/chapters/06-procedures-and-stack.md) | 栈帧结构详解、call/ret微操作 |
| 07 | [程序的机器级表示——数据与进阶](docs/chapters/07-data-and-memory-layout.md) | 数组与指针的汇编、结构体对齐与填充 |
| 08 | [处理器体系结构——ISA设计](docs/chapters/08-isa-design.md) | Y86-64指令集、HCL硬件控制语言 |
| 09 | [处理器体系结构——流水线](docs/chapters/09-pipelining.md) | 流水线原理与性能、数据冒险与转发 |
| 10 | [优化程序性能](docs/chapters/10-performance-optimization.md) | CPE性能度量、编译器优化与局限 |
| 11 | [存储器层次结构——技术](docs/chapters/11-memory-hierarchy.md) | SRAM/DRAM/SSD对比、时间与空间局部性 |
| 12 | [存储器层次结构——Cache](docs/chapters/12-cache.md) | 缓存组织结构(S/E/B)、直接映射/组相联 |
| 13 | [链接——静态链接](docs/chapters/13-static-linking.md) | ELF目标文件格式、符号与符号表 |
| 14 | [链接——动态链接](docs/chapters/14-dynamic-linking.md) | 共享库(.so)机制、GOT与PLT延迟绑定 |
| 15 | [异常控制流——异常与进程](docs/chapters/15-exceptions-and-processes.md) | 异常四种分类、fork写时复制 |
| 16 | [异常控制流——信号](docs/chapters/16-signals.md) | 信号发送与接收、信号处理函数安全写法 |
| 17 | [虚拟内存——地址翻译](docs/chapters/17-virtual-memory.md) | 虚拟寻址的动机、多级页表结构 |
| 18 | [虚拟内存——内存分配](docs/chapters/18-memory-allocation.md) | mmap与munmap、显式分配器设计策略 |
| 19 | [系统级I/O](docs/chapters/19-system-io.md) | Unix I/O模型与FD、open/read/write调用 |
| 20 | [网络编程——基础](docs/chapters/20-network-fundamentals.md) | TCP/IP协议栈、套接字接口详解 |
| 21 | [网络编程——进阶](docs/chapters/21-network-advanced.md) | 迭代/并发服务器模型、CGI动态内容生成 |
| 22 | [并发编程——线程基础](docs/chapters/22-thread-basics.md) | 线程vs进程对比、Pthreads API |
| 23 | [并发编程——高阶模式](docs/chapters/23-concurrency-patterns.md) | 读写锁(rwlock)、线程池设计与实现 |
| 24 | [经典Lab实战(I)](docs/chapters/24-classic-labs-i.md) | Data Lab位运算挑战、Bomb Lab GDB拆弹 |
| 25 | [经典Lab实战(II)](docs/chapters/25-classic-labs-ii.md) | Cache Lab缓存模拟、Shell Lab进程管理 |
| 26 | [经典Lab实战(III)——Proxy Lab](docs/chapters/26-proxy-lab.md) | 并发Web代理架构、生产者消费者模型 |
| 27 | [现代系统新趋势](docs/chapters/27-modern-systems.md) | RISC-V开放指令集、GPU异构计算CUDA |
| 28 | [综合项目：手写高性能Web服务器](docs/chapters/28-web-server.md) | epoll事件驱动架构、线程池+任务队列 |

## 仓库结构

```text
CSAPP-tutorial/
├── docs/
│   ├── index.md                  # 首页
│   ├── chapters/                 # 正式 28 章 Markdown 教程
│   ├── guides/                   # 学习路线、内容规范
│   ├── labs/                     # 实验说明
│   ├── public/                   # 图标及历史链接兼容跳转页
│   └── .vitepress/               # 站点配置、主题和构建产物
├── interactive/                  # 后续交互教学器规划
├── labs/                         # 位运算、汇编、Cache、进程、内存与并发实验
├── CMakeLists.txt                # C11/POSIX 实验构建、CTest 注册
├── scripts/                      # 内容、链接、示例、产物验证
├── tests/labs/                   # 黄金输出、输入 trace、退出码验证
├── tests/e2e/                    # Playwright 浏览器验收
├── courses.json                  # 章节元数据单一来源
├── package.json
└── .github/workflows/           # CI 与 GitHub Pages 部署
```

## 质量与贡献

每次 PR 运行内容验证、VitePress 构建、生成页面检查、浏览器端到端检查，以及 GCC/Clang 实验编译与 CTest 黄金验收。可独立编译的 C 示例放在 `labs/`，书中片段不默认承诺可直接构建。

[实验总览](docs/labs/index.md) · [贡献指南](CONTRIBUTING.md) · [内容规范](docs/guides/content-style.md) · [第三方版权说明](NOTICE.md) · [开源许可](LICENSE)
