# 13–18 章第二轮深度推导：证据、模型和实验边界

本记录仅涵盖这次新增的推导，不代表对六篇旧页面的每个历史事实做过全面独立复核。图片是原创教学示意而非硬件/内核转储。

| 章 | 核心可证伪论断 | 依据 | 检验与限制 |
| --- | --- | --- | --- |
| 13 | 在给定 S=0x401100、P=0x4010c1、A=-4 时，PC32 位移是 0x3b，小端指令为 E8 3B 00 00 00 | [System V AMD64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI/)、[GNU readelf](https://sourceware.org/binutils/docs/binutils/readelf.html) | `python3 examples/deep-ch13-18-models.py 13`；工具链可能产生 PLT32，不保证所有调用 PC32 |
| 14 | RELATIVE 重定位按装载基址 B 与加数 A 计算 B+A；这不等于导入函数符号解析 | [glibc 动态链接器安全章节](https://www.sourceware.org/glibc/manual/latest/html_node/Dynamic-Linker-Hardening.html)、[ld.so(8)](https://man7.org/linux/man-pages/man8/ld.so.8.html) | `python3 examples/deep-ch13-18-models.py 14`；`readelf -rW` 检查编译器选择，不预设每个条目类型 |
| 15 | fork 后用户变量独立，父子继承的 FD 可引用同一 OFD 并共享偏移，waitpid 可回收子进程终止状态 | [fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)、[open(2)](https://man7.org/linux/man-pages/man2/open.2.html)、[waitpid(2)](https://man7.org/linux/man-pages/man2/waitpid.2.html) | 模型 `15`；实际 POSIX C fork 子进程先读 AB，pipe 通知父进程再读 CD，waitpid 检查退出码 7；不依赖调度 |
| 16 | check → pause 存在 lost wakeup；sigprocmask + sigsuspend 的原子换掩码与睡眠能够避免该间隙 | [sigsuspend(2)](https://man7.org/linux/man-pages/man2/sigsuspend.2.html)、[signal-safety(7)](https://man7.org/linux/man-pages/man7/signal-safety.7.html) | 模型 `16` 与实际 POSIX C pending SIGUSR1、sigsuspend；不验证可能死锁的坏路径，不推广到所有多线程信号安排 |
| 17 | VA 0x00007f123456789a 在四级 4KiB 模型中索引是 254/72/418/359，偏移 0x89a | [Linux Page Tables](https://www.kernel.org/doc/html/latest/mm/page_tables.html)、[Intel SDM](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) | 模型 `17`；PPN 0x2a7 是虚构的教学输入，不是实际进程物理地址 |
| 18 | 固定池 64F/32A/64F/32B/32F 总空闲 160、最大连续块 64；释放 A 可合并为 160F | [malloc(3)](https://man7.org/linux/man-pages/man3/malloc.3.html) | 模型 `18` 与安全非零长度 realloc C 程序；不预测 glibc 的真实 arena、RSS 或调用次数 |

## 一次运行所有验证

```bash
python3 examples/deep-ch13-18-models.py all
cc -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror -pedantic \
   examples/deep-ch13-18-posix.c -o /tmp/deep-posix
/tmp/deep-posix fork
/tmp/deep-posix signal
/tmp/deep-posix realloc
npm test
npm run build
```

在 Linux x86-64 还可执行：

```bash
cc -std=c11 -O0 -c examples/deep-ch13-18-reloc.c -o /tmp/deep-reloc.o
readelf -rW /tmp/deep-reloc.o
objdump -dr /tmp/deep-reloc.o
cc -std=c11 -O0 -fPIC -shared examples/deep-ch13-18-shared.c -o /tmp/deep-shared.so
readelf -rW /tmp/deep-shared.so
```

浏览器自动化在 1440/390/360px 宽度检查所有 6 个网页的原交互、新 SVG 加载、焦点与页面宽度；其结果与截图必须根据实际工作流报告记录，不由此文档预断。

## 追加：13–18 章第三轮（`deep-NNb`）重定位/信号/分页/分配的逐条校验

本轮在 13–18 各追加一节 `deep-NNb`、一张外链图 `chapter-assets/NN-deep2.svg` 与确定性模型 `examples/deep-ch13-18-b.py`（新增 16b 的可编译示例 `examples/deep-ch13-18-b-signals.c`）。下表只记录本轮新增的论断与检验方式，不覆盖旧页面的全部历史断言。

| 章 | 核心可证伪论断 | 依据 | 检验与限制 |
| --- | --- | --- | --- |
| 13b | PLT32 的通式为 L+A−P；当链接器判定符号不可抢占时可退化为符号自身地址，因此不能把 PLT32 与 PC32 断言为普遍等价或普遍不同 | [System V AMD64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI/)、[GNU readelf](https://sourceware.org/binutils/docs/binutils/readelf.html) | `python3 examples/deep-ch13-18-b.py 13b`；L=0x401030、S=0x401100、P=0x4010c1、A=-4 时 R_plt=-0x95 与 R_pc=0x3b 相差 L-S |
| 14b | GOT 槽并非都为 B+A：RELATIVE=B+A，而 GLOB_DAT/JUMP_SLOT 写入符号查找得到的 S，IRELATIVE 还需先调用 resolver | [System V AMD64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI/)、[ld.so(8)](https://man7.org/linux/man-pages/man8/ld.so.8.html) | `python3 examples/deep-ch13-18-b.py 14b`；B1=0x70000000 时 RELATIVE 随 B 变、S=0x72100000 不随 B 变；数值为固定算例 |
| 15b | 继承的 fd 指向同一 OFD 故共享偏移；重新 open 建新 OFD 则偏移独立；FD_CLOEXEC 的 fd 在 exec 后关闭 | [open(2)](https://man7.org/linux/man-pages/man2/open.2.html)、[fcntl(2)](https://man7.org/linux/man-pages/man2/fcntl.2.html) | 模型 `15b`；用 pipe/waitpid 同步，不靠打印或延时判断顺序 |
| 16b | 传统信号多次产生合并为一个 pending，实时信号按信号号 FIFO 排队；队列有 RLIMIT_SIGPENDING 上限 | [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html)、[sigqueue(2)](https://man7.org/linux/man-pages/man2/sigqueue.2.html)、[pthread_sigmask(3)](https://man7.org/linux/man-pages/man3/pthread_sigmask.3.html) | 模型 `16b` 与 C 示例 `queue` 模式；示例在 macOS 上实时部分输出 rt-skip，不把某实现的队列长度当标准常量 |
| 17b | 分页级数、VA 宽度、基页大小必须同时声明：四级=4×9+12（48 位），五级加一层 PML5=5×9+12（57 位）；大页在 PD/PDPT 提前停止遍历 | [Linux Page Tables](https://www.kernel.org/doc/html/latest/mm/page_tables.html)、[Intel SDM](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) | 模型 `17b` 用已知字段构造并回解 57 位地址；示例中的页框号为教学占位值，非真实物理页 |
| 18b | malloc 成功不等于占用等量物理内存、free 不保证立即 munmap/降 RSS；分配器用 arena/bins 并对大请求可能走 mmap（阈值实现定义） | [malloc(3)](https://man7.org/linux/man-pages/man3/malloc.3.html)、[GNU libc Memory Allocation](https://sourceware.org/glibc/manual/latest/html_node/Memory-Allocation.html) | 模型 `18b` 只验证乘法溢出预检与失败 realloc 的旧指针有效性；不给出任何实测内存数字 |

本轮验证命令：`python3 examples/deep-ch13-18-b.py all`、`cc -std=c11 -Wall -Wextra -Werror -pedantic examples/deep-ch13-18-b-signals.c && /tmp/x queue`、`npm test`。浏览器部分以本地真实 HTTP 服务 + Chromium 在 1440/390/360px 运行；未执行时记为未验证。
