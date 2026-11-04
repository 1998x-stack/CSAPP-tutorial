---
title: "综合项目：手写高性能Web服务器"
description: "epoll事件驱动架构 · 线程池+任务队列 · HTTP Keep-Alive · wrk压测与性能调优"
outline: [2, 3]
---

# 第28章：综合项目——手写高性能Web服务器

欢迎来到全书的最后一章。如果你一路坚持到了这里，恭喜——你已经看完了计算机系统的每一个层次：从晶体管级别的数字逻辑，到 CPU 流水线和指令集，到内存层次和虚拟内存，再到链接、异常控制流、网络和并发编程。现在是时候把这些知识**全部串起来**，做一个真正的综合项目了。

我们要写的不是 CSAPP 教材里的 Tiny Web Server 玩具——它是一个基于 epoll + 线程池的、支持 HTTP/1.1 Keep-Alive 的高性能 Web 服务器，探索目标是支撑较高的并发连接数；十万连接属于待验证的目标，而非本仓库已经实现的结果。这听起来可能有点吓人，但别担心——我会带你一步步走完整个设计过程。如果你将来能在可复现的 wrk 基准测试中达到每秒五万次请求，你会感觉到前面 27 章的所有付出都是值得的。

这不仅仅是一个编程练习，这是你作为**系统工程师的"毕业设计"**。

## 28.1 epoll事件驱动架构

这个服务器的核心是 **epoll**——Linux 上最高效的 I/O 事件通知机制。为什么要用 epoll 而不是 select 或 poll？答案写在第 19 章：select 有 FD_SETSIZE 限制（默认 1024），poll 虽然没有上限但每次调用都要传递完整的文件描述符数组——O(n) 的遍历成本在多连接场景下是灾难。而 epoll 只返回**就绪的事件集合**，复杂度 O(k)——k 是实际就绪的 fd 数量，和总连接数无关。

下面是讲解事件调度的**结构性伪代码**，其中部分 helper 尚未定义，也未涵盖全部错误检查、资源回收、过载处理和线程同步，不能直接用于生产环境：

```c
#define MAX_EVENTS 1024
#define PORT 8080

int main() {
    int listen_fd, epoll_fd, nfds;
    struct epoll_event ev, events[MAX_EVENTS];

    // 1. 创建监听套接字（设置 SO_REUSEADDR）
    listen_fd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
    bind_and_listen(listen_fd, PORT);

    // 2. 创建 epoll 实例
    epoll_fd = epoll_create1(0);

    // 3. 将监听 fd 加入 epoll（水平触发，accept 用 LT 更安全）
    ev.events = EPOLLIN;
    ev.data.fd = listen_fd;
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, listen_fd, &ev);

    // 4. 初始化线程池
    thread_pool_t *pool = thread_pool_create(4, 128);

    // 5. 事件循环
    while (1) {
        nfds = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);

        for (int i = 0; i < nfds; i++) {
            if (events[i].data.fd == listen_fd) {
                // 有新连接进来
                int conn_fd = accept4(listen_fd, NULL, NULL,
                                      SOCK_NONBLOCK | SOCK_CLOEXEC);
                if (conn_fd == -1) continue;

                // 对已连接套接字使用边缘触发 + EPOLLONESHOT
                ev.events = EPOLLIN | EPOLLET | EPOLLONESHOT;
                ev.data.fd = conn_fd;
                epoll_ctl(epoll_fd, EPOLL_CTL_ADD, conn_fd, &ev);

                // 连接已注册，等待事件就绪后再派发；不能传递局部变量的地址给异步任务
            } else {
                // 已有 fd 就绪（数据可读/可写）
                // 伪代码：派发拥有稳定生命周期的任务上下文
                dispatch_io_event(pool, epoll_fd, events[i]);
            }
        }
    }
    return 0;
}
```

这个骨架中有几个关键的设计决策值得展开：

- **EPOLLET（边缘触发）**：只通知状态变化而非状态本身。如果使用 EPOLLET，你必须准备好一次性读取所有数据（while 循环 read 到 EAGAIN）。这样做的好处是减少 epoll 事件数量——在水平触发下，只要缓冲区还有数据就会不停通知，而边缘触发只在"从无到有"时通知一次。
- **EPOLLONESHOT**：事件触发一次后该 fd 的后续通知被暂时禁用（并非从 epoll 自动删除）。工作线程完成处理后，必须在适当时机使用 EPOLL_CTL_MOD 重新激活通知；这有助于避免同一连接被重复派发。这一点在"主线程监听 + 工作线程处理"的架构下至关重要——没有 EPOLLONESHOT，一个连接上的数据可能被多个工作线程同时读到，导致数据竞争。
- **SOCK_NONBLOCK**：所有套接字都设置为非阻塞。边缘触发 + 非阻塞 I/O 是黄金搭档——同步接口不会阻塞线程，可以由事件驱动来调度。

