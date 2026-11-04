---
title: "链接——动态链接"
description: "共享库(.so)机制 · GOT与PLT延迟绑定 · 位置无关代码(PIC) · LD_PRELOAD插桩技术"
outline: [2, 3]
---

# 第十四章：链接——动态链接

上一章我们学习了静态链接——链接器把多个 .o 文件和 .a 静态库打包成一个独立的可执行文件。静态链接有很明显的缺陷：每个可执行文件都自带一份 `printf` 的代码，100 个程序就有 100 份 printf 的副本，浪费磁盘空间和内存。更糟糕的是，如果 libc 发现了一个安全漏洞需要修复，你得重新链接所有依赖它的程序——这简直是一场噩梦。

动态链接（Dynamic Linking）就是来解决这些问题的。它的核心思想是：把链接过程推迟到程序加载时甚至运行时进行。共享库（Shared Library，Linux 上为 .so 文件，Windows 上为 .dll 文件）在磁盘和内存中都只有一份物理副本，被所有程序共享。这一章，我们深入这个机制的核心——看看 GOT、PLT、PIC 这些听起来很高深的概念到底是什么。

## 14.1 共享库的动机

我们从一个实际的对比开始：

| 特性 | 静态链接（.a） | 动态链接（.so） |
| --- | --- | --- |
| 可执行文件大小 | 大（包含所有库代码的副本） | 小（只包含引用信息） |
| 磁盘空间占用 | 每个程序一份副本 | 所有程序共享一份 |
| 运行时内存占用 | 每个进程一份副本 | 共享库代码在物理内存中只有一份 |
| 库更新 | 需要重新链接 | 替换 .so 文件即可（重启程序） |
| 启动速度 | 快（地址已固定） | 稍慢（需要运行时重定位 + 符号解析） |
| 版本兼容性 | 不会意外升级 | 可能遇到 "DLL Hell" |
| 编译方式 | `gcc -static main.c` | `gcc -fPIC -shared lib.c -o lib.so` |

在 Linux 上，libc 默认就是以动态库（`libc.so.6`）形式提供的。试试这个命令：

```bash
$ ldd /bin/ls
    linux-vdso.so.1 (0x00007ffd3a5c0000)
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f8a1c400000)
    /lib64/ld-linux-x86-64.so.2 (0x00007f8a1c600000)
```

`ldd` 命令显示一个可执行文件依赖的所有共享库。你会发现，就连最简单的 `ls` 命令也依赖多个共享库。这就是现代 Linux 系统的常态——几乎所有程序都在使用动态链接。

## 14.2 GOT 与 PLT

动态链接面临一个根本性难题：编译器在编译 main.c 时，并不知道 `printf` 在共享库中的地址——因为共享库的加载地址是在运行时才确定的（地址空间布局随机化 ASLR 进一步确保这一点）。那么，编译器如何生成对 printf 的函数调用指令？

答案就是 **GOT（全局偏移表）** 和 **PLT（过程链接表）** 这两个精巧的机制。

**PLT（过程链接表）**

PLT 是放在 `.text` 节中的一段小代码桩（stub）。每个外部函数在 PLT 中有一个条目。PLT 条目的功能如下：

```asm
# PLT 条目示例（对于 printf 函数）
printf@plt:
    jmp *printf@GOT        # 跳转到 GOT 中记录 printf 地址的位置
    push $index             # 如果第一次调用，把函数索引压栈
    jmp resolver            # 跳转到动态链接器解析函数
```

**GOT（全局偏移表）**

GOT 是放在 `.data` 节中的一个地址数组。每个外部函数（或全局变量）在 GOT 中有一个 8 字节条目。初始时，GOT 条目指向 PLT 中对应的 push 指令——这实现了**延迟绑定（Lazy Binding）**：

1. **第一次调用**：通过 PLT 跳转到 GOT，GOT 指向 PLT 的下一行（push index），然后跳转到动态链接器中的函数解析器（resolver）。解析器找到 printf 的实际地址，更新 GOT 条目，然后调用 printf。
1. **后续调用**：再次调用 printf 时，PLT 跳转到 GOT，这次 GOT 已经指向 printf 的真实地址——直接执行 printf，无需再次解析。

用图来表示就是：

```text
第一次调用:  main → printf@plt → GOT(初始) → push index → resolver → 找到printf → GOT=printf地址 → 执行printf
后续调用:   main → printf@plt → GOT(已更新) → 直接执行printf
```

这种"第一次慢，后面快"的设计就是**延迟绑定（Lazy Binding）**——只在函数第一次被调用时才解析其地址。它的好处很明显：

- 启动速度更快（不需要在加载时解析所有函数）
- 如果某个函数在整个程序运行期间从未被调用，就永远不需要解析它

::: tip
**相关环境变量**：你可以用 `LD_BIND_NOW=1` 来禁用延迟绑定——让动态链接器在加载时就解析所有符号。这会增加启动时间但消除了"第一次调用慢"的问题。对于实时性要求高的程序可能有意义。你也可以用 `LD_DEBUG=all` 来观察动态链接器的详细工作过程，非常有利于调试和理解。
:::

## 14.3 位置无关代码（PIC）

共享库有一个特殊要求：它必须能在内存中的**任何地址**加载。这在两个层面上有必要：

- ASLR（地址空间布局随机化）要求库的基地址每次加载可能不同
- 不同的程序可能把库加载到不同的地址（因为内存布局不同）

