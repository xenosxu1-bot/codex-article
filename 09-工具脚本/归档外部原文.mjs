import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  buildFingerprint,
  htmlToPlainText
} from './内容去重工具.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const defaultArchiveRoot = path.join(repoRoot, '10-外部原文归档');

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

function usage() {
  return [
    '用法：node 09-工具脚本/归档外部原文.mjs --id EXT-YYYYMMDD-001 --title 标题 --source-url URL --source-html 原始HTML路径 --captured-at YYYY-MM-DD [--rights user-provided]',
    '说明：原始 HTML 按字节复制为 source.html；content.md 与 content.txt 仅由 HTML 自动转换，不进行人工改写。'
  ].join('\n');
}

function extractDivById(html, id) {
  const startPattern = new RegExp(`<div\\b[^>]*\\bid=["']${id}["'][^>]*>`, 'i');
  const startMatch = startPattern.exec(html);
  if (!startMatch) return html;
  const start = startMatch.index + startMatch[0].length;
  const tagPattern = /<\/?div\b[^>]*>/gi;
  tagPattern.lastIndex = start;
  let depth = 1;
  let match;
  while ((match = tagPattern.exec(html))) {
    depth += /^<\/div\b/i.test(match[0]) ? -1 : 1;
    if (depth === 0) return html.slice(start, match.index);
  }
  throw new Error('无法闭合微信公众号正文容器 #js_content');
}

function safeDirectoryName(value) {
  return value.replace(/[<>:"/\\|?*]/g, '-').trim();
}

function relative(absolutePath) {
  return path.relative(repoRoot, absolutePath).split(path.sep).join('/');
}

const args = parseArgs(process.argv.slice(2));
for (const required of ['id', 'title', 'source-url', 'source-html', 'captured-at']) {
  if (!args[required]) {
    console.error(usage());
    throw new Error(`缺少必填参数 --${required}`);
  }
}

const archiveDirectory = path.join(defaultArchiveRoot, safeDirectoryName(`${args.id}-${args.title}`));
try {
  await fs.access(archiveDirectory);
  throw new Error(`归档目录已存在：${relative(archiveDirectory)}`);
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}

const sourceHtmlPath = path.resolve(args['source-html']);
const sourceHtml = await fs.readFile(sourceHtmlPath, 'utf8');
const articleHtml = extractDivById(sourceHtml, 'js_content');
const text = htmlToPlainText(articleHtml);
if (text.length < 200) throw new Error('提取到的原文正文不足 200 个字符，已停止归档。');

const sourceOutput = path.join(archiveDirectory, 'source.html');
const markdownOutput = path.join(archiveDirectory, 'content.md');
const textOutput = path.join(archiveDirectory, 'content.txt');
const metadataOutput = path.join(archiveDirectory, 'metadata.json');
await fs.mkdir(archiveDirectory, { recursive: true });
await fs.copyFile(sourceHtmlPath, sourceOutput);
await fs.writeFile(markdownOutput, `# ${args.title}\n\n${text}\n`, 'utf8');
await fs.writeFile(textOutput, `${text}\n`, 'utf8');
const sourceHash = crypto.createHash('sha256').update(await fs.readFile(sourceOutput)).digest('hex');
const metadata = {
  schema_version: '1.0',
  archive: {
    id: args.id,
    title: args.title,
    kind: 'external-original',
    status: 'dedupe-reference',
    source_html_path: relative(sourceOutput),
    converted_markdown_path: relative(markdownOutput),
    normalized_text_path: relative(textOutput)
  },
  sources: [{
    label: '用户提供的外部原文',
    url: args['source-url'],
    type: 'user-provided'
  }],
  rights: {
    classification: args.rights || 'user-provided',
    repository_policy: '原始快照仅用于内容去重与追溯；公开范围由内容权利人确认。'
  },
  integrity: {
    captured_at: args['captured-at'],
    source_html_sha256: sourceHash,
    converted_text_fingerprint: buildFingerprint(text),
    conversion: '从 source.html 的 #js_content 自动提取正文并转换；未进行人工改写。'
  },
  deduplication: {
    max_allowed_repeat_percent: 50,
    formula: '重复度 = 正文五字片段 Dice 相似度 × 85% + 标题二字片段 Dice 相似度 × 15%；结果必须低于 50%。',
    exact_title_policy: '规范化标题完全一致时直接阻止，需要人工改题或明确豁免。'
  }
};
await fs.writeFile(metadataOutput, `${JSON.stringify(metadata, null, 2)}\n`, 'utf8');
console.log(`已归档外部原文：${relative(archiveDirectory)}（正文 ${Array.from(text).length} 字符）。`);