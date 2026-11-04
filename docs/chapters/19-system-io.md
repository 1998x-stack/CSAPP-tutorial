---
title: "系统级I/O"
description: "Unix I/O模型与FD · open/read/write调用 · I/O重定向(dup2) · RIO鲁棒I/O包设计"
outline: [2, 3]
---

# 第十九章：系统级I/O

在之前的章节中，我们深入讨论了虚拟内存——操作系统给每个进程描绘了一幅"独占整台机器"的美好画卷。但进程终究不能活在自己的世界里，它要和外界交互：从磁盘读文件、往终端写日志、通过网络收发数据。所有这些交互，都离不开一个最基本的系统机制——**输入/输出（I/O）**。

你可能会说："I/O 有什么好学的？不就是 `printf`、`scanf`、`fread`、`fwrite` 吗？" 你用的这些确实是 C 标准库的 I/O 函数，但它们只是上层封装。我见过太多因为不懂底层系统级 I/O 而掉进坑里的案例：一个 `read()` 调用只读了部分数据就返回了，程序直接崩溃；混合使用 `printf` 和 `write` 导致输出顺序错乱——而这些问题的根源，都在于不理解 Unix 系统级 I/O 到底怎么工作的。这一章，我们就来把 I/O 这层窗户纸捅破。

## 19.1 Unix I/O 模型：一切皆文件

Unix 的设计哲学里有一句经典名言——**"Everything is a file"**（一切皆文件）。对 Unix 来说，打开一个磁盘文件、向终端写入数据、从网络套接字读取数据，甚至获取系统信息（如 `/proc` 下的内容），都统一抽象为"文件"这个概念。所有 I/O 操作都通过同一个接口完成：`open()` → `read()`/`write()` → `close()`。

每个进程在被创建时，操作系统会为其维护一个**文件描述符表**（file descriptor table）。文件描述符（fd）本质上是这张表的一个**整数索引**。当你打开一个文件时，系统在表中新增一项，返回最小的可用整数作为 fd；当你关闭文件时，对应表项被释放。

每个 Unix 进程在启动时，默认打开三个标准的文件描述符：

| 文件描述符 | 名称 | 默认绑定 | C 标准流 |
| --- | --- | --- | --- |
| `0` | stdin（标准输入） | 键盘 | `stdin` |
| `1` | stdout（标准输出） | 终端显示 | `stdout` |
| `2` | stderr（标准错误） | 终端显示 | `stderr` |

这三个描述符默认都指向终端设备。但通过**重定向**，可以把它们指向任何文件——这正是 Shell 中 `ls > out.txt`、`./a.out 2>&1` 等操作的底层实现原理。

文件描述符背后有两层重要的状态。第一层是**文件描述符表**（per-process），每个表项指向一个**打开文件表项**（系统级）。打开文件表项记录了关键的**当前文件位置**（current file position），即下一次读写操作从文件的哪个字节开始。这个位置会随着 `read()`/`write()` 自动推进。了解这个机制，你就能理解为什么多个进程同时写入同一个文件时会出现相互覆盖的问题——它们共享同一个文件位置吗？不，每个进程有自己的 fd 表，但如果两个进程通过 `fork()` 继承同一个 fd，那么它们**共享**同一个打开文件表项，包括同一个文件位置。这既是强大的 IPC 机制，也是潜在的 bug 源头。

## 19.2 open/read/write/close 系统调用

让我们看看这几个最核心的系统调用。它们的声明在 `<fcntl.h>`、`<unistd.h>` 中：

```c
#include <fcntl.h>
#include <unistd.h>

// 打开文件：返回文件描述符，失败返回 -1
int open(const char *path, int flags, mode_t mode);

// 标志位（定义在 <fcntl.h>）:
// O_RDONLY  — 只读打开
// O_WRONLY  — 只写打开
// O_RDWR    — 读写打开
// O_CREAT   — 文件不存在则创建
// O_TRUNC   — 若文件已存在，截断为 0 长度
// O_APPEND  — 每次写入前将文件位置定位到末尾

// 读：尝试读取 count 字节到 buf，返回实际读到的字节数
ssize_t read(int fd, void *buf, size_t count);

// 写：从 buf 写入 count 字节到 fd，返回实际写入的字节数
ssize_t write(int fd, const void *buf, size_t count);

// 关闭文件描述符
int close(int fd);
```

`read()` 的返回值需要特别注意：返回值等于 0 表示读到 **EOF**（文件结束）；返回值等于 -1 表示出错（需要检查 `errno`）；返回正数则表示实际读取的字节数。你可能会问："我要求读 4096 字节，它就一定返回 4096 吗？"**不一定**。这就是所谓的 **short count**（短计数）问题。

