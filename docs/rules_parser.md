# Rule Expressions and Rule Sheets

DRAM uses a small expression language to turn gene annotations and annotation
metadata into traits, summaries, and visualizations. This page describes the
rule-sheet format, expression grammar, aliases, rule availability options, and
the functions supported by the current Rule-Parser.

## Rule Sheets in DRAM

Rules are stored in tab-separated value (TSV) files. DRAM uses them when
evaluating traits with `--traits` and when building heatmaps with `--visualize`.
Custom sheets can be supplied with `--trait_rules_tsv` and `--viz_rules_tsv`.
Traits are evaluated through dram-viz and produce both a traits table and a
heatmap, so traits can use the same coverage functions as visualization rules.

DRAM automatically loads its common rule sheet for both traits and
visualizations. The common sheet contains reusable alias definitions, so a
custom rule sheet can reference a shared definition such as `@DNRA` without
copying its full expression. The maintained
[dram-viz rule sheets](https://github.com/BortonWrightonLabs/dram-viz/tree/main/dram_viz/data)
and
[common rules sheet](https://github.com/BortonWrightonLabs/Rule-Parser/blob/main/src/rules_common.tsv)
are useful examples when creating a custom sheet.

### Rule-Sheet Columns

| Column | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Output label for an evaluated rule. Leave it empty on a helper-only alias row. |
| `rule` | Yes | Rule expression to parse and evaluate. |
| `alias` | No | Reusable name assigned to the expression in the same row. |
| `rule_options` | No | Strict JSON controlling whether the rule is included. |
| `long_name` | Visualization only | Longer label shown in visualization metadata. |
| `group` or `topic_ecosytem` |  No | Groups related rules into a heatmap. |
| Other metadata | No | Columns such as `module`, or `notes` may organize downstream output. |

A row with a `name` is emitted as a result. A row with an `alias` defines a
reusable expression. A row may contain both, or it may leave `name` empty to
define a helper alias that is not emitted as a result.

Blank lines are allowed in rule sheets. A rule may also span physical lines
when the complete TSV field is enclosed in double quotes. For portability,
prefer one rule per physical line unless a long expression needs formatting.

### Common Alias Sheet Example

```text
name	alias	rule
	NitrateReduction	[K00370 & K00371] | [K02567 & K02568]
	NitriteReduction	K00362 | K03385
	Methanogen	K00399
```

### Traits Sheet Example

```text
name	rule	rule_options	topic_ecosystem
nitrate-reducer	@NitrateReduction	{}	traits
taxonomy-supported-methanogen	@Methanogen	{"include_when":{"all_columns_present":["taxonomy"]}}	traits
methanogen-without-taxonomy	@Methanogen	{"include_when":{"all_columns_absent":["taxonomy"]}}	traits
```

### Visualization Sheet Example

```text
name	rule	rule_options	long_name	group
nitrogen-reduction	path_steps(@NitrateReduction,@NitriteReduction)	{}	Nitrate and nitrite reduction	Nitrogen
ferredoxin-complex	path_subunits(K00196 & K00197 & K00198)	{}	Ferredoxin oxidoreductase complex	Carbon
```

### Multiline Rule Example

```text
name	rule	group
carbon-pathway	"path_steps(
[K00192 | K00195],
[K00193 & K00197 & K00194]
)"	Carbon
```

## Identifiers and Aliases

### Gene Identifiers

A bare identifier is always treated as a gene or feature identifier:

```text
K00370
nirK
EC:1.7.2.1
```

Feature matching is case-insensitive during evaluation. Identifiers containing
spaces or other characters outside the normal identifier syntax must be
enclosed in backticks:

```text
`multi word gene identifier`
```

### Alias References

Reference an alias by prefixing its name with `@`:

```text
@NitrateReduction & @NitriteReduction
```

Alias names containing spaces or other special characters can be enclosed in
backticks:

```text
@`Nitrate reduction`
```

Aliases are resolved recursively before evaluation. The parser reports an
error when:

- an `@Alias` reference has no definition;
- aliases form a cycle; or
- a bare gene identifier has the same name as a defined alias.

The last check prevents a misspelled alias reference from silently being
interpreted as a gene. If an alias named `NitrateReduction` exists, use
`@NitrateReduction`; a bare `NitrateReduction` is rejected. Gene identifiers
and alias names must therefore be unique within the combined custom and common
rule sheets.

### Qualified Identifiers

The grammar accepts `qualifier@identifier` for source- or namespace-qualified
feature names used by maintained rule sheets. Currently this is a convenience feature to help make certain items more clear what database they come from, but does not change any rule parsing itself:

```text
Fe@MtrA
Fe@MtrB_TIGR03509
```

The position of `@` is significant: `Fe@MtrA` is a qualified gene identifier,
while `@MtrA` is an alias reference.

## Expression Grammar

### Boolean Operators

| Operator | Meaning |
| --- | --- |
| `&` | Logical AND |
| `\|` | Logical OR |

Chains containing only one operator are valid:

```text
A & B & C
A | B | C
```

DRAM does not assign implicit precedence when `&` and `|` are mixed. Use square
brackets to state the intended grouping:

```text
[A & B] | C
A | [B & C]
```

Expressions such as `A | B & C` and `A & B | C` are invalid. Square brackets,
not parentheses, group rule expressions. Parentheses are reserved for function
calls.

### Step Expressions

Commas separate steps in a pathway or ordered set of evaluations:

```text
[A & B], [C | D], E
```

Boolean operators describe alternatives or required features within a step;
commas describe separate steps. Step expressions are commonly passed to
`percent`, `at_least`, and visualization coverage functions.

### Pipe Expressions

The pipe operator, `->`, passes filtered annotation data from one function to
the next:

```text
filter_contains(kegg_description,"nitrate reductase") -> column_count_values(heme_regulatory_motif_count,ge,4,ge,3)
```

Pipes are useful when a column aggregation should apply only to annotation rows
that pass one or more filters.

## Rule Options

The optional `rule_options` column contains strict JSON. JSON object keys and
string values must use double quotes. Leave the cell empty or use `{}` when no
options are needed.

Rule availability can depend on the annotation-file schema:

```json
{"include_when":{"all_columns_present":["taxonomy"]}}
```

The rule is included only when every listed column is present.

```json
{"include_when":{"all_columns_absent":["taxonomy"]}}
```

The rule is included only when every listed column is absent. Both conditions
may be combined when they refer to different columns:

```json
{"include_when":{"all_columns_present":["taxonomy"],"all_columns_absent":["dbcan_id"]}}
```

Presence refers to a column existing in the annotation TSV, regardless of
whether individual values are empty. A rule that does not satisfy its
`include_when` condition is omitted from the output; it is not evaluated as a
false result.

## Functions

Comparison arguments use `gt`, `ge`, `lt`, `le`, `eq`, or `ne`.

### `not(expression)`

Negates a Boolean expression.

```text
not(A & B)
```

### `percent(threshold, steps)`

Returns true when at least the specified percentage of steps is satisfied.
The threshold is an integer percentage.

```text
percent(60, [A & B, C | D, E])
```

### `at_least(count, mode, steps)`

Returns true when the total across the supplied steps is at least `count`. The
mode controls whether repeated hits contribute once or multiple times.

| Mode | What is counted | When to use it |
| --- | --- | --- |
| `PRESENCE` | The number of listed steps that are present. Each step contributes at most one, even when its genes occur multiple times. | Use when the rule requires a minimum number of distinct genes, subunits, or pathway steps. |
| `COUNTS` | The total number of matching gene occurrences across the listed steps. Repeated hits contribute to the total. | Use when copy number or the combined number of matching genes is biologically meaningful. |

For example, suppose a genome contains two copies of `A`, no copies of `B`, and
one copy of `C`. Two distinct steps are present, but there are three matching
genes in total. With a threshold of three, the modes differ:

```text
at_least(3, PRESENCE, [A, B, C])
at_least(3, COUNTS, [A, B, C])
```

The `PRESENCE` expression is false because only `A` and `C` are present. The
`COUNTS` expression is true because their occurrence counts sum to three. Use
uppercase `PRESENCE` or `COUNTS` in rule sheets. Counts apply most directly to
bare feature steps. A compound Boolean step such as `[A | B]` resolves to one
satisfied or unsatisfied step and therefore contributes at most one.

### `tax(label)`

Returns true when a sample's `taxonomy` value contains the supplied label. It
returns false when the annotation file has no `taxonomy` column. Use
`rule_options` when a taxonomy-dependent rule should be omitted instead.

```text
tax(g__Methanosarcina)
```

### `column_count_values(column, value_op, value_threshold, count_op, count_threshold)`

Compares each value in `column` with `value_threshold`, counts matching rows per
sample, and compares that count with `count_threshold`.

```text
column_count_values(heme_regulatory_motif_count,ge,4,ge,3)
```

### `column_sum_values(column, operation, threshold)`

Sums a numeric column per sample and compares the result with `threshold`.

```text
column_sum_values(heme_regulatory_motif_count,ge,10)
```

### `filter_contains(column, substring)`

Selects rows whose string value in `column` contains the supplied substring.
It is normally used before a pipe.

```text
filter_contains(kegg_description,"nitrate reductase")
```

### `filter_compare(column, operation, threshold)`

Selects rows whose numeric value in `column` satisfies the comparison. It is
normally used before a pipe.

```text
filter_compare(heme_regulatory_motif_count,ge,4)
```

### dram-viz Coverage Functions

`path_steps` and `path_subunits` produce coverage information for dram-viz.
They are accepted in both visualization and trait rule sheets because DRAM
evaluates traits through dram-viz and produces a traits heatmap. Parser uses
outside dram-viz must explicitly enable these functions or they are rejected.

#### `path_steps(step1, step2, ...)`

Reports the number and fraction of pathway steps present.

```text
path_steps(K00192 & K00195, K00193 & K00197 & K00194)
```

#### `path_subunits(expression)`

Reports the number and fraction of subunits present in a complex.

```text
path_subunits(K00244 & K00245 & K00246 & K00247)
```

## Troubleshooting

### Ambiguous Boolean Operators

If an expression contains both `&` and `|`, group each mixed portion with
square brackets. Also check that every opening bracket has a closing bracket.

### Alias Errors

For an undefined alias, check spelling and capitalization and confirm that the
alias exists in either the custom or common sheet. For a bare identifier that
matches an alias, add the `@` prefix if the alias was intended or rename the
alias if the identifier is genuinely a gene ID. Break alias cycles by replacing
at least one recursive reference with its underlying expression.

### Malformed `rule_options`

Use strict, single-line JSON with double-quoted keys and values. Check matching
braces and brackets. For example, this value is missing its final brace and is
invalid:

```text
{"include_when":{"all_columns_present":["taxonomy"]}
```

### Missing Annotation Columns

Column-based functions require the named annotation columns. Use
`rule_options.include_when.all_columns_present` when a rule should exist only
for inputs containing those columns. This avoids false results or evaluation
errors caused by unavailable data.

### Inspecting Required Features

When running dram-viz directly, add `--save_needed_features` to write
`needed_features.txt`. This lists the gene identifiers collected from the
expanded rules and can help diagnose spelling, capitalization, qualification,
and alias-expansion problems.
