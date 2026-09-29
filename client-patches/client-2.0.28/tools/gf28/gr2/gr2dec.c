/* gr2dec: decompress all sections of a Granny2 file (Oodle1 via opengr2's oodle1.c) and write them raw to stdout */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "oodle1.h"
static int unoodle1(uint8_t* c, uint32_t cl, uint8_t* d, uint32_t dl, uint32_t s1, uint32_t s2) {
    if (!cl) return 1;
    TParameter p[3]; memcpy(p, c, sizeof(p));
    TDecoder dec; Decoder_Init(&dec, c + sizeof(p));
    uint32_t steps[] = { s1, s2, dl }; uint8_t* ptr = d;
    for (int i = 0; i < 3; i++) { TDictionary dict; Dictionary_Init(&dict, &p[i]);
        while (ptr < d + steps[i]) ptr += Dictionary_Decompress_Block(&dict, &dec, ptr);
        Dictionary_Free(&dict); }
    return 1;
}
int main(int argc, char** argv) {
    FILE* f = fopen(argv[1], "rb"); if (!f) return 2;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t* b = malloc(n); if (fread(b, 1, n, f) != (size_t)n) return 3; fclose(f);
    uint32_t hsize = *(uint32_t*)(b + 16);
    uint32_t* fi = (uint32_t*)(b + 32);
    uint32_t secoff = fi[3], seccnt = fi[4];
    for (uint32_t i = 0; i < seccnt; i++) {
        uint32_t* s = (uint32_t*)(b + 32 + secoff + i * 44);
        uint32_t comp = s[0], off = s[1], csz = s[2], dsz = s[3], st0 = s[5], st1 = s[6];
        if ((uint64_t)off + csz > (uint64_t)n) return 4;
        uint8_t* out = calloc(1, dsz + 16);
        if (comp == 0) memcpy(out, b + off, dsz);
        else if (comp == 2) { uint8_t* c = calloc(1, csz + 8); memcpy(c, b + off, csz); unoodle1(c, csz, out, dsz, st0, st1); free(c); }
        else { fprintf(stderr, "compression %u unsupported\n", comp); return 5; }
        fwrite(out, 1, dsz, stdout); free(out);
    }
    (void)hsize; return 0;
}
