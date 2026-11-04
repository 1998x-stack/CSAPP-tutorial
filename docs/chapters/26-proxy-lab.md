---
title: "经典Lab实战(III)——Proxy Lab"
description: "并发Web代理架构 · 生产者消费者模型 · HTTP缓存层实现 · ab压测性能调优"
outline: [2, 3]
---

# 第26章：经典Lab实战(III)——Proxy Lab

如果 CSAPP 的所有 Lab 是一场考试，那 Proxy Lab 就是最后一道大综合题。前面的 Data Lab 考你位运算，Bomb Lab 考你汇编阅读，Malloc Lab 考你内存管理——它们都是单项技能测试。而 Proxy Lab 要求你把**网络编程、并发编程、缓存设计、系统级 I/O** 全部串起来，写一个真正能用的并发 Web 代理服务器。

我记得 CMU 的课程评价里，很多学生说 Proxy Lab 是"最虐但也收获最大的 Lab"。原因很简单：你写的不是一个玩具程序，而是一个真正在网络上收发数据的代理。当你第一次通过自己写的代理成功加载出一个网页时——那种成就感是其他 Lab 无法比拟的。当然，前提是你忍受了一整晚调试 `select()` 或 `epoll` 返回奇奇怪怪值的痛苦。

这一章我按照 Proxy Lab 的核心任务来组织：先讲并发代理的基本架构，然后深入生产者-消费者线程模型，接着是实现 HTTP 缓存层，最后用 ab 工具做性能测试。

## 26.1 并发Web代理架构

一个 HTTP 代理的本质是什么？简单来说：**代理同时扮演客户端和服务器**。它从浏览器（客户端）接收 HTTP 请求，解析后转发给目标 Web 服务器，再把服务器的响应回传给浏览器。整个过程对浏览器来说，代理就是"目标服务器"；对目标服务器来说，代理就是"浏览器"。

具体到一个多线程代理的实现，它需要以下几个核心组件：

| 组件 | 角色 | 功能描述 | 线程安全要求 |
| --- | --- | --- | --- |
| Listener 线程 | 主线程 | 绑定端口、accept 新连接，将已连接描述符放入缓冲区 | 仅主线程访问，无需锁 |
| Worker 线程池 | 消费者 | 从缓冲区取出连接描述符，执行 HTTP 请求转发/响应回传 | 缓冲区的互斥访问（信号量/锁） |
| Cache 层 | 共享资源 | 缓存 HTTP 响应（URI → content），LRU 淘汰 | 读写锁保护，支持并发读取 |
| Logger | 辅助 | 记录每次请求的日志（主机名、路径、响应大小等） | 写锁或独立日志线程 |

下面是一个请求的生命周期：

1. 浏览器发送 HTTP GET 请求到代理的监听端口（通常为 8888）
1. Listener 线程 accept 连接，将已连接描述符插入共享缓冲区
1. 某个 Worker 线程从缓冲区取出描述符，解析 HTTP 请求行和目标 URL
1. Worker 线程检查缓存：如果命中且未过期，直接返回缓存内容
1. 缓存未命中：Worker 线程与目标 Web 服务器建立 TCP 连接，发送请求
1. 收到服务器响应后，Worker 线程将响应回传给浏览器，同时尝试缓存
1. Worker 线程关闭与客户端的连接（或等待 keep-alive 下的下一个请求）

::: tip
**编程提示**：写代理时的头号陷阱是**阻塞 I/O 在并发模型中的位置**。如果你的 Worker 线程以阻塞方式读取客户端请求，而客户端传输很慢，这个线程就会被卡住无法服务其他请求。所以 Proxy Lab 的并发性需要仔细设计——要么用预线程化（prethreading），要么用非阻塞 I/O + 事件驱动。CSAPP 教材中建议用前一种方式，因为它更简单且足以应对 Lab 的要求。
:::

## 26.2 生产者-消费者线程模型

既然选择了多线程方案，我们需要一个线程安全的**有界缓冲区**（bounded buffer），让 Listener 线程（生产者）和 Worker 线程（消费者）之间传递连接描述符。CSAPP 教材中提供了一个非常优雅的 `sbuf` 包（safe buffer），我们用信号量来实现它。

```asm
typedef struct {
    int *buf;          // 缓冲区数组
    int n;             // 最大容量
    int front;         // 读索引
    int rear;          // 写索引
    sem_t mutex;       // 互斥信号量（保护索引操作）
    sem_t slots;       // 空槽位数量
    sem_t items;       // 已用槽位数量
} sbuf_t;

void sbuf_init(sbuf_t *sp, int n) {
    sp->buf = calloc(n, sizeof(int));
    sp->n = n;
    sp->front = sp->rear = 0;
    sem_init(&sp->mutex, 0, 1);
    sem_init(&sp->slots, 0, n);
    sem_init(&sp->items, 0, 0);
}

void sbuf_insert(sbuf_t *sp, int item) {
    sem_wait(&sp->slots);               // 等待空槽位
    sem_wait(&sp->mutex);               // 加锁
    sp->buf[sp->rear] = item;
    sp->rear = (sp->rear + 1) % sp->n;  // 环形缓冲区
    sem_post(&sp->mutex);               // 解锁
    sem_post(&sp->items);               // 增加已用槽位计数
}

int sbuf_remove(sbuf_t *sp) {
    sem_wait(&sp->items);               // 等待有可用项
    sem_wait(&sp->mutex);               // 加锁
    int item = sp->buf[sp->front];
    sp->front = (sp->front + 1) % sp->n;
    sem_post(&sp->mutex);               // 解锁
    sem_post(&sp->slots);               // 增加空槽位计数
    return item;
}
```

