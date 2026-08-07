import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  compareContent,
  contentToPlainText,
  MAX_ALLOWED_REPEAT_PERCENT
} from './内容去重工具.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const defaultExternalRoot = path.join(repoRoot, '10-外部原文归档');
const defaultCatalogPath = path.join(repoRoot, '07-资料与流程', '04-索引与报告', '内容库索引.jsonl');
const defaultAssetPath = path.join(repoRoot, '07-资料与流程', '03-资产与核验', '文章资产登记表.md');
const defaultReportDirectory = path.join(repoRoot, '07-资料与流程', '04-索引与报告', '内容去重报告');

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith('--')) continue;
    const key = argument.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith('--')) throw new Error(`缺少参数 --${key} 的值`);
    values[key] = value;
    index += 1;
  }
  return values;
}

function relative(absolutePath) {
  return path.relative(repoRoot, absolutePath).split(path.sep).join('/');
}

function relativeFrom(baseDirectory, absolutePath) {
  return path.relative(baseDirectory, absolutePath).split(path.sep).join('/');
}

function dateStamp() {
  return new Date().toISOString().slice(0, 10);
}

function canonicalWechatUrl(value) {
  const parsed = new URL(value);
  if (!/^(?:www\.)?mp\.weixin\.qq\.com$/i.test(parsed.hostname)) return null;
  if (!/^\/s\//.test(parsed.pathname)) return null;
  return `https://mp.weixin.qq.com${parsed.pathname}`;
}

function classify(comparison) {
  if (comparison.exceeds_limit) return '阻止';
  if (comparison.repeat_percent >= 30 || comparison.title_similarity_percent >= 50) return '人工复核';
  return '通过';
}

async function loadCatalog(catalogPath) {
  return (await fs.readFile(catalogPath, 'utf8'))
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function loadManifestArticles(manifest) {
  if (!Array.isArray(manifest.articles) || !manifest.articles.length) throw new Error('原创清单缺少 articles 数组');
  const seen = new Set();
  return manifest.articles.flatMap((article) => {
    const url = canonicalWechatUrl(article?.url || '');
    if (!url || seen.has(url)) return [];
    seen.add(url);
    return [{
      title: String(article.title || '').trim(),
      url,
      published_at: article.published_at || null
    }];
  });
}

function updateAssetRegister(text, records, asOf) {
  const lines = text.split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => line.includes('| 编号 |') && line.includes('正文路径') && line.includes('发布状态'));
  if (headerIndex < 0) throw new Error('文章资产登记表未找到标准文章表头');
  const headerCells = lines[headerIndex].trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
  const repeatColumn = '原创清单最高重复度';
  let repeatIndex = headerCells.indexOf(repeatColumn);
  if (repeatIndex < 0) {
    headerCells.push(repeatColumn);
    repeatIndex = headerCells.length - 1;
  }
  lines[headerIndex] = '| ' + headerCells.join(' | ') + ' |';
  const dividerIndex = headerIndex + 1;
  if (lines[dividerIndex]?.trim().startsWith('|')) {
    const dividerCells = lines[dividerIndex].trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
    while (dividerCells.length < headerCells.length) dividerCells.push('---');
    dividerCells[repeatIndex] = '---:';
    lines[dividerIndex] = '| ' + dividerCells.join(' | ') + ' |';
  }
  for (let index = headerIndex + 2; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim().startsWith('|')) continue;
    const cells = line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
    if (!/^\d{1,2}$/.test(cells[0] || '')) continue;
    const id = cells[0].padStart(2, '0');
    const record = records.find((item) => item.id === id);
    while (cells.length < headerCells.length) cells.push('');
    cells[repeatIndex] = record ? `${record.max_repeat_percent}%` : '—';
    lines[index] = '| ' + cells.join(' | ') + ' |';
  }
  const manifestLink = relativeFrom(asOf.assetDirectory, asOf.manifestPath);
  const reportLink = relativeFrom(asOf.assetDirectory, asOf.reportPath);
  const note = `> 原创清单最高重复度：按 [${manifestLink}](<${manifestLink}>) 对应归档正文计算，取每篇仓库文章与原创清单全部文章的最大值；公式为“正文五字片段 Dice 相似度 × 85% + 标题二字片段 Dice 相似度 × 15%”。具体匹配对象见 [重复度报告](<${reportLink}>)。`;
  const noteIndex = lines.findIndex((line) => line.startsWith('> 原创清单最高重复度：'));
  if (noteIndex >= 0) lines[noteIndex] = note;
  else lines.splice(headerIndex, 0, note);
  const updatedAtIndex = lines.findIndex((line) => line.startsWith('> 更新时间：'));
  if (updatedAtIndex >= 0) lines[updatedAtIndex] = `> 更新时间：${asOf.date}`;
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').replace(/\n?$/, '\n');
}

function toMarkdown(report) {
  const lines = [
    '# 原创清单与仓库文章重复度报告',
    '',
    `- 计算时间：${report.calculated_at}`,
    `- 原创清单：${report.source.manifest}`,
    `- 清单导出时间：${report.source.exported_at || '未提供'}`,
    `- 对比范围：${report.summary.formal_articles} 篇仓库正式文章 × ${report.summary.original_articles} 篇原创文章`,
    `- 最高重复度：${report.summary.max_repeat_percent}%`,
    `- 公式：${report.policy.formula}`,
    '',
    '| 编号 | 仓库文章 | 最高重复度 | 正文相似度 | 标题相似度 | 匹配原创文章 | 判定 |',
    '| ---: | --- | ---: | ---: | ---: | --- | --- |'
  ];
  for (const row of report.rows) {
    lines.push(`| ${row.id} | ${row.title} | ${Number(row.max_repeat_percent).toFixed(2)}% | ${Number(row.body_similarity_percent).toFixed(2)}% | ${Number(row.title_similarity_percent).toFixed(2)}% | ${row.match.id} ${row.match.title} | ${row.result} |`);
  }
  return lines.join('\n') + '\n';
}

