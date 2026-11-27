# 逐页复核矩阵 · 2026-11-22

本表将“可验证的结构修改”与“完整技术内容复核”严格区分。发布前需要 GitHub Actions 运行；浏览器截图、移动设备与交互行为若未实际执行，均记为**待验收**，不是已通过。

## 2026-11-22 · 05–12 章第二轮深度复核

新增 8 个独立的定量推导、8 个独立 SVG、8 个可执行的 Python 断言与对应内容回归测试。重点是明确模型中的输入、数值、公式与失效边界，不是凭视觉效果或演示数值推断真实硬件性能。

已审核断言清单见 [05–12 第二轮来源与测试记录](../evidence/05-12-deep-review.md)。跨设备浏览器截图和线上发布是否成功，应以 GitHub Actions 和 Pages 实际运行记录为准。

## 2026-11-22 · 13–18 章第二轮因果推演

新增 6 个专题验证模块、6 张具有独立 `title`/`desc` 的 SVG 及可编译 C / Python 脚本。重点复核 **PC-relative ELF 重定位、`R_X86_64_RELATIVE`、fork 与 open-file description、信号等待竞态、四级页表字段和固定池碎片合并**。具体断言、引用与适用范围见 [13–18 来源复核账本](../evidence/13-18-deep-review.md)。这一批的浏览器验收由专门 workflow 负责，未执行时不可宣称已通过。

## 2026-11-22 · 第 19–23 章第二轮深度复核

新增 5 套逐章技术推导和原创 SVG、五条可编译执行的 POSIX C 路径、Python 数值/状态断言，并增加 1440/390/360px 全章浏览器验收。重点是短 I/O、字节流分帧、poll 就绪/EOF、线程互斥与有界条件变量队列。来源与错误边界详见 [19–23 复核账本](../evidence/19-23-deep-review.md)。这不是对历史页面所有断言或生产服务器性能的完整审计。

## 2026-11-22 · 第 24–28 章第三轮深度推演

新增 5 套逐章技术推导和原创 SVG、一个纯标准库的确定性模型脚本 `examples/deep-ch24-28-models.py`，以及内容回归测试 `tests/content/deep-ch24-28.test.mjs`。重点是容量契约不变量、状态不变量、HTTP/1.1 报文定界、RV64I 字段解码与非阻塞双游标。来源与错误边界见 [24–28 复核账本](../evidence/24-28-deep-review.md)。本批未新增独立 workflow，浏览器验收以本地运行日志为准，未执行时记为未验证。

## 2026-11-22 · 第 01–04 章基础章深度推演

为第 01–04 章补充与 05–28 一致的 `deep-study` 独立推导：原创内联 SVG 与纯标准库确定性模型 `examples/deep-ch01-04.py`，回归测试 `tests/content/deep-ch01-04.test.mjs`。四节分别处理可执行文件段与 `.bss` 的文件后端差异、有符号溢出的相加前边界判断、`0.1` 的 binary64 精确分数与次正规边界、以及 System V 与 Windows x64 的整数参数寄存器差异。来源见各章 `docs/evidence/NN.json`；浏览器验收以仓库内真实 HTTP 服务的本地运行日志为准，未执行时记为未验证。

## 2026-11-26 · 第 05–08 章第三轮深度推演

在 05–12 第二轮基础上，为 05–08 各追加一节 `deep-NNb` 深描、一张原创图与纯标准库确定性模型 `examples/deep-ch05-08-b.py`，回归测试 `tests/content/deep-ch05-08-b.test.mjs`。四节分别处理条件传送的求值差异、变参寄存器保存区与 `%al`、无符号边界检查的宽度反例、`popq rA` 写回顺序。来源、断言与不能外推的边界见 [05–08 第三轮账本](../evidence/05-08-deep-review.md)。浏览器验收以本地真实 HTTP 服务日志为准，未执行时记为未验证。

## 2026-11-26 · 第 09–12、19–21 章第四轮深度推演

在第二轮基础上，为 09、10、11、12 各追加 `deep-NNb` 深描、一张外链 SVG（`chapter-assets/NN-deep2.svg`）与纯标准库确定性模型 `examples/deep-ch09-12-b.py`，回归测试 `tests/content/deep-ch09-12-b.test.mjs`；为 19、20、21 各追加 `deep-NNb` 深描、一张内联 SVG 与模型 `examples/deep-ch19-23-b.py`，回归测试 `tests/content/deep-ch19-23-b.test.mjs`。

