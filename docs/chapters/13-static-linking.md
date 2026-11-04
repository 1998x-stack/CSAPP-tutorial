---
title: "链接——静态链接"
description: "ELF目标文件格式 · 符号与符号表 · 静态库与ar工具 · 强符号与弱符号陷阱"
outline: [2, 3]
---

# 第十三章：链接——静态链接

在第一章的计算机系统漫游中，我提到过 C 程序变成可执行文件需要经过四个阶段：预处理、编译、汇编、链接。前三步我们已经在第 2 到第 7 章（信息的表示、机器级表示）中有了深入的理解。但链接——这个将多个目标文件"粘合"成最终可执行文件的步骤——往往被当作"黑盒子"对待。

实际上，链接过程中隐藏着大量容易踩坑的地方。你有没有遇到过这样的场景：明明在头文件里声明了一个全局变量，链接时报"undefined reference"；或者更诡异的——改了某个全局变量的值，结果程序莫名其妙崩溃了。这些问题很可能出在链接阶段。

这一章我们要打开链接器的"黑盒子"，深入理解 ELF 文件格式、符号解析和重定位的过程。这不仅是知识层面的"补课"，更是在实战中少踩坑的保障。

## 13.1 ELF 可重定位目标文件

ELF（Executable and Linkable Format）是 Linux 系统上目标文件和可执行文件的标准格式。它从 Solaris 系统引入，现在已经成为 Linux 世界的通用标准。

一个 ELF 可重定位目标文件（`.o` 文件）的结构如下：

| 节（Section） | 描述 | 常见内容 |
| --- | --- | --- |
| `.text` | 已编译的机器代码 | 所有函数的指令 |
| `.rodata` | 只读数据 | 字符串常量、switch 跳转表 |
| `.data` | 已初始化的全局和静态变量 | int global = 42; |
| `.bss` | 未初始化或初始化为 0 的全局/静态变量 | int global;（实际不占文件空间） |
| `.symtab` | 符号表 | 函数名、全局变量名、地址 |
| `.rel.text` | .text 节的重定位信息 | 哪些位置需要在链接时修改地址 |
| `.rel.data` | .data 节的重定位信息 | 引用了外部符号的数据项 |
| `.debug` | 调试符号表（用 -g 编译时产生） | 行号、局部变量信息 |
| `.line` | 源代码行号与机器码的映射 | 用于调试器 |
| `.strtab` | 字符串表 | 符号名、节名称 |

一个重要的细节：**.bss 节不占用磁盘空间**。它只是一个"占位符"，在链接后或运行时被分配内存并初始化为 0。所以你在 C 文件中声明 `int big_array[1000000];`，`.o` 文件并不会因此变大 4MB——这些 0 只会在运行时分配。

::: tip
**查看 ELF 文件**：Linux 提供了 `readelf` 和 `objdump` 工具来检查 ELF 文件。用 `readelf -h a.o` 查看 ELF 头，`readelf -S a.o` 查看所有节。编译时加 `-g` 选项可以看到额外的 .debug 节。
:::

## 13.2 符号与符号表

每个可重定位目标文件都有一张**符号表（.symtab）**，记录了文件中定义或引用的所有符号。符号分为三类：

- **全局符号（Global Symbols）**：在当前文件中定义，可以被其他文件引用。例如非 static 的函数和全局变量。
- **外部符号（External Symbols）**：在当前文件中引用但定义在其他文件中的全局符号。链接器需要找到它们的定义。
- **局部符号（Local Symbols）**：用 static 定义的函数和变量，只在当前文件可见。注意，局部"自动变量"（函数内的局部变量）不在符号表中——它们在栈上管理，与链接无关。

来看一个具体的 `readelf -s` 输出示例：

```bash
$ readelf -s main.o

Symbol table '.symtab' contains 14 entries:
   Num:    Value  Size Type    Bind   Vis      Ndx Name
     0:        0     0 NOTYPE  LOCAL  DEFAULT  UND
     1:        0     0 FILE    LOCAL  DEFAULT  ABS main.c
     2:        0     0 SECTION LOCAL  DEFAULT    1
     3:        0     0 SECTION LOCAL  DEFAULT    3
     4:        0     0 SECTION LOCAL  DEFAULT    4
     5:        0     0 SECTION LOCAL  DEFAULT    5
     6:        0     0 SECTION LOCAL  DEFAULT    7
     7:        0     0 SECTION LOCAL  DEFAULT    8
     8:        0     4 OBJECT  GLOBAL DEFAULT    3 global_var
     9:        8     4 OBJECT  GLOBAL DEFAULT  COM global_weak
    10:       16     4 OBJECT  GLOBAL DEFAULT    3 global_init
    11:        0    36 FUNC    GLOBAL DEFAULT    1 main
    12:        0     0 NOTYPE  GLOBAL DEFAULT  UND printf
    13:        0     0 NOTYPE  GLOBAL DEFAULT  UND exit
```

