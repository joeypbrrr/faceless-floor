# Discovery config — why each term and source

Config: [`config/discovery.json`](config/discovery.json). Checked from this research machine on **Nov 7, 2026, 1:15–1:45 AM ET**.
Rules: public, unauthenticated pages only. No logins, no accounts, no API keys we don't have, no CAPTCHA or Cloudflare bypass. A blocked source gets logged and shown on the site, and nobody works around it.

## Goal
Find **high-signal, low-competition faceless pages** that are easy to copy as a *format* (never their content) and can earn money: ~1-minute Shorts on ad revenue, affiliate/product pages and meme pages.

## Queries per platform
| Team | Query / tag | Why |
|---|---|---|
| YouTube Shorts scouts | `faceless shorts channel` | Channels that call themselves faceless |
| | `reddit stories shorts` | Reddit narration over gameplay is the biggest faceless Shorts format |
| | `did you know facts shorts` | AI/voice-over facts: cheap, high volume |
| | `motivation shorts stock footage` | Edit-only motivation, no talent on camera |
| | `oddly satisfying shorts` | Visual-only, loops well |
| | `ai story shorts` | Fast-growing AI narrative segment |
| | `scary stories shorts` | Narration + visuals, heavy comments |
| Faceless niche scouts | `reddit stories #shorts`, `aita reddit story #shorts`, `fun facts #shorts`, `history facts #shorts`, `motivational quotes #shorts`, `oddly satisfying #shorts`, `amazon finds #shorts`, `space facts #shorts`, `true crime story #shorts`, `ai generated story #shorts` | Video search ranks the most-viewed Shorts per niche; the agent opens the top 3 and resolves the channel |
| Meme page scouts | YouTube hashtag pages `#memes`, `#brainrot`, `#dankmemes`, `#funnyanimals`, `#redditstories` | Public hashtag pages list viral Shorts |
| TikTok scouts | `site:tiktok.com faceless reddit stories`, `… fun facts voiceover account`, `… satisfying videos account`, `… motivation quotes page` | DuckDuckGo Lite, then Bing. Profile URLs and any `/video/` URLs are extracted. From this machine DuckDuckGo returns a CAPTCHA (not bypassed) and Bing often ignores `site:` |
| TikTok scouts | HypeAuditor public rankings: [global](https://hypeauditor.com/top-tiktok/), [United States](https://hypeauditor.com/top-tiktok-united-states/), [United Kingdom](https://hypeauditor.com/top-tiktok-united-kingdom/), [Canada](https://hypeauditor.com/top-tiktok-canada/), [Australia](https://hypeauditor.com/top-tiktok-australia/) | No login. First 50 rows each: followers, 30-day average views, likes, comments, shares. Averages are a cross-check, never the per-video median |
| TikTok scouts | Public niche articles and the Reddit RSS thread listed in `config/discovery.json` `tiktok.articles` | These pages are where `/video/<id>` links actually show up. The profile page's `itemList` is empty, so it cannot list recent uploads |
| Instagram scouts | `site:instagram.com faceless motivation page`, `… meme page reels`, `… facts page reels` | Finds handles; Instagram profile stats are behind a login wall, so their numbers stay unknown |
| Floor lead | Reddit RSS search `faceless` in r/NewTubers, r/youtubers, r/PartneredYoutube, r/Tiktokhelp, r/InstagramMarketing (2 subs per cycle, rotating) | Creator discussions about which faceless niches work right now, plus channels mentioned in them |
| Floor lead | `best faceless youtube channels examples 2026`, `faceless youtube shorts channels making money examples` | Public roundups that name channels |

## Directories and aggregators (checked Nov 7, 2026)
| Source | Status | Notes |
|---|---|---|
| YouTube search (videos/channels) | ✅ reachable | Main discovery source |
| YouTube watch pages | ✅ reachable | Exact views, likes, comment count, publish date |
| YouTube channel pages | ✅ reachable | Subscriber count (YouTube rounds it) and latest shorts |
| YouTube hashtag pages | ✅ reachable | Viral Shorts per tag |
| Social Blade — YouTube channel pages | ✅ reachable | 14-day daily view deltas, used in the real-vs-fake check |
| Social Blade — TikTok user pages | ✅ reachable | Followers, likes, videos |
| Social Blade — Top 100 YouTube | ✅ reachable | Mega-channels only, so low relevance |
| TikTok public profile pages | ✅ reachable | Followers, hearts, video count, bio. `userInfo.itemList` is empty, so recent videos are not listed |
| TikTok public video pages | ✅ reachable | `webapp.video-detail` → `statsV2.playCount`, likes, comments, caption, `textLanguage`, caption language, `IsAigc` |
| TikTok oEmbed | ✅ reachable | Official `https://www.tiktok.com/oembed?url=…`. On Nov 7, 2026 the JSON confirmed `type: video`, `provider_name`, and `embed_product_id` (the video id). It did not include `author_name`, a title, or a view count |
| HypeAuditor Top TikTok rankings (global, US, UK, Canada, Australia) | ✅ reachable, no login | 50 public rows per page in the Nuxt payload. Per-account report URLs are Cloudflare-blocked and are not opened |
| Reddit public RSS search | ✅ reachable, rate-limited (429 after a few requests) | Kept to 2 subs per cycle |
| Playboard Shorts charts | ✅ reachable | Not wired in yet |
| NoxInfluencer rankings | ✅ reachable | Not wired in yet |
| Bing web search | ⚠️ reachable but degraded | From this machine, results ignore the `site:` operator. Used only as a fallback |
| DuckDuckGo Lite | ⚠️ worked once, then HTTP 202 (anti-bot) | Tried first each cycle; skipped when it blocks |
| DuckDuckGo HTML | ❌ HTTP 202 anti-bot | |
| Google Search | ❌ JS / consent wall | |
| Mojeek | ❌ HTTP 403 | |
| YouTube Trending | ❌ no video data (page discontinued) | |
| YouTube channel RSS | ❌ HTTP 404 | |
| TikTok tag pages | ❌ bot challenge | Not bypassed |
| TikTok discover pages | ❌ redirect to homepage | |
| TikTok Creative Center | ❌ JS app, redirects | Needs a logged-in session for data |
| Instagram profiles / hashtag pages | ❌ login wall | |
| Social Blade — Instagram | ❌ Cloudflare 403 | Not bypassed |
| Reddit public JSON | ❌ HTTP 403 | We use RSS instead |

## Seeds
See `seeds` in `config/discovery.json`. Every seed was opened and its numbers read on Nov 7, 2026. The pipeline deep-dives seeds every cycle.

## TikTok (scored like YouTube)

Module: `research/tiktok.py`, called from the hourly cycle in `research/pipeline.py`. A TikTok-only refresh of the current snapshot (it does not re-fetch YouTube) is `python3 research/pipeline.py --tiktok-only`.

Same qualification as YouTube: median views, an upload inside 14 days, faceless / AI check, like rate 0.5–25%, comments on at least 2 sampled videos, and a follower count read from the profile. Two TikTok-only rules:

- **English only.** Each sampled caption is labelled from TikTok's `textLanguage` and caption `languageCode`, plus [langdetect](https://github.com/Mimino666/langdetect) 1.0.9 (Apache-2.0, vendored under `research/vendor/`) on the caption and the bio. A video with conflicting signals is not counted as English. The account is included only when at least 60% of classified captions are English. The profile `language` field is the account UI language and is recorded, not used as the verdict. Accounts with no caption sample are screened out, not listed as candidates.
- **Full vs partial.** A full qualifier needs 6 public videos that each have a play count, a like count, and a publish time inside 14 days. Fewer than that is `coverage: partial`: the median is still computed on whatever was verified, and the account stays off the Top 10. HypeAuditor's 30-day average views are stored beside the median and are never copied into it.

What is read, and what is not:

- Profile HTML (`__UNIVERSAL_DATA_FOR_REHYDRATION__` → `webapp.user-detail`) for followers, hearts, video count, and bio. No cookies are sent or stored.
- Video HTML (`webapp.video-detail` → `itemInfo.itemStruct.statsV2.playCount`) for views, likes, comments, caption, language, and TikTok's own AIGC flag (`IsAigc` / `AIGCDescription`). That flag is the TikTok equivalent of YouTube's "altered or fully generated" label.
- Official oEmbed (`/oembed?url=`) to confirm a video URL. On Nov 7, 2026 it returned `type`, `provider_name`, and `embed_product_id` (must match the video id) and did not return a view count or author name.
- HypeAuditor ranking pages for the seed lists above. Rows whose public name or bio matches a faceless/AI niche are opened on TikTok. The rest stay in the ranking table. They are not marked faceless or not-faceless, because their videos were not opened.
- Face check, when the OpenCV models are installed: one public cover image per verified video, same YuNet + SFace rule as YouTube. A recurring real face fails. An AI face still needs the AI rule or a dated manual review; the detector cannot tell them apart.

Pass on Nov 7, 2026 (2:52 AM ET), merged into the existing snapshot: 250 HypeAuditor rows (50 on each of the five lists), 6 English-verified TikTok candidates, 0 full qualifiers. All 6 are partial because fewer than six verified videos fall inside 14 days. Three sampled accounts were screened out as not English. `@askthereddit`'s only found video URL returns TikTok status 10204, so it has no caption sample and is not a candidate. YouTube's verified Top 10 was left as already published.

Known limits, checked from this research machine on Nov 7, 2026:

- The profile payload's `itemList` is empty, so the page does not reveal the latest uploads.
- DuckDuckGo Lite answers the video search with a CAPTCHA. It is not bypassed.
- Bing returns HTTP 200 and ignores `site:`, and it did not return `tiktok.com/@handle/video/<id>` links.
- Social Blade TikTok, TikTok tag pages, TikTok Creative Center, and HypeAuditor per-account report URLs are bot-challenged or JS shells. They are logged and skipped.
- Video URLs therefore come from links in the public articles in config. Those links are often not the account's latest six. The median is labelled partial unless six verified videos all fall inside 14 days.
- Wayback CDX was offline and the Common Crawl index timed out on a prefix query during this check, so neither is wired into the hourly cycle.

## Faceless check
- **Automated:** OpenCV YuNet face detection plus SFace identity matching on YouTube's public frame thumbnails (hq1–hq3) of the 6 latest shorts.
- **Faceless** means no person recurs on camera across 2 or more of those shorts.
- **AI-generated content counts as faceless** (Joey's rule, Nov 7, 2026). AI voiceover, AI images or video, AI avatars and synthetic narration are a *positive* faceless signal, never a disqualifier. Each candidate gets an `ai_generated` flag (`yes` / `no` / `unknown`) with evidence:
  - `yes` when YouTube's own "How this was made: sounds or visuals were altered or fully generated" label is on at least 1 sampled short, or AI tells (e.g. "AI-generated", "made with AI", "AI story", "AI voice", `#ai…` tags, Midjourney, ElevenLabs, Sora, Veo, Kling, Hailuo, text-to-speech) appear in the titles/descriptions of at least 2 sampled shorts, or the channel name/about text describes its content as AI-made.
  - `no` when 3+ shorts and the about text were read with no label and no tells. That means no public AI evidence, not proof of human production.
  - `unknown` when not enough public text was read.
  - `ai_generated = yes` sets faceless to **yes**. The exception is a face recurring across 3+ shorts: the detector can't tell an AI face from a real one, so the verdict is **unclear** until a dated manual review says AI face (faceless) or real human (fails).
  - An AI-generated face or avatar is not a real human and counts as faceless. A real human's face on camera still fails. All other criteria (views, recency, engagement, followers) are unchanged.
- **Manual reviews** (dated, with evidence) live in `config/reviews.json` and override the automated check. Example: `@justicebuys1` failed review because a presenter appears on camera; `@AIMagicalFamily` passed because its recurring faces are AI-generated people.

## Replication rule
Notes describe **formats, hooks, length and cadence only**. Make original scripts and use our own or licensed footage. Never repost anyone's content.