这个设计的美妙之处在于：**三个信号量各自承担了不同的职责**。`mutex` 保护索引操作的互斥性，`slots` 确保生产者不会在缓冲区满时继续写入，`items` 确保消费者不会在缓冲区空时去取数据。后两个信号量还天然地实现了**条件同步**——消费者在缓冲区空时自动阻塞，不用 busy-waiting 浪费 CPU。

那么主程序的结构就是：

```c
int main(int argc, char **argv) {
    int listenfd, connfd;
    socklen_t clientlen;
    struct sockaddr_in clientaddr;
    sbuf_t sbuf;

    listenfd = Open_listenfd(argv[1]);    // 创建监听套接字
    sbuf_init(&sbuf, SBUFSIZE);           // 初始化有界缓冲区
    for (int i = 0; i < NTHREADS; i++)    // 创建 Worker 线程池
        Pthread_create(&tid, NULL, thread, &sbuf);

    while (1) {
        clientlen = sizeof(clientaddr);
        connfd = Accept(listenfd, (SA *)&clientaddr, &clientlen);
        sbuf_insert(&sbuf, connfd);        // 将连接交给 Worker 线程
    }
}

void *thread(void *vargp) {
    sbuf_t *sp = (sbuf_t *)vargp;
    Pthread_detach(pthread_self());
    while (1) {
        int connfd = sbuf_remove(sp);     // 取一个连接处理
        serve_client(connfd);             // 解析请求、转发、回传
        Close(connfd);
    }
}
```

这就是一个典型的**预线程化服务器**（prethreaded server）。Listener 线程只负责 accept，Worker 线程在启动时全部创建好，永不销毁。相比于"每来一个连接创建一条线程"的按需模式，预线程化避免了频繁创建/销毁线程的开销，响应延迟更稳定。

::: info
**核心洞察**：sbuf 包的三个信号量设计是并发编程中**互斥 + 同步分离**的经典范例。初学者往往只用一把大锁保护整个缓冲区——这样虽然正确，但消费者在空缓冲区上会 busy-waiting 浪费 CPU 时间。用两个计数信号量来做条件同步，是更高阶的思维。这个模式在你以后写生产者-消费者队列时会反复用到。
:::

## 26.3 HTTP缓存层实现

代理的第二个核心功能是**缓存**。如果每次请求都要去目标服务器取数据，代理就只起到了"中间人"的作用，并没有提升用户体验。加上缓存后，同一个资源第二次请求时，代理可以直接返回本地缓存的内容，响应时间可以从几百毫秒降到几微秒。

在 Proxy Lab 中，缓存需要满足以下设计要求：

- **缓存键**：使用完整的 URI（含 query string）作为键
- **缓存值**：存储整个 HTTP 响应（状态行 + 头部 + 响应体）
- **过期策略**：采用 LRU（Least Recently Used）淘汰最久未访问的条目
- **最大容量**：配置总缓存大小的上限（如 1MB）
- **线程安全**：多个 Worker 线程可以同时读取缓存，写操作需要互斥

| 操作 | 锁类型 | 说明 | 时间复杂度 |
| --- | --- | --- | --- |
| cache_lookup(uri) | 读锁 | 在哈希表中查找 URI，若命中则更新 LRU 链表，返回响应数据 | O(1) 平均 |
| cache_insert(uri, response) | 写锁 | 插入新条目，若缓存满则逐出 LRU 尾部条目，必要时更新全局总大小 | O(1) 均摊 |
| cache_evict() | 写锁 | 淘汰最久未使用的条目，直到缓存空间足够容纳新条目 | O(1) |

实现时的一个关键决策：**读写锁 vs 互斥锁**。考虑到缓存读远多于写的特性（一个热门资源可能被几千个请求读取，但只在首次写入），用读写锁可以大幅提升并发度。多个 Worker 线程可以同时进行 cache_lookup，只有当某个线程需要 insert 时才会阻塞其他访问者。

```text
typedef struct cache_entry {
    char uri[MAX_URI_LEN];
    char *content;                // 完整的 HTTP 响应
    size_t content_size;
    struct cache_entry *prev;     // LRU 链表指针
    struct cache_entry *next;
    time_t timestamp;
} cache_entry_t;

typedef struct {
    cache_entry_t *head;          // LRU 链表头（最近使用）
    cache_entry_t *tail;          // LRU 链表尾（最久未用）
    size_t total_size;            // 当前缓存总大小
    size_t max_size;              // 缓存上限
    pthread_rwlock_t rwlock;      // 读写锁
} cache_t;

void cache_lookup(cache_t *cache, const char *uri,
                  char **out_content, size_t *out_size) {
    pthread_rwlock_rdlock(&cache->rwlock);
    // 哈希查找 URI → 命中则更新 LRU 位置
    // 注意：更新 LRU 本质上需要写链表，但这里可以用
    // 读锁升级的技巧——在严格实现中需要写锁
    // 注意：读锁下不能修改链表! 实际操作时需要写锁
    // 这里简化展示思路
    pthread_rwlock_unlock(&cache->rwlock);
}
```

