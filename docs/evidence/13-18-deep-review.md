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