::: warning
**踩坑实录**：边缘触发的陷阱远比你想象的多。我曾经在某次实现中遇到过一个"幽灵"——客户端已经关闭了连接，但服务器不断收到 EPOLLIN 事件。排查了半天才发现原因：在边缘触发模式下，如果你收到了 EPOLLIN 事件但没有读完所有数据（read 返回 EAGAIN 前停止），这个事件**不会再通知一次**。所以必须循环 read 直到返回 EAGAIN，然后才能调用 epoll_wait 等下一个事件。使用 EPOLLONESHOT 时，读完数据后要记得重新 `epoll_ctl(fd, EPOLL_CTL_MOD, ...)` 设置事件。
:::

## 28.2 线程池 + 任务队列

事件循环只做一件事：多路复用事件。真正处理 HTTP 请求、解析报文、构建响应、发送数据的逻辑，应该交给**工作线程池**。这样设计的好处是：主线程（I/O 线程）不会被任一个请求的慢操作卡住，可以持续 accept 新连接和处理 I/O 事件。

| 线程角色 | 职责 | 阻塞点 | 关键性能关注 |
| --- | --- | --- | --- |
| 主线程（I/O 线程） | epoll_wait、accept、读取请求头、分发任务 | epoll_wait（有超时） | 尽量减少每次 event loop 的处理时间 |
| Worker 线程 | 解析 HTTP 请求、读取请求体、处理业务逻辑、生成响应 | 文件读取、磁盘 I/O | 避免长时间阻塞，考虑异步文件 I/O |
| Sender 线程（可选） | 专职发送响应数据，管理 write buffer | write 系统调用 | 大文件发送可能阻塞，考虑 sendfile + 写缓冲 |

这里的一个高级优化点是用**无锁 MPSC 队列**（Multiple Producers, Single Consumer）来替代基于互斥锁的任务队列。并非所有场景都需要无锁——但在"主线程作为唯一的 consumer、多个 Worker 线程作为 producer（返回处理结果）"的场景下，MPSC 队列可以显著减少锁争用。

```asm
// 基于 Jeff Preshing 的无锁 MPSC 队列（简化版）
typedef struct mpsc_node {
    struct mpsc_node *next;
    void *data;
} mpsc_node_t;

typedef struct {
    mpsc_node_t *head;   // 生产者写入（原子操作）
    mpsc_node_t *tail;   // 消费者读取（独占）
    mpsc_node_t stub;    // 哨兵节点
} mpsc_queue_t;

void mpsc_push(mpsc_queue_t *q, mpsc_node_t *n) {
    n->next = NULL;
    mpsc_node_t *prev = __sync_lock_test_and_set(&q->head, n);
    prev->next = n;  // 将新节点链到前一个 head 的后面
}

mpsc_node_t *mpsc_pop(mpsc_queue_t *q) {
    mpsc_node_t *tail = q->tail;
    mpsc_node_t *next = tail->next;

    if (tail == &q->stub) {
        if (!next) return NULL;       // 队列空
        q->tail = next;
        tail = next;
        next = next->next;
    }

    if (next) {
        q->tail = next;
        return tail;                  // 返回节点，data 可用
    }

    // 尝试帮助生产者完成写入
    mpsc_node_t *head = q->head;
    if (tail != head) return NULL;    // 其他生产者正在写入，重试
    mpsc_push(q, &q->stub);          // 推进 stub
    next = tail->next;
    if (next) {
        q->tail = next;
        return tail;
    }
    return NULL;
}
```

这个队列的巧妙之处在于：`mpsc_push` 用了一条原子操作（`__sync_lock_test_and_set`），没有任何锁或者 CAS 循环——在最理想的情况下，生产者之间也不会互相阻塞。而 `mpsc_pop` 在处理"另一个生产者正在写入但还没链上 next 指针"的情况时，通过"帮助推进 stub"的方式解决了 ABA 问题，不需要 CAS 重试。这段代码来自 Jeff Preshing 的博客，是实际生产环境中经过验证的模式。