上面的代码中有一个隐含的问题：**LRU 更新需要修改链表，但这和读锁矛盾**。一种实用的解决方案是：在读锁保护下查找并拷贝数据（不对 LRU 链表做修改），只在写锁下进行插入和 LRU 淘汰。这样做的代价是"访问顺序"不绝对精确，但换来了极高的读并发——在代理场景下，这种 tradeoff 是值得的。

::: warning
**踩坑实录**：我在实现 Proxy Lab 的缓存时遇到过一个经典的死锁问题。我的代码流程是：cache_lookup 获取读锁 → 发现 URI 不存在 → 释放读锁 → 获取写锁 → 再次检查 URI（double-checked locking）。但问题在于，在释放读锁和获取写锁之间，另一个线程可能已经插入了这个 URI。如果不做 double-check，就会覆盖已有的缓存。更隐蔽的问题是——当多个线程同时发现缓存未命中时，它们会竞争写锁，只有第一个线程去真正请求服务器，后面的线程必须等待。这就是**缓存惊群（cache stampede）**，高性能缓存系统必须处理的经典问题。
:::

## 26.4 性能测试与调优

代理写好了，它到底有多快？我们用 **ApacheBench (ab)** 来做压力测试。ab 是一个轻量级的 HTTP 压测工具，可以指定并发数和总请求数，输出吞吐量、延迟分布等关键指标。

以下输出仅演示性能报告的格式，**不是本仓库在真实环境中复现的测量结果**。正式测试须记录 CPU、系统版本、编译选项、服务端负载和完整测试脚本。

```bash
$ ab -n 10000 -c 50 http://localhost:8888/http://example.com/

Server Software:        TinyWebServer
Document Length:        1256 bytes
Concurrency Level:      50
Time taken for tests:   3.452 seconds
Complete requests:      10000
Requests per second:    2896.88 [#/sec] (mean)
Time per request:       17.260 [ms] (mean)
Percentage of requests served within a certain time (ms):
  50%    15
  90%    25
  99%    48
```

不同代理模型的**示意性假设数据**（未验证，不能用于性能结论）：

| 模型 | 并发级别 | 吞吐量 (req/s) | P50 延迟 (ms) | P99 延迟 (ms) | CPU 利用率 |
| --- | --- | --- | --- | --- | --- |
| 单线程（迭代 accept） | 50 | ~1,200 | 38 | 112 | 15% |
| 每连接一线程 | 50 | ~2,400 | 20 | 58 | 45% |
| 预线程化（4 Worker） | 50 | ~3,500 | 14 | 42 | 55% |
| 预线程化（8 Worker）+ 缓存命中 | 50 | ~12,000+ | 4 | 12 | 40% |

这些假设结果可以用来讨论影响性能的因素，但实际结论必须通过统一环境的重复基准测试证明：

- 单线程模型的问题在于——一个慢请求会 blocking 后续所有请求。因为 `accept()` 之后的服务过程是串行的
- 每连接一线程模型虽然解决了并发问题，但线程创建/销毁的开销在连接频繁断开时非常显著
- 预线程化模型将线程的创建成本前置到启动阶段，Worker 线程在程序生命周期内永不消亡——具体收益依赖负载，不能断言在所有情况下都是最高效的方案
- 缓存命中时性能提升极其显著（3 倍以上）——这说明磁盘/网络 I/O 是真正的瓶颈，缓存减少了绝大部分的网络往返

::: info
**实战洞察**：做 Proxy Lab 的性能测试时，我遇到过一个非常反直觉的现象——增加 Worker 线程数到一定程度后，吞吐量**不再增长甚至下降**。分析后发现原因是：过多的线程导致上下文切换开销超过了并发带来的收益。在 Linux 上，用 `perf context-switches` 可以清楚地看到这一点。这再次印证了 Amdahl 定律——如果代理的瓶颈在网络 I/O（即等待网络响应的空闲时间），那么工作线程数不应简单等同于并发连接数，应结合非阻塞 I/O、任务队列、实际阻塞时间及吞吐和尾延迟测试调整。
:::

Proxy Lab 是 CSAPP 课程中通往综合能力的最后一块拼图。它要求你把网络编程（socket API、HTTP 协议）、并发编程（信号量、线程池、读写锁）和系统性能思维（缓存、瓶颈分析）融会贯通。写好这个 Lab，你已经具备了开发中等规模系统软件的基本能力。

下一章，我们将跳出 CSAPP 的传统范畴，看看现代计算机系统正在发生哪些激动人心的变化——从 RISC-V 开放指令集到 eBPF 内核可编程，从 GPU 异构计算到 CXL 新型互联。
