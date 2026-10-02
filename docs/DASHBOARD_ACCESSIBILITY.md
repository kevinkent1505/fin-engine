# Dashboard Accessibility and Responsive Design

The Fin Engine dashboard uses glassmorphism as a visual layer, not as a reason to reduce readability. Business information, source provenance, and chart meaning must remain understandable without relying on transparency, blur, color, hover, or a desktop-sized screen.

## Design principles

### Glass with readable surfaces

Primary dashboard panels use the shared `glass-panel` class. Secondary surfaces use `glass-subpanel`, and the sticky application header uses `glass-header`.

The implementation deliberately keeps the glass surfaces relatively opaque and pairs them with dark slate text. Do not make a panel more transparent if doing so reduces text or chart contrast against the page background.

The visual system uses:

```text
light translucent surfaces
subtle borders
background blur
soft shadows
high-contrast text
restrained blue / green / amber accents
```

Glass treatment is progressively enhanced. In forced-colors mode, blur, transparency effects, and decorative grid backgrounds are removed so platform colors can take over.

## Responsive behavior

The dashboard supports small screens down to a 320 px layout width.

The major responsive rules are:

- desktop sidebar at `lg` and above;
- sticky horizontal navigation below `lg`;
- minimum 44 px navigation/link touch targets;
- one-column page content first, expanding to multi-column layouts at larger breakpoints;
- metric cards move from one column to two and four columns as space allows;
- long tables become horizontally scrollable rather than shrinking text beyond readability;
- charts use responsive SVG view boxes with an explicitly scrollable minimum width on narrow screens;
- headings reduce in size on phones and scale up at tablet/desktop breakpoints;
- cards use smaller padding on phones and larger padding when space is available.

Do not introduce fixed desktop widths for page content. When a visualization genuinely needs horizontal space, allow the chart itself to scroll while keeping the page viewport stable.

## Keyboard access

The shell provides a `Skip to main content` link that becomes visible on focus.

Primary navigation:

- is implemented with real links;
- exposes `aria-current="page"` for the active route;
- has visible focus rings;
- preserves a minimum 44 px target height.

Scrollable chart and table regions are keyboard focusable so keyboard users can reach and scroll them when necessary.

Do not replace semantic links or buttons with clickable `div` elements.

## Focus treatment

The global stylesheet provides a strong `:focus-visible` outline. Components may provide more context-specific focus rings, but they must not remove visible focus without an equivalent replacement.

Avoid `outline: none` unless a visible focus indicator is added in the same rule/component.

## Charts

Charts must not communicate meaning through color alone.

Current D3/SVG charts provide:

- visible text labels;
- an SVG `<title>` and `<desc>`;
- `role="img"` with `aria-labelledby`;
- accompanying screen-reader-only data tables;
- stronger text/stroke contrast than the initial POC;
- horizontally scrollable chart regions on narrow screens.

When adding a chart, preserve the same pattern. A screen reader should be able to obtain the underlying values even if it cannot interpret the SVG geometry.

## Tables

Business tables should use native table semantics:

- `<caption>` (visible or `sr-only`);
- `scope="col"` for column headings;
- `scope="row"` when the first cell identifies the row;
- a horizontally scrollable wrapper on small screens when needed.

Do not replace data tables with arbitrary CSS grids solely for visual convenience.

## Color and status

Source confidence uses both text and color:

```text
official
observed
illustrative
```

The color is supplementary. The textual status must always remain present.

Likewise, positive, caution, and reference states must keep readable labels rather than relying on green, amber, or blue alone.

## Motion

The dashboard honors `prefers-reduced-motion: reduce` by removing or effectively disabling transitions and animations.

Do not add motion that is required to understand a number or navigate the product.

## Forced colors / high contrast

The stylesheet contains a `forced-colors: active` fallback. Glass surfaces become normal canvas surfaces with visible system borders, and decorative grid backgrounds are removed.

New components should remain understandable when background colors, gradients, shadows, and blur disappear.

## Content accessibility

Business copy should use plain language and explicitly state the semantic meaning of values.

Examples:

```text
Marketplace asking price
Official NJKB reference
Auction limit reference
Illustrative POC data
```

Avoid presenting a numeric value without enough context for a business user to understand what it represents.

## Manual verification checklist

Before considering a dashboard change complete, check at minimum:

```text
[ ] 320 px phone width has no page-level horizontal overflow
[ ] 375 / 390 px phone layout is readable without zoom
[ ] tablet layout does not create awkward empty columns
[ ] desktop sidebar and content remain usable at 1024 px+
[ ] keyboard can reach all navigation and interactive/scrollable regions
[ ] active navigation is announced with aria-current
[ ] skip link reaches the main content
[ ] focus indicators are visible
[ ] charts include title/description and a non-visual data representation
[ ] tables use captions and heading scopes
[ ] status is not conveyed by color alone
[ ] reduced-motion preference does not hide information
[ ] forced-colors mode still exposes boundaries and hierarchy
[ ] browser zoom at 200% remains usable
```

## Recommended automated checks

As the POC becomes production-oriented, add an end-to-end browser test layer with automated accessibility checks (for example Playwright plus axe-core) for each dashboard route.

The automated checks should supplement, not replace, keyboard, zoom, responsive, and screen-reader-oriented manual review.