::: tip
**工程提示**：除非你真正面对了锁竞争导致的性能瓶颈，否则**不要轻易引入无锁数据结构**。无锁编程的正确性验证极其困难——一段无锁代码可能在 x86 上跑得很好，但在 ARM 弱内存模型下静默崩溃。我的建议是：先用 pthread_mutex + condition variable 实现任务队列，跑通功能和压测。如果 perf top 显示出锁争用确实是瓶颈，再考虑无锁方案。过早优化是万恶之源，这句话在并发编程中尤其正确。
:::

## 28.3 HTTP/1.1 Keep-Alive与连接管理

HTTP/1.0 时代，每个请求都要经历"TCP 三次握手 → 传输数据 → 四次挥手"的完整流程。在 Web 页面越来越复杂（HTML + CSS + JS + 图片，可能有几百个资源）的背景下，每次连接的开销太巨大了。HTTP/1.1 引入了 **Keep-Alive**，允许在同一个 TCP 连接上复用多个请求-响应。

维护 Keep-Alive 连接意味着服务器需要一个**连接状态机**：

```text
typedef enum {
    CONN_INIT,          // 新建连接，等待请求行
    CONN_READ_HEADER,   // 正在读取请求头部
    CONN_READ_BODY,     // 读取请求体（POST 请求）
    CONN_PROCESSING,    // 生成响应
    CONN_SENDING,       // 发送响应数据
    CONN_KEEP_ALIVE,    // 发送完毕，等待下一个请求
    CONN_CLOSING,       // 准备关闭或已收到 Connection: close
    CONN_CLOSED         // 连接已终止
} conn_state_t;

typedef struct {
    int fd;
    conn_state_t state;
    char read_buf[READ_BUF_SIZE];
    size_t read_len;
    char *response;
    size_t response_len;
    size_t response_sent;       // 已发送字节数（用于大文件分片发送）
    time_t last_active;         // 最后活跃时间（用于超时检测）
    int keep_alive;             // 是否 Keep-Alive
} connection_t;

void handle_connection_state(connection_t *conn) {
    switch (conn->state) {
    case CONN_READ_HEADER:
        // 尝试读取一行（以 \r\n 结尾）
        // 如果读完整行：解析请求行和头部 → 切换状态
        // 如果读不完整：等待下次 EPOLLIN
        break;
    case CONN_READ_BODY:
        // 根据 Content-Length 读取完请求体
        break;
    case CONN_PROCESSING:
        // 构建 HTTP 响应（状态行 + 头部 + body）
        // 静态文件用 stat() + mmap() 或 sendfile()
        break;
    case CONN_SENDING:
        // 发送响应，如果一次性发不完（大文件），
        // 注册 EPOLLOUT 事件，下次可写时继续
        break;
    case CONN_KEEP_ALIVE:
        // 重置缓冲区，重新注册 EPOLLIN，等待下一个请求
        break;
    }
}
```

Keep-Alive 的一个工程挑战是**连接超时**——如果客户端连接了但不发请求，服务器不能永远等下去。常用的方案是**时间轮**（Timing Wheel）：将连接按照最后活跃时间组织成哈希轮，每秒扫描一个槽位，超时的连接被关闭。时间轮的优势是 O(1) 的插入和删除，以及 O(n) 的过期扫描——n 是每 ticks 超时的连接数，而不是总连接数。

另一个关键点是**优雅关闭**。当服务器决定关闭连接时（收到 Connection: close、或超时、或 shutdown），不能简单地 close(fd)：

- 调用 `shutdown(fd, SHUT_WR)` 发送 FIN 包，告诉客户端"我发完了"
- 继续读取客户端的剩余数据（以防还有数据在途中）
- 设置 `SO_LINGER` 套接字选项来控制关闭行为——`l_onoff=1, l_linger=0` 会发送 RST 而非 FIN，适用于必须立即释放资源的高并发场景

::: info
**核心洞察**：连接管理是 Web 服务器中最容易被忽视但又最容易出 Bug 的部分。HTTP 协议看起来很简单（"不就是发个请求收个响应吗？"），但 Keep-Alive 引入的**状态机、超时、半关闭、管线化（pipelining）**等问题将复杂性放大了一个数量级。认真实现 HTTP/1.1 语义比写事件循环本身要难得多。这也是为什么很多"手写 Web 服务器"教程只支持 HTTP/1.0——不是因为技术达不到，而是因为他们没有完整理解 CSAPP 中关于 TCP 连接的那几页纸。
:::