七节分别处理：转发优先级（选最新在途生产者）、向量宽度下的 CPE 下界、写策略的内存流量、LRU 替换轨迹、非阻塞输出游标、HTTP/1.1 报文定界（RFC 9112 §6）与 LT/ET 就绪语义。来源、断言与不能外推的边界见 [09–12 账本](../evidence/09-12-deep-review.md) 与 [19–21 账本](../evidence/19-21-deep-review.md)。浏览器验收以本地真实 HTTP 服务 + Chromium 在 1440/390/360px 运行；未执行时记为未验证。

## 2026-11-26 · 第 13–18 章第三轮（重定位 / 信号 / 分页 / 分配）

在 13–18 第二轮基础上，为每章追加一节 `deep-NNb`、一张外链图 `chapter-assets/NN-deep2.svg` 与确定性模型 `examples/deep-ch13-18-b.py`（含 16b 可编译示例 `examples/deep-ch13-18-b-signals.c`），并新增回归测试 `tests/content/deep-ch13-18-b.test.mjs`。六节分别处理：PLT32 与 PC32 的差异矩阵、GOT 槽的 RELATIVE/GLOB_DAT/JUMP_SLOT/IRELATIVE 分类、OFD 共享与 FD_CLOEXEC、传统信号合并 vs 实时信号排队、四级与五级分页及大页偏移、分配器抽象与内核映射/物理页的区分。来源、断言与不能外推的边界见 [13–18 账本](../evidence/13-18-deep-review.md)。

为保留既有数量断言，`scripts/verify-snippets.py` 的每章 SVG 计数由 4 调整为 5，并校验尾部两个图依次为 `NN-deep.svg`、`NN-deep2.svg`，未删除旧断言。浏览器验收以本地真实 HTTP 服务 + Chromium 在 1440/390/360px 运行；未执行时记为未验证。

## 2026-11-27 · 第 22–28 章第五轮（原子内存序 / 取消 / 位运算 / Cache / HTTP 新鲜度 / SIMT / 半关闭）

在既有深描基础上，为 22–28 各追加一节 `deep-NNb`、一张外链图 `chapter-assets/NN-deep2.svg` 与纯标准库确定性模型 `examples/deep-ch22-28-b.py`，新增回归测试 `tests/content/deep-ch22-28-b.test.mjs`。七节分别处理：C11 原子内存序的发布/订阅规则、POSIX 延迟取消与清理处理器、Data Lab 逻辑右移的掩码与移位未定义行为、组相联 Cache 的命中/驱逐复算、RFC 9111 新鲜度与当前年龄、SIMT 分支发散的分遍执行、以及半关闭与 `EPIPE`。来源、断言与不能外推的边界见 [22–28 账本](../evidence/22-28-deep-review.md)。浏览器验收以本地真实 HTTP 服务 + Chromium 在 1440/390/360px 运行；未执行时记为未验证。

## 当前页面工程基线

- 入口：`index.html` 与 `01.html`–`28.html`；顺序和元数据由 `courses.json` 约束。
- 兼容性：保留公开路径、已有锚点、SVG 和实验资源；`docs/.vitepress` 不是当前站点构建入口。
- 统一项：每个 HTML 页的描述、canonical、可缩放 viewport、两条语义化跨章链接；缺少导航的页面补原生 HTML TOC；窄屏章节栏优化为可横向滚动。
- 校验：`npm test` 中的 `course-wide.test.mjs` 覆盖上述可自动断言的结构；`npm run build` 检查 Pages 输出资源。

## 按章工作记录与下一轮深度方向

