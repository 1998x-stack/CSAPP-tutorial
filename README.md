# CSAPP 中文实践教程

> 28 章中文图解与可复现实验，从数据表示、机器级程序到操作系统与网络服务。**独立学习项目，非 CS:APP 官方译本。**

**[在线阅读](https://1998x-stack.github.io/CSAPP-tutorial/)** · [从第 01 章开始](https://1998x-stack.github.io/CSAPP-tutorial/01.html) · [跨章系统追踪](https://1998x-stack.github.io/CSAPP-tutorial/#traces) · [学习路线](docs/guides/learning-path.md) · [贡献指南](CONTRIBUTING.md)

本项目按知识依赖关系重新组织 28 章，以原理解释、图解、代码示例和实验练习串联整套课程。章节编号是**本项目的教学编排**，不与《Computer Systems: A Programmer's Perspective》第三版原书章节一一对应。

## 先开始学习

1. **在线阅读：**打开 [课程首页](https://1998x-stack.github.io/CSAPP-tutorial/)，按章节顺序学习；每章可从前后章导航继续。
2. **本地阅读：**克隆仓库后，在项目根目录执行 `python3 -m http.server 8000`，浏览器访问 `http://localhost:8000/`。
3. **动手练习：**阅读 `examples/` 中的独立示例，再到 `labs/` 尝试可编译的练习；记录编译器、系统及观察结果。

> 首页通过 `fetch('courses.json')` 加载课程数据，因此不建议直接双击 `index.html` 使用 `file://` 打开。

## 把章节串成一条系统因果链

首页除了 28 章目录，还提供三个无需脚本即可访问的跨章阅读路线：

- **从 Hello 到进程启动：**[01 程序的一生](01.html) → [13 静态链接](13.html) → [14 动态链接](14.html) → [15 进程与异常](15.html)。
- **追踪一条访存指令：**[04 机器级表示](04.html) → [11 存储层次](11.html) → [12 Cache](12.html) → [17 地址翻译](17.html)。
- **从字节到 HTTP 服务：**[19 系统 I/O](19.html) → [20 TCP socket](20.html) → [23 同步与线程池](23.html) → [28 综合服务器](28.html)。

每个章节页底部有两条带具体问题的跨章链接，方便从一个概念追踪其系统级后果；移动端的章节目录按横向滚动方式访问。

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


## 19–23 章：从字节流到正确的并发服务

这五篇独立 HTML 文章各增加一组有输入、状态、推导、失败边界与源码断言的深度讲解，并配原创 SVG：

- [19 短 I/O 与 EOF](19.html#deep-19)：管道写入 3 字节，`read(...,7)` 仅返回 3，下一次返回 0；逐项解释正数、EOF、`EINTR`、`EAGAIN`。
- [20 TCP 字节流分帧](20.html#deep-20)：4 字节网络序长度 `5` + `HELLO`，累计读取、不信任超大长度以及 EOF 截断。
- [21 就绪事件](21.html#deep-21)：`poll` 在对端关闭后可报告可处理事件，但 `read` 可以返回 EOF；状态机区分读、处理、待写和关闭。
- [22 线程同步](22.html#deep-22)：逻辑丢失更新与 C 数据竞争未定义行为的区别；四线程共享互斥计数器，每个累加 10,000 次。
- [23 条件变量与有界队列](23.html#deep-23)：`count≤2`、生产/消费谓词、`while` 重新验证、关闭广播与排空任务。

验证使用可独立编译的 **真实 POSIX C** 和确定性 Python 模型，不需要外部网络或猜测调度：

```bash
python3 examples/deep-ch19-23-models.py all
cc -std=c11 -Wall -Wextra -Werror -pedantic -pthread examples/deep-ch19-23.c -o /tmp/deep-io
for mode in short-read frame readiness mutex queue; do /tmp/deep-io "$mode"; done
```

来源、适用条件和不可推广的结论见 [19–23 专项复核账本](docs/evidence/19-23-deep-review.md)。Chromium QA 对 5 章 × 1440/390/360px 检查 SVG、旧交互、焦点、整页溢出与打印可见性；是否通过应以工作流实际结果为准。

## 13–18 章：从 ELF 到内存分配的第二轮系统推演

这 6 篇章节在保留原有章节、源码和交互的基础上新增了<strong>明确边界的完整推演</strong>和自绘的 SVG 图解：

- [13 ELF 重定位](13.html#deep-13)：PC-relative 相对位移 `S+A-P`、4 字节机器码字段和 `readelf`/`objdump` 观察范围。
- [14 动态装载](14.html#deep-14)：`R_X86_64_RELATIVE` 的 `B+A` 与导入符号的 GOT/PLT 绑定分工。
- [15 进程与文件描述符](15.html#deep-15)：`fork` 的内存独立性、共享 open file description 偏移、`waitpid` 退出状态与协调实验。
- [16 信号安全](16.html#deep-16)：丢失唤醒的竞态时序，以及 `sigprocmask` 与 `sigsuspend` 的原子边界。
- [17 页表遍历](17.html#deep-17)：48 位规范虚拟地址拆成四组 9 位索引和 12 位偏移，区分 TLB miss 与 page fault。
- [18 分配器碎片](18.html#deep-18)：固定池的最大连续块、合并前后变化、`realloc` 保留旧指针及乘法溢出检查。

```bash
python3 examples/deep-ch13-18-models.py all
cc -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror -pedantic \
    examples/deep-ch13-18-posix.c -o /tmp/deep-posix
/tmp/deep-posix fork
/tmp/deep-posix signal
/tmp/deep-posix realloc
```

每个算例的假设、参考规范、可验证范围与不能外推的结论，见 [13–18 章专项复核账本](docs/evidence/13-18-deep-review.md)。网站使用自动化浏览器在 1440、390、360 像素下检查图像、滚动、交互与打印语义，测试是否通过以 GitHub Actions 实际运行结果为准。

## 05–12 章：逐步推演与可执行自检

第 05–12 章各增加一篇独立的深度推导和一张可访问的 SVG 因果图：条件码与 signed/unsigned 分支、System V 栈对齐、结构体 padding、Y86-64 存储指令、load-use 停顿、CPE 两种理论下界、Cache/TLB 工作集以及缓存相联度冲突。

每章直接在网页中解释输入、变换、状态、结果和适用边界，并提供不依赖第三方库的可执行验证脚本：

```bash
python3 examples/deep-ch05-12.py all   # 运行八章的确定性断言
python3 examples/deep-ch05-12.py 09    # 仅检查流水线时序
```

这些脚本验证数学/状态模型，不会伪装成真实硬件性能实验。核验清单和技术来源见 [05–12 深度复核记录](docs/evidence/05-12-deep-review.md)。

## 在本地验证与构建

依赖：**Node.js 22+、Python 3.10+、C11 编译器（GCC/Clang）**。常规静态构建不需要安装 npm 包。

```bash
npm test                 # 内容 / 链接 / C 示例 / 章节回归测试
npm run build            # 生成 dist/ 静态站点
python3 -m http.server 8000 -d dist
# 打开 http://localhost:8000/
```

单独执行：`npm run check:content`、`npm run check:links`、`npm run check:snippets`、`npm run check:linking`。新增的全站元数据、锚点、跨章链接和缩放检查通过 `tests/content/course-wide.test.mjs` 随 `npm test` 执行。GitHub Actions 的 `ci.yml` 校验内容并构建，`pages.yml` 在 `main` 更新后部署 `dist/`。浏览器截图、交互专项检查由独立工作流执行，不应仅凭 `npm test` 推定其结果。

## 仓库目录

```text
CSAPP-tutorial/
├── index.html                 # 正式首页（稳定的公开 URL）
├── 01.html … 28.html          # 正式章节页：保留已有链接
├── courses.json               # 唯一课程顺序和章节元数据
├── home.css / theme.css       # 首页 / 基础章节样式
├── course-improvements.css    # 28 章统一导航、知识桥与移动端适配
├── olah-*.css / chapter-olah.css  # 历史章节样式，渐进合并
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

## 逐页检查与变更边界

质量状态分为三层：**结构覆盖**（统一元数据、页面链接和移动端导航）、**专题精修**（新增具体推导或修订开场）与**浏览器验收**（需工作流实际运行）。本轮不能把 28 页的结构覆盖等同于每篇技术断言都已完全复核，具体清单与后续专项任务见 [逐页复核矩阵](docs/guides/chapter-review-matrix.md)。

保留 `01.html`–`28.html` 的公开路径和原有 SVG 资源路径；不将 `docs/.vitepress/` 误写为当前发布入口。正式站点由 `scripts/build-static.mjs` 根据 `courses.json` 打包。

## 内容可靠性、贡献与授权

每章的来源与技术断言记录统一放在 [`docs/evidence/`](docs/evidence/README.md)，便于追溯图表、标准与示例适用条件；这些记录不意味着所有叙述均经过独立复核。勘误、实验改进或新图解请参考 [贡献指南](CONTRIBUTING.md)。

本项目非 CMU 或 CS:APP 官方项目，不提供受版权限制的教材或官方实验材料。参见 [来源与免责声明](NOTICE.md) 和 [LICENSE](LICENSE)。
