# CSAPP 第 24–28 章：第三轮可核对技术断言

这里只记录本批新增的命题，不代表对既有整章的所有句子完成独立技术审核。所有 SVG 都是简化模型；本批全部验证用纯标准库的确定性 Python 模型完成，不依赖网络、不承诺任何实机性能结果，也不复现任何 Lab 个人实例。

| 章 | 具体可验证结论 | 规范与参考资料 | 正向实验 |
| --- | --- | --- | --- |
| 24 | 定长缓冲区保留结尾 NUL 时要求 `N ≤ C−1`；超长输入应判定为“截断”并保留待清理字节；`2^40 × 2^30` 在 64 位 `size_t` 中回绕，`1024 × 8` 在范围内 | [Attack Lab 官方讲义](https://csapp.cs.cmu.edu/3e/attacklab.pdf)、[size_t](https://en.cppreference.com/w/c/types/size_t) | Python `24`：`capacity=16` 下 `N=2/15/40` 三例，断言截断时保留 `cap-1=15` 字节 |
| 25 | 教学直接映射缓存 `s=1,E=1,b=3` 对 `0x00,0x08,0x00,0x10` 得到 `hit 1 / miss 3 / eviction 1`；即时合并把相邻空闲块归为一段 | [CS:APP3e Labs](https://csapp.cs.cmu.edu/3e/labs.html)、[setpgid(2)](https://man7.org/linux/man-pages/man2/setpgid.2.html)、[waitpid(2)](https://man7.org/linux/man-pages/man2/waitpid.2.html) | Python `25`：缓存重放 + 块阵列合并断言；不声称真实硬件命中率 |
| 26 | HTTP/1.1 消息边界由首部与 `Content-Length`、`chunked` 或连接关闭确定；剩余字节属于下一条消息；截断的体不交付 | [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112)、[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111) | Python `26`：按 1/7/20/全长分块重组；流水线两请求拆包；chunked `Wiki+pedia` 停在 0 长度分块 |
| 27 | RV64I `add x10,x11,x12` 编码为 `0x00C58533`；`ld x5,8(x6)` 编码为 `0x00833283`；I 型 12 位立即数需符号扩展（`-4`） | [RISC-V Unprivileged ISA](https://docs.riscv.org/reference/isa/unpriv/unpriv-index.html)、[CUDA Programming Model](https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/programming-model.html) | Python `27`：编码后解码回相同字段；不代表任何微架构吞吐 |
| 28 | 非阻塞连接由输入/输出双游标描述：短写 `1536,0,2560` 累计 4096 且不重发；`EAGAIN` 只暂停本轮；代际号使陈旧事件失效 | [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html)、[RFC 9112](https://www.rfc-editor.org/rfc/rfc9112) | Python `28`：请求分片重组 + 短写偏移 + 代际号；不提供任何 RPS 或连接数承诺 |

## 一次性复现

```bash
python3 examples/deep-ch24-28-models.py all
npm test
npm run build
```

本地 Chromium 以 `file://` 逐个打开 24–28 章，在 1440px/390px/360px 宽度下检查 SVG 渲染、主文档横向溢出、JS 控制台错误与至少一次交互；结果记录在运行日志目录的 `qa/deep-qa.json`，不提交进仓库。本次未新增独立 CI 工作流，若相关自动化未运行，应明确标记为未在 CI 验证。

## 不能推广的边界

- 24 的容量模型只演示“完整/截断”两态与 `size_t` 回绕，不构成任何攻击载荷或栈布局说明。
- 25 的计数来自教学参数 `s=1,E=1,b=3` 与固定轨迹，真实 Cache Lab 接受不同 `s/E/b`，不能硬编码。
- 26/28 只验证定界与游标逻辑，不实现全部首部、状态码、TLS、请求走私防护或生产服务器特性。
- 27 的字段编码来自 ISA 规范，不能从 ISA 推断频率、功耗或实际吞吐；Roofline 参数仍为教学假设。
