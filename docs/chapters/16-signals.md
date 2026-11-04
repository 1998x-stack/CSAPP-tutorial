---
title: "异常控制流——信号"
description: "信号发送与接收 · 信号处理函数安全写法 · sigaction与信号阻塞 · setjmp/longjmp跳转"
outline: [2, 3]
---

# 第十六章：异常控制流——信号

想象一下：你写了一个服务，在后台安静地运行了三天。突然终端上跳出一个 `Segmentation fault (core dumped)`。程序为什么会收到这个信号？是谁发给它的？能不能在程序里拦住这个信号做一些清理操作再退出？这些问题，就是本章要回答的。

上一章我们讨论了异常、系统调用、fork 和 execve——这些都是"同步"的控制流突变：程序主动或被动地让内核接管控制权。而**信号（signal）**是另一种更灵活的 ECF 形式——它允许内核（或其他进程）**异步地**通知目标进程一个事件的发生。信号处理函数的执行，完全打断了程序的正常控制流，这既赋予了程序响应外部事件的能力，也引入了一系列微妙的陷阱。

## 16.1 信号的发送与接收

信号的"发送"是指内核更新目标进程的某个 pending 位，"接收"是指目标进程在从内核态返回用户态之前检查这些位并触发处理。以下是最常见的一些信号：

| 信号 | 默认行为 | 典型触发场景 |
| --- | --- | --- |
| `SIGINT` (2) | 终止进程 | 键盘按下 Ctrl+C |
| `SIGKILL` (9) | 终止进程（不可捕获/忽略） | `kill -9` |
| `SIGSEGV` (11) | 终止并产生 core dump | 访问非法内存地址（段错误） |
| `SIGFPE` (8) | 终止并产生 core dump | 除零错误或浮点运算异常 |
| `SIGALRM` (14) | 终止进程 | `alarm()` 定时器到期 |
| `SIGCHLD` (17) | 忽略 | 子进程停止或退出 |
| `SIGTERM` (15) | 终止进程 | `kill` 命令默认发送 |
| `SIGPIPE` (13) | 终止进程 | 向已关闭的管道/套接字写入 |

::: info
**关键区分**：`SIGKILL` 和 `SIGSTOP` (19) 是两个"无敌"的信号——程序不能捕获、不能忽略、也不能阻塞它们。这保证了管理员永远有办法杀死一个失控的进程。其他信号都可以被捕获或忽略。
:::

一个经常被忽视的点：**SIGPIPE**。当你往一个已经关闭的 TCP 连接或管道写数据时，内核会直接发 SIGPIPE 杀死你的进程。很多网络服务的意外退出就是这个信号干的——解决方法是在启动时调用 `signal(SIGPIPE, SIG_IGN)` 忽略它，让 `write()` 正常返回 -1 而不是直接崩掉。

## 16.2 信号处理函数的正确写法

信号处理函数有一个根本性的约束：它和主程序是**并发执行**的（虽然是单核意义上的"并发"）。这意味着你永远不知道信号到来时，主程序恰好执行到了哪一行。因此，信号处理函数必须遵守一套严格的规则：

```c
#include <signal.h>
#include <unistd.h>

volatile sig_atomic_t got_signal = 0;

void handle_signal(int sig) {
    // 仅设置一个标志位——这是安全的
    got_signal = 1;
}

int main() {
    signal(SIGINT, handle_signal);

    while (1) {
        if (got_signal) {
            // 主循环检查标志位，做实际处理
            write(STDOUT_FILENO, "收到信号，准备清理...\n", 22);
            got_signal = 0;
        }
        // 做正常的工作...
    }
    return 0;
}
```

上面这段代码遵循了信号处理的核心模式——处理函数只做最小的事情，具体的逻辑交给主循环。这里的关键是 `volatile sig_atomic_t`：

- `volatile` 告诉编译器每次访问都从内存读取，不要用寄存器缓存的值——否则主循环可能永远看不到标志位的更新。
- `sig_atomic_t` 保证读写是原子的——在常见的架构上就是 `int`。

信号处理函数内部**严禁**调用非异步信号安全的函数。常见的"安全函数"列表包括 `write()`、`_exit()`、`sigaction()` 等。而 `printf()`、`malloc()`、`free()`、`fgets()` 都是不安全的——因为它们内部可能持有锁，如果信号在主程序持有锁的间隙到达，就会产生死锁。

