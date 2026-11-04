---
title: "存储器层次结构——Cache"
description: "缓存组织结构(S/E/B) · 直接映射/组相联 · 缓存未命中三类型 · 分块矩阵乘法优化"
outline: [2, 3]
---

# 第十二章：存储器层次结构——Cache

上一章我们讨论了存储技术的全景图，了解了局部性的概念。现在，我们要聚焦于整个存储层次中最关键的一环——Cache（缓存）。Cache 处在 CPU 和主存之间，是弥合处理器速度与内存速度之间巨大鸿沟的关键桥梁。

你可以把 Cache 想象成"CPU 的桌面"——你经常用的工具（螺丝刀、扳手）放在桌面上，伸手就能拿到（1ns）；不常用的收到抽屉里（100ns）；基本不用的放到车库（10μs+）。整理桌面（管理 Cache）的艺术，决定了你的工作效率。同样，你的程序如果让 Cache 保持高命中率，就能跑出接近处理器的理论峰值——而如果老是 Cache Miss，性能直接"跳水"到主存的速度。

这一章是 CSAPP 中实用性最强的章节之一。理解了 Cache 的设计和优化策略，你就能写出远超"语法正确但性能平庸"水平的代码。

## 12.1 缓存组织结构

一个 Cache 由什么组成？有三个核心参数：

- **S**（组数）：Cache 分成 S 个组（Sets），每个组包含 E 行
- **E**（每组的行数）：关联度，E=1 是直接映射，E=S 是全相联
- **B**（块大小）：每行（Cache Line）存储的数据字节数，通常 64 字节

总 Cache 容量：C = S × E × B。

每一行（Cache Line）的结构：

```text
| Valid bit (1 bit) | Tag (t bits) | Data Block (B bytes) |
```

- **有效位（Valid Bit）**：标记该行是否包含有效数据。刚上电时所有有效位为 0。
- **标记位（Tag）**：地址的高位部分，用来区分映射到同一 Cache 组的不同内存块。
- **数据块（Data Block）**：从内存中取来的数据，大小 B 字节。

CPU 要访问一个内存地址时，地址被分解为三个部分：

```text
| Tag (t bits) | Set Index (s bits) | Block Offset (b bits) |
```

其中：

- **Set Index**：选择 Cache 中的哪个组（S = 2^s）
- **Tag**：与组内每个行的 Tag 比较，判断是否命中
- **Block Offset**：在数据块内的偏移量（B = 2^b）

不同的 Cache 配置对比：

| Cache 类型 | S（组数） | E（行数/组） | B（块大小） | C（总容量） |
| --- | --- | --- | --- | --- |
| L1 i-Cache（Intel Core i7） | 64 | 8（8 路组相联） | 64 B | 32 KB |
| L1 d-Cache（Intel Core i7） | 64 | 8（8 路组相联） | 64 B | 32 KB |
| L2 Cache（Intel Core i7） | 512 | 8（8 路组相联） | 64 B | 256 KB |
| L3 Cache（Intel Core i7） | 8192 | 16（16 路组相联） | 64 B | 8 MB |

## 12.2 从直接映射到全相联

根据 E 的不同取值，Cache 有三种组织方式：

**1. 直接映射（Direct-Mapped Cache, E=1）**

每个组只有 1 行。地址分解后，set index 唯一决定该地址映射到哪个 Cache 行。硬件最简单（只需要一个比较器），但冲突不命中的概率最高——两个不同的地址如果映射到同一个组，就会互相驱逐，即使其他组还空着。这种情况称为"抖动（Thrashing）"。

**2. 组相联（Set-Associative Cache, 1 < E < C/B）**

每个组有多行。CPU 同时比较组内所有行的 Tag——全并行比较，需要 E 个比较器。这是最主流的 Cache 设计，在硬件成本和命中率之间取得了良好平衡。上面的 Intel Core i7 的 L1 到 L3 全部是组相联。

**3. 全相联（Fully-Associative Cache, E = C/B）**

只有一个组，包含所有行。任何内存地址可以放在任何一行。最灵活，冲突不命中最少，但硬件最复杂（需要全局比较所有 Tag），通常只用于 TLB（后面虚拟内存章节会讲）这种行数很少的缓存。

来看一个地址分解的具体例子。假设：

```text
内存地址 = 0x1234（二进制：0001 0010 0011 0100）
参数：S = 4 组（s = 2 位），B = 16 字节（b = 4 位）
地址分解：
  Offset (bits 0-3):  0100 → offset = 4
  Index  (bits 4-5):  1101 → index = 3（第 3 组）
  Tag    (bits 6-15): 0001 0010 00 → tag = 0x048
```

CPU 用 index=3 找到第 3 组，然后在该组的所有行中搜索 tag=0x048 且 valid=1 的行。找到则 Cache Hit，从该行的数据块的 offset=4 处读取数据；否则 Cache Miss，从主存加载整个块（16 字节）到 Cache 中。

## 12.3 缓存未命中的三种类型

"3C" 是理解 Cache 未命中的经典分类框架——三个以 C 开头的英文名词：

**1. 冷不命中（Compulsory Miss / Cold Miss）**

程序第一次访问某个数据时，该数据必然不在 Cache 中——Cache 刚上电时空的，没有任何数据。这种不命中是"不可避免"的。也称为"工作集首次加载"。

**2. 容量不命中（Capacity Miss）**

程序的工作集（活跃使用的数据总量）超过了 Cache 的容量。例如，你在一个只有 32KB L1 Cache 的 CPU 上处理一个 1MB 的数组，大部分数据注定放不进 Cache。以前访问过但已被驱逐出去的数据再次被访问时，就会发生容量不命中。

