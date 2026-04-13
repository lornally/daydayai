import fs from "node:fs/promises";

const INPUT = new URL("../体育电影推荐片单.md", import.meta.url);
const OUTPUT_JSON = new URL("../bili_scan_results.json", import.meta.url);
const OUTPUT_MD = new URL("../bili_scan_results.md", import.meta.url);

function stripHtml(text = "") {
  return text.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
}

function normalize(text = "") {
  return text
    .toLowerCase()
    .replace(/[《》"'“”‘’()（）:：,，.!?+\-_/\\|]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parseDurationToMinutes(raw = "") {
  const parts = raw.split(":").map((part) => Number(part));
  if (parts.some((v) => Number.isNaN(v))) return 0;
  if (parts.length === 3) return parts[0] * 60 + parts[1] + parts[2] / 60;
  if (parts.length === 2) return parts[0] + parts[1] / 60;
  return 0;
}

function uniq(items) {
  return [...new Set(items.filter(Boolean))];
}

function parseEntries(markdown) {
  const lines = markdown.split("\n");
  let inFilmArea = false;
  const entries = [];
  const seen = new Set();

  for (const line of lines) {
    if (line.startsWith("## 先看这一批")) {
      inFilmArea = true;
      continue;
    }
    if (line.startsWith("## 资料参考")) break;
    if (!inFilmArea) continue;
    if (!line.startsWith("- 《")) continue;

    const m = line.match(/^- 《([^》]+)》([^：(]*?)\s*\((\d{4})/);
    if (!m) continue;

    const cnTitle = m[1].trim();
    const tail = m[2].trim();
    const year = m[3].trim();
    const engRaw = tail.replace(/\s+/g, " ").trim();
    const engTitles = uniq(
      engRaw
        .split("/")
        .map((s) => s.trim())
        .filter((s) => s && !/^[，,、]/.test(s))
    );

    const key = `${cnTitle}__${engTitles[0] || ""}__${year}`;
    if (seen.has(key)) continue;
    seen.add(key);

    const hasChineseCnTitle = /[\u4e00-\u9fff]/.test(cnTitle);
    const searchTerms = hasChineseCnTitle
      ? uniq([cnTitle, ...engTitles.slice(0, 1)].filter((s) => s && s.length > 1))
      : uniq([cnTitle, ...engTitles].filter((s) => s && s.length > 1));

    entries.push({
      cnTitle,
      engTitles,
      year,
      searchTerms,
    });
  }

  return entries;
}

function scoreCandidate(entry, item, term) {
  const title = stripHtml(item.title || "");
  const desc = stripHtml(item.description || "");
  const titleNorm = normalize(title);
  const descNorm = normalize(desc);
  const durationMinutes = parseDurationToMinutes(item.duration || "");

  let score = 0;
  const titleNeedles = uniq([entry.cnTitle, ...entry.engTitles, term]).map(normalize).filter(Boolean);
  for (const needle of titleNeedles) {
    if (!needle) continue;
    if (titleNorm.includes(needle)) score += 8;
    if (descNorm.includes(needle)) score += 3;
  }

  if (durationMinutes >= 100) score += 8;
  else if (durationMinutes >= 70) score += 6;
  else if (durationMinutes >= 40) score += 4;
  else if (durationMinutes >= 20) score += 1;

  const rawTitle = title.toLowerCase();
  if (/完整版|正片|全\d+集|合集|纪录片|中字|双字|电影/.test(rawTitle)) score += 3;
  if (title.includes(`《${entry.cnTitle}》`) || title.startsWith(entry.cnTitle) || title.includes(`${entry.cnTitle}（`) || title.includes(`${entry.cnTitle}(`)) {
    score += 6;
  }
  if (/解说|混剪|预告|盘点|速看|reaction|反应|剪辑|片段|电影解说|一口气看完|影视回顾|深度解析|万字精讲|原声|ost|主题曲|片尾|结尾|直播课|有声书|播客|bts/.test(rawTitle)) score -= 12;

  return {
    score,
    durationMinutes,
    title,
    bvid: item.bvid,
    url: item.bvid ? `https://www.bilibili.com/video/${item.bvid}/` : "",
    typename: item.typename || "",
    author: item.author || "",
    rawDuration: item.duration || "",
    term,
  };
}

async function searchTerm(term) {
  const url = `https://api.bilibili.com/x/web-interface/search/type?search_type=video&page=1&page_size=8&keyword=${encodeURIComponent(term)}`;
  const res = await fetch(url, {
    headers: {
      "user-agent": "Mozilla/5.0",
      "accept": "application/json,text/plain,*/*",
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${term}`);
  const json = await res.json();
  return json?.data?.result || [];
}

async function main() {
  const markdown = await fs.readFile(INPUT, "utf8");
  const entries = parseEntries(markdown);
  const results = [];

  for (const entry of entries) {
    const candidates = [];
    for (const term of entry.searchTerms.slice(0, 3)) {
      try {
        const items = await searchTerm(term);
        for (const item of items) {
          candidates.push(scoreCandidate(entry, item, term));
        }
      } catch (err) {
        candidates.push({ score: -999, error: String(err), term });
      }
    }

    const deduped = [];
    const seen = new Set();
    for (const c of candidates) {
      const k = c.bvid || `${c.term}__${c.title}`;
      if (seen.has(k)) continue;
      seen.add(k);
      deduped.push(c);
    }
    deduped.sort((a, b) => b.score - a.score || b.durationMinutes - a.durationMinutes);
    const best = deduped[0] || null;

    let status = "未命中";
    if (best && best.score >= 18 && best.durationMinutes >= 40) status = "高置信命中";
    else if (best && best.score >= 11 && best.durationMinutes >= 20) status = "待复核";

    results.push({
      ...entry,
      status,
      best,
      top3: deduped.slice(0, 3),
    });
  }

  const found = results.filter((r) => r.status === "高置信命中");
  const review = results.filter((r) => r.status === "待复核");
  const missed = results.filter((r) => r.status === "未命中");

  const lines = [];
  lines.push("# B站全量初筛结果");
  lines.push("");
  lines.push(`- 扫描日期：2026-04-11`);
  lines.push(`- 扫描范围：文档中自“先看这一批”起至“资料参考”前的去重片名`);
  lines.push(`- 去重后片名数：${results.length}`);
  lines.push(`- 高置信命中：${found.length}`);
  lines.push(`- 待复核：${review.length}`);
  lines.push(`- 未命中：${missed.length}`);
  lines.push("");
  lines.push("## 高置信命中");
  lines.push("");
  lines.push("| 片名 | 年份 | 搜索词 | 命中标题 | 时长 | 链接 |");
  lines.push("| --- | --- | --- | --- | --- | --- |");
  for (const r of found) {
    lines.push(`| ${r.cnTitle} | ${r.year} | ${r.best.term} | ${r.best.title.replace(/\|/g, "/")} | ${r.best.rawDuration} | [打开](${r.best.url}) |`);
  }
  lines.push("");
  lines.push("## 待复核");
  lines.push("");
  lines.push("| 片名 | 年份 | 搜索词 | 候选标题 | 时长 | 链接 |");
  lines.push("| --- | --- | --- | --- | --- | --- |");
  for (const r of review) {
    lines.push(`| ${r.cnTitle} | ${r.year} | ${r.best.term} | ${r.best.title.replace(/\|/g, "/")} | ${r.best.rawDuration} | [打开](${r.best.url}) |`);
  }
  lines.push("");
  lines.push("## 未命中");
  lines.push("");
  for (const r of missed) {
    lines.push(`- ${r.cnTitle} (${r.year})`);
  }
  lines.push("");

  await fs.writeFile(OUTPUT_JSON, JSON.stringify(results, null, 2), "utf8");
  await fs.writeFile(OUTPUT_MD, lines.join("\n"), "utf8");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