::: warning
**真实踩坑故事**：我曾经在一个信号处理函数里写了 `free()` 来释放一些全局资源。看起来挺合理？结果线上死锁了。原因是 `malloc`/`free` 内部使用了一个全局锁（arena lock），信号到来时主程序可能正处在 `malloc` 内部，已经拿了锁。信号处理函数里的 `free()` 也想拿同一把锁——于是一个线程死锁了自己。这就是"重入（reentrant）"问题：信号处理函数必须假设自己打断了一条不安全的代码路径。
:::

## 16.3 信号阻塞与sigaction

信号阻塞有两种形式：

- **隐式阻塞**：当内核正在执行某个信号的处理函数时，这个信号会被自动阻塞，直到处理函数返回。这防止了同一信号无限递归。
- **显式阻塞**：调用 `sigprocmask()` 有选择地阻塞一组信号。这用于保护临界区——不希望被信号打断的关键代码段。

提到信号处理函数的注册，就不得不比较 `signal()` 和 `sigaction()`：

```c
#include <signal.h>

void handler(int sig) { /* ... */ }

int main() {
    struct sigaction sa;
    sa.sa_handler = handler;
    sigemptyset(&sa.sa_mask);       // 处理期间不额外阻塞信号
    sa.sa_flags = SA_RESTART;       // 自动重启被中断的系统调用

    sigaction(SIGINT, &sa, NULL);   // 注册 SIGINT 的处理函数

    // 显式阻塞 SIGINT，保护临界区
    sigset_t mask, old_mask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGINT);
    sigprocmask(SIG_BLOCK, &mask, &old_mask);

    // 临界区：不希望被 SIGINT 打断的代码
    // ...

    // 恢复原来的信号掩码
    sigprocmask(SIG_SETMASK, &old_mask, NULL);
    return 0;
}
```

::: tip
**为什么推荐 sigaction 而不是 signal？**历史原因：早期 Unix 的 `signal()` 在不同系统上行为不一致。有些系统在处理函数执行后会自动把信号重置为默认行为，导致需要重新注册；有些系统不会自动重启被中断的慢速系统调用（如 `read()` 等待套接字数据时被信号中断会返回 `EINTR`）。`sigaction()` 是 POSIX 标准的接口，行为在所有现代 Unix 上一致。即使你觉得麻烦，也请养成用 `sigaction` 的习惯。
:::

## 16.4 非本地跳转

正常情况下，函数的调用和返回遵循严格的栈结构——`setjmp/longjmp` 打破了这一规则。它们允许程序从一个函数调用**直接跳转**到另一个函数，跨越中间所有的栈帧。

```c
#include <setjmp.h>
#include <stdio.h>

jmp_buf env;

void risky_function() {
    if (/* 发生不可恢复的错误 */) {
        longjmp(env, 1);  // 跳回 setjmp 处，返回值为 1
    }
}

int main() {
    if (setjmp(env) == 0) {
        // 正常路径
        risky_function();
    } else {
        // 错误恢复路径
        printf("从错误中恢复过来了！\n");
    }
    return 0;
}
```

`setjmp` 保存当前的寄存器状态、栈指针、程序计数器到 `jmp_buf` 中。第一次调用返回 0。`longjmp` 从 `jmp_buf` 恢复这些寄存器的值——相当于把程序的执行"传送"回之前的某个执行点。第二个参数（上面的 1）成为 `setjmp` 的返回值。

这个机制的两个重要应用场景：

- **错误恢复**：在深层嵌套的调用链中发生错误时，不用一层层返回错误码，直接 longjmp 到顶层的错误处理逻辑。
- **信号处理中的跳转**：信号处理函数可以 longjmp 回主循环，用于实现超时机制——比如用 `SIGALRM` 打断一个可能永远阻塞的 `read()` 调用。

有趣的是，C++ 和 Java 中的 `try`/`catch`/`throw` 异常机制，其底层原理与 `setjmp/longjmp` 非常相似。只不过语言级别的异常还会做更多工作——栈展开时的析构函数调用、异常类型匹配等。

::: info
**例外**：使用 longjmp 要格外小心。如果从信号处理函数中 longjmp 出去，信号掩码可能不会被正确恢复，导致该信号被永久阻塞。正确的做法是使用 `sigsetjmp/siglongjmp`，它们会保存和恢复信号掩码。
:::

信号是用户态最强大的异步事件处理机制。但如果使用不当，死锁、竞态条件、未定义行为随时可能出现。从下一章开始，我们将进入计算机系统中另一个革命性的抽象——**虚拟内存**。它让每个进程仿佛拥有整个地址空间，而信号机制将在这个过程中继续扮演"事件通知"的角色。