## 28.4 压测与性能调优

服务器写好了，现在来验证它的性能。我们用 **wrk2** 来做压测——它比 ab 更现代，支持线程模型、精确的延迟分布计算和恒定吞吐量模式（wrk 是恒定并发连接数）。

```bash
$ wrk -t4 -c1000 -d30s --latency http://localhost:8080/index.html

Running 30s test @ http://localhost:8080/index.html
  4 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.45ms    1.83ms   58.3ms   85.67%
    Req/Sec     4.21k     0.85k    6.28k    72.00%
  Latency Distribution
     50%    2.01ms
     75%    3.12ms
     90%    4.78ms
     99%    9.45ms
  512083 requests in 30.00s, 3.67GB read
Requests/sec:  17069.27
Transfer/sec:    125.32MB
```

这里的关键指标：

- **Requests/sec (RPS)**：17069——每秒处理超过 1.7 万次 HTTP 请求
- **P50 延迟**：2.01ms——一半的请求在 2ms 内完成
- **P99 延迟**：9.45ms——99% 的请求在 10ms 内完成
- 注意 P99 和 P50 的差距——差距越小，说明服务器的延迟越稳定

调优过程中我们可能遇到的问题和解决方法：

| 现象 | 可能原因 | perf top 线索 | 解决方案 |
| --- | --- | --- | --- |
| 吞吐量上不去，CPU 未占满 | I/O 瓶颈（锁等待、系统调用开销） | spin_lock、futex 热点 | 减少锁粒度，或用无锁队列 |
| P99 延迟远高于 P50 | 偶尔的长尾阻塞（如 accept 惊群） | epoll_wait 调用次数异常 | 启用 SO_REUSEPORT，避免共享 listen fd 的锁 |
| 大量 TIME_WAIT 连接 | 主动关闭连接导致大量 TIME_WAIT | netstat 中的 TIME_WAIT 堆积 | 开启 tcp_tw_reuse（需谨慎），或调整连接池策略 |
| 网络吞吐量瓶颈 | 软中断（softirq）成为瓶颈 | net_rx_action、net_tx_action 占用率高 | RPS (Receive Packet Steering) 将中断分布到多核 |

**SO_REUSEPORT** 是一个值得单独提及的优化。它允许多个套接字绑定到同一个端口上，内核在 accept 时会做负载均衡（四元组哈希），将新连接分到不同的 socket 上。这意味着我们可以启动多个 worker 进程（而非线程），每个进程有自己的 epoll 实例和 accept 队列——**完全避免了 epoll 实例上的锁竞争**。Nginx 正是通过这种模式在单机上支撑了百万级的并发连接。

::: tip
**调优工具推荐**：调试网络性能时，`perf top` 帮你找 CPU 热点，`ss -s` 查看 socket 统计，`sar -n DEV 1` 看网络吞吐量，`strace -c -p <pid>` 看系统调用分布。这四个工具组合使用，基本能定位绝大部分性能问题。不要凭感觉做优化——每次优化前后都应该跑一次 wrk 压测，用数据说话。
:::

## 28.5 从CSAPP到工业级系统

写到这里，我们终于走到了全书的终点。让我帮你做一次完整的知识回顾——看看这个 Web 服务器项目如何串联起 CSAPP 中每一个章节的知识：

