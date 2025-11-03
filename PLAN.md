### Goal
Build a robust Python CLI that reads each translation directory under `inputs/`, parses the translation’s SCML to produce two JSON files per translation (`notes.json`, `resources.json`) formatted to match the examples, and copies the relevant images into the translation’s output folder.

### Success Criteria
- For each translation (e.g., `ESV`, `LSB`, `NASB`, `NKJV`):
  - Create `output/<TRANSLATION>/notes.json` identical in structure to `example_notes.json`:
    - Array of objects with keys: `start` (int), optional `end` (int), `content` (string)
    - No extra keys (e.g., do NOT include `book` or `book_id`)
  - Create `output/<TRANSLATION>/resources.json` identical in structure to `example_resources.json`:
    - Array of objects with keys: `id` (string), `title` (string), `content` (string), `type` (string)
    - Resource `id` should be the image filename from the translation’s images folder (see Open Questions for text-only resources)
  - Copy all images referenced by the selected resources from `inputs/<TRANSLATION>/<TRANSLATION>_images/` into `output/<TRANSLATION>/images/`.
- CLI can run for one translation or all, and works on large SCMLs via streaming parsing.
- Output is deterministic and whitespace-normalized.

### Inputs and Expected Layout
- Inputs root: `inputs/`
  - Per translation: `inputs/<TRANSLATION>/`
    - SCML file (e.g., `ESV.scml`, `LSB.scml`)
    - Images folder: `inputs/<TRANSLATION>/<TRANSLATION>_images/` containing jpgs used by the SCML (`ESV_images/`, `LSB_images/`, etc.)
- SCML references images using paths like `images/<filename>.jpg`. We will map these to the actual filesystem source folder `<TRANSLATION>_images/`.

### Outputs and Directory Structure
- Per translation output directory: `output/<TRANSLATION>/`
  - `notes.json`
  - `resources.json`
  - `images/` (copied referenced images)

### SCML Structures Observed (ESV and sample)
- Study notes (commentary) are represented by `<com id="comBBCCCVVV[optionalSuffix]"> ... </com>` typically within chapters with semantic like “Study Notes and Features for <Book>” (e.g., `id="anc01"`).
  - Header reference lives under `<bcv><xbr t="BOOK CH:V[-CH:V or -V]"><display></xbr></bcv>` as the first child of `<com>`.
  - Body contains inline formatting: `<b>`, `<bi>`, `<i>`, cross-references `<xbr t="...">Display</xbr>`, and other inline tags. Some `<com>` ids may have suffix letters (e.g., `com01012001a`).
- Study resources (maps/charts/figures) in ESV are encapsulated in `<sidebar id="..."> ... </sidebar>` with IDs like:
  - `sbc...` (charts)
  - `sbm...` (maps/figures)
  - Inside sidebar:
    - One or more `<figure>` blocks. Decorative rule images often appear as `<img src="images/hcp-rule.jpg"/>` and should be ignored for resource identity.
    - The resource’s human title is typically in `<figh><xref>Title</xref></figh>`; some include titles in `<th><xref>Title</xref></th>`.
    - The resource’s representative image appears as `<fig><img src="images/<content-image>.jpg"/></fig>` (e.g., `hcp-esvmacarthursb02-fig18.jpg`).
- Additional structural tags observed: `<figure>`, `<figh>`, `<fig>`, `<table>`, `<list>`, `<cell>`, `<td*>`, etc., which we will serialize to text/HTML-like content.

### Target JSON Schemas
- notes.json (match exactly `example_notes.json`):
```
[
  { "start": 1001001, "content": "<b><a>Gen. 1:1</a></b> ..." },
  { "start": 1001003, "end": 1001005, "content": "<b><a>Gen. 1:3-5</a></b> ..." }
]
```
- resources.json (match exactly `example_resources.json`):
```
[
  { "id": "hcp-esvmacarthursb02-fig18.jpg", "title": "...", "content": "...", "type": "figure" },
  { "id": "sbch-01007004", "title": "The Flood Chronology", "content": "...", "type": "chart" }
]
```
Note: In our implementation, `id` will be the image filename for image-backed resources. See Open Questions for text-only resources and non-unique images.

### CLI Design
- Command: `python3 study_notes_cli.py [--inputs-dir inputs] [--output-dir output] (--translation ESV | --all)`
- Options:
  - `--inputs-dir`: default `./inputs`
  - `--output-dir`: default `./output`
  - `--translation`: process only a single translation (e.g., `ESV`). Mutually exclusive with `--all`.
  - `--all`: process all translations found under `inputs/` (subdirectories containing `*.scml`).
