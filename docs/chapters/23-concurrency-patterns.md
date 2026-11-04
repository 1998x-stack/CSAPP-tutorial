---
title: "并发编程——高阶模式"
description: "读写锁(rwlock) · 线程池设计与实现 · 死锁预防与诊断 · Helgrind/TSan调试"
outline: [2, 3]
---

# 第二十三章：并发编程——高阶模式

上一章我们掌握了 Pthread 的基本功：怎么创建线程、怎么用 mutex 保护共享数据、怎么用条件变量做同步。这些就像是给你一把枪和几发子弹，能打中靶子，但真要上战场还远远不够。现实世界中的并发系统远比"几个线程抢一把锁"复杂——同一个数据可能有大量读者、少量写者；线程的创建和销毁需要几十微秒的开销，高频场景下根本承受不住；锁用不好就会死锁，死锁一发生整个服务就卡死了。

这一章我们来讨论这些"上了战场才遇到的问题"：读写锁怎么让读者并行、线程池如何复用线程减少开销、死锁怎么从设计层面避免，以及当并发 BUG 真的出现了，有哪些军火库里的工具能帮你定位。

## 23.1 读写锁——读者共享，写者独占

假如你有一个配置缓存，99% 的操作是读配置，只有 1% 是修改配置。用最基本的 mutex 保护当然可以——但它过于保守了：读操作之间本来不会互相干扰，mutex 却强制它们串行化。这就好比图书馆里明明有 100 个座位，管理员说"一次只准一个人进去读书"。

Pthread 提供了 **读写锁（readers-writer lock）** 来解决这个问题：`pthread_rwlock_t`。它的规则很简单——**多个读者可以同时持有读锁，但写者必须独占写锁**。也就是说：有写者在写时，任何人都不准读；没有写者时，所有读者可以同时读。

```c
#include <pthread.h>

pthread_rwlock_t rwlock = PTHREAD_RWLOCK_INITIALIZER;

// 读线程
void *reader(void *arg) {
    pthread_rwlock_rdlock(&rwlock);
    // 读取共享数据（多个读者可以同时进入这里）
    pthread_rwlock_unlock(&rwlock);
    return NULL;
}

// 写线程
void *writer(void *arg) {
    pthread_rwlock_wrlock(&rwlock);
    // 修改共享数据（独占，读者和其他写者都在等待）
    pthread_rwlock_unlock(&rwlock);
    return NULL;
}
```

下面这个对比表格清楚地展示了 mutex 和 rwlock 在读多写少场景下的差异：

| 特性 | pthread_mutex_t | pthread_rwlock_t |
| --- | --- | --- |
| 并发读 | 不支持，读操作之间也串行 | 支持，所有读者可同时进入 |
| 写者等待 | 所有等待者（读/写）公平竞争 | 写者等所有当前读者释放 |
| 读多写少场景 | 性能较差，锁竞争高 | 性能极好，读者几乎不竞争 |
| 开销 | 轻量，~25 ns/次 | 稍重，~40 ns/次 |
| 适用场景 | 读写比例接近，或临界区极小 | 读 >> 写（如配置缓存、路由表） |

::: warning
**读写锁的饥饿问题**：如果读者源源不断地进来，写者可能永远拿不到写锁——这叫"写者饥饿"。Linux 的 `pthread_rwlock` 默认偏向读者，在高并发下写者可能长时间得不到调度。解决办法之一是使用**写者优先**的变种（如 `pthread_rwlockattr_setkind_np` 设为 `PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP`），或是干脆用 RCU（Read-Copy-Update，Linux 内核的独门绝技）来彻底消灭读写锁的竞争。
:::

## 23.2 线程池——让线程"活"起来

在高并发服务中，每个任务都创建一个新线程是灾难性的——创建线程需要调用 `clone()` 系统调用、分配栈空间、注册 TLS，整套流程下来几十微秒。如果任务本身只执行几微秒（比如一次简单的日志写入），那创建线程的时间比干活的时间还长。

**线程池**的思路是：预先创建一批线程，让它们循环地从队列里取任务执行。线程不是"用完就死"，而是"干完活回来继续等任务"。这样就把线程创建的开销平摊到了每次任务执行中。下面是一个简单的线程池实现：

```c
#include <pthread.h>
#include <stdbool.h>

typedef struct task_s {
    void (*func)(void *arg);
    void *arg;
    struct task_s *next;
} task_t;

typedef struct {
    pthread_t *threads;     // 线程数组
    task_t *head, *tail;   // 任务队列（链表）
    pthread_mutex_t lock;
    pthread_cond_t notify;
    bool shutdown;          // "毒丸"信号：优雅关闭
} thread_pool_t;

void *worker(void *pool) {
    thread_pool_t *tp = (thread_pool_t *)pool;
    while (1) {
        pthread_mutex_lock(&tp->lock);
        while (tp->head == NULL && !tp->shutdown)
            pthread_cond_wait(&tp->notify, &tp->lock);
        if (tp->shutdown && tp->head == NULL) {
            pthread_mutex_unlock(&tp->lock);
            return NULL;
        }
        task_t *t = tp->head;
        tp->head = t->next;
        pthread_mutex_unlock(&tp->lock);
        t->func(t->arg);  // 执行任务（注意：锁已释放）
        free(t);
    }
}

void tp_submit(thread_pool_t *tp, void (*f)(void*), void *arg) {
    task_t *t = malloc(sizeof(task_t));
    t->func = f; t->arg = arg; t->next = NULL;
    pthread_mutex_lock(&tp->lock);
    if (tp->tail) tp->tail->next = t;
    else          tp->head = t;
    tp->tail = t;
    pthread_cond_signal(&tp->notify);
    pthread_mutex_unlock(&tp->lock);
}

void tp_shutdown(thread_pool_t *tp) {
    pthread_mutex_lock(&tp->lock);
    tp->shutdown = true;  // 设定"毒丸"
    pthread_cond_broadcast(&tp->notify);
    pthread_mutex_unlock(&tp->lock);
    for (int i = 0; i < NTHREADS; i++)
        pthread_join(tp->threads[i], NULL);
}
```

