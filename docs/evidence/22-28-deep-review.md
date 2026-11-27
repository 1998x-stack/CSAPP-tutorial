# 22–28 章第五轮深度复核账本（原子内存序 / 取消 / 位运算 / Cache / HTTP 新鲜度 / SIMT / 半关闭）

本轮为 22–28 各追加一节 `deep-NNb`、一张外链图 `chapter-assets/NN-deep2.svg`，
以及纯标准库确定性模型 `examples/deep-ch22-28-b.py`（新增回归测试
`tests/content/deep-ch22-28-b.test.mjs`）。下表只记录本轮新增的可证伪论断与检验方式，
不覆盖旧页面的全部历史断言；所有数字均为教学算例或语言/协议规定的确定性结果。

| 章 | 核心可证伪论断 | 依据 | 检验与限制 |
| --- | --- | --- | --- |
| 22b | `relaxed` 只保证该原子对象操作不可分割，不发布负载；`release` 存储与 `acquire` 加载配对、且加载读到该存储的值时，存储前的写入对加载后的读取可见；`seq_cst` 再叠加全局总顺序 | [C 原子内存序](https://en.cppreference.com/w/c/atomic/memory_order.html)、[C 内存模型](https://en.cppreference.com/w/c/language/memory_model.html) | `python3 examples/deep-ch22-28-b.py 22b`；relaxed 得到（flag, old），release-acquire/seq_cst 得到（flag, new）。语言语义模型，非硬件实测 |
| 23b | 默认延迟取消只在取消点生效；跨取消点仍持有的资源必须由清理处理器释放，否则 `join` 返回后互斥锁永久锁定 | [pthread_cancel(3)](https://man7.org/linux/man-pages/man3/pthread_cancel.3.html)、[pthread_cleanup_push(3)](https://man7.org/linux/man-pages/man3/pthread_cleanup_push.3.html) | 模型 `23b`：无处理器时 `locked=True` 且未回收；有处理器时 `locked=False` 且回收恰一次 |
| 24b | 有符号右移结果实现定义；移位量 ≥ 字长属未定义行为；逻辑右移用掩码 `~(~0<<(32-n))` 并单独处理 `n=0` | [C11 §6.5.7](https://port70.net/~nsz/c/c11/n1570.html#6.5.7) | 模型 `24b`：`0x80000000>>4` 逻辑移位为 `0x08000000`（非 `0xF8000000`），`n=0` 走单独分支 |
| 25b | 组相联 Cache 的命中/未命中/驱逐由 s/E/b 与替换策略共同决定，且 `hit+miss=access` | CS:APP Cache Lab 契约；[csim 参考](https://csapp.cs.cmu.edu/3e/cachelab.pdf) | 模型 `25b`：`s=2,E=2,b=4`、轨迹 `0x000,0x100,0x000,0x200,0x000` 得 `access=5,hit=2,miss=3,evict=1`。教学模拟，非实机缓存测量 |
| 26b | 可复用当且仅当当前年龄 < 新鲜期，且 `Vary`/`Authorization` 门通过；新鲜期 max-age 优先于 `Expires−Date` | [RFC 9111 §4.2](https://www.rfc-editor.org/rfc/rfc9111.html) | 模型 `26b`：`max-age` 优先；`当前年龄=max(表观, Age+延迟)+驻留`；fresh/stale 判定。RFC 算术复算，非代理实测 |
| 27b | SIMT 下一个 warp 的非一致分支按不同路径分遍串行执行，一致分支只需一遍 | [CUDA C++ Programming Guide · SIMT Architecture](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#simt-architecture) | 模型 `27b`：一致 1 遍、两路混合 2 遍、`k` 路 switch `k` 遍。架构行为模型，非 GPU 实测时序 |
| 28b | `shutdown(SHUT_WR)` 只关写方向、读方向仍可用；对端停读后首写可能成功、随后返回 `EPIPE`；应忽略 `SIGPIPE` 并视 `EPIPE` 为正常终止 | [shutdown(2)](https://man7.org/linux/man-pages/man2/shutdown.2.html)、[socket(7)](https://man7.org/linux/man-pages/man7/socket.7.html)、[signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html) | 模型 `28b`：半关闭后 `read_open=True`；对端停读时首写 `OK`、次写 `EPIPE`。POSIX 契约模型，非真实抓包；成功写次数为教学取值 |

本轮验证命令：`python3 examples/deep-ch22-28-b.py all`、`npm test`。
浏览器验收以本地真实 HTTP 服务 + Chromium 在 1440/390/360px 运行；未执行时记为未验证。
