# Illustrated chapters 02–04 — source and test notes

The lesson structure uses the causal, progressive-disclosure approach described in [Olah-style-posts](https://github.com/1998x-stack/Olah-style-posts/tree/main/skills/olah-style-paper-posts). All diagrams and prose in these lessons were newly authored; no reference article or figure was copied.

## Source boundaries

- Course **02**: byte order, two's-complement interpretation, C integer conversions, signed/unsigned overflow. See [evidence ledger](../../evidence/02.json).
- Course **03**: IEEE binary32/64, category encodings, nearest-even rounding and reproducible precision-dependent comparisons. See [evidence ledger](../../evidence/03.json).
- Course **04**: System V AMD64 (not Windows x64), AT&T syntax, register subsets, effective-address arithmetic, division. See [evidence ledger](../../evidence/04.json).

These are course chapters 02–04, not one-to-one mappings of the official CS:APP book chapter numbers.

## Reproducible checks

Run \`npm test\`: existing navigation/content tests, HTML code-block checks, XML SVG parsing, Node syntax checks for inline interactions, and compiled C examples are included. A browser-side screenshot audit at desktop 1440px and mobile 390px/360px is a separate quality gate; don't infer that this passed solely from CI.

The original SVG diagrams are located in \`chapter-assets/\`, and chapter-specific presentation is in \`olah-chapters.css\`. Existing lessons 01 and 05–28 retain their theme/layout. No external font/script is required for the new lessons.

## Additional illustrated lessons 16–18

- **16**: POSIX signals: generation/pending/delivery, async-safe handlers, atomic `sigsuspend` waiting and nonlocal-jump constraints. See [evidence](../../evidence/16.json) and [C experiment](../../examples/olah-ch16-signals.c).
- **17**: virtual-to-physical page mapping, 4-/5-level paging scope, TLB misses versus page faults, illustrative page-address calculation. See [evidence](../../evidence/17.json) and [C experiment](../../examples/olah-ch17-vm.c).
- **18**: `mmap` semantics, user-space allocator block management, deterministic fixed-pool fragmentation and mark-sweep boundaries. See [evidence](../../evidence/18.json) and [C experiment](../../examples/olah-ch18-allocator.c).

These lessons add 9 original stand-alone SVG diagrams under `chapter-assets/`. CI covers C snippets, XML SVG parsing, inline JS syntax, full navigation, and Playwright 1440/390/360 px screenshot checks. `scripts/build-static.mjs` now copies both lesson stylesheets and SVG assets into `dist/`, making offline and GitHub Pages output consistent. The script references explain which behavior is an illustrative model, which is POSIX, and which is Linux-specific.