- `--copy-all-images`: copy entire `<TRANSLATION>_images/` folder (not just referenced) into output. Default: copy entire folder (per decision below).
  - `--strict-images`: fail if a referenced image file is missing in the inputs folder; default is to warn and skip that resource.
  - `--progress/--no-progress`: enable/disable progress messages.

### Processing Flow (per translation)
1. Prepare paths:
   - `scml_path = inputs/<TRANSLATION>/<TRANSLATION>.scml`
   - `images_src_dir = inputs/<TRANSLATION>/<TRANSLATION>_images/`
   - `out_dir = output/<TRANSLATION>/` and `out_images_dir = output/<TRANSLATION>/images/`
2. Stream-parse the SCML using `xml.etree.ElementTree.iterparse` with events `('start', 'end')`.
3. Maintain minimal state for current book context (optional for resources; not emitted in JSON to match examples).
4. On element end events:
   - If `elem.tag == 'com'`: process as a study note
   - If `elem.tag == 'sidebar'`: process as a study resource
   - Clear elements after processing to control memory usage
5. After streaming is complete:
   - Sort notes by `start`
   - Write `notes.json` and `resources.json`
   - Copy images (referenced or all, depending on CLI flags)

### Study Notes Extraction (from <com>)
- Extract `start` from the numeric portion of `com` id: `comBBCCCVVV[letter?]` → `BBCCCVVV` as integer.
- Extract possible `end` from the `<bcv><xbr t="..."/>` value:
  - Accept forms: `Book C:V`, `Book C:V–V`, `Book C:V–C:V` using both en-dash and hyphen.
  - Compute numeric `end` id for same-chapter ranges and cross-chapter ranges.
- Build `content`:
  - Generate a header like `"<b><a>Gen. 1:1</a></b>"` from the display portion (prefer the `<xbr>` inner text for display; fall back to an abbreviated display generated from the `t` attribute).
  - Serialize the remainder of the `<com>` content (excluding the `<bcv>` node) into an HTML-like string:
    - Preserve `<b>`, `<bi>` as `<b>`; `<i>` as `<i>`.
    - Convert `<xbr t="...">Display</xbr>` to `<a ref='Full Book Name X:Y[–...]'>Display</a>` (as in the example and existing code), escaping quotes.
    - Concatenate text and child tails; collapse whitespace.
- Emit:
  - `{ "start": <int>, ["end": <int>], "content": <string> }`

### Resource Extraction (from <sidebar>)
- Recognize target sidebars by id prefix:
  - `sbc` → `type = "chart"`
  - `sbm` → `type = "figure"` (maps treated as figures per example_resources.json)
- Locate content images inside the sidebar:
  - Search for `<fig><img src="images/<filename>.jpg"/></fig>` entries.
  - Ignore decorative assets (e.g., `hcp-rule.jpg`, `ctorntop.jpg`, `ctornbottom.jpg`, `csorn.jpg`, logos). Prefer filenames containing `fig`/`map` patterns (e.g., `*-fig*.jpg`, `*-map*.jpg`).
  - If multiple non-decorative images are present, emit one resource entry per image (include all).
  - For image-backed entries, set `id = <filename>.jpg` (basename only, no path).
- Extract `title`:
  - Prefer `<figh><xref>Title</xref></figh>` if present; else `<th><xref>Title</xref></th>`; else fallback to `sidebar id`.
- Build `content` by serializing textual content of the sidebar (excluding purely decorative figures):
  - Serialize headings, tables, list items, and paragraphs into a readable string.
  - Preserve cross-references as `<a ref='...'>...</a>`; collapse whitespace.
- Emit:
  - For each non-decorative image found: `{ "id": <image filename>, "title": <string>, "content": <string>, "type": <"chart"|"figure"> }`
  - If no non-decorative image is present (text-only sidebar): include it with `id` generated as a slug from the article content or title (see Decisions below).

-### Image Copying Strategy
- Default: copy entire `<TRANSLATION>_images/` folder into `output/<TRANSLATION>/images/` (per decision).
- Optional flag (inverse): `--only-referenced-images` to copy only images referenced by emitted resources.
- Validate that each referenced `<filename>.jpg` exists in `<TRANSLATION>_images`; if missing:
  - With `--strict-images`: skip the resource and log an error; otherwise warn and continue (resource omitted).

### Normalization and Formatting Rules
- Collapse any run of whitespace to a single space in emitted `content`.
- Escape quotes in HTML attributes.
- Preserve `<b>`, `<i>`, and `<a ref='...'>...` markup; remove SCML-only structural tags from output.
- Ensure `notes.json` strictly contains only `start`, optional `end`, and `content`.

