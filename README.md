# CSAPP 中文实践教程

> 28 章中文图解与可复现实验，从数据表示、机器级程序到操作系统与网络服务。**独立学习项目，非 CS:APP 官方译本。**

**[在线阅读](https://1998x-stack.github.io/CSAPP-tutorial/)** · [从第 01 章开始](https://1998x-stack.github.io/CSAPP-tutorial/01.html) · [学习路线](docs/guides/learning-path.md) · [贡献指南](CONTRIBUTING.md)

本项目按知识依赖关系重新组织 28 章，以原理解释、图解、代码示例和实验练习串联整套课程。章节编号是**本项目的教学编排**，不与《Computer Systems: A Programmer's Perspective》第三版原书章节一一对应。

## 先开始学习

1. **在线阅读：**打开 [课程首页](https://1998x-stack.github.io/CSAPP-tutorial/)，按章节顺序学习；每章可从前后章导航继续。
2. **本地阅读：**克隆仓库后，在项目根目录执行 `python3 -m http.server 8000`，浏览器访问 `http://localhost:8000/`。
3. **动手练习：**阅读 `examples/` 中的独立示例，再到 `labs/` 尝试可编译的练习；记录编译器、系统及观察结果。

> 首页通过 `fetch('courses.json')` 加载课程数据，因此不建议直接双击 `index.html` 使用 `file://` 打开。

## 学习路线与章节索引

| 阶段 | 章节 | 学习重点 |
| --- | --- | --- |
| 表示与执行 | 01–10 | 数据表示、汇编、处理器与程序性能 |
| 内存与链接 | 11–18 | 存储层次、ELF、异常控制流与虚拟内存 |
| 系统编程 | 19–23 | I/O、网络服务器、线程与同步 |
| 实验与项目 | 24–28 | CSAPP 风格练习、现代体系结构、高性能服务器 |

### 一、表示、执行与性能

从位和编码出发，走到汇编、处理器与优化。

| 章节 | 主要内容 |
| --- | --- |
| [01 · 计算机系统漫游](01.html) | hello程序的一生、硬件组成与存储层次 |
| [02 · 信息的表示与处理——整数](02.html) | 大小端字节序、补码编码 |
| [03 · 信息的表示与处理——浮点数](03.html) | IEEE 754格式、规格化与非规格化 |
| [04 · 程序的机器级表示——基础](04.html) | x86-64寄存器全景、数据传送与算术指令 |
| [05 · 程序的机器级表示——控制流](05.html) | 条件码寄存器、条件跳转与CMP/TEST |
| [06 · 程序的机器级表示——过程与栈](06.html) | 栈帧结构详解、call/ret微操作 |
| [07 · 程序的机器级表示——数据与进阶](07.html) | 数组与指针的汇编、结构体对齐与填充 |
| [08 · 处理器体系结构——ISA设计](08.html) | Y86-64指令集、HCL硬件控制语言 |
| [09 · 处理器体系结构——流水线](09.html) | 流水线原理与性能、数据冒险与转发 |
| [10 · 优化程序性能](10.html) | CPE性能度量、编译器优化与局限 |

### 二、内存、链接与运行时

理解缓存、程序装载、进程与虚拟内存。

| 章节 | 主要内容 |
| --- | --- |
| [11 · 存储器层次结构——技术](11.html) | SRAM/DRAM/SSD对比、时间与空间局部性 |
| [12 · 存储器层次结构——Cache](12.html) | 缓存组织结构(S/E/B)、直接映射/组相联 |
| [13 · 链接——静态链接](13.html) | ELF目标文件格式、符号与符号表 |
| [14 · 链接——动态链接](14.html) | 共享库(.so)机制、GOT与PLT延迟绑定 |
| [15 · 异常控制流——异常与进程](15.html) | 异常四种分类、fork写时复制 |
| [16 · 异常控制流——信号](16.html) | 信号发送与接收、信号处理函数安全写法 |
| [17 · 虚拟内存——地址翻译](17.html) | 虚拟寻址的动机、多级页表结构 |
| [18 · 虚拟内存——内存分配](18.html) | mmap与munmap、显式分配器设计策略 |

### 三、系统 I/O、网络与并发

学习 Unix I/O、TCP、服务器和线程同步。

| 章节 | 主要内容 |
| --- | --- |
| [19 · 系统级I/O](19.html) | Unix I/O模型与FD、open/read/write调用 |
| [20 · 网络编程——基础](20.html) | TCP/IP协议栈、套接字接口详解 |
| [21 · 网络编程——进阶](21.html) | 迭代/并发服务器模型、CGI动态内容生成 |
| [22 · 并发编程——线程基础](22.html) | 线程vs进程对比、Pthreads API |
| [23 · 并发编程——高阶模式](23.html) | 读写锁(rwlock)、线程池设计与实现 |

### 四、经典实验与综合项目

把原理落到实验和可复现的系统项目中。

| 章节 | 主要内容 |
| --- | --- |
| [24 · 经典Lab实战(I)](24.html) | Data Lab位运算挑战、Bomb Lab GDB拆弹 |
| [25 · 经典Lab实战(II)](25.html) | Cache Lab缓存模拟、Shell Lab进程管理 |
| [26 · 经典Lab实战(III)——Proxy Lab](26.html) | 并发Web代理架构、生产者消费者模型 |
| [27 · 现代系统新趋势](27.html) | RISC-V开放指令集、GPU异构计算CUDA |
| [28 · 综合项目：手写高性能Web服务器](28.html) | epoll事件驱动架构、线程池+任务队列 |

## 在本地验证与构建

依赖：**Node.js 22+、Python 3.10+、C11 编译器（GCC/Clang）**。常规静态构建不需要安装 npm 包。

```bash
npm test                 # 内容 / 链接 / C 示例 / 章节回归测试
npm run build            # 生成 dist/ 静态站点
python3 -m http.server 8000 -d dist
# 打开 http://localhost:8000/
```

单独执行：`npm run check:content`、`npm run check:links`、`npm run check:snippets`、`npm run check:linking`。GitHub Actions 的 `ci.yml` 校验内容并构建，`pages.yml` 在 `main` 更新后部署 `dist/`。浏览器截图、交互专项检查由独立工作流执行，不应仅凭 `npm test` 推定其结果。

## 仓库目录

```text
CSAPP-tutorial/
├── index.html                 # 正式首页（稳定的公开 URL）
├── 01.html … 28.html          # 正式章节页：保留已有链接
├── courses.json               # 唯一课程顺序和章节元数据
├── *.css                      # 当前页面使用的共享与章节样式
├── assets/chapters/           # 第 05–07 章插图
├── chapter-assets/            # 多个图解章节现有插图
├── examples/                  # 独立 C / Python 教学示例
├── labs/                      # 分主题实验与配套源码
├── interactive/               # 交互式实验规格与说明
├── docs/
│   ├── evidence/              # 01.json–28.json：统一章节来源记录
│   ├── chapters/              # 迁移说明、质量记录及部分现有插图
│   ├── guides/                # 学习路线、内容规范与图解说明
│   ├── labs/                  # 实验导航
│   └── .vitepress/            # 预备的 VitePress 配置，非当前构建入口
├── scripts/                   # 内容验证、静态打包及浏览器 QA
├── tests/                     # 内容回归测试与 E2E 说明
└── .github/workflows/         # CI / GitHub Pages / 章节专项 QA
```

**目录兼容说明：** 现有插图分布在 `assets/chapters/`、`chapter-assets/` 和 `docs/chapters/assets/`，是为了保持现有 HTML 的相对路径及 GitHub Pages 地址可用；不要在未同步页面、测试与构建脚本时直接搬迁。构建产物 `dist/` 由脚本生成，不是编辑源文件的位置。

**版本边界：** 当前发布路径仍是原生 HTML。`docs/.vitepress/` 是未来 Markdown 迁移的预备结构，不能将其描述为现已上线的 VitePress 站点；迁移安排见 [章节说明](docs/chapters/README.md)。

## 内容可靠性、贡献与授权

每章的来源与技术断言记录统一放在 [`docs/evidence/`](docs/evidence/README.md)，便于追溯图表、标准与示例适用条件；这些记录不意味着所有叙述均经过独立复核。勘误、实验改进或新图解请参考 [贡献指南](CONTRIBUTING.md)。

本项目非 CMU 或 CS:APP 官方项目，不提供受版权限制的教材或官方实验材料。参见 [来源与免责声明](NOTICE.md) 和 [LICENSE](LICENSE)。
