import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const archiveRoot = path.join(repoRoot, '10-外部原文归档');
const archiveScript = path.join(path.dirname(fileURLToPath(import.meta.url)), '归档外部原文.mjs');

function usage() {
  return [
    '用法：node 09-工具脚本/批量归档微信公众号原创.mjs --manifest 文章清单.json --captured-at YYYY-MM-DD [--rights account-owner-authorized] [--delay-ms 800] [--report 同步记录.json] [--dry-run]',
    '清单格式：{ "articles": [{ "title": "标题", "url": "https://mp.weixin.qq.com/s/...", "published_at": "YYYY-MM-DD" }] }。',
    '说明：已存在相同来源 URL 的归档会跳过；新条目的 source.html 保存抓取到的原始响应字节，正文文件仅自动转换，不做人工改写。'
  ].join('\n');
}

function parseArgs(argv) {
  const values = {};
  const flags = new Set(['dry-run', 'help']);
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith('--')) continue;
    const key = argument.slice(2);
    if (flags.has(key)) { values[key] = true; continue; }
    const value = argv[index + 1];
    if (!value || value.startsWith('--')) throw new Error(`缺少参数 --${key} 的值`);
    values[key] = value;
    index += 1;
  }
  return values;
}

function canonicalWechatUrl(value) {
  const parsed = new URL(value);
  if (!/^(?:www\.)?mp\.weixin\.qq\.com$/i.test(parsed.hostname)) throw new Error(`不是微信公众号文章链接：${value}`);
  if (!/^\/s\//.test(parsed.pathname)) throw new Error(`不是微信公众号文章正文链接：${value}`);
  return `https://mp.weixin.qq.com${parsed.pathname}`;
}

function safeFileStem(index) {
  return String(index).padStart(3, '0');
}

function nextArchiveId(existingIds, capturedAt) {
  const compactDate = capturedAt.replace(/-/g, '');
  let number = 1;
  while (existingIds.has(`EXT-${compactDate}-${String(number).padStart(3, '0')}`)) number += 1;
  const id = `EXT-${compactDate}-${String(number).padStart(3, '0')}`;
  existingIds.add(id);
  return id;
}

async function listExistingArchives() {
  const existingUrls = new Set();
  const existingIds = new Set();
  for (const entry of await fs.readdir(archiveRoot, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const metadataPath = path.join(archiveRoot, entry.name, 'metadata.json');
    try {
      const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf8'));
      if (metadata.archive?.id) existingIds.add(metadata.archive.id);
      for (const source of metadata.sources || []) {
        if (source?.url) existingUrls.add(canonicalWechatUrl(source.url));
      }
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  return { existingUrls, existingIds };
}

function runNode(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, args, { cwd: repoRoot, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', chunk => { stdout += chunk; });
    child.stderr.on('data', chunk => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', code => code === 0 ? resolve({ stdout, stderr }) : reject(new Error(`归档命令失败（退出码 ${code}）：${stderr || stdout}`)));
  });
}

const args = parseArgs(process.argv.slice(2));
if (args.help) { console.log(usage()); process.exit(0); }
for (const required of ['manifest', 'captured-at']) {
  if (!args[required]) throw new Error(`缺少必填参数 --${required}\n${usage()}`);
}
if (!/^20\d{2}-\d{2}-\d{2}$/.test(args['captured-at'])) throw new Error('--captured-at 必须是 YYYY-MM-DD。');
const delayMs = Number(args['delay-ms'] || 800);
if (!Number.isFinite(delayMs) || delayMs < 0) throw new Error('--delay-ms 必须是非负数字。');
const manifestPath = path.resolve(args.manifest);
const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
if (!Array.isArray(manifest.articles) || !manifest.articles.length) throw new Error('清单中没有 articles。');
const { existingUrls, existingIds } = await listExistingArchives();
const normalized = [];
const duplicateManifestUrls = new Set();
for (const article of manifest.articles) {
  if (!article?.title || !article?.url) throw new Error('每条文章必须包含 title 与 url。');
  const url = canonicalWechatUrl(article.url);
  if (duplicateManifestUrls.has(url)) continue;
  duplicateManifestUrls.add(url);
  normalized.push({ title: String(article.title).trim(), url, published_at: article.published_at || null });
}
const temporaryDirectory = path.join(repoRoot, '.tmp', `wechat-original-import-${args['captured-at']}`);
if (!args['dry-run']) await fs.mkdir(temporaryDirectory, { recursive: true });
const report = { schema_version: '1.0', imported_at: args['captured-at'], manifest: path.relative(repoRoot, manifestPath).split(path.sep).join('/'), total_in_manifest: normalized.length, created: [], skipped_existing: [], failed: [] };

for (let index = 0; index < normalized.length; index += 1) {
  const article = normalized[index];
  if (existingUrls.has(article.url)) {
    report.skipped_existing.push(article);
    continue;
  }
  const archiveId = nextArchiveId(existingIds, args['captured-at']);
  if (args['dry-run']) {
    report.created.push({ ...article, archive_id: archiveId, dry_run: true });
    continue;
  }
  try {
    const response = await fetch(article.url, { redirect: 'follow', headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136 Safari/537.36', 'Accept-Language': 'zh-CN,zh;q=0.9' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    const html = bytes.toString('utf8');
    if (!/<div\b[^>]*\bid=["']js_content["']/i.test(html)) throw new Error('响应中未找到微信公众号正文容器 #js_content。');
    const temporarySource = path.join(temporaryDirectory, `${safeFileStem(index + 1)}.html`);
    await fs.writeFile(temporarySource, bytes);
    await runNode([archiveScript, '--id', archiveId, '--title', article.title, '--source-url', article.url, '--source-html', temporarySource, '--captured-at', args['captured-at'], '--rights', args.rights || 'account-owner-authorized']);
    await fs.rm(temporarySource, { force: true });
    existingUrls.add(article.url);
    report.created.push({ ...article, archive_id: archiveId, bytes: bytes.length });
  } catch (error) {
    report.failed.push({ ...article, archive_id: archiveId, error: error.message });
  }
  if (delayMs && index < normalized.length - 1) await new Promise(resolve => setTimeout(resolve, delayMs));
}
if (!args['dry-run']) await fs.rm(temporaryDirectory, { recursive: true, force: true });
if (args.report) {
  const reportPath = path.resolve(args.report);
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2) + '\n', 'utf8');
}
console.log(JSON.stringify({ total_in_manifest: report.total_in_manifest, created: report.created.length, skipped_existing: report.skipped_existing.length, failed: report.failed.length, report: args.report ? path.relative(repoRoot, path.resolve(args.report)).split(path.sep).join('/') : null }, null, 2));
if (report.failed.length) process.exitCode = 2;
