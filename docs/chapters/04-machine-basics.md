---
title: "程序的机器级表示——基础"
description: "x86-64寄存器全景 · 数据传送与算术指令 · lea指令妙用 · 寻址模式详解"
outline: [2, 3]
---

# 第四章：程序的机器级表示——基础

大家好，我是你们的讲师。从这一章开始，我们将进入一个全新的世界——**程序的机器级表示**。

前面两章我们一直在讲"数据怎么存"——整数在寄存器里怎么编码，浮点数在内存里怎么布局。但从现在开始，我们要问的是"**指令怎么动**"。你写的 C 语言 `a = b + c`，在 CPU 眼里到底是什么样的？

让我分享一个我早年做嵌入式开发时的经历。有一次，我写的通信协议栈在特定环境下隔几个小时就随机死机。代码评审过三遍没发现问题，日志分析也看不出规律。最后我打印了崩溃时的汇编上下文，对照指令一条条看——发现编译器优化后，一个 volatile 变量被"聪明"地优化掉了，导致中断和主循环之间共享的变量不同步。那一刻我意识到：不了解汇编，你在某些 bug 面前就是瞎子。

本章的焦点是 x86-64 架构——这是当今绝大多数桌面和服务器 CPU 使用的指令集。我们只讲最核心、最常用的指令，不讲冷门内容。

## 4.1 x86-64 寄存器全景图

x86-64 架构提供了 16 个 64 位通用寄存器，外加程序计数器（PC / %rip）和条件码寄存器（后面两章会细讲）。理解这些寄存器是看懂汇编代码的第一步。

| 64 位寄存器 | 32 位子集 | 16 位子集 | 8 位子集 | 角色/用途 | 保存责任 |
| --- | --- | --- | --- | --- | --- |
| %rax | %eax | %ax | %al | 返回值、累加器 | Caller-saved |
| %rbx | %ebx | %bx | %bl | 基址寄存器 | Callee-saved |
| %rcx | %ecx | %cx | %cl | 第 4 个函数参数、计数器 | Caller-saved |
| %rdx | %edx | %dx | %dl | 第 3 个函数参数、数据寄存器 | Caller-saved |
| %rsi | %esi | %si | %sil | 第 2 个函数参数、源索引 | Caller-saved |
| %rdi | %edi | %di | %dil | 第 1 个函数参数、目标索引 | Caller-saved |
| %r8 | %r8d | %r8w | %r8b | 第 5 个函数参数 | Caller-saved |
| %r9 | %r9d | %r9w | %r9b | 第 6 个函数参数 | Caller-saved |
| %r10 | %r10d | %r10w | %r10b | 临时寄存器 | Caller-saved |
| %r11 | %r11d | %r11w | %r11b | 临时寄存器 | Caller-saved |
| %r12 | %r12d | %r12w | %r12b | 通用寄存器 | Callee-saved |
| %r13 | %r13d | %r13w | %r13b | 通用寄存器 | Callee-saved |
| %r14 | %r14d | %r14w | %r14b | 通用寄存器 | Callee-saved |
| %r15 | %r15d | %r15w | %r15b | 通用寄存器 | Callee-saved |
| %rsp | %esp | %sp | %spl | 栈指针（Stack Pointer） | 专用 |
| %rbp | %ebp | %bp | %bpl | 基址指针（Frame Pointer，可选） | Callee-saved |

这里最关键的概念是 **Caller-saved vs Callee-saved**。Caller-saved 寄存器由调用者负责保存（如果调用后还要用）；Callee-saved 寄存器由被调用者负责保存（如果被调用者想用，必须先 push 保存，返回前 pop 恢复）。这个机制在第六章讲过程调用时会详细分析。

## 4.2 数据传送指令家族

最常用的指令就是 **mov** 指令——它把数据从一个位置复制到另一个位置。x86-64 的 mov 指令有四种主要变体：

| 指令 | 操作数大小 | 示例 | 含义 |
| --- | --- | --- | --- |
| `movb` | 1 字节 | `movb %al, %bl` | 复制 1 字节 |
| `movw` | 2 字节 | `movw %ax, %bx` | 复制 1 个字（word） |
| `movl` | 4 字节 | `movl %eax, %ebx` | 复制双字（double word），同时将高 32 位清零 |
| `movq` | 8 字节 | `movq %rax, %rbx` | 复制四字（quad word） |

另外还有一个特殊的 `movabsq`，用于将 64 位立即数加载到寄存器——普通的 `movq` 只能接受 32 位立即数（符号扩展后），而 64 位立即数必须用 `movabsq`。

**push 和 pop：**

`pushq %rax` 等价于以下两步的微操作：

```asm
subq $8, %rsp       # 栈指针减 8
movq %rax, (%rsp)   # 将 %rax 的值写入新的栈顶
```

`popq %rax` 等价于：

```asm
movq (%rsp), %rax   # 从栈顶读取到 %rax
addq $8, %rsp       # 栈指针加 8
```

**lea 指令——不访问内存的"计算器"：**

`lea`（Load Effective Address）是一个被低估的强力指令。它的本意是计算有效地址，但因为地址计算涉及灵活的加法和移位，聪明的程序员（和编译器）把它当作了"免内存访问的算术指令"：

```asm
leaq (%rdi, %rsi, 4), %rax   # %rax = %rdi + %rsi * 4
leaq 8(%rdx), %rax            # %rax = %rdx + 8
```