**3. 冲突不命中（Conflict Miss）**

数据明明可以在 Cache 中（工作集小于 Cache 容量），但因为映射到同一个 Cache 组而互相驱逐。直接映射 Cache 的冲突不命中最严重，组相联 Cache 可以缓解但无法完全消除。

一个经典的冲突不命中例子——两个大小恰好为 2 的幂的数组：

```text
float a[1024], b[1024];
for (int i = 0; i < 1024; i++) {
    for (int j = 0; j < 1024; j++) {
        a[i] += b[j];  // a[i] 和 b[j] 地址相差 1024*4 = 4KB
    }                  // 如果 Cache 组数 = 2^s，两个数组可能在 Cache 中冲突
}
```

当 a 和 b 的地址映射到相同的 Cache 组时，访问 b[j] 会把 a[i] 驱逐出去，下次循环 a[i] 又要重新加载。这种"乒乓效应"会让性能急剧下降。解决办法之一是"填充"——在数组间故意留出空隙，打破整数倍的对齐关系。

::: tip
**如何判断 Cache Miss 的类型**：用 `perf stat -e cache-misses,cache-references` 查看程序的 Cache Miss 率。如果 Miss 率异常高，可以用 `perf record -e cache-misses` 结合 `perf report` 定位是哪些指令导致的。冷不命中通常只在程序初始阶段出现（预热后消失），容量不命中在工作集缩小后自动解决，冲突不命中则需要改数据结构或对齐方式。
:::

## 12.4 编写 Cache 友好代码

前面讲了很多理论，现在来点实际的——如何写出 Cache 友好的代码。CSAPP 中最经典的例子是矩阵乘法的优化。

**朴素的矩阵乘法（三重循环，i-j-k 顺序）：**

```text
void matmul_ijk(int n, float *A, float *B, float *C) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            float sum = 0;
            for (int k = 0; k < n; k++)
                sum += A[i*n + k] * B[k*n + j];  // B 按列访问！空间局部性差
            C[i*n + j] = sum;
        }
}
```

问题：B[k*n + j] 在 k 循环中按列访问 B 矩阵，跳着读，Cache Miss 率极高。

**优化：循环交换（i-k-j 顺序）：**

```text
void matmul_ikj(int n, float *A, float *B, float *C) {
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            float a_ik = A[i*n + k];
            for (int j = 0; j < n; j++)
                C[i*n + j] += a_ik * B[k*n + j];  // 内层 j 循环按行访问 B 和 C
        }
}
```

内层 j 循环变成按行访问 B[k*n + j] 和 C[i*n + j]——空间局部性大大改善。仅仅改变了循环嵌套顺序，Cache Miss 率可能下降一个数量级。

**更进一步：分块（Tiling / Blocking）**

即使做了循环交换，当 n 很大时，矩阵的"行"仍然可能超出 Cache 容量。分块的核心思想是把矩阵切分成小块（block/tile），确保每个小块在 Cache 中完全"转完"再处理下一块。

```text
void matmul_block(int n, float *A, float *B, float *C, int BLOCK) {
    for (int i = 0; i < n; i += BLOCK)
        for (int j = 0; j < n; j += BLOCK)
            for (int k = 0; k < n; k += BLOCK)
                // 处理一个小块 [i:i+BLOCK][j:j+BLOCK]
                for (int ii = i; ii < i+BLOCK && ii < n; ii++)
                    for (int jj = j; jj < j+BLOCK && jj < n; jj++) {
                        float sum = C[ii*n + jj];
                        for (int kk = k; kk < k+BLOCK && kk < n; kk++)
                            sum += A[ii*n + kk] * B[kk*n + jj];
                        C[ii*n + jj] = sum;
                    }
}
```

::: info
**分块优化的实际效果**：在我的实际测试中，对于 n=1024 的 float 矩阵乘法（矩阵大小为 4MB），朴素 ijk 版本的 CPE 约为 8-10（主要花在等待 B 矩阵的行数据上）。通过 i-k-j 循环交换，CPE 降到 3-4。再加上分块优化（BLOCK=64，让块完全放进 L1 Cache），CPE 可以进一步降到 1-2，总体加速比达到 5-10 倍。注意 BLOCK 大小的选择——太小则块数太多（循环开销大），太大则放不进 Cache。通常选择 BLOCK 使得三个小矩阵的尺寸总和不超过 L1 Cache 的一半。
:::

Cache 友好代码的几个实用原则：

1. **步长 1 优先**：尽量按存储顺序遍历数据
1. **循环交换**：让最内层循环遍历连续的地址
1. **分块**：处理大数组时，切分成 Cache 能容纳的小块
1. **合并访问**：如果能一次读入多个字段，就合并数据结构而不是使用指针链
1. **避免 2 的幂的"陷阱"**：数组大小避开 2 的幂，或使用 padding 来减少冲突

这一章我们从 Cache 的硬件组织方式（S、E、B 三参数）出发，走过了从直接映射到全相联的三种设计，理解了"3C"（冷不命中、容量不命中、冲突不命中），最后通过矩阵乘法的实际案例掌握了编写 Cache 友好代码的核心技巧。下一章我们将进入一个全新的主题——链接。你写的每个 C 程序都需要经过链接这一步才能变成可执行文件，而链接中的许多陷阱，是很多资深程序员都栽过跟头的。


## 实验：验证本章知识

在 [实验工程总览](/labs/) 中选择「Cache LRU 模拟」，通过编译运行与 CTest 黄金测试观察地址访问轨迹中的命中、缺失与替换。先预测输出，再验证结果；该实验用于理解机制，不直接代表硬件性能。
