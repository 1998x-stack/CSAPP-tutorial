---
title: "网络编程——基础"
description: "TCP/IP协议栈 · 套接字接口详解 · HTTP请求响应格式 · getaddrinfo协议编程"
outline: [2, 3]
---

# 第二十章：网络编程——基础

上一章我们详细讨论了 Unix 系统级 I/O。你学会了用 `open()`/`read()`/`write()` 操作磁盘文件，也明白了缓冲机制和 RIO 包的设计思想。但你有没有想过——当你在浏览器里输入一个网址，按下回车，数据是怎么从千里之外的服务器传到你屏幕上的？网络通信和文件 I/O 共用一套底层接口吗？

答案是：**是的**。在 Unix/Linux 中，网络套接字（socket）也是"文件"——一切皆文件。你可以用 `read()` 从 socket 中读取网络数据，用 `write()` 往 socket 中发送数据。但网络通信比磁盘文件 I/O 要复杂得多：数据是流式的、没有边界、可能延迟到达、可能乱序——这些特性让网络编程成为系统编程中最容易出错、也最有意思的领域之一。从本章开始，我们将用两章的篇幅，系统学习网络编程。

## 20.1 TCP/IP 协议栈回顾

在深入套接字接口之前，我们先快速回顾一下 TCP/IP 协议栈的分层模型。每一层都对其上层隐藏了实现细节——这正是"层层抽象"这一贯穿全书的核心思想在网络领域的体现。

| 层级 | 名称 | 典型协议 | 核心职责 |
| --- | --- | --- | --- |
| 第4层 | **应用层** | HTTP、FTP、SMTP、DNS | 应用程序之间的数据格式与交互语义 |
| 第3层 | **传输层** | TCP、UDP | 端到端连接、可靠传输、流量控制 |
| 第2层 | **网络层** | IP、ICMP | 数据包路由、寻址、分片与重组 |
| 第1层 | **链路层** | 以太网、WiFi、PPP | 物理介质上的帧传输、MAC 寻址 |

当你在浏览器中输入 `https://www.example.com` 并回车时，从上到下的数据流动大致是这样的：

- **应用层**：浏览器构造一个 HTTP GET 请求，交给传输层
- **传输层**：TCP 把 HTTP 数据封装成段（segment），添加源端口和目标端口（例如 49152 → 443）
- **网络层**：IP 把 TCP 段封装成数据报（datagram），添加源 IP 和目标 IP
- **链路层**：以太网把 IP 数据报封装成帧（frame），通过网卡发送到物理线路

在接收端，数据从下到上逐层"剥壳"：链路层去掉帧头→网络层去掉 IP 头→传输层去掉 TCP 头→应用层拿到原始的 HTTP 数据。

在网络编程中，最重要的概念是**套接字（socket）**。套接字是应用层和传输层之间的抽象接口。一个套接字由一个 **IP 地址**和一个**端口号**唯一标识。IP 地址定位到主机，端口号定位到该主机上的具体进程。

TCP 是**面向连接**的协议。在通信开始前，客户端和服务器需要通过**三次握手（three-way handshake）**建立连接：

1. 客户端发送 SYN 包（同步序列号）
1. 服务器回复 SYN+ACK（确认并同步自己的序列号）
1. 客户端发送 ACK（确认）

三次握手完成后，双方才能开始传输数据。这保证了可靠性，但也引入了额外的延迟——这就是为什么在 HTTP 短连接场景下，TCP 握手是一个不可忽视的开销。

## 20.2 套接字接口详解

套接字接口是 Unix 系统提供的一组用于网络通信的函数。只要掌握了这五个核心函数——`socket()`、`bind()`、`listen()`、`accept()`、`connect()`——你就能写出绝大多数基于 TCP 的网络程序。

先来看服务器的标准流程。服务器首先创建一个"监听套接字"，然后反复接受客户端的连接请求：

```c
#include <sys/socket.h>
#include <netinet/in.h>

int main() {
    // 1. socket()：创建套接字
    int listen_fd = socket(AF_INET,      // IPv4
                           SOCK_STREAM,  // TCP（流式）
                           0);           // 协议自动选择

    // 2. bind()：将套接字绑定到本地地址和端口
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;  // 任意本地 IP
    server_addr.sin_port = htons(8080);        // 端口 8080

    bind(listen_fd, (struct sockaddr *)&server_addr,
         sizeof(server_addr));

    // 3. listen()：将套接字变为监听状态
    listen(listen_fd, 10);  // 最多 10 个等待连接

    while (1) {
        // 4. accept()：等待并接受客户端连接（阻塞）
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);
        int conn_fd = accept(listen_fd,
                             (struct sockaddr *)&client_addr,
                             &addr_len);

        // 5. 用 conn_fd 读写数据
        char buf[1024];
        read(conn_fd, buf, sizeof(buf));
        write(conn_fd, "HTTP/1.1 200 OK\r\n\r\nHello!", 27);

        close(conn_fd);
    }
}
```

客户端则更加简单：

```c
int main() {
    int client_fd = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    server_addr.sin_port = htons(8080);

    // connect()：连接到服务器
    connect(client_fd,
            (struct sockaddr *)&server_addr,
            sizeof(server_addr));

    write(client_fd, "GET / HTTP/1.1\r\n\r\n", 17);

    char buf[1024];
    read(client_fd, buf, sizeof(buf));
    printf("%s", buf);

    close(client_fd);
    return 0;
}
```

