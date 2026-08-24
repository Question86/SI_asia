# Senna Source Manifest

_Generated: 2026-08-24T09:08:42+00:00_

Scope: actual runtime sources after base + hot + macro overlay merge.

## Counts

- Configured sources: `49`
- Active sources: `41`

### By lane

- base: `10`
- hot: `20`
- macro_policy: `11`

### By type

- github_search: `1`
- hackernews: `1`
- manual_note: `1`
- rss: `37`
- webpage_check: `1`

## Sources by lane

### base

- `openai_news_rss` — OpenAI News RSS / `rss` / class `-` / host `openai.com` / from `config/sources.yaml`
- `github_blog_atom` — GitHub Blog Atom / `rss` / class `-` / host `github.blog` / from `config/sources.yaml`
- `github_changelog_atom` — GitHub Changelog Atom / `rss` / class `-` / host `github.blog` / from `config/sources.yaml`
- `heise_security_atom` — heise Security Alerts / `rss` / class `-` / host `www.heise.de` / from `config/sources.yaml`
- `bsi_cert_bund_advisories` — BSI CERT-Bund Security Advisories / `rss` / class `germany_security_advisory` / host `wid.cert-bund.de` / from `config/sources.yaml`
- `bsi_cert_bund_csw` — BSI CERT-Bund Cyber-Sicherheitswarnungen / `rss` / class `germany_security_advisory` / host `www.bsi.bund.de` / from `config/sources.yaml`
- `cert_eu_security_advisories` — CERT-EU Security Advisories / `rss` / class `europe_security_advisory` / host `cert.europa.eu` / from `config/sources.yaml`
- `cert_fr_alerts` — CERT-FR Alertes / `rss` / class `europe_security_advisory` / host `www.cert.ssi.gouv.fr` / from `config/sources.yaml`
- `cert_fr_advisories` — CERT-FR Avis de sécurité / `rss` / class `europe_security_advisory` / host `www.cert.ssi.gouv.fr` / from `config/sources.yaml`
- `manual_notes` — Manual Notes Inbox / `manual_note` / class `-` / host `-` / from `config/sources.yaml`

### hot

