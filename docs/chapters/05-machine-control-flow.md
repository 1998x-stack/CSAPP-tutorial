---
title: "程序的机器级表示——控制流"
description: "条件码寄存器 · 条件跳转与CMP/TEST · if-else/switch实现 · 循环的三种汇编模式"
outline: [2, 3]
---

# 第五章：程序的机器级表示——控制流

大家好，我是你们的讲师。上一章我们学了 x86-64 的基本指令——mov、add、lea 这些指令一条接一条地顺序执行，就像按菜谱一步一步操作。但现实中的程序不是这样线性执行的——它有 `if` 条件判断、`while` 循环、`switch` 多路分支。CPU 是如何实现"根据条件选择不同的执行路径"的？

答案藏在两类关键机制里：**条件码寄存器**和**跳转指令**。条件码记录上一条运算的"副作用"（结果是否为 0、是否溢出等），跳转指令根据条件码决定是否跳转到某个地址。

说到条件跳转，就不得不提**分支预测**。现代 CPU 是流水线执行的——它会提前把后续指令取到流水线里。遇到条件跳转时，CPU 必须猜测会走哪条路。猜对了，流水线填满，效率很高；猜错了，需要清空流水线重新取指令——这一下浪费大约 10-20 个时钟周期。一个需要高性能的工程师，写代码时会考虑分支预测的影响。我见过一个对性能极度敏感的场景：在某实时音频处理引擎中，工程师竟然用算术运算代替了一个 if-else 分支，只为了减少分支预测错误带来的延迟抖动。

## 5.1 条件码寄存器

x86-64 的 CPU 内部维护了一组**条件码寄存器**，每个条件码是 1 位（一个标志位）。最常用的四个是：

| 条件码 | 名称 | 何时被置 1 | 简单理解 |
| --- | --- | --- | --- |
| **CF** | 进位标志（Carry Flag） | 无符号运算结果超出范围（产生进位/借位） | 无符号溢出 |
| **ZF** | 零标志（Zero Flag） | 运算结果为 0 | 结果为 0 |
| **SF** | 符号标志（Sign Flag） | 运算结果为负数（最高位为 1） | 结果为负 |
| **OF** | 溢出标志（Overflow Flag） | 有符号运算结果超出范围（补码溢出的两种情况） | 有符号溢出 |

条件码由**算术和逻辑指令**自动设置。例如执行 `addq %rax, %rbx` 后，CPU 会根据运算结果更新 ZF/SF/CF/OF。除此之外，还有两条"专用"的、只修改条件码不修改目标寄存器的指令：

- `cmpq src2, src1` —— 计算 `src1 - src2`，只改条件码，不存结果。等价于 `subq` 但是丢弃结果。用于比较大小。
- `testq src2, src1` —— 计算 `src1 & src2`，只改条件码（ZF 和 SF），不存结果。通常用于检查某一位或判断是否为 0，如 `testq %rax, %rax` 判断 %rax 是否为零。

::: info
**关键思考**：CPU 设计者为什么要把"修改条件码"和"修改寄存器"分成不同的指令？这是 RISC 思想的体现——一条指令只做一件事。如果每次算术运算都无副作用地修改条件码，流水线实现会更复杂。现代 x86 虽然不完全符合 RISC 哲学，但在这里体现了精细的设计决策。
:::

## 5.2 条件跳转

有了条件码，我们就可以根据它们来做**条件跳转**了。跳转指令的核心是 `j` 系列：

| 指令 | 跳转条件 | 含义（C 语义） |
| --- | --- | --- |
| `jmp Label` | 无条件 | `goto Label;` |
| `je Label` | ZF = 1 | `if (==) goto Label;` |
| `jne Label` | ZF = 0 | `if (!=) goto Label;` |
| `jg Label` | SF = OF 且 ZF = 0 | `if (>) goto Label;`（有符号） |
| `jge Label` | SF = OF | `if (>=) goto Label;`（有符号） |
| `jl Label` | SF != OF | `if (<) goto Label;`（有符号） |
| `jle Label` | SF != OF 或 ZF = 1 | `if (<=) goto Label;`（有符号） |
| `ja Label` | CF = 0 且 ZF = 0 | `if (>) goto Label;`（无符号） |
| `jb Label` | CF = 1 | `if (<) goto Label;`（无符号） |

一个典型的 `cmp + je` 模式：

```asm
# C 代码：if (a == 10) goto done;
cmpq $10, %rdi      # 比较 a 和 10
je    .L_done       # 如果相等，跳转到 done
# ... 其他代码 ...
.L_done:
    ret
```

::: tip
**关于分支预测**：现代 CPU 有分支预测单元（Branch Prediction Unit），会学习跳转行为的模式。对于绝大多数有规律的分支（如循环的末尾跳转），预测准确率超过 95%。但那些**完全随机**的分支（如二分查找、随机数据排序的比较）预测准确率接近 50%，这时候分支错误带来的性能损失是真实存在的。在性能敏感的代码中，可以尝试用 `_builtin_expect`（C）或 `[[likely]]/[[unlikely]]`（C++20）给编译器提示。
:::

## 5.3 if-else 与 switch-case

**if-else 的汇编实现**——本质上就是一组条件跳转：

```asm
// C 代码
long absdiff(long a, long b)
{
    if (a > b)
        return a - b;
    else
        return b - a;
}

// GCC -O1 汇编
absdiff:
    cmpq    %rsi, %rdi     # 比较 a 和 b
    jle     .L_else        # 如果 a <= b，跳到 else
    movq    %rdi, %rax     # rax = a
    subq    %rsi, %rax     # rax = a - b
    ret
.L_else:
    movq    %rsi, %rax     # rax = b
    subq    %rdi, %rax     # rax = b - a
    ret
```

