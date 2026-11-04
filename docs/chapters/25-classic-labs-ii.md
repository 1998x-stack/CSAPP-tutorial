---
title: "经典Lab实战(II)"
description: "Cache Lab缓存模拟 · Shell Lab进程管理 · Malloc Lab分配器"
outline: [2, 3]
---

# 第二十五章：经典Lab实战(II)——Cache/Shell/Malloc

如果说前三个 Lab 是让你"看懂"计算机系统，那 Cache、Shell、Malloc 这三个 Lab 就是让你"构建"计算机系统。你要亲手写一个缓存模拟器、实现一个 Unix Shell 的核心功能、以及设计一个动态内存分配器——每一个都是真实系统组件的缩影。当你完成这三个 Lab 时，你写的代码已经触及了计算机系统的三个核心模块：存储层次、进程管理、内存管理。

这其中的每个 Lab 都有实际的工程难度。不少同学在 Cache Lab 的 Part B 卡了一周，在 Shell Lab 被信号竞态折磨得怀疑人生，在 Malloc Lab 为了提升 1% 的利用率而反复调整策略——但正是这种"折磨"让你从"会用"进阶到"会设计"。

## 25.1 Cache Lab——手写缓存模拟器

Cache Lab 分为两个部分。Part A 要求你实现一个缓存模拟器，能模拟组相联缓存的行为——给定一个内存访问轨迹文件，输出总的 hits、misses 和 evictions 次数。Part B 则要求你通过分块（blocking）技术优化矩阵转置，最小化 cache miss。

**Part A: 模拟器核心逻辑**

```asm
// 简化的缓存模拟器核心（C 语言）
#define MAX_LINES 64

typedef struct {
    int valid;          // 有效位
    int tag;            // 标记位
    int lru_counter;    // 用于 LRU 替换
} cache_line_t;

typedef struct {
    cache_line_t *lines;
    int E;              // 每组行数（associativity）
} cache_set_t;

cache_set_t *cache;
int hits = 0, misses = 0, evictions = 0;
int lru_clock = 0;

void access_cache(unsigned long address) {
    // 从地址中提取 set index 和 tag
    int set_idx = (address >> b) & ((1 << s) - 1);
    unsigned long tag = address >> (b + s);

    cache_set_t *set = &cache[set_idx];
    int empty = -1, lru_idx = 0;

    for (int i = 0; i < set->E; i++) {
        if (set->lines[i].valid && set->lines[i].tag == tag) {
            hits++;  // Cache hit: 找到匹配的行
            set->lines[i].lru_counter = ++lru_clock;
            return;
        }
        if (!set->lines[i].valid) empty = i;
        if (set->lines[i].lru_counter < set->lines[lru_idx].lru_counter)
            lru_idx = i;  // 追踪最久未使用的行
    }

    misses++;  // Cache miss: 需要加载行
    int victim = (empty != -1) ? empty : (evictions++, lru_idx);
    set->lines[victim].valid = 1;
    set->lines[victim].tag = tag;
    set->lines[victim].lru_counter = ++lru_clock;
}
```

**Part B: 矩阵转置优化**

矩阵转置的朴素实现中，内层循环按列访问源矩阵、按行写入目标矩阵——访问模式与缓存布局不匹配，导致大量 conflict miss。解决思路是**分块（blocking/tiling）**：把矩阵分成小块，使每块能完全装入缓存，块内局部性最大化。

- **32×32**：用 8×8 分块，每块 64 个 int（256 字节），正好能装入 32 字节/行 × 8 行的缓存中。miss 率从 ~50% 降到 ~5%。
- **64×64**：更棘手，因为 64×64 矩阵的同一列元素会映射到同一缓存组。需要用 4×4 分块 + 对角线重排（diagonal copying）的技巧来压住 miss。
- **61×67**：非 2 的幂的矩阵，conflict miss 的规律更难预测。需要尝试不同分块大小（16×16、8×8、4×4），用自动测试脚本寻找最优解。

::: info
**分块的核心洞察**：Cache Lab 教会你最重要的一个道理——**算法的计算复杂度一样，不代表性能一样**。两个时间复杂度同为 O(n²) 的转置实现，因为缓存访问模式不同，实际运行时间可能相差 5-10 倍。这就是为什么当你的程序性能瓶颈在内存而非 CPU 时，优化算法步骤数量不如优化数据访问模式有效。
:::

## 25.2 Shell Lab——实现 Unix Shell

Shell Lab 要求你实现 `tsh`（Tiny Shell），一个支持作业控制的简易 Unix Shell。你需要处理以下核心机制：

- **内置命令**：`quit`（退出 shell）、`jobs`（列出所有作业）、`bg `（后台继续运行）、`fg `（前台继续运行）。
- **前台/后台作业管理**：用 `&` 后缀启动后台作业，否则为前台作业。前台作业独占终端，后台作业在后台执行。维护一个作业列表（job list），记录每个作业的 PID、JID、状态。
- **SIGCHLD 信号收割**：子进程终止时向父进程发送 SIGCHLD。父进程的信号处理程序调用 `waitpid` 回收子进程，并更新作业状态。
- **信号阻塞防止竞态**：在 `fork` 之后、将子进程加入 job list 之前，必须阻塞 SIGCHLD，否则子进程可能在父进程添加作业前就终止并被回收，导致作业被添加到列表两次或出现 dangling 条目。