什么时候会出现 short count？以下几种情况：

- 读取普通文件时遇到文件末尾（还剩 100 字节，但你要求读 4096）
- 从终端（stdin）读取时，通常一次只返回一行
- 从网络套接字读取时，网络缓冲区的数据可能小于请求量
- 被信号中断时，读完的部分已经返回

下面是一个直接用 Unix I/O 实现的文件拷贝程序。看似简单，实际上正确性需要考虑 short count 问题：

```c
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int fd_src = open(argv[1], O_RDONLY);
    int fd_dst = open(argv[2], O_WRONLY | O_CREAT | O_TRUNC, 0644);
    char buf[4096];
    ssize_t n;

    while ((n = read(fd_src, buf, sizeof(buf))) > 0) {
        char *p = buf;
        ssize_t remaining = n;
        while (remaining > 0) {
            ssize_t written = write(fd_dst, p, remaining);
            if (written < 0) exit(1);
            remaining -= written;
            p += written;
        }
    }

    close(fd_src);
    close(fd_dst);
    return 0;
}
```

注意内层的 while 循环——即使 `read()` 返回了 n 字节，`write()` 也可能只写入了部分数据。这个"循环直到写完"的模式，是可靠 I/O 编程的基础。

::: info
**核心洞察**：`read()` 和 `write()` 的 short count 不是 bug，是特性。它们给了内核灵活性——当数据还没准备好时，可以先返回已有的部分，而不必让进程无限等待。你的代码必须有能力处理 short count。
:::

## 19.3 I/O 重定向的原理

Shell 中的重定向操作看起来像魔法一样：`ls > out.txt` 可以把原本输出到终端的内容写入文件。这个魔法的本质是什么？答案就是 `dup2` 系统调用。

```c
#include <unistd.h>

// 将 oldfd 复制到 newfd（如果 newfd 已打开，先关闭它）
int dup2(int oldfd, int newfd);
```

`dup2` 做的事情是：关闭 `newfd` 当前指向的文件描述符表项，然后让 `newfd` 指向 `oldfd` 所指向的同一个打开文件表项。从此以后，对 `newfd` 的读写操作，实际上操作的是 `oldfd` 的那个文件。

要实现 `ls > out.txt`，Shell 的流程大致是这样的：

```text
// 伪代码：Shell 如何实现 "ls > out.txt"
pid_t pid = fork();

if (pid == 0) {
    // 子进程：重定向 stdout 并执行 ls
    int fd = open("out.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    dup2(fd, STDOUT_FILENO);   // 关闭 stdout(1)，让它指向 out.txt
    close(fd);                 // 原始的 fd 不再需要
    execlp("ls", "ls", NULL);  // ls 的输出会写入 out.txt
}

wait(NULL);  // 父进程等待子进程结束
```

同理，`ls 2>&1` 的原理就是 `dup2(1, 2)`——让 stderr 指向 stdout 所指向的终端。管道 `|` 也是类似的思路，只不过中间多了一个由 `pipe()` 创建的内核缓冲区。

::: tip
**小技巧**：想要在代码里实现"把日志同时写入文件和控制台"？试试 `fork()` 一个子进程，父进程保持正常输出，子进程通过 `dup2` 将 stdout 重定向到日志文件。这是很多守护进程的实现思路。
:::

## 19.4 标准 I/O 库的缓冲机制

你可能已经注意到，前面我们用 `read()`/`write()` 直接操作文件描述符，而日常编程中更常用的是 `fread()`/`fwrite()`/`printf()`/`fgets()` 这些 C 标准库函数。这两套 API 之间是什么关系？

简单来说，**标准 I/O 库（stdio）是在系统级 I/O 上封装了一层用户态的缓冲区**。系统调用 `read()`/`write()` 每次都要陷入内核——上下文切换的开销是很大的（大约几百纳秒到几微秒）。如果每次 printf 输出一个字符都要做一次系统调用，效率会极其低下。stdio 的做法是：先把数据写入用户空间的缓冲区，等缓冲区满了（或者遇到换行符，或者程序主动 `fflush`）才真正调用 `write()`。

stdio 支持三种缓冲策略：

| 缓冲类型 | 适用场景 | 行为 | 默认缓冲区大小 |
| --- | --- | --- | --- |
| **全缓冲**（_IOFBF） | 普通磁盘文件 | 缓冲区填满后才写入内核 | 4096 或 8192 字节 |
| **行缓冲**（_IOLBF） | 终端（stdin/stdout） | 遇到换行符或缓冲区满时写入 | 通常与全缓冲相同 |
| **无缓冲**（_IONBF） | stderr | 每次写入立即输出 | 无缓冲区 |