注意几个关键细节：`htons()` 函数——网络字节序是大端（big-endian）的，而 x86 处理器是小端的（little-endian）。`htons` 将"主机字节序"转换为"网络字节序"。这个细节被很多初学者忽略，导致端口号错误。另外，`accept()` 返回的 `conn_fd` 是一个**新**的文件描述符，专门用于和该客户端通信。原始的 `listen_fd` 继续监听新的连接请求。

::: tip
**小技巧**：服务器在 `bind()` 之前经常会遇到"Address already in use"错误，这是因为之前的连接处于 TIME_WAIT 状态。解决方案是在 `bind()` 之前设置 `SO_REUSEADDR` 选项：`int optval = 1; setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));`。这在开发测试中几乎是标配。
:::

## 20.3 HTTP 协议实战

理论讲完了，让我们看看真实世界中最广泛使用的应用层协议——HTTP。HTTP（超文本传输协议）是 Web 的基石。一个 HTTP 请求由三部分组成：**请求行**、**头部**、**主体**（可选）。

来看一个实际的 HTTP 请求是什么样的：

```text
GET /index.html HTTP/1.1           ← 请求行：方法 + URI + 版本
Host: www.example.com              ← 头部：Host 是唯一必需的
User-Agent: Mozilla/5.0            ← 头部：标识客户端
Accept: text/html,application/json ← 头部：可接受的响应类型
                                   ← 空行（CRLF）：标识头部结束
                                   ← GET 请求通常没有主体
```

服务器收到请求后，返回响应：

```text
HTTP/1.1 200 OK                    ← 状态行：版本 + 状态码 + 描述
Content-Type: text/html            ← 头部
Content-Length: 1234               ← 头部：主体字节数
                                   ← 空行
<!DOCTYPE html>                    ← 主体开始
<html><body>Hello!</body></html>
```

常见的 HTTP 状态码：

| 状态码 | 含义 | 典型场景 |
| --- | --- | --- |
| `200` | OK（成功） | 请求成功，返回内容 |
| `301` | Moved Permanently（永久重定向） | 网站更换域名 |
| `400` | Bad Request（错误请求） | 请求格式不对 |
| `404` | Not Found（资源不存在） | 请求的页面不存在 |
| `500` | Internal Server Error（服务器内部错误） | 服务器崩溃 |

对于 HTTP 响应，`Content-Length` 头部告诉客户端响应主体有多少字节。客户端读完这么多字节后，就知道这个响应结束了。但如果服务器在生成响应时还不知道内容大小呢？比如动态生成的页面。这时可以使用**分块传输编码（chunked transfer encoding）**，服务器将响应分成多个数据块，每个块前面有块的大小，最后以一个大小为 0 的块结束。

## 20.4 getaddrinfo——协议独立的地址解析

在之前的代码示例中，我们硬编码了 `struct sockaddr_in`（IPv4 专用结构体）。这在实际工程中有两个问题：第一，写死了 IPv4，无法支持 IPv6；第二，需要手动填充 IP 地址和端口，容易出错。现代网络编程强烈建议使用 `getaddrinfo()`，它提供了协议独立的地址解析，且同时支持 IPv4 和 IPv6。

```c
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>

int getaddrinfo(const char *node,     // 主机名或 IP
                const char *service,  // 端口号或服务名（如 "http"）
                const struct addrinfo *hints,  // 过滤条件
                struct addrinfo **res);        // 返回的链表

void freeaddrinfo(struct addrinfo *res);  // 释放链表

// addrinfo 结构体包含：
// struct addrinfo {
//     int     ai_flags;      // AI_PASSIVE, AI_CANONNAME 等
//     int     ai_family;     // AF_INET, AF_INET6, AF_UNSPEC
//     int     ai_socktype;   // SOCK_STREAM, SOCK_DGRAM
//     int     ai_protocol;   // IPPROTO_TCP 等
//     socklen_t ai_addrlen;  // 地址长度
//     struct sockaddr *ai_addr;  // 指向 sockaddr 结构
//     char   *ai_canonname;  // 主机规范名
//     struct addrinfo *ai_next; // 链表下一个节点
// };
```

用 `getaddrinfo` 重写服务器端的 bind 部分：

```text
struct addrinfo hints, *list, *p;
memset(&hints, 0, sizeof(hints));
hints.ai_family   = AF_UNSPEC;     // IPv4 或 IPv6 都可以
hints.ai_socktype = SOCK_STREAM;   // TCP
hints.ai_flags    = AI_PASSIVE;    // 用于 bind（通配地址）

getaddrinfo(NULL, "8080", &hints, &list);

int listen_fd;
for (p = list; p != NULL; p = p->ai_next) {
    listen_fd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
    if (listen_fd < 0) continue;
    if (bind(listen_fd, p->ai_addr, p->ai_addrlen) == 0)
        break;  // bind 成功
    close(listen_fd);
}

freeaddrinfo(list);
```

::: info
**核心要点**：`AF_UNSPEC` 告诉 getaddrinfo 同时返回 IPv4 和 IPv6 的地址，程序依次尝试 bind。这样一来，你的代码可以不加修改地同时运行在纯 IPv4 网络、纯 IPv6 网络和双栈网络上。这是编写可移植网络程序的黄金标准——不再需要为 IPv4 和 IPv6 各写一套代码。
:::

好了，网络编程的基础知识已经铺好了。你现在知道了一个 TCP 连接从创建到销毁的完整流程：socket → bind → listen → accept → read/write → close。也知道了 HTTP 协议的请求-响应格式。下一章，我们将在这个基础上迈出关键一步——让你的服务器同时服务**多个客户端**。从迭代服务器到并发服务器，从不阻塞到多路复用——网络编程真正的挑战才刚刚开始。