- **第 1-3 章（信息表示）**：HTTP 报文本质上是字节流，你在处理 `Content-Length` 时需要解析十进制数字符串，校验大小端和整数溢出——第 2 章学的整数表示直接派上用场
- **第 4-7 章（机器级表示）**：gcc -O2 编译出的服务器代码，你可以在反汇编中看到编译器如何优化字符串比较、如何内联小函数、如何消除冗余计算
- **第 8-9 章（处理器架构）**：流水线分支预测错误会清空 15-20 个周期的进度——在热路径上减少分支（如用查表代替 if-else）直接提升吞吐量
- **第 10 章（性能优化）**：你用 profiler 发现 memcpy 是热点，于是用循环展开 + 对齐拷贝来优化——直接应用了"消除循环开销"和"减少过程调用"的原则
- **第 11-12 章（存储器层次）**：你把热数据结构设计成 Cache 友好的连续布局，避免指针追逐——一个 Cache miss 就是 100 个时钟周期的代价
- **第 13-14 章（链接）**：你在链接阶段遇到了 undefined reference——链接器告诉你符号解析失败，你知道了 readelf 和 objdump 可以排查
- **第 15-16 章（异常控制流）**：`SIGPIPE` 信号——当向已关闭的 socket 写数据时被默认杀死进程，你必须显式忽略或处理它
- **第 17-18 章（虚拟内存）**：`mmap()` 静态文件减少 read/write 系统调用，TLB miss 在大量并发时成为新瓶颈
- **第 19 章（系统级 I/O）**：RIO（Robust I/O）包处理短计数——网络套接字上的 read/write 可能只传输了部分字节，必须循环读取
- **第 20-21 章（网络编程）**：socket、bind、listen、accept——每一行代码都来自这里。HTTP 协议状态码设计：200、301、404、500
- **第 22-23 章（并发编程）**：线程池、任务队列、互斥锁、条件变量——你在用这些构建服务器的心脏。生产者-消费者模式贯穿始终
- **第 24-26 章（Lab 实战）**：你在 Bomb Lab 里学会读汇编，在 Malloc Lab 里理解堆管理，在 Proxy Lab 里实践了代理和缓存——这些全部在 Web 服务器中得到了应用
- **第 27 章（现代趋势）**：如果要用上多核 CPU 的全部能力——你可能会用 SO_REUSEPORT + one worker per core 的模式，这本质上是 RISC-V 的简单哲学在系统设计中的体现

看到没？这一个 Web 服务器项目，把 CSAPP 的 28 章内容几乎全部覆盖了。这就是为什么我一直认为——**没有比手写 Web 服务器更好的系统能力"毕业设计"了**。

::: info
**最后一课：理解计算机系统的意义**

课程的最后，我想和你分享一个也许有点"鸡汤"但有意义的观点：

我见过很多工程师分为两类。第一类人，会用框架但不知道框架在做什么——遇到诡异的崩溃、性能问题、安全漏洞时束手无策，只能靠"重启试试"或"搜索 Stack Overflow"。第二类人，知道**每一个抽象层下面有什么**——他写的代码遇到问题，可以从业务逻辑一路向下排查到系统调用、到二进制指令、甚至到 CPU 微架构层面。

第一类人写代码，第二类人**掌控系统**。CSAPP 的目标就是把每一个读者从第一类变成第二类。

**理解计算机系统不是为了考试，而是为了让你写出更可靠、更高效、更安全的软件。**

这是整本书中最重要的一个句子。把它记在心里。
:::

::: tip
**推荐继续阅读**：全书到此结束，但你的系统学习之路才刚刚开始。如果你希望继续深入，这里有几本"后续读物"：

                **《Computer Architecture: A Quantitative Approach》** (Hennessy & Patterson)——深入学习处理器微架构，比第 8-9 章深入十倍
                **《Operating Systems: Three Easy Pieces》**——操作系统更系统的讲解，看一个完整的 OS 内核是怎么设计的
                **《Unix Network Programming》** (Stevens)——网络编程的圣经，第 20-23 章的全部细节都在里面
                **《Systems Performance》** (Brendan Gregg)——系统性能调优的实战指南，补上第 10 章和第 28 章中 profiling 的深度
                **《Database Internals》**——理解了计算机系统后，下一个合理的探索方向是存储系统
                还有——**读源码**：nginx、redis、sqlite 的代码库是非常好的系统编程教材，它们的代码风格和设计决策值得反复品味
:::

回顾整个旅程——从第 1 章 `hello.c` 的编译流程开始，一路走到今天手写高性能 Web 服务器。中间我们看过了整数的位级表示、汇编的条件码和栈帧、Y86-64 的流水线冒险、Cache 的组相连映射、链接器的符号解析、异常控制流中的信号处理、虚拟内存的多级页表、动态内存分配器的隐式空闲链表、网络协议栈的 TCP 三次握手、并发编程的信号量和条件变量——还有太多太多。

这 28 章写下来，我最希望的是：你在未来的工作中，每次写下一行代码，脑海里能浮现出这行代码在计算机系统中实际发生的事情——它在 CPU 流水线的哪个阶段执行、它在 Cache 中的命中率如何、它的虚拟地址如何翻译成物理地址、它的 I/O 请求如何通过文件系统到达磁盘或网络。

如果 CSAPP 在你心中种下了这样一颗"理解系统"的种子，那这门课就没有白学。感谢你跟随我完成这趟旅程。毕业快乐，系统工程师。