可以用 `setvbuf` 来修改缓冲策略：

```c
#include <stdio.h>

int setvbuf(FILE *stream, char *buf, int mode, size_t size);
// mode: _IOFBF (全缓冲) / _IOLBF (行缓冲) / _IONBF (无缓冲)
```

这里有一个极易踩坑的地方——**混合使用 stdio 和 Unix I/O**。

::: warning
**真实踩坑故事**：曾经有一个线上服务，在排查问题时打印了很多 `printf` 调试日志，同时偶尔调用 `write(STDOUT_FILENO, ...)` 输出一些二进制数据到同一个终端。结果诡异的事情发生了：`printf` 输出的日志和 `write` 输出的二进制数据顺序错乱了——按理说先 `printf` 后 `write`，输出却先看到 `write` 的内容。原因就是 `printf` 用的是 stdio 的行缓冲（还没遇到换行符，数据在用户缓冲区里躺着），而 `write` 直接绕过缓冲区进了内核，所以后调用的反而先输出了。解决方法是：在 `write` 调用前加一句 `fflush(stdout)`，强制清空 stdio 缓冲区。
:::

这个教训告诉我们：**永远不要在同一个文件描述符上混合使用 stdio 和 Unix I/O，除非你非常清楚缓冲机制并做好 fflush**。

## 19.5 RIO（鲁棒 I/O）包设计

从上面的讨论我们看到，可靠地处理 short count 需要对 `read()`/`write()` 进行封装。CSAPP 教材中提供了一个非常实用的工具包——**RIO（Robust I/O）包**。RIO 的核心思想就是一个"循环"：不管系统调用返回了多少字节，循环调用直到读够/写够为止。

RIO 提供两类函数：

- **无缓冲版本**：`rio_readn()` 和 `rio_writen()`，直接处理 short count
- **带缓冲版本**：`rio_readlineb()` 和 `rio_readnb()`，在内置缓冲区中读取，避免每个字节都做系统调用

```asm
// RIO 无缓冲版本：保证读/写 n 字节
ssize_t rio_readn(int fd, void *usrbuf, size_t n) {
    size_t nleft = n;
    ssize_t nread;
    char *bufp = (char *)usrbuf;

    while (nleft > 0) {
        if ((nread = read(fd, bufp, nleft)) < 0) {
            if (errno == EINTR)  // 被信号中断，重新读
                nread = 0;
            else
                return -1;       // 真正的错误
        } else if (nread == 0) {
            break;               // EOF
        }
        nleft -= nread;
        bufp += nread;
    }
    return n - nleft;            // 返回实际读到的字节数
}

// RIO 带缓冲版本：内部维护一个 buffer
// rio_readlineb 从缓冲区中逐字节扫描，直到遇到换行符
// 这样避免了每个字符都调用 read() 的巨大开销
```

注意代码中的 `EINTR` 检查。系统调用被信号中断时，它返回 -1 并设置 `errno = EINTR`。对于慢速设备（如终端、网络套接字），这种情况经常发生。如果我们的代码不处理 `EINTR`，就会误判为 I/O 错误。

::: info
**真实踩坑故事**：一位同事在开发一个高并发的代理服务器时，使用 `read()` 从网络套接字读取 HTTP 请求。在低流量压力测试下一切正常，但在生产环境收到大量请求时，`read()` 经常返回 1024 字节而不是他预期的 4096 字节。他的代码是做了一次 `read(fd, buf, 4096)`，然后假设数据已经全部到位，直接开始解析。结果是——请求被截断了，解析失败，服务返回 400 错误。这个 bug 花费了整整一个下午才排查出来。解决方案就是用 RIO 风格的循环读取。
:::

这个 bug 的根本原因是什么呢？网络数据是分片到达的。TCP 是流式协议，没有"消息边界"的概念。你调一次 `read()` 最多只能读到现在内核缓冲区里已有的数据——如果只到了 1024 字节，你就只能读到 1024 字节。这不是错误，这是 TCP 的正常行为。你必须反复调用 `read()` 直到拿到完整的消息。

讲到这里，我们已经把 Unix I/O 的核心机制学完了。从文件描述符到系统调用，从重定向到缓冲机制，再到鲁棒的 RIO 封装——这些都是系统编程的"基本功"。下一章，我们将把这些知识应用到**网络编程**中。你会发现，网络 I/O 本质上就是文件 I/O 的一种特例——毕竟，"一切皆文件"。


## 实验：验证本章知识

在 [实验工程总览](/labs/) 中选择「文件描述符共享」，通过编译运行与 CTest 黄金测试观察POSIX `dup()` 共享当前文件偏移。先预测输出，再验证结果；该实验用于理解机制，不直接代表硬件性能。