这个线程池有几个设计要点值得注意：

- **工作线程在条件变量上等待**，不需要轮询——这是最省 CPU 的等待方式。
- **任务执行时释放互斥锁**——如果执行任务时还握着锁，其他线程连提交任务都会被阻塞。
- **毒丸（poison pill）**——`shutdown = true` 是一个信号，告诉所有工作线程"别再等了，准备退出"。

## 23.3 死锁的预防——四个条件的逐一破解

死锁（deadlock）是所有并发程序员的噩梦。Coffman 等人在 1971 年总结出了死锁的**四个必要条件**，缺一不可。换句话说，只要打破其中任意一个，死锁就不可能发生。

| 条件 | 含义 | 破解方法 |
| --- | --- | --- |
| **互斥（Mutual Exclusion）** | 资源一次只能被一个线程使用 | 用无锁数据结构（lock-free）替代锁，或者用读写锁让读不互斥 |
| **持有并等待（Hold and Wait）** | 线程拿着一个锁的同时去请求另一个锁 | 一次性申请所有锁（原子获取），或者先释放已有锁再获取新锁 |
| **不可抢占（No Preemption）** | 锁一旦被持有，其他线程不能强行夺走 | 用 `pthread_mutex_trylock`，拿不到就释放已有锁，重试 |
| **循环等待（Circular Wait）** | 线程 A 等 B 的锁，B 等 C 的锁，C 等 A 的锁 | **锁顺序加锁（lock ordering）**——所有线程按固定顺序获取锁 |

实际工程中，最常用也最有效的是**打破循环等待**：给所有锁排一个全局顺序，所有线程必须按照这个顺序加锁，不得违反。比如锁 A 的编号为 1，锁 B 的编号为 2，那么任何线程如果同时需要 A 和 B，必须先锁 A 再锁 B，绝对不能反过来。

::: warning
**真实踩坑故事：支付系统的锁顺序翻转**——我有一个朋友（真的不是我自己）曾经在一个支付系统中按"账户 ID 大小"来排序加锁，逻辑上是想避免死锁。结果某次重构时，一个同事在一个新的转账接口中把顺序写反了：先锁 to_account，再锁 from_account。而老接口是先锁 from_account 再锁 to_account。当同时触发 A → B 和 B → A 两笔转账时，两个线程各持一锁、等对方释放——完美死锁。线上服务瞬间全部卡死，支付宝账单信息迟迟不回，直到监控报警手动 kill 进程。教训：**锁顺序必须用代码规范强制执行**，可以写一个 `lock_two_accounts(a, b)` 的辅助函数，内部按地址大小排序，彻底杜绝人为犯错的余地。
:::

::: info
**死锁检测工具**：在 Linux 上，可以用 `pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_ERRORCHECK)` 来启用 mutex 的错误检查模式——同一个线程重复加锁会立即报错，而不是死锁。如果你在用 GCC 的 `-fsanitize=thread`，它还能在运行时检测死锁并打印调用栈，诊断效果比肉眼 Review 代码好太多了。
:::

## 23.4 并发调试武器库

并发 BUG 是出了名的难以复现——每次运行结果可能都不一样，加个 `printf` 甚至会让它消失（Heisenbug）。好在工具链已经为我们准备了相当丰富的武器：

- **Valgrind Helgrind**：用 `valgrind --tool=helgrind ./your_program` 运行。Helgrind 会在运行时检测数据竞争——两个线程同时访问同一变量，且至少一个是写操作——并精确报告变量地址和调用栈。缺点是慢，程序会慢 10-50 倍。
- **ThreadSanitizer（TSan）**：编译时加 `-fsanitize=thread -g -O1`，运行时自动检测竞态。速度比 Helgrind 快得多（只慢 2-5 倍），精度也更高。是 Google 团队开发的业界标准。
- **GDB 多线程调试**：`info threads` 列出所有线程及当前指令；`thread apply all bt` 打印所有线程的完整调用栈——这个命令对于死锁诊断是神兵利器：你能一眼看出哪个线程拿着什么锁，在等什么锁。
- **perf lock**：`perf lock record ./your_program` 记录内核级锁事件；`perf lock report` 生成锁竞争报告，显示哪些锁的 contention 最高。

::: tip
**TSan 使用实战**：假设你怀疑程序有数据竞争，但又不知道在哪里。只需三步：(1) CFLAGS 加上 `-fsanitize=thread -g -O1 -fno-omit-frame-pointer`；(2) 重新编译；(3) 运行。TSan 会在第一次检测到竞态时打印详细报告，包含两个冲突访问的完整调用栈。需要注意：TSan 不能和 `-fsanitize=address`（ASan）同时使用，两者有冲突。
:::

学好这些工具，远比在代码里乱加 sleep "等"出 bug 来的靠谱。并发调试是一门"用工具说话"的科学，不是玄学。

至此，并发编程的理论和模式全部结束。从下一章开始，我们进入 CSAPP 最激动人心的部分——七个经典 Lab 的实战讲解。你把理论学得再好，不动手做 Lab 也终究是纸上谈兵。让我们一起迎接挑战吧。


## 实验：验证本章知识

在 [实验工程总览](/labs/) 中选择「有界生产者–消费者」，通过编译运行与 CTest 黄金测试观察互斥锁、条件变量、队列关闭与数据完整性。先预测输出，再验证结果；该实验用于理解机制，不直接代表硬件性能。
