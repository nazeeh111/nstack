# Authored native fast-mode alternative

This is the separately selected bounded native-binary sample lane, not the original Docker workflow or comprehensive coverage.


# Google Maps Scraper

Use the pinned gosom/google-maps-scraper runtime through its entry in the installation-local native-tools index, or the `runtime_recipe` in this skill's SOURCE.json. That recipe is retained in an immutable code release so it survives checkout removal. Read its help before running it.

Infer the requested public-place query and location. Fast mode requires a public search-center latitude/longitude; verify or obtain it before running. The default sample radius is1000meters. Do not infer the user’s personal location. Ask only for missing information that changes the result. Start with one representative query, a fresh task-owned output directory and a bounded run. The installed recipe uses fast HTTP mode, concurrency1 and depth1. It disables upstream telemetry, passes no proxy/provider credentials, and needs no Docker or additional browser runtime. The official Mac binary is amd64; Apple Silicon uses already-present Rosetta. It never installs Rosetta automatically.

```
python3 /recorded/absolute/path/maps_scraper.py run --query "public place type in location" --geo "latitude,longitude" --outdir /owned/fresh/output
```

Inspect `run.json`, the actual results and exit status. A zero exit with no rows is incomplete. Preserve partial output on errors or interruption. Never overwrite an existing output directory, advertise comprehensive coverage from a shallow sample, or treat scraped data as independently verified facts. For follow-on use, retain place/source URLs when available, query, observed date, coordinates and the actual source/runtime identity. Check duplicates and fields relevant to the task. Show only the useful columns; keep raw results private unless their publication is explicitly authorized.

Fast mode can return `data_id` while `place_id` and per-place `link` are empty. Preserve the actual identifier and query/center receipt; do not invent missing identifiers or URLs.

Fast mode targets category/business lists. A direct query for one named entity can return an empty business list; ordinary native browsing is the appropriate route for that single-place lookup. Do not mistake this parser outcome for a complete scrape or a proven access block.

Do not submit private user data in search queries, import cookies, inspect browser profiles or credentials, create cloud resources, connect a database, send outreach, set up paid proxies or bypass CAPTCHAs/access blocks. Stop on an access block and preserve evidence. Broader coverage, website crawling for emails and extra reviews require an actual scoped user request and separate dependency/permission evidence. They are not tested or activated by this fast-mode install.

The upstream skill's automatic refresh, mutable Docker pulls, sponsor prompts, credential setup and service startup are not installed. Update only through a newly reviewed pin. Source and MIT attribution: [gosom/google-maps-scraper](https://github.com/gosom/google-maps-scraper), runtime v1.18.2 at `146aefe83844960bb534f335261a4435783a58cc`.
