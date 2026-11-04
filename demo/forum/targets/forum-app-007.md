# 007 — Safe content in the existing Quarkus JSON forum

Implement the canonical content-sanitization feature in the pinned Java product. Existing
threads already persist text and emit an outbox event atomically. Preserve that transaction,
authentication, CSRF, security headers and the plain-text mobile client's body field. No new
dependency, endpoint, database column or migration is needed. The application returns JSON,
so derive safe HTML from the normalized stored Markdown instead of storing redundant HTML.

## Required interfaces and behavior

Add public `local.aeion.forum.ContentSanitizer` with static `sanitize(String raw)`, returning a
public record with `markdown()` and `html()` string accessors. Add nested public static
`ContentTooLargeException extends RuntimeException`; its message is `content_too_large`.
Null input means empty text, preserving the existing empty-body business refusal.

Normalize to Unicode NFC, turn CRLF/CR into LF, remove control/format codepoints except LF/TAB,
collapse horizontal whitespace outside fenced code, strip non-code lines, collapse blank-line
runs to one blank line, and remove leading/trailing blank lines. Preserve code-block indentation
and trailing spaces. Normalization must be idempotent. Both original and normalized text are
bounded to 4000 Unicode codepoints, not UTF-16 units; HTML is bounded to 32768 UTF-8 bytes.
Exceeding a limit throws ContentTooLargeException, never truncates or stores partial work.

Produce a deliberately small Markdown subset, with no raw HTML passthrough or attributes:

- Paragraphs: `bonjour` -> `<p>bonjour</p>`. Join lines within a paragraph with one space.
- Separate block outputs with one LF, without a final LF.
- `**fort** et *doux*` -> `<p><strong>fort</strong> et <em>doux</em></p>`.
- `- un\n- deux` -> `<ul><li>un</li><li>deux</li></ul>`.
- `1. un\n2. deux` -> `<ol><li>un</li><li>deux</li></ol>`.
- `> bonjour\n> monde` -> `<blockquote><p>bonjour monde</p></blockquote>`.
- A triple-backtick fence with optional language opens a code block; ignore the language label.
  ` ```java\n  <x>  \n``` ` (without the outer spaces) produces
  `<pre><code>  &lt;x&gt;  \n</code></pre>`.

Only p/strong/em/ul/ol/li/blockquote/pre/code elements are allowed. Escape HTML metacharacters
before emitting text. Images, tables, links, autolinks, event handlers, raw HTML and URL-looking
text remain inert text. No network/file/process access. This is not full CommonMark; nested
Markdown is not required. Code content must remain literal, including Markdown punctuation.

In ThreadService.create, normalize before validating/storing body; the database and the
outbox must not retain original transport bytes. Keep existing invalid_title/invalid_body
business refusals. In ThreadsResource, add body_html on create/read/list, derived through the
same sanitizer from stored body. Preserve body as normalized plain Markdown, not escaped HTML.
Map ContentTooLargeException to HTTP 413 with `{"error":"content_too_large"}` before any
thread/outbox insert. Existing rows are rendered safely on read; no bulk rewrite is requested.

## Protected acceptance

The external test checks 30 hostile payloads against an XML parser that allows only the tags
above and no attributes, exact fixtures for the subset and normalization, stored canonical
Markdown, repeat rendering, codepoint limits including supplementary Unicode, JSON 413, and no
outbox write on refusal. The full existing suite must also pass. Sources needed for the edit
are supplied separately as pinned source context. Return complete focused implementation
files; do not modify the test database harness, existing tests or the external contract. A
small independent candidate test is optional. Keep the entire changed-file review below its
24000-character envelope.
