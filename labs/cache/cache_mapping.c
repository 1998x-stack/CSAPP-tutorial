#include <assert.h>
#include <stdio.h>
enum { SETS = 4, MAX_WAYS = 2, BLOCK_BYTES = 16 };
typedef struct { unsigned tag; int valid; } Line;
typedef struct { Line line[SETS][MAX_WAYS]; } Cache;
static int access_block(Cache *cache, unsigned address, int ways) {
    const unsigned block = address / BLOCK_BYTES;
    const unsigned set = block % SETS;
    const unsigned tag = block / SETS;
    for (int w = 0; w < ways; ++w) {
        if (cache->line[set][w].valid && cache->line[set][w].tag == tag)
            return 1;
    }
    for (int w = 0; w < ways; ++w) {
        if (!cache->line[set][w].valid) {
            cache->line[set][w] = (Line){ tag, 1 };
            return 0;
        }
    }
    // 本实验不会触发两路均满后的第三个不同 tag；固定替换 Way 0。
    cache->line[set][0] = (Line){ tag, 1 };
    return 0;
}
int main(void) {
    assert((0x1234u & 15u) == 4u);
    assert(((0x1234u >> 4) & 3u) == 3u);
    assert((0x1234u >> 6) == 0x48u);
    const unsigned accesses[] = { 0x00, 0x40, 0x00 };
    Cache direct = {0}, two_way = {0};
    char d[4], t[4];
    for (int i = 0; i < 3; ++i) {
        d[i] = access_block(&direct, accesses[i], 1) ? 'H' : 'M';
        t[i] = access_block(&two_way, accesses[i], 2) ? 'H' : 'M';
    }
    d[3] = t[3] = '\0';
    assert(d[0] == 'M' && d[1] == 'M' && d[2] == 'M');
    assert(t[0] == 'M' && t[1] == 'M' && t[2] == 'H');
    printf("direct=%s two-way=%s\n", d, t);
    return 0;
}
