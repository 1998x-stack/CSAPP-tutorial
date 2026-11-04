# 缓存地址拆解实验

目标：依据组索引位数 s 和块内偏移位数 b，将地址拆分为 tag、set 和 offset。

运行：\`cc -std=c11 -Wall -Wextra -pedantic cache_geometry.c -o cache_geometry && ./cache_geometry\`

预期：\`set=1 offset=12\`。本示例仅验证算术逻辑，不是硬件性能测试。

