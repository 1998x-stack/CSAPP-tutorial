# 软件 Cache 模拟实验

用法：`lab_cache_sim <sets> <ways> <block_bits> <trace_path>`。

- `sets`：组数，必须是 1～1024 之间的 2 的幂；
- `ways`：每组 Cache 行数，1～32；
- `block_bits`：块内偏移位数，0～63；
- trace 每行形如 `L 0x10`、`S 0x10` 或 `M 0x10`，分别表示读、写和读改写（两个访问）；
- 每条 Cache 行采用时间戳记录最近使用，容量满后替换最久未被使用的行（LRU）。

~~~bash
./.build/labs/lab_cache_sim 4 2 4 tests/labs/fixtures/lru.trace
# hits=4 misses=5 evictions=2
~~~

`tests/labs/fixtures` 包含 LRU、直接映射和无效操作输入；测试同时验证正确结果及错误返回码。`lab_cache_geometry` 展示从地址提取组与块内偏移的简单算术。

模拟器**不模拟真实多级 CPU Cache**、写回与一致性协议，不应用于评价硬件性能。