这个输出展示的符号表信息丰富：

- `global_var`（在 .data 节，Ndx=3，已初始化）
- `global_weak`（在 COMMON，Ndx=COM，未初始化）
- `global_init`（在 .data 节，已初始化）
- `main`（函数，在 .text 节，Ndx=1）
- `printf` 和 `exit`（UND，表示未定义——需要链接器在其他目标文件中解析）

注意 COMMON 和 .bss 的区别：COMMON 是未初始化的全局变量（弱符号），而 .bss 是初始化为 0 的全局和静态变量。这个区分在后面讨论强符号/弱符号时至关重要。

## 13.3 静态库与 ar 工具

你可能每天都用 `-lm`、`-lpthread` 这些选项链接标准库。这些库文件（`libc.a`、`libm.a` 等）本质上是多个 `.o` 文件打包在一起——用 `ar` 工具打包。

```bash
# 创建静态库
$ gcc -c addvec.c multvec.c      # 编译成 .o
$ ar rcs libvector.a addvec.o multvec.o  # 打包成静态库

# 使用静态库
$ gcc -c main.c
$ gcc -o prog main.o -L. -lvector  # 链接静态库
```

链接器处理静态库的原则是**"按需提取"**——只把 main.o 中引用了的目标模块（如 addvec.o）从库中提取出来链接，而不是把整个 libvector.a 都塞进可执行文件。

这就引出了一个非常重要的陷阱：**库在命令行中的顺序**。

::: warning
**库顺序的致命陷阱**：在链接命令中，静态库必须放在引用它的目标文件**之后**！为什么？因为链接器是从左到右扫描文件列表的。当它看到一个目标文件时，会把该文件引用的未解析符号记录在"待解析列表"中。当它看到一个库时，会检查库中的模块是否能解析当前列表中的符号——如果能，就提取该模块；如果不能，就跳过整个库。所以如果库出现在引用它的文件**之前**，链接器扫描到库时还不知道需要哪些符号——就跳过了！最终导致 undefined reference 错误。

ZZCSAPPBLOCK002ZZ
:::

这个陷阱每年坑害无数程序员（包括我自己）。记住：**目标文件 → 库1 → 库2**，如果有相互依赖，重复列出必要的库。

## 13.4 强符号与弱符号

链接器在处理多重定义的符号时，会遵循一套"强/弱"规则：

- **强符号（Strong Symbol）**：函数名、已初始化的全局变量
- **弱符号（Weak Symbol）**：未初始化的全局变量

规则很简单：

1. **不允许有多个强符号**——链接器报"multiple definition"错误
1. **一个强符号 + 多个弱符号**——强符号胜出
1. **多个弱符号**——任选一个（通常是 COMMON 中最大的那个）

规则 2 是嵌入式系统中最常见的 bug 来源。来看一个真实案例：

```c
/* file1.c */
#include <stdio.h>
int global = 100;  // 强符号

void func() {
    printf("global = %d\n", global);
}

/* file2.c */
int global;  // 弱符号（未初始化）

int main() {
    func();
    global = 42;
    func();
    return 0;
}
```

```bash
$ gcc file1.c file2.c -o prog && ./prog
global = 100
global = 42
```

这个例子看起来工作正常。但如果弱符号在不同文件中被声明为**不同类型**呢？

```c
/* file1.c */
double global = 3.14;  // 强符号，double 类型

/* file2.c */
int global;  // 弱符号，int 类型，链接器选择 double 版本

int main() {
    printf("global = %d\n", global);  // 未定义行为！
    return 0;
}
```

这里编译器在 file2.c 中假设 `global` 是 int（4 字节），但链接后它实际上是 double（8 字节）——类型信息在链接阶段丢失了。程序打印出的 "global" 值完全就是 garbage，而且可能会破坏相邻的内存！

::: info
**强符号规则的实际教训**：这个 bug 的可怕之处在于——链接器不会给出任何警告！它"静默"地用强符号覆盖了弱符号。你的程序可能正常跑很久，直到某个看似无关的修改导致弱符号的定义变成了不同的强符号，然后程序崩溃得一塌糊涂。最佳实践是：**尽量避免使用全局变量**。如果必须用，用 static 限定可见范围，或者显式初始化为 0。对于大型项目，可以考虑使用 `-fno-common` 编译选项来把所有的弱符号都视为强符号——这样链接器会在多重定义时报错，而不是静默覆盖。
:::

这一章我们详细解析了 ELF 可重定位目标文件的内部结构，学会了用 `readelf` 查看符号表，理解了静态库链接时按需提取的原则以及库顺序的重要性，最后揭开了强符号/弱符号这个静默 bug 的根源。下一章，我们将讨论静态链接的"进阶版"——动态链接，看看共享库是如何在运行时被加载和解析的。
