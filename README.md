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

### Themes on the dev store

| Theme | Role | ID |
|---|---|---|
| `Melt-theme-v1` | Published (live) | `165005426913` |
| `Development (…)` | Temporary, created by `shopify theme dev` | varies per machine |

`Melt-theme-v1` is **our theme** — Dawn pushed as an unpublished theme and then published from the admin. Newer dev stores ship with Horizon as the default live theme; this store no longer has it.

Note that "live theme" and "live site" are different things. This is a development store, so nothing here is customer-facing — the published theme is just whichever theme the store URL serves.

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

### Which URL shows what

| URL | Serves |
|---|---|
| `http://127.0.0.1:9292` | Your **local files**, rendered by Shopify against the store's real data. Backed by a temporary development theme, visible only to you, expires after ~7 days idle. |
| `https://holdens-melt-dev.myshopify.com` | Whichever theme is **published** — currently `Melt-theme-v1`. |

`shopify theme dev` never touches the published theme, which is why local changes don't appear at the myshopify URL until you push.

### Pushing to the dev store

`shopify theme push` uploads **files on disk, not commits** — so commit first, or you'll lose track of what's actually deployed.

Safest route, which overwrites nothing:

```bash
shopify theme push --unpublished --theme "Melt develop" --store=holdens-melt-dev.myshopify.com
```

Then preview it in Online Store → Themes and hit **Publish** when you're happy. The previously published theme drops to unpublished but stays in the library as a rollback. Preview also gives you a shareable link for client review without publishing.

To update the published theme in place:

```bash
shopify theme push --theme 165005426913 --store=holdens-melt-dev.myshopify.com
```

**Careful with `--live`.** It doesn't publish a new theme — it overwrites the files inside whichever theme is currently published, with no backup. While `config/settings_data.json` is still syncing (see `.shopifyignore`), that also replaces any theme-editor settings on that theme with local defaults.

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
