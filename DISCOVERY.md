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
| TikTok scouts | `site:tiktok.com faceless reddit stories`, `… fun facts voiceover account`, `… satisfying videos account`, `… motivation quotes page` | TikTok search/tag pages are blocked, so web search finds public profile URLs, then the profile page is read for followers, likes and video count |
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
| TikTok public profile pages | ✅ reachable (sometimes bot-challenged) | Followers, hearts, video count. No per-video views |
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

## Faceless check
- **Automated:** OpenCV YuNet face detection plus SFace identity matching on YouTube's public frame thumbnails (hq1–hq3) of the 6 latest shorts.
- **Faceless** means no person recurs on camera across 2 or more of those shorts.
- **Manual reviews** (dated, with evidence) live in `config/reviews.json` and override the automated check. Example: `@justicebuys1` failed review because a presenter appears on camera.

## Replication rule
Notes describe **formats, hooks, length and cadence only**. Make original scripts and use our own or licensed footage. Never repost anyone's content.
