# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

The Shopify theme for **The Melt Co.** ("Melt"), built by **Holdens** (Manchester agency). It's a fork of **Shopify Dawn 16.0.0** — the `dawn-baseline` tag marks the unmodified starting point.

Melt are a British artisan maker of luxury handmade scented candles, reed diffusers and organic body/skincare, based at Backridge Farm in Lancashire. This project is a full replatform from WordPress/WooCommerce.

## Architecture

Standard Dawn / Online Store 2.0 layout — `layout/`, `templates/` (JSON), `sections/`, `snippets/`, `assets/`, `config/`, `locales/`.

**There is no build step.** Dawn ships build-step-free and we're keeping it that way. CSS is plain CSS, JS is vanilla with Web Components. Don't introduce SCSS, a bundler, or a `package.json` without asking first.

## Commands

```bash
shopify theme dev --store=holdens-melt-dev.myshopify.com   # local dev, http://127.0.0.1:9292
shopify theme check                                        # lint — must pass before a PR
shopify theme list
shopify theme pull                                         # pull theme-editor changes back
shopify theme push                                         # deploy (--unpublished / --live)
```

Deploys are **manual CLI** during the build. The Shopify GitHub integration is deliberately not connected yet — don't suggest connecting it as a fix for something.

## Branches

`main` = production/live · `develop` = integration/dev store · `feature/*` off develop.

Work happens on `develop` unless told otherwise. Don't commit or push unless asked.

## Conventions

- **Theme Check must pass.** Config in `.theme-check.yml`.
- **No hard-coded user-facing copy.** Everything goes through `locales/en.default.json` and the `t` filter.
- **Prefer Dawn's existing patterns** — Web Components, Section Rendering API, `image_url` with responsive `srcset` — over new abstractions.
- **Merchant experience matters.** New sections need sensible presets, grouped settings and clear labels in `{% schema %}`; Melt's team will use the theme editor daily.
- **Accessibility is not optional.** Dawn's semantics, focus management and keyboard handling are there deliberately — don't strip them while restyling.

## Two things that are easy to get wrong

**1. URL handles are SEO-critical.** This is a migration from an established WooCommerce site with real organic traffic and a redirect map in progress. Product, collection and page handles are not free to change. Flag any change that affects a URL, and never rename handles as incidental cleanup.

The old site's taxonomy is faceted — everything under `/scented-candles/` split by fragrance / season / type / occasion — and how that maps onto Shopify collections is an open IA question, not settled. Don't assume a structure.

**2. Don't prune Dawn sections speculatively.** Aggressive pruning of unused sections is planned, but only once wireframes are signed off. Deleting a section before we know what the design needs means rebuilding it later.

## Brand voice

Warm, understated, rural, quietly confident. First-person plural, storytelling, dry humour. Not shouty, not corporate. **Never over-claim.**

Any placeholder or example copy written into the theme should sound like Melt. Several brand claims are still unverified (founding date, "traditional slow-burning techniques", 36-hour make time) — don't put them in copy.