| 章 | 本轮内容工作 | 下一轮优先逐条核对 |
| --- | --- | --- |
| 01 | 统一元数据、跨章桥；原交互与路线保留；新增段/`.bss` 文件后端 deep-study（`examples/deep-ch01-04.py 01`） | 编译/加载/运行示例的命令预期与平台差异 |
| 02 | 新增整数提升和 uint8_t 中间表达式推导；新增有符号溢出相加前判断 deep-study（`examples/deep-ch01-04.py 02`） | C 标准/编译器选项下有符号溢出诊断 |
| 03 | 新增 binary64 ULP 可运行计算；新增 `0.1` 精确分数与次正规边界 deep-study（`examples/deep-ch01-04.py 03`） | 舍入模式与非规格化边界 |
| 04 | 新增 LEA 与 MOV 的地址/解引用对照；新增 System V 与 Windows x64 参数寄存器 deep-study（`examples/deep-ch01-04.py 04`） | System V ABI 与 Windows x64 差别 |
| 05 | 新增页内目录、跨章桥；第三轮 `deep-05b` 条件传送会无条件求值两路（`examples/deep-ch05-08-b.py 05b`） | 条件码、cmov 与未定义行为案例 |
| 06 | 新增页内目录、跨章桥；第三轮 `deep-06b` 变参寄存器保存区与 `%al`（`06b`） | 栈对齐、红区与变参 |
| 07 | 新增页内目录、跨章桥；第三轮 `deep-07b` 无符号边界检查与宽度反例（`07b`） | 对齐与边界检查、ROP 安全讨论 |
| 08 | 新增页内目录、跨章桥；第三轮 `deep-08b` `popq %rsp` 写回顺序（`08b`） | Y86-64 编码表与 SEQ 控制信号 |
| 09 | 新增页内目录、跨章桥；第四轮 `deep-09b` 转发优先级选最新在途生产者（`examples/deep-ch09-12-b.py 09b`） | load-use 冒险与暂停/转发周期 |
| 10 | 新增页内目录、跨章桥；第四轮 `deep-10b` 向量宽度下的 CPE 下界（`10b`） | CPE/吞吐量、基准可复现性 |
| 11 | 新增页内目录、跨章桥；第四轮 `deep-11b` 写策略流量计数（`11b`） | 存储山测量、SSD 对比的版本边界 |
| 12 | 新增页内目录、跨章桥；第四轮 `deep-12b` S/E/B 拆分与 LRU 替换轨迹（`12b`） | S/E/B 地址拆分及替换轨迹 |
| 13 | 引言、自绘图和相对位移 `S+A-P` 算例、ELF 目标文件检查脚本 | PLT32 与 PC32 在不同编译器链接方式的实例矩阵 |
| 14 | 引言、自绘图和相对装载重定位 `B+A`、PLT/GOT 绑定边界 | TLS/IFUNC 与全 RELRO 选项在多平台差异 |
| 15 | 引言、自绘图和 COW / OFD 共享偏移、`fork/waitpid` 同步实验 | 多线程 fork 限制及并发文件访问、exec FD_CLOEXEC |
| 16 | 新增信号丢失唤醒推导、sigsuspend 掩码原子切换和 C 程序 | 多线程信号归属和实时信号排队语义 |
| 17 | 新增四级页表 9+9+9+9+12 字段拆分与翻译分类图 | 5 级分页、大页和访问权限故障诊断 |
| 18 | 新增固定池碎片/合并推导、安全 realloc 和 C 程序 | 多 arena 分配器与实际 RSS、mmap 策略测量 |
| 19 | 新增短读/EOF 教学图、真实管道实验与 POSIX 返回值矩阵；第四轮 `deep-19b` 非阻塞输出游标（`19b`） | 非阻塞 I/O 多种 fd、信号打断条件和 robust RIO 资源释放 |
| 20 | 新增 4B 网络序长度 + HELLO 自定义分帧、socketpair 模型和边界检查；第四轮 `deep-20b` HTTP/1.1 定界（`20b`） | RFC 9112 的 chunked、重叠 Content-Length 安全案例 |
| 21 | 新增 poll 下 EOF 就绪、连接状态转换与真实管道校验；第四轮 `deep-21b` LT/ET 就绪（`21b`） | epoll LT/ET、公平读取预算与 CPU 工作移交 |
| 22 | 新增锁内计数的完整不变量、四线程各 10000 次同步验证 | C11 原子内存序和锁竞争测量 |
| 23 | 新增容量 2 条件队列、等待谓词、关闭广播和排空可运行例子 | 线程池多生产者、多消费者与取消语义 |
| 24 | 新增容量契约不变量、数组退化与 `size_t` 乘法回绕模型 | Bomb/Attack 特定实例的合法环境复现 |
| 25 | 新增教学缓存重放与相邻空闲块合并断言 | Cache/Malloc/Shell Lab 官方评分器对照 |
| 26 | 新增 RFC 9111 共享缓存四道关 + RFC 9112 报文定界模型 | Vary、Authorization、老化与 revalidation 实测 |
| 27 | 新增 Roofline 单位对照 + RV64I 字段编解码模型 | eBPF、CXL 版本与具体硬件验证 |
| 28 | 新增短写/连接所有权不变量表 + 非阻塞双游标与代际号模型 | ET epoll、fd 复用与关闭竞态实验 |

## 验收顺序

1. 运行 `npm test` 与 `npm run build`；确认 `dist/course-improvements.css` 及 29 个 HTML 入口。
2. 浏览器分别检查 1440px、390px、360px 宽度：无横向溢出、目录可滚动、图像和 MathML 可读。
3. 对每个含交互按钮的章节，至少操作一个非默认状态并观察输出；检查控制台错误。
4. 针对第 02/03/04/26/27/28 章重新核对示例与引用，记录条件和实际输出。
5. 提交 PR、检查 Actions 和页面部署记录，再更新“已上线”状态。

**说明：**上述技术复核条目是待执行的审查计划，不代表本轮已完成实机测量或浏览器截图。
