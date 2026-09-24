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
shopify theme dev --store=melt-co-uk-maqm6c3j.myshopify.com   # local dev, http://127.0.0.1:9292
shopify theme check                                            # lint — must pass before a PR
shopify theme list
shopify theme pull --live                                      # pull theme-editor changes back (commit first)
shopify theme push --live                                      # deploy to Holdens Dawn Theme (see below)
```

Deploys are **manual CLI** during the build. The Shopify GitHub integration is deliberately not connected yet — don't suggest connecting it as a fix for something.

Store `melt-co-uk-maqm6c3j.myshopify.com` — a paid **client transfer store** (replaced the earlier `holdens-melt-dev` Partner dev store, which is retired). It transfers to Melt at handover and will take the `melt.co.uk` domain once acquired. Its published theme is **`Holdens Dawn Theme`** (id `195550380358`) — our Dawn fork.

**Pre-launch, "live" is still a dev site.** The customer-facing site is the WooCommerce store at `https://www.themeltco.com/` until the Shopify launch in October 2026. The Shopify store is password-protected with no SEO, so `shopify theme push --live` is acceptable while Lawrence is the sole editor. Still commit before any push or pull — both overwrite without merging and ignore Git state.

**This changes once Ted (Melt) starts working in the admin, and at launch.** From then on: no `--live` pushes without Lawrence explicitly asking; use `--unpublished` and share the preview; never overwrite `templates/*.json`, `config/settings_data.json`, `sections/*-group.json` or `locales/*.json` on the live theme without confirming, since they carry merchant edits.

`shopify theme push` uploads working-tree files, not commits. `127.0.0.1:9292` serves local files via a temporary development theme and never touches the published one.

## Branches

`main` = production/live · `develop` = integration (currently what's on Holdens Dawn Theme) · `feature/*` off develop.

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
