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

You also need staff or collaborator access to the Melt store (`melt-co-uk-maqm6c3j`).

## Stores

| Environment | Store | Notes |
|---|---|---|
| Pre-launch / production | `melt-co-uk-maqm6c3j.myshopify.com` | Paid client transfer store. Password protected. Ownership transfers to Melt at handover. Will take the `melt.co.uk` domain once acquired. |
| Current live site | `https://www.themeltco.com/` | WordPress/WooCommerce — stays live until the Shopify launch in October 2026. |

The earlier Partner dev store (`holdens-melt-dev.myshopify.com`) is retired.

- Admin: `https://admin.shopify.com/store/melt-co-uk-maqm6c3j`

### Themes on the store

| Theme | Role | ID |
|---|---|---|
| `Holdens Dawn Theme` | Published (live) | `195550380358` |
| `Development (…)` | Temporary, created by `shopify theme dev` | varies per machine |

`Holdens Dawn Theme` is **our theme** — this repo's Dawn fork. Horizon (the new-store default) has been deleted.

Until launch, "live theme" and "live site" are different things: the store is password protected with no SEO, so the published theme is effectively a dev site. The customer-facing site is still WooCommerce.

## Getting started

```bash
git clone git@github.com:holdensdevteam/melt-shopify-theme.git
cd melt-shopify-theme
git checkout develop
```

Open in VS Code and install the recommended extensions when prompted — `.vscode/` is committed so the whole team gets the same Liquid setup.

Then start the dev server:

```bash
shopify theme dev --store=melt-co-uk-maqm6c3j.myshopify.com
```

First run opens a browser for Partner authentication. It uploads your local files as a **development theme** (separate from anything published) and serves a live-reloading preview.

- Storefront preview: `http://127.0.0.1:9292`
- Store admin: `https://admin.shopify.com/store/melt-co-uk-maqm6c3j`
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
| `develop` | Integration branch. Matches `Holdens Dawn Theme` pre-launch. |
| `feature/*` | Branched off `develop`, PR'd back into it. |

Tag `dawn-baseline` marks unmodified Dawn 16.0.0, for diffing our changes against upstream.

## Deployment

**During the build, deploys are manual** via `shopify theme push`. The Shopify GitHub integration is deliberately not connected yet — its bidirectional sync gets messy mid-build.

Closer to launch we'll connect it. When we do, `config/settings_data.json` starts flowing back from the admin whenever anyone edits in the theme editor, so read the notes in `.shopifyignore` before that switch happens.

### Which URL shows what

| URL | Serves |
|---|---|
| `http://127.0.0.1:9292` | Your **local files**, rendered by Shopify against the store's real data. Backed by a temporary development theme, visible only to you, expires after ~7 days idle. |
| `https://melt-co-uk-maqm6c3j.myshopify.com` | Whichever theme is **published** — currently `Holdens Dawn Theme`. Password protected. |

`shopify theme dev` never touches the published theme, which is why local changes don't appear at the myshopify URL until you push.

### Pushing to the store

`shopify theme push` uploads **files on disk, not commits**, and `shopify theme pull` overwrites local files — neither merges or looks at Git. **Commit before every push and every pull.**

**Pre-launch, with one editor (now):** pushing straight to the published theme is fine, because the store isn't customer-facing yet.

```bash
shopify theme push --live --store=melt-co-uk-maqm6c3j.myshopify.com
shopify theme pull --live --store=melt-co-uk-maqm6c3j.myshopify.com   # bring theme-editor changes back, then commit
```

**Once Melt are editing in the admin, and after launch:** stop pushing `--live`. Push to an unpublished theme, preview it, then publish from Online Store → Themes (the old theme stays in the library as a rollback):

```bash
shopify theme push --unpublished --theme "Melt develop" --store=melt-co-uk-maqm6c3j.myshopify.com
```

`--live` doesn't publish a new theme — it overwrites the files inside whichever theme is published, with no backup. These files carry theme-editor edits and are the danger zone: `templates/*.json`, `config/settings_data.json`, `sections/*-group.json`, `locales/*.json`. Narrow the blast radius with `--only` / `--ignore` when in doubt.

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