注意 lea 不访问内存——它只是做地址计算并存结果！这就让 lea 成了一个隐形的加法+乘法指令，而且比用 add+imul 组合更快。

## 4.3 算术与逻辑指令

x86-64 提供了一套丰富的算术与逻辑指令。来看一个 C 函数和它编译后的汇编对比：

```asm
// C 源码
long arith(long a, long b, long c)
{
    return a + b * 4 - c / 8 + (a & 0xFF);
}

// GCC -O1 编译后的汇编
arith:
    leaq    (%rdi, %rdi, 4), %rax   // %rax = a * 5 (用 lea 做乘法)
    addq    %rax, %rsi              // %rsi = b + a*5
    movq    %rdx, %rax              // %rax = c
    sarq    $3, %rax                // %rax = c >> 3 (有符号除以 8)
    subq    %rax, %rsi              // %rsi = (b+a*5) - (c/8)
    movzbl  %dil, %eax              // %eax = a & 0xFF (零扩展)
    addq    %rsi, %rax              // %rax = (b+a*5-c/8) + (a&0xFF)
    ret
```

常用算术与移位指令速览：

| 指令 | 含义 | 注意事项 |
| --- | --- | --- |
| `addq src, dst` | dst += src | 影响条件码 |
| `subq src, dst` | dst -= src | 影响条件码 |
| `imulq src, dst` | dst *= src（有符号） | 64 位乘法结果可能溢出 |
| `imulq src` | `%rdx:%rax = %rax * src` | 单操作数版本，结果 128 位存入 rdx:rax |
| `idivq src` | `%rax = %rdx:%rax / src`，`%rdx = 余数` | 有符号除法，需先符号扩展 %rax 到 %rdx |
| `salq k, dst` / `shlq k, dst` | dst <<= k（左移） | 左移同算术/逻辑，无区别 |
| `sarq k, dst` | dst >>= k（算术右移，保留符号位） | 有符号数的右移 |
| `shrq k, dst` | dst >>= k（逻辑右移，高位补 0） | 无符号数的右移 |
| `andq src, dst` | dst &= src |  |
| `orq src, dst` | dst \|= src |  |
| `xorq src, dst` | dst ^= src |  |
| `negq dst` | dst = -dst |  |
| `notq dst` | dst = ~dst |  |

::: tip
**编译实践**：自己动手试试！写一个简单的 C 文件，然后执行 `gcc -O1 -S test.c -o test.s` 来查看生成的汇编代码。注意不同优化级别（`-O0` vs `-O1` vs `-O2`）产生的汇编差异巨大。`-O0` 几乎每行 C 代码都有对应汇编，便于调试；`-O2` 的代码简洁高效但更难对应源码。
:::

## 4.4 寻址模式详解

x86-64 的寻址模式可以归纳为三类操作数类型：**立即数（Immediate）**、**寄存器（Register）**、**内存（Memory）**。

而内存寻址中最强大的是**比例变址寻址（Indexed Addressing）**，其通用格式为：

```text
Imm(%rb, %ri, s)   →   有效地址 = Imm + %rb + %ri * s
```

其中 `Imm` 是立即数偏移（1, 2 或 4 字节），`%rb` 是基址寄存器，`%ri` 是变址寄存器（不能是 %rsp），`s` 是比例因子（1, 2, 4 或 8）。

| 寻址模式 | 示例 | 有效地址计算 | 使用场景 |
| --- | --- | --- | --- |
| 立即数寻址 | `$0x42` | 常数本身 | 加载常量 |
| 寄存器寻址 | `%rax` | 寄存器中的值 | 寄存器间数据移动 |
| 绝对寻址 | `0x404000` | 固定的内存地址 | 访问全局变量 |
| 基址寻址 | `(%rax)` | %rax 中的值 | 指针解引用 |
| 基址+偏移量 | `8(%rax)` | %rax + 8 | 访问结构体字段 |
| 基址+变址 | `(%rax, %rbx)` | %rax + %rbx | 数组索引 |
| 变址+比例因子 | `(, %rbx, 4)` | %rbx * 4 | int 数组的元素访问 |
| 比例变址寻址 | `(%rax, %rbx, 8)` | %rax + %rbx * 8 | long 数组的元素访问 |
| 比例变址+偏移 | `16(%rax, %rbx, 4)` | 16 + %rax + %rbx * 4 | 结构体数组成员访问 |

::: info
**编译器使用 lea 进行优化的常见模式**：

                `leaq (%rdi, %rdi, 2), %rax` → `%rax = %rdi * 3`（乘以 3）
                `leaq (%rdi, %rdi, 4), %rax` → `%rax = %rdi * 5`（乘以 5）
                `leaq (%rdi, %rdi, 8), %rax` → `%rax = %rdi * 9`（乘以 9）
                `leaq (%rdx, %rdx, 2), %rax; salq $2, %rax` → `%rax = %rdx * 12`（乘以 12 = 3×4）

这些技巧表明：**lea 是 x86-64 中最好的"免费"算术指令**——因为它只做地址计算，不访问内存，通常能在 1 个时钟周期内完成。
:::

以上就是本章的全部内容。我们走马观花地看了寄存器布局、数据传送指令、算术逻辑指令和寻址模式。这些知识就像乐高积木——单独的每块都很简单，但组合起来就能构建出复杂的程序行为。

下一章，我们将在这套基础指令之上，学习"程序如何做决策"——条件码、条件跳转，以及如何用汇编实现 C 语言的 if-else、switch-case 和循环。