### Edge Cases and Handling
- `<com id>` suffix letters (e.g., `com01012001a`): extract only the numeric portion for `start`.
- Ranges in `<xbr t>`:
  - `Book C:V–V` → same chapter; compute `end` using same chapter.
  - `Book C:V–C2:V2` → cross-chapter; compute `end` across chapters.
  - If `end` computed equals `start`, omit `end`.
- Unknown book abbreviations: fall back to best-effort mapping; warn on unknowns (use a mapping similar to current `BOOK_INFO`).
- Sidebars without a suitable content image: see Open Questions; provisional plan is to skip or assign a fallback id.
- Duplicate resource images: if the same `<filename>.jpg` appears in multiple sidebars, de-duplicate by `id`, merging content with a separator, or keep the first occurrence and warn (see Open Questions).

### Performance and Memory
- Use `ET.iterparse` (streaming) to avoid loading entire SCML into memory.
- Clear processed elements immediately with `elem.clear()`.
- Avoid storing large intermediate structures; append as we go.

### CLI Behavior: One vs. All Translations
- `--translation ESV`:
  - Process only `inputs/ESV/ESV.scml` and `inputs/ESV/ESV_images/`.
- `--all`:
  - Discover any `inputs/*/*.scml`; for each subdir, infer translation code from directory name and SCML filename.
- Create `output/<TRANSLATION>/` per translation, without overwriting other translations.

### Validation and QA
- Schema checks:
  - `notes.json`: each item must have `start` (int), `content` (non-empty string), optional `end` (int ≥ start when present); no extra keys.
  - `resources.json`: each item must have `id` (string), `title` (non-empty), `content` (non-empty), `type` ∈ {`chart`, `figure`} (extendable if needed).
- Spot-check cross-references: ensure `<a ref='Full Book Name X:Y–...'>Display</a>` format appears in both notes and resources when applicable.
- File counts:
  - Print totals after processing (notes count, resources count, images copied).

### Implementation Breakdown (High-Level Tasks)
1. Core utilities
   - Book mapping (`BOOK_INFO`) and reference parsing/formatting helpers (display string, numeric id composition, cross-chapter range handling).
   - Content serialization that:
     - Skips `<bcv>` in `<com>` body
     - Converts `<xbr>` to `<a ref='...'>...` with proper escaping
     - Preserves `<b>`/`<bi>` and `<i>` as `<b>`/`<i>`
     - Serializes tables/lists into readable text
2. Notes extractor (streamed)
   - On `</com>`: build a note object as specified and append to list.
3. Resources extractor (streamed)
   - On `</sidebar>`:
     - Determine type from id prefix (`sbc`/`sbm`)
     - Extract title (prefer `<figh>` > `<th>`)
     - Resolve representative image (exclude decorative; prefer `*-fig*.jpg`)
     - Build textual content and append resource entry
4. Images copying
   - Based on referenced image set (or all, if flag set), copy to `output/<TRANSLATION>/images/`.
5. CLI wrapper
   - Argument parsing, per-translation loop, progress logging, error handling.
6. Validation and final writes
   - Sort notes by `start`, write JSON with `indent=2`, print summary.

### Extension Points (Future-Proofing)
- Add support for additional resource types (e.g., introductions as `type: "introduction"`) when an image-backed id policy is clarified.
- Optional inclusion of `book` or `book_id` metadata if desired by downstream consumers (not emitted by default to keep parity with examples).
- Pluggable image-selection rules (e.g., prioritize explicit `data-main="true"` if present in other translations).

### Decisions and Defaults (from stakeholder)
1. Include text-only resources:
   - If a sidebar has no non-decorative images, include it as a resource.
   - `id` generation:
     - If a meaningful title exists, generate `id` as a slug of the title.
     - Otherwise, generate `id` as a slug of the leading content text (first 8–12 words), normalized.
2. Sidebars with multiple images:
   - Include all non-decorative images by emitting one resource per image (shared title/content/type), with `id` set to the image filename.
3. Non-image introductions & articles:
   - Include them in `resources.json`.
   - `id` is a slug derived from the article/introduction title.
   - Type classification: `introduction` if clearly an introduction; otherwise `article`.
4. Image copying:
   - Copy the entire `<TRANSLATION>_images/` folder into the output by default.
   - Provide an opt-in flag to copy only referenced images.

Note: These decisions override earlier defaults in this plan where they differ.

### Resource Extraction (chapters and non-sidebar study materials)
- In addition to sidebars, include non-image introductions and study articles that appear as `<chapter>` elements outside Bible text chapters:
  - Detection heuristics (case-insensitive): `semantic` contains keywords like `introduction`, `article`, `how to`, `overview`, `chronology`, or chapters under front/back matter divisions.
  - Exclude pure Bible text chapters (e.g., semantic like `Genesis 1`).