const args = parseArgs(process.argv.slice(2));
const catalogPath = path.resolve(args.catalog || defaultCatalogPath);
const assetPath = path.resolve(args.asset || defaultAssetPath);
const manifestPath = path.resolve(args.manifest || (await fs.readdir(defaultExternalRoot)).filter((name) => /^微信原创文章清单-.*\.json$/.test(name)).sort().at(-1) ? path.join(defaultExternalRoot, (await fs.readdir(defaultExternalRoot)).filter((name) => /^微信原创文章清单-.*\.json$/.test(name)).sort().at(-1)) : '');
if (!manifestPath || manifestPath === path.parse(repoRoot).root) throw new Error('未找到微信公众号原创清单 JSON');
const reportDate = args['as-of'] || dateStamp();
if (!/^20\d{2}-\d{2}-\d{2}$/.test(reportDate)) throw new Error('--as-of 必须是 YYYY-MM-DD');
const catalog = await loadCatalog(catalogPath);
const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
const manifestArticles = loadManifestArticles(manifest);
const manifestUrlSet = new Set(manifestArticles.map((article) => article.url));
const externalEntries = catalog.filter((entry) => entry.kind === 'external-archive' && entry.source_url && manifestUrlSet.has(canonicalWechatUrl(entry.source_url)));
const archiveByUrl = new Map(externalEntries.map((entry) => [canonicalWechatUrl(entry.source_url), entry]));
const missingArchives = manifestArticles.filter((article) => !archiveByUrl.has(article.url));
if (missingArchives.length) throw new Error(`原创清单中有 ${missingArchives.length} 篇文章没有对应外部归档，先完成归档再计算。`);
const formalEntries = catalog.filter((entry) => entry.kind === 'formal-article');
const rows = [];
for (const formal of formalEntries) {
  const raw = await fs.readFile(path.join(repoRoot, formal.text_path), 'utf8');
  const candidate = { title: formal.title, text: contentToPlainText(raw, path.extname(formal.text_path)) };
  const matches = [];
  for (const article of manifestArticles) {
    const reference = archiveByUrl.get(article.url);
    const referenceText = await fs.readFile(path.join(repoRoot, reference.text_path), 'utf8');
    const comparison = compareContent(candidate, { title: article.title || reference.title, text: referenceText });
    matches.push({ article, reference, comparison });
  }
  matches.sort((left, right) => right.comparison.repeat_percent - left.comparison.repeat_percent || right.comparison.body_similarity_percent - left.comparison.body_similarity_percent || right.comparison.title_similarity_percent - left.comparison.title_similarity_percent);
  const best = matches[0];
  rows.push({
    id: formal.id,
    title: formal.title,
    path: formal.text_path,
    max_repeat_percent: best.comparison.repeat_percent,
    body_similarity_percent: best.comparison.body_similarity_percent,
    title_similarity_percent: best.comparison.title_similarity_percent,
    result: classify(best.comparison),
    match: { id: best.reference.id, title: best.article.title || best.reference.title, url: best.article.url, published_at: best.article.published_at }
  });
}
rows.sort((left, right) => Number(left.id) - Number(right.id));
const maxRepeat = Math.max(...rows.map((row) => row.max_repeat_percent), 0);
const reportBase = `原创清单对仓库文章重复度-${reportDate}`;
const reportDirectory = path.resolve(args['report-dir'] || defaultReportDirectory);
await fs.mkdir(reportDirectory, { recursive: true });
const report = {
  schema_version: '1.0',
  calculated_at: new Date().toISOString(),
  source: { manifest: relative(manifestPath), exported_at: manifest.exported_at || null, original_articles: manifestArticles.length },
  policy: { formula: '重复度 = 正文五字片段 Dice 相似度 × 85% + 标题二字片段 Dice 相似度 × 15%', max_allowed_repeat_percent: MAX_ALLOWED_REPEAT_PERCENT, value_definition: '每篇仓库正式文章与原创清单全部文章比较后的最高重复度' },
  summary: { formal_articles: rows.length, original_articles: manifestArticles.length, max_repeat_percent: maxRepeat, blocked: rows.filter((row) => row.result === '阻止').length, review: rows.filter((row) => row.result === '人工复核').length, pass: rows.filter((row) => row.result === '通过').length },
  rows
};
const reportJsonPath = path.join(reportDirectory, reportBase + '.json');
const reportMdPath = path.join(reportDirectory, reportBase + '.md');
const assetText = await fs.readFile(assetPath, 'utf8');
const updatedAsset = updateAssetRegister(assetText, rows, { date: reportDate, assetDirectory: path.dirname(assetPath), manifestPath, reportPath: reportMdPath });
await fs.writeFile(assetPath, updatedAsset, 'utf8');
await fs.writeFile(reportJsonPath, JSON.stringify(report, null, 2) + '\n', 'utf8');
await fs.writeFile(reportMdPath, toMarkdown(report), 'utf8');
console.log(JSON.stringify({ asset: relative(assetPath), report_json: relative(reportJsonPath), report_md: relative(reportMdPath), summary: report.summary }, null, 2));