| 信号 | 默认行为 | 在 Shell Lab 中的处理 |
| --- | --- | --- |
| **SIGCHLD** | 忽略 | 调用 `waitpid(-1, &status, WNOHANG)` 循环收割已终止的子进程，更新作业状态 |
| **SIGINT**（Ctrl+C） | 终止前台进程 | 将 SIGINT 转发到前台作业的进程组 |
| **SIGTSTP**（Ctrl+Z） | 挂起前台进程 | 将 SIGTSTP 转发到前台作业的进程组，标记为 Stopped |

::: tip
**fork+exec+signal 的竞态陷阱**：Shell Lab 最常见的 BUG 是信号竞态——你在 `fork()` 后、`addjob()` 前收到了子进程的 SIGCHLD。解决方法是：在 fork 之前用 `sigprocmask(SIG_BLOCK, &mask, NULL)` 阻塞 SIGCHLD，把 addjob 做完之后再用 `sigprocmask(SIG_UNBLOCK, &mask, NULL)` 解除。这期间累积的 SIGCHLD 会在解除后统一递送。这是 Unix 信号编程的经典模式——**先屏蔽信号、做关键操作、再解除屏蔽**。
:::

## 25.3 Malloc Lab——动态内存分配器

Malloc Lab 让你实现自己的 `malloc`、`free` 和 `realloc`。你面对一个内存堆区域（通过 `mem_sbrk` 扩展），需要设计数据结构来管理空闲块和已分配块，目标是最大化"吞吐量 × 内存利用率"这个综合评分。

以下是几种常见的设计方案，性能和复杂度逐步递增：

- **隐式空闲链表（Implicit Free List）**——最简单的方案。每个块有头部和脚部（boundary tag），存储块大小和分配位。遍历链表查找空闲块（first-fit / next-fit / best-fit）。释放时检查相邻块是否空闲，合并。优点是实现简单，缺点是分配时间与空闲块数量成 O(n) 关系。
- **显式空闲链表（Explicit Free List）**——在空闲块中嵌入前驱和后继指针（利用空闲块的数据区，反正它没被使用），形成一个空闲块的双向链表。分配时只需遍历空闲链表，速度更快。通常配合 LIFO（后进先出）策略：新释放的块插到链表头部，分配时也从头部开始 first-fit。
- **分离适配（Segregated Fit）**——维护多个大小类别的空闲链表（如 16 字节、32 字节、64 字节……4096 字节、更大）。分配时直接查对应大小类的链表。这是 glibc ptmalloc2 的核心策略，时间复杂度近乎 O(1)。评分最高的方案通常采用这种设计。

```text
// 隐式空闲链表的边界标记（边界标记法）
// 每个块的头尾各有一个 size|alloc 标记，方便合并

typedef struct {
    int header;                // [31:3] 块大小 | [0:1] 分配位
    /* 数据区从这里开始 */
} block_t;

#define GET_SIZE(p)   (*(int *)(p) & ~7)
#define GET_ALLOC(p)  (*(int *)(p) & 1)
#define HDRP(bp)      ((char *)(bp) - 4)       // 头部地址
#define FTRP(bp)      ((char *)(bp) + GET_SIZE(HDRP(bp)) - 8)  // 脚部地址
#define NEXT_BLKP(bp) ((char *)(bp) + GET_SIZE((char *)(bp) - 4))

void *malloc(size_t size) {
    // first-fit: 遍历堆，找第一个足够大的空闲块
    // 如果找到：分割（块太大则分裂成两个），标记已分配
    // 如果没找到：调用 mem_sbrk 扩展堆
}

void free(void *bp) {
    // 标记为空闲
    // 检查相邻块，立即合并（immediate coalescing）
}
```

::: info
**真实世界的影响**：Malloc Lab 不是纸上谈兵。Linux 上默认的 glibc **ptmalloc2**（基于 Doug Lea 的 dlmalloc）和 Facebook 开源的 **jemalloc**（基于 FreeBSD 的 allocator，现用于 Rust、Redis、MariaDB）之间的性能差距可能在特定负载下达到 2-10 倍。jemalloc 的核心优化包括：每个线程一个本地缓存（避免锁竞争）、arena 分区（减少内存碎片）、以及更精细的 size class 划分。理解 Malloc Lab 的原理后，你就能明白为什么 Redis 切换到 jemalloc 后内存碎片率从 15% 降到了 3%。如果你对内存分配器有深入兴趣，还可以研究 Google 的 **TCMalloc**（Thread-Caching Malloc），它在多线程场景下有更极致的性能。
:::

我们已经走过了 CSAPP 七个经典 Lab 中的六个，还剩下最后一个——Proxy Lab。下一章我们将学习如何实现一个并发 HTTP 代理服务器，把网络编程、并发控制、系统 I/O 的知识熔于一炉。这是对你这 25 章以来所有知识的终极考验，也是最接近真实生产环境的一次演练。
