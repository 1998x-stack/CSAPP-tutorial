#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint64_t tag;
    uint64_t used;
    int valid;
} CacheLine;

typedef struct {
    CacheLine *lines;
    unsigned sets;
    unsigned ways;
    unsigned block_bits;
    uint64_t clock;
    uint64_t hits;
    uint64_t misses;
    uint64_t evictions;
} Cache;

static int parse_uint(const char *text, unsigned *out) {
    if (text == NULL || text[0] == '\0' || text[0] == '-') {
        return 0;
    }
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(text, &end, 10);
    if (errno || end == text || *end || value > 1024UL) {
        return 0;
    }
    *out = (unsigned)value;
    return 1;
}

static void access_cache(Cache *cache, uint64_t addr) {
    uint64_t block = addr >> cache->block_bits;
    unsigned set = (unsigned)(block % cache->sets);
    uint64_t tag = block / cache->sets;
    CacheLine *lines = cache->lines + (size_t)set * cache->ways;
    CacheLine *empty = NULL;
    CacheLine *oldest = &lines[0];
    ++cache->clock;
    for (unsigned i = 0; i < cache->ways; ++i) {
        CacheLine *line = &lines[i];
        if (line->valid && line->tag == tag) {
            ++cache->hits;
            line->used = cache->clock;
            return;
        }
        if (!line->valid && !empty) empty = line;
        if (line->valid && line->used < oldest->used) oldest = line;
    }
    ++cache->misses;
    CacheLine *target = empty ? empty : oldest;
    if (!empty) ++cache->evictions;
    target->tag = tag;
    target->used = cache->clock;
    target->valid = 1;
}

int main(int argc, char **argv) {
    unsigned sets = 0, ways = 0, block_bits = 0;
    if (argc != 5 || !parse_uint(argc > 1 ? argv[1] : NULL, &sets) ||
        !parse_uint(argv[2], &ways) || !parse_uint(argv[3], &block_bits) ||
        sets < 1 || sets > 1024 || (sets & (sets - 1U)) != 0U ||
        ways < 1 || ways > 32 || block_bits > 63) {
        fputs("invalid cache geometry\n", stderr);
        return 2;
    }
    FILE *fp = fopen(argv[4], "r");
    if (!fp) {
        fputs("cannot open trace\n", stderr);
        return 2;
    }
    Cache cache = {0};
    cache.sets = sets;
    cache.ways = ways;
    cache.block_bits = block_bits;
    cache.lines = calloc((size_t)sets * ways, sizeof(*cache.lines));
    if (!cache.lines) {
        fclose(fp);
        fputs("out of memory\n", stderr);
        return 2;
    }

    char line[128];
    unsigned line_number = 0;
    int status = 0;
    while (fgets(line, sizeof(line), fp)) {
        ++line_number;
        char op = '\0', extra = '\0';
        uint64_t address = 0;
        if (line[0] == '#' || line[0] == '\n') continue;
        if (!strchr(line, '\n') && !feof(fp)) {
            status = 2;
            break;
        }
        if (sscanf(line, " %c %" SCNx64 " %c", &op, &address, &extra) != 2 ||
            (op != 'L' && op != 'S' && op != 'M')) {
            status = 2;
            break;
        }
        access_cache(&cache, address);
        if (op == 'M') access_cache(&cache, address);
    }
    if (ferror(fp)) status = 2;
    fclose(fp);
    if (status == 0) {
        printf("hits=%" PRIu64 " misses=%" PRIu64 " evictions=%" PRIu64 "\n",
               cache.hits, cache.misses, cache.evictions);
    } else {
        fprintf(stderr, "invalid trace line %u\n", line_number);
    }
    free(cache.lines);
    return status;
}
