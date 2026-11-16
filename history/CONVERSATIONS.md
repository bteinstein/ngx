# Past conversations in the claude.ai project (summary)

Full transcripts stay in the claude.ai project; this is the gist of each chat, newest first.

- **15 Nov — Daily trade volume for October.** Official volumes exist only for 6 Nov (and partly
  11 Nov); others are from broker lists or news. Planned running ngxprices in Claude Code on the web:
  connect GitHub repo bteinstein/ngx, environment "ngx" with Custom network access `*.ngxgroup.com`,
  setup script `pip install -e .`, branch `feature/volume-and-metadata`; test one day first.
- **13 Nov — Dashboard refresh.** Added 13 Nov closes (APT Securities, checked against GTI). Seplat
  ex-dividend. Linkage 3.1bn volume flagged as doubtful.
- **12 Nov — Dashboard update + trigger check.** 11 Nov provisional figures replaced with official
  closes (Okomu Oil corrected to ₦1,137.10). INTBREW closed ₦8.40, below its ₦8.50 trigger: normal
  volume, no dividend explanation, proposed capital reorganisation. Owner asked whether to keep or
  reset triggers after the 11 Nov decision date (unanswered).
- **11 Nov — Update dashboard (two chats).** Added 9–10 Nov from GTI Research; 11 Nov live snapshot
  (provisional). Sunu below trigger on 10 Nov on thin volume; no Sunu dividend in play (last ₦0.10,
  Jun 2025; ₦9.3bn rights issue Feb 2026 for recapitalisation).
- **9 Nov — Stocks with over 20% losses.** Corrected to use the whole portfolio, not just the new buys.
  Discussed running `ngxprices live` at 12:00 and 15:00 instead of waiting until night.
- **6 Nov — Refresh.** Presco news: dividend decision likely with FY results (Q1–Q2 2027); Saro Oil
  Palm acquisition (~$46.7M, related-party concerns); rights issue ~₦250bn.
- **2–4 Nov — Updates.** Century Securities lists used. Aradel fell 10% to ₦1,296: not a buy under the
  plan (buy-stop is above ₦1,740). Discussion of whether International Breweries was dragging the
  portfolio.
- **20–29 Oct — Daily updates.** Kobo Terminal then Century Securities as price sources. Presco
  limit-down 27 Oct (−₦210.6K). Zenith ₦1.50 interim dividend (qualified 23 Oct, paid 30 Oct).
- **16 Oct — Upcoming dividends.** Zenith confirmed; Seplat quarterly expected; MTN none left in 2026.
- **11–15 Oct — Setup.** Dashboard built from the owner's 11 Oct screenshots (Meristem, AfriInvest,
  InvestNaija) plus the 12 Oct contract notes; mapping confirmed 13 Oct. ₦2.2M plan agreed from the
  GlobFolio webinar slides and CoachOge DCF sheets.
- **Early Nov — ngxprices research.** Built the NGX price collection method and Python package
  (see the research paper link in CLAUDE.md).