可以看到，编译器把 if-else 翻译成了 `cmp + jle` + 两条分支代码。注意：编译器喜欢把**更常见的路径**放在紧跟着跳转指令的位置（fall-through），而不常见的路径放在跳转目标处。

**switch-case 的汇编实现**——这才是真正有意思的部分。当 case 值连续且数量较多时，编译器会生成一个**跳转表（Jump Table）**：

```asm
// C 代码
void switch_demo(int op)
{
    switch (op) {
        case 0: do_a(); break;
        case 1: do_b(); break;
        case 2: do_c(); break;
        case 3: do_d(); break;
        default: do_default(); break;
    }
}

// GCC -O1 汇编（简化）
switch_demo:
    cmpq    $3, %rdi         # 检查 op 是否超过范围
    ja      .L_default       # 如果 > 3，跳到 default
    jmp     *.L_jump_table(, %rdi, 8)  # 从跳转表取目标地址

.L_jump_table:
    .quad .L_case0
    .quad .L_case1
    .quad .L_case2
    .quad .L_case3
```

跳转表的本质是一个**函数指针数组**——CPU 直接根据输入的索引 `op` 在数组中查到目标地址，然后一条 `jmp` 指令跳过去。整个过程只需要**1 次内存访问 + 1 次间接跳转**，无论有多少个 case，耗时都是常数。

相比之下，if-else if 链需要一条一条比较，耗时随着分支数量线性增长。这就是**为什么**编译器在 case 值连续、case 数量较多时（通常 > 4）总是倾向于生成跳转表而不是比较链。

::: info
**性能对比**：假设有 10 个 case，用 if-else if 链平均需要比较 5 次才能找到匹配分支，最坏情况 10 次。而跳转表永远是 1 次间接跳转。代价是跳转表本身占用的少量额外内存（每个条目 8 字节）。这是一种典型的"用空间换时间"的优化策略。
:::

## 5.4 循环的三种汇编模式

C 语言有三种循环语法：`do-while`、`while`、`for`。有趣的是，它们在汇编层面实际只对应**两种**基本模式——因为 for 循环本质上是 while 循环的语法糖。理解循环的汇编实现有一个绝佳的方法：把它翻译成**goto-C**。

**模式一：do-while（条件在后）**

这是最直接、最"诚实"的模式——先执行循环体，再检查条件。至少执行一次。

```asm
// C 源码
long fact_do(long n)
{
    long result = 1;
    do {
        result *= n;
        n--;
    } while (n > 1);
    return result;
}

// 等价的 goto-C
long fact_do_goto(long n)
{
    long result = 1;
.loop:
    result *= n;
    n--;
    if (n > 1)
        goto .loop;
    return result;
}

// 对应的汇编（简写）
fact_do:
    movq    $1, %rax       # result = 1
.loop:
    imulq   %rdi, %rax     # result *= n
    decq    %rdi           # n--
    cmpq    $1, %rdi       # 比较 n 和 1
    jg      .loop          # 如果 n > 1，继续循环
    ret
```

**模式二：while 与 for（条件在前）**

while 和 for 的区别只在于语法层面，汇编代码完全一样。核心策略是：先无条件跳转到条件检查处（跳至底部），检查不满足就直接跳过循环。

```asm
// C 源码
long fact_while(long n)
{
    long result = 1;
    while (n > 1) {
        result *= n;
        n--;
    }
    return result;
}

// 等价的 goto-C（"跳至中间"模式）
long fact_while_goto(long n)
{
    long result = 1;
    goto .test;
.loop:
    result *= n;
    n--;
.test:
    if (n > 1)
        goto .loop;
    return result;
}

// 对应的汇编（简写）
fact_while:
    movq    $1, %rax       # result = 1
    jmp     .test          # 先跳到条件检查
.loop:
    imulq   %rdi, %rax     # result *= n
    decq    %rdi           # n--
.test:
    cmpq    $1, %rdi       # 比较 n 和 1
    jg      .loop          # 如果 n > 1，继续循环
    ret
```

为什么编译器要把 while 翻译成"先跳到底部再检查"的模式？这个设计很妙：把条件检查放在循环体的末尾，这样只需要**一个条件跳转**（在末尾控制回跳），而不是在循环入口处也要跳转。你可以想象一下，如果 while 翻译成"检查→不满足就跳过→执行体→无条件跳回检查"——那就是 **两个跳转**（一个条件跳转 + 一个无条件跳转）每个循环迭代都要执行，效率更低。

::: warning
**⚠️ 循环优化陷阱**：编译器在优化循环时（特别是 `-O2` 以上），会做大量的变换——循环展开、向量化、循环不变量外提等。你看到生成的汇编可能和 C 源码的结构完全不对应，但计算结果是等价的。**不要**试图从优化后的汇编反推 C 逻辑——它可能已经被彻底重组了。
:::

这一章我们学习了程序控制流在机器层面的实现方式。条件码记录运算结果的特征，跳转指令实现路径选择，if-else 翻译成条件跳转，switch 翻译成跳转表（当条件允许时），三种循环本质上都归结为"条件跳转 + 回跳"的模式。

下一章，我们将迈入汇编学习中最精彩的部分——**过程（函数）调用**。call 指令如何跳转、ret 指令如何返回、参数和局部变量在栈上怎么摆放、递归函数在底层是什么样的——这些问题将逐一得到解答。
