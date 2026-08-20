# Melt — Shopify Theme

The Shopify theme for [The Melt Co.](https://www.themeltco.com/), built by [Holdens](https://holdens.agency) as part of the WooCommerce → Shopify replatform.

Forked from [Shopify Dawn](https://github.com/Shopify/dawn) at **v16.0.0** — see the `dawn-baseline` tag for the unmodified starting point.

---

## Prerequisites

| Tool | Version |
|---|---|
| Node.js | v20+ (v24.19.0 in use, via NVM) |
| Shopify CLI | v4.7.0+ — `npm install -g @shopify/cli@latest` |
| Git | with SSH access to the `holdensdevteam` org |

You also need to be a member of the Holdens Shopify Partner organisation to access the dev store.

## Stores

| Environment | Store | Notes |
|---|---|---|
| Development | `holdens-melt-dev.myshopify.com` | Partner dev store. Test orders only (Bogus Gateway). Password protected. Ownership transfers to Melt at launch. |
| Production | TBC | Not yet provisioned. |

The dev store's **live** theme is Horizon, which ships by default on new dev stores. Leave it alone — don't delete it and don't publish over it. Local development renders our theme regardless of what's published.

## Getting started

```bash
git clone git@github.com:holdensdevteam/melt-shopify-theme.git
cd melt-shopify-theme
git checkout develop
```

Open in VS Code and install the recommended extensions when prompted — `.vscode/` is committed so the whole team gets the same Liquid setup.

Then start the dev server:

```bash
shopify theme dev --store=holdens-melt-dev.myshopify.com
```

First run opens a browser for Partner authentication. It uploads your local files as a **development theme** (separate from anything published) and serves a live-reloading preview.

- Storefront preview: `http://127.0.0.1:9292`
- Store admin: `https://holdens-melt-dev.myshopify.com/admin`
- Theme editor for your dev theme: the URL printed in the terminal on startup

## Everyday commands

```bash
shopify theme dev      # local dev server with hot reload
shopify theme check    # lint (also runs in CI on every push and PR)
shopify theme list     # list themes on the store
shopify theme pull     # pull theme-editor changes back into local files
shopify theme push     # upload to a theme
```

`shopify theme push` targets a theme you pick interactively. Add `--unpublished` to create a new one, or `--live` to overwrite the published theme — be deliberate with `--live`.

## Branches

| Branch | Purpose |
|---|---|
| `main` | Production-ready. Matches the live store. |
| `develop` | Integration branch. Matches the dev store. |
| `feature/*` | Branched off `develop`, PR'd back into it. |

Tag `dawn-baseline` marks unmodified Dawn 16.0.0, for diffing our changes against upstream.

## Deployment

**During the build, deploys are manual** via `shopify theme push`. The Shopify GitHub integration is deliberately not connected yet — its bidirectional sync gets messy mid-build.

Closer to launch we'll connect it. When we do, `config/settings_data.json` starts flowing back from the admin whenever anyone edits in the theme editor, so read the notes in `.shopifyignore` before that switch happens.

## Staying in sync with Dawn

The `upstream` remote points at Shopify/dawn:

```bash
git fetch upstream
git log --oneline dawn-baseline..upstream/main
```

We **cherry-pick** fixes we want rather than merging Dawn releases wholesale — this theme will diverge substantially from Dawn and full merges would fight us.

## Conventions

- **No build step.** Dawn is build-step-free and we're keeping it that way. Don't add SCSS or a bundler without a real reason.
- **Design system before markup.** Colour schemes, typography, spacing and button/card styles get settled in `config/settings_schema.json` before section markup is edited.
- **All user-facing copy goes through `locales/en.default.json`.** No hard-coded strings in Liquid.
- **Theme Check must pass** before a PR is opened. Config lives in `.theme-check.yml`.
- **URL handles are SEO-critical.** This is a migration from an established WooCommerce site with an existing redirect map. Changing a product, collection or page handle is not a free action — flag it in the PR.

## Project context

Melt's brand voice is warm, understated and rural — first-person plural, storytelling, dry humour. Never over-claim. Any placeholder copy written into the theme should read like Melt, not like Dawn's lorem ipsum.

## Licence

Derived from Shopify Dawn, which is MIT licensed — see [LICENSE.md](/LICENSE.md). Melt-specific work is © Holdens.