- Title extraction order of preference within a chapter:
  1) `<ctfm>`, 2) `<ah>` or `<inh>`, 3) first `<h1>`/`<h2>`, 4) fallback to `semantic`.
- Content serialization: reuse the same serializer used for sidebars (lists, tables, paras, and cross-references to `<a ref='...'>...</a>`; collapse whitespace).
- `id` for non-image chapter resources: slug derived from the selected title.
- `type`:
  - `introduction` when the chapter clearly denotes an introduction.
  - `article` for general articles, guides, indexes (unless you later prefer more granular types).

### SCML Structure Reference (for maintainers and future agents)
- DTD/version differences:
  - Sample file uses ScML v3.0.0; ESV uses v2.4.1. Tag sets are largely compatible but minor tag name variations exist (e.g., emphasis tags like `<bi>`, small caps via `<ac>`, tetragrammaton styling via `<tetr-bi>`).
- Top-level hierarchy:
  - `<scml>` → `<division>` (e.g., `id="fm"` for front matter) → `<book>` → `<chapter>` → content elements.
- Books and chapters:
  - A canonical Bible book typically has `book id="bkNN"` and chapters `chapter id="chNNCCC"` with `semantic` like `Genesis 1`.
  - Study note sections often appear as a chapter like `id="anc01"` (or similar) titled “Study Notes and Features for <Book>”.
- Study notes:
  - Each note is a `<com id="comBBCCCVVV[letter?]">`.
  - The first child `<bcv><xbr t="...">display</xbr></bcv>` encodes the verse/range. Content continues after `<bcv>`; inline cross-references use `<xbr t="...">`.
- Cross-references:
  - `<xbr t="Book Chap:Verse[-Chap:Verse|-Verse]">Display</xbr>`.
  - We convert to `<a ref='Full Book Name Chap:Verse[–...]'>Display</a>`.
- Sidebars (resources):
  - `<sidebar id="sbc...">` often indicates charts; `<sidebar id="sbm...">` indicates maps/figures.
  - Titles often appear in `<figh><xref>Title</xref></figh>` or `<th><xref>Title</xref></th>`.
  - Images inside `<figure>` → `<fig><img src="images/<filename>.jpg"/></fig>`.
  - Decorative assets to ignore commonly include: `hcp-rule.jpg`, `ctorntop.jpg`, `ctornbottom.jpg`, `csorn.jpg`, logos.
- Front/back matter and articles:
  - Front matter `chapter` examples: `toc`, `howto`, `indcharts`, `introduction`, etc., often use tags like `<ctfm>`, `<ah>`, `<pf>`, `<pcon>`, `<list>` with items `<bl>`, `<blf>`, `<bll>`, and tables `<table>` with cells `<cell>`, `<tdnl>`, `<tdul>`.
  - Indexes use `<index>` with items `<in>` and internal `<xref>`.
- Table of contents:
  - `tocpt` are section titles; `toc1`, `toc2` level entries link via `<xref idref="...">` to targets elsewhere in the SCML.
- Images pathing:
  - In SCML, images appear as `src="images/<filename>.jpg"`; on disk they live in `inputs/<TRANSLATION>/<TRANSLATION>_images/<filename>.jpg`.
- Other inline formatting you may see:
  - `<bi>` (bold-italic styled content but we normalize to `<b>` or `<i>` as appropriate), `<sm>` (small caps/size), `<ac>` (small caps annotation), `<tetr-bi>` (special styling), plus headings `<h1>`, `<h2>` in some files.


### Risks and Mitigations
- Huge files: Streaming parse with `iterparse` and immediate `elem.clear()`.
- Variant SCML tags across translations: Use robust tag handling and fallbacks for title and content.
- Image mismatch between SCML and filesystem: add `--strict-images` and detailed warnings.
- Over/under-inclusion of resources: start with `sbc`/`sbm` sidebars; we can expand after a small sample run.

### Dry Run Plan (ESV)
- Run the CLI for `ESV` only.
- Verify that `notes.json` structure matches `example_notes.json` (keys and formatting), and that sample entries for Genesis 1 are correct.
- Verify that `resources.json` includes entries like “The Nations of Genesis 10” using image `hcp-esvmacarthursb02-fig18.jpg` with `type: "figure"`, and that images are copied under `output/ESV/images/`.
- Confirm whitespace normalization and cross-reference anchor format.

### Deliverables
- New CLI module (single entrypoint) with:
  - Streaming SCML parse
  - Notes and resources extraction as specified
  - Image copying
  - Flags for single/all translations and image policies
- README snippet for running the CLI
- Deterministic `notes.json` and `resources.json` per translation under `output/`

