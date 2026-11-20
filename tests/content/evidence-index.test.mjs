import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = fileURLToPath(new URL("../../", import.meta.url));
const evidenceDir = join(root, "docs/evidence");
const chapters = JSON.parse(readFileSync(join(root, "courses.json"), "utf8")).chapters;

test("all 28 chapters have exactly one readable evidence ledger", () => {
  assert.equal(chapters.length, 28);
  const expected = chapters.map((ch) => `${ch.num}.json`).sort();
  const actual = readdirSync(evidenceDir).filter((f) => f.endsWith(".json")).sort();
  assert.deepEqual(actual, expected);
  for (const chapter of chapters) {
    const ledger = JSON.parse(readFileSync(join(evidenceDir, `${chapter.num}.json`), "utf8"));
    assert.ok(Array.isArray(ledger.claims) && ledger.claims.length > 0, `${chapter.num}: missing claims`);
    assert.ok(ledger.claims.every((claim) => typeof claim.claim === "string" && claim.claim.trim()), `${chapter.num}: malformed claim`);
    assert.ok(!existsSync(join(root, "docs/chapters", `${chapter.num}-evidence.json`)));
    assert.ok(!existsSync(join(root, "evidence", `${chapter.num}.json`)));
  }
});