传统的非 PIC 代码中，对全局变量和函数的访问都使用绝对地址。如果把这样的代码编译成共享库，链接器必须在加载时修改代码中的地址——但代码段（.text）通常是只读的，而且被多个进程共享，不能修改。这就是矛盾所在！

解决办法是 **PIC（Position-Independent Code，位置无关代码）**。PIC 的核心技巧是**通过 PC 相对寻址来访问 GOT**。GOT 放在数据段中，每个进程有自己的 GOT 副本（可写），所以可以在运行时修改。代码段通过 GOT 间接访问数据，而 GOT 的地址通过 PC 相对寻址获得——无论代码加载到哪个地址，PC 相对偏移量都是固定的。

来看编译出的代码差异：

```asm
# 非 PIC 版本（需要重定位）
movq $0x605010, %rax      # 直接使用绝对地址访问全局变量
movq (%rax), %rdx

# PIC 版本（位置无关）
call next                  # 获取当前 PC
next: popq %rax           # %rax = next 的运行时地址
addq $GOT_offset, %rax   # %rax = GOT 的地址
movq (%rax), %rdx         # 通过 GOT 间接访问全局变量
```

当然，实际中编译器不会用 `call/pop` 这么原始的方式——它使用更高效的技巧（如 x86-64 的 RIP 相对寻址）来计算 GOT 地址。编译时加 `-fPIC` 选项即可生成位置无关代码。

::: info
**PIC 的性能代价**：PIC 并非没有代价。间接寻址（通过 GOT）相比直接寻址多了几次访存操作，通常导致 5-10% 的性能损失（在 GOT 命中的情况下）。这就是为什么在性能关键的场景中，有时会选择静态链接。但大多数情况下，共享库节省的内存和多进程共享的好处远大于这点性能损失。在 x86-64 平台上，由于 RIP 相对寻址的引入，PIC 的开销已经大大降低，几乎可以忽略不计。
:::

## 14.4 LD_PRELOAD 库插桩

动态链接的强大之处不仅在于运行时加载，还在于提供了**拦截和替换**函数的能力。这通过 `LD_PRELOAD` 环境变量实现：你可以指定一个共享库，让动态链接器在所有其他库**之前**加载它。由于符号解析顺序规则，LD_PRELOAD 库中的符号会覆盖其他库（包括 libc）中的同名符号。

来看一个实战例子——用 LD_PRELOAD Hook malloc 来统计内存使用：

```c
/* memtrace.c — LD_PRELOAD 拦截 malloc/free */
#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>
#include <stdlib.h>

static int malloc_count = 0;
static size_t total_bytes = 0;

void *malloc(size_t size) {
    static void *(*real_malloc)(size_t) = NULL;
    if (!real_malloc)
        real_malloc = dlsym(RTLD_NEXT, "malloc");  // 找到真正的 malloc

    void *ptr = real_malloc(size);
    malloc_count++;
    total_bytes += size;

    // 记录每次分配的信息（生产环境要加锁！）
    fprintf(stderr, "[MEMTRACE] malloc(%zu) = %p (total=%zu, count=%d)\n",
            size, ptr, total_bytes, malloc_count);
    return ptr;
}

void free(void *ptr) {
    static void (*real_free)(void *) = NULL;
    if (!real_free)
        real_free = dlsym(RTLD_NEXT, "free");

    fprintf(stderr, "[MEMTRACE] free(%p)\n", ptr);
    real_free(ptr);
}
```

```bash
# 编译共享库
$ gcc -shared -fPIC -o libmemtrace.so memtrace.c -ldl

# 使用 LD_PRELOAD 拦截任何程序的 malloc/free
$ LD_PRELOAD=./libmemtrace.so ./my_program arg1 arg2
# 运行输出中会混入 malloc/free 的追踪信息！
```

这个例子用 `dlsym(RTLD_NEXT, "malloc")` 找到了"下一个"malloc——也就是 libc 中的真正 malloc，然后包装它。LD_PRELOAD 的强大之处在于：你不需要修改目标程序的代码甚至不需要重新编译，就能介入它的内存分配、文件操作、网络请求等。

::: info
**LD_PRELOAD 的更多用法**：

                **内存错误检测**：拦截 malloc/free，在分配的内存前后添加"保护区域"，检测越界写入和释放后使用（类似 Electric Fence 和 AddressSanitizer 的原理）
                **性能分析**：拦截 malloc/free，记录分配热点（类似于 valgrind 的 massif 工具）
                **兼容性修复**：拦截存在 bug 的库函数，提供修正版本
                **功能扩展**：拦截 open/read/write 添加透明加密、压缩功能

注意：LD_PRELOAD 对 setuid/setgid 程序不起作用（安全原因）。并且滥用 LD_PRELOAD 可能导致意外行为——尤其是当你拦截的函数内部又调用了被拦截的函数时（死循环陷阱）。
:::

这一章我们完成了链接部分的"双拼"——从静态链接到动态链接。你理解了共享库的优势（节省空间、独立更新），掌握了 GOT+PLT+延迟绑定的工作机制，区分了 PIC 和非 PIC 代码，最后还学会了用 LD_PRELOAD 进行库插桩这一实战利器。从下一章开始，我们将进入一个全新的主题——异常控制流（Exceptional Control Flow, ECF）。你写的每个程序都会涉及系统调用、信号处理、进程控制——这些都属于 ECF 的范畴。理解了 ECF，你就理解了操作系统的"灵魂"。
