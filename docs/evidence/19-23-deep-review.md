# CSAPP 第 19–23 章：第二轮可核对技术断言

这里只记录本批新增的命题，不代表对既有整章的所有句子完成独立技术审核。所有 SVG 都是简化模型；可执行 C 代码验证真实 POSIX API，Python 仅验证离散状态和数值，不承诺任何实机性能结果。

| 章 | 具体可验证结论 | 规范与参考资料 | 正向实验 |
| --- | --- | --- | --- |
| 19 | 管道端写入 3B 并关闭后，最多读 7B 返回 3，再读返回 0；必须区分短读/EOF/EINTR/EAGAIN | [read(2)](https://man7.org/linux/man-pages/man2/read.2.html)、[write(2)](https://man7.org/linux/man-pages/man2/write.2.html) | C `short-read`、Python `19` |
| 20 | 4B 大端长度=5 + HELLO 的字节序列为 `00 00 00 05 48 45 4c 4c 4f`；接收分片不定义记录边界 | [RFC 9112 HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)、[tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html) | C `frame` 通过 AF_UNIX `socketpair` + read_exact，Python `20`；不代表 TCP 的段分割 |
| 21 | 写端关闭且缓冲已空，读端被 poll 报告可处理的 EOF 事件，read 返回 0；ready 不等于完整消息 | [poll(2)](https://man7.org/linux/man-pages/man2/poll.2.html)、[epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html) | C `readiness`、Python `21` |
| 22 | mutex 保护整个读改写 + 4 个线程分别加 10000 次，可确保 join 后计数器=40000；普通非原子变量的数据竞争是未定义行为 | [pthread_mutex_lock(3p)](https://man7.org/linux/man-pages/man3/pthread_mutex_lock.3p.html)、[pthread_join(3)](https://man7.org/linux/man-pages/man3/pthread_join.3.html) | C `mutex`、Python `22`；不运行故意产生数据竞争的例子 |
| 23 | `count ∈ [0,2]`、入队数−出队数=count；条件等待在锁内用 while 重验；关闭广播后消费者排空 6 项，总和=21 | [pthread_cond_wait(3p)](https://man7.org/linux/man-pages/man3/pthread_cond_wait.3p.html)、[pthread_cond_broadcast(3p)](https://man7.org/linux/man-pages/man3/pthread_cond_broadcast.3p.html) | C `queue`、Python `23`；不声称固定调度顺序或生产级公平性 |

## 一次性复现

```bash
python3 examples/deep-ch19-23-models.py all
cc -std=c11 -Wall -Wextra -Werror -pedantic -pthread examples/deep-ch19-23.c -o /tmp/deep-io
for mode in short-read frame readiness mutex queue; do /tmp/deep-io "$mode"; done
npm test
npm run build
```

独立 Chromium 工作流遍历 19–23 各章的 1440px/390px/360px 宽度，检查原有交互、新增 SVG 资源、键盘焦点、主文档横向溢出、打印可见性与控制台错误。若工作流尚未成功，应明确标记为未完成。