- `hatena_hotentry_it` — Hatena Bookmark Hotentry IT / `rss` / class `japan_social_link_radar` / host `b.hatena.ne.jp` / from `config/hot_sources.yaml`
- `e27_asia_startups_feed` — e27 Asia Startup and Tech Feed / `rss` / class `asia_tech_media` / host `e27.co` / from `config/hot_sources.yaml`
- `jpcert_english_alerts` — JPCERT/CC English Alerts / `rss` / class `security_advisory` / host `www.jpcert.or.jp` / from `config/hot_sources.yaml`
- `twcert_security_news` — TWCERT/CC Security News RSS / `rss` / class `security_advisory` / host `www.twcert.org.tw` / from `config/hot_sources.yaml`
- `google_trends_japan_hot` — Google Trends Japan Hot Feed / `rss` / class `regional_trend_radar` / host `trends.google.co.jp` / from `config/hot_sources.yaml`
- `japan_digital_agency_news` — Japan Digital Agency News RSS / `rss` / class `apac_public_institution` / host `www.digital.go.jp` / from `config/hot_sources.yaml`
- `google_trends_korea_hot` — Google Trends South Korea Hot Feed / `rss` / class `regional_trend_radar` / host `trends.google.co.kr` / from `config/hot_sources.yaml`
- `google_trends_taiwan_hot` — Google Trends Taiwan Hot Feed / `rss` / class `regional_trend_radar` / host `trends.google.com.tw` / from `config/hot_sources.yaml`
- `google_trends_thailand_hot` — Google Trends Thailand Hot Feed / `rss` / class `regional_trend_radar` / host `trends.google.co.th` / from `config/hot_sources.yaml`
- `google_trends_philippines_hot` — Google Trends Philippines Hot Feed / `rss` / class `regional_trend_radar` / host `trends.google.com.ph` / from `config/hot_sources.yaml`
- `google_trends_vietnam_hot` — Google Trends Vietnam Hot Feed / `rss` / class `regional_trend_radar` / host `trends.google.com.vn` / from `config/hot_sources.yaml`
- `restofworld_feed` — Rest of World Global Tech Feed / `rss` / class `global_south_tech_media` / host `restofworld.org` / from `config/hot_sources.yaml`
- `reliefweb_mindanao_recovery_watch` — ReliefWeb Mindanao Recovery Watch / `webpage_check` / class `humanitarian_recovery_watch` / host `reliefweb.int` / from `config/hot_sources.yaml`
- `jpcert_english_blog` — JPCERT/CC English Blog Atom / `rss` / class `security_advisory` / host `blogs.jpcert.or.jp` / from `config/hot_sources.yaml`
- `jvn_vulnerability_notes` — JVN Japan Vulnerability Notes / `rss` / class `security_advisory` / host `jvn.jp` / from `config/hot_sources.yaml`
- `twcert_tvn_vulnerability_notes` — TWCERT/CC TVN Vulnerability Notes RSS / `rss` / class `security_advisory` / host `www.twcert.org.tw` / from `config/hot_sources.yaml`
- `github_trending_all_daily` — GitHub Trending RSS All Languages Daily / `rss` / class `open_source_platform` / host `mshibanami.github.io` / from `config/hot_sources.yaml`
- `github_search_japan_twitter_trend_rss_tools` — GitHub Search: Japan Twitter/X Trend RSS Tooling / `github_search` / class `open_source_platform` / host `-` / from `config/hot_sources.yaml`
- `usgs_m45_earthquakes_hour` — USGS M4.5+ Earthquakes Past Hour / `rss` / class `geoscience_institute` / host `earthquake.usgs.gov` / from `config/hot_sources.yaml`
- `hn_release_security_burst` — Hacker News Release/Security Burst / `hackernews` / class `platform_social` / host `-` / from `config/hot_sources.yaml`

### macro_policy

- `fed_monetary_policy_press` — Federal Reserve Monetary Policy Press Releases / `rss` / class `central_bank` / host `www.federalreserve.gov` / from `config/macro_sources.yaml`
- `fed_speeches_testimony` — Federal Reserve Speeches and Testimony / `rss` / class `central_bank` / host `www.federalreserve.gov` / from `config/macro_sources.yaml`
- `fed_policy_rates` — Federal Reserve Policy Rates Feed / `rss` / class `central_bank` / host `www.federalreserve.gov` / from `config/macro_sources.yaml`
- `fed_selected_interest_rates_h15` — Federal Reserve Selected Interest Rates H.15 / `rss` / class `central_bank` / host `www.federalreserve.gov` / from `config/macro_sources.yaml`
- `ecb_press_policy` — ECB Press Releases Speeches Interviews / `rss` / class `central_bank` / host `www.ecb.europa.eu` / from `config/macro_sources.yaml`
- `ecb_statistical_press` — ECB Statistical Press Releases / `rss` / class `central_bank` / host `www.ecb.europa.eu` / from `config/macro_sources.yaml`
- `ecb_open_market_operations` — ECB Open Market Operations and Communication / `rss` / class `central_bank` / host `www.ecb.europa.eu` / from `config/macro_sources.yaml`
- `ecb_yield_curve` — ECB Euro Area Yield Curve / `rss` / class `central_bank` / host `www.ecb.europa.eu` / from `config/macro_sources.yaml`
- `bis_press_releases` — BIS Press Releases / `rss` / class `central_bank_network` / host `www.bis.org` / from `config/macro_sources.yaml`
- `bis_central_bank_speeches` — BIS Central Bankers Speeches / `rss` / class `central_bank_network` / host `www.bis.org` / from `config/macro_sources.yaml`
- `bis_statistics` — BIS Statistical Releases / `rss` / class `central_bank_network` / host `www.bis.org` / from `config/macro_sources.yaml`
