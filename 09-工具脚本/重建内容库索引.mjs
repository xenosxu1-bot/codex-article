import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  buildFingerprint,
  contentToPlainText,
  deriveTitleFromPath,
  extractMarkdownTitle
} from './内容去重工具.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const formalDirectories = ['01-工具教程', '02-AI知识', '03-好文方法', '04-安全治理', '05-案例实战', '06-热点追踪'];
const externalRoot = path.join(repoRoot, '10-外部原文归档');
const outputPath = path.join(repoRoot, '07-资料与流程', '内容库索引.jsonl');

function relative(absolutePath) {
  return path.relative(repoRoot, absolutePath).split(path.sep).join('/');
}

async function listFormalEntries() {
  const entries = [];
  for (const directory of formalDirectories) {
    const directoryPath = path.join(repoRoot, directory);
    let names = [];
    try {
      names = await fs.readdir(directoryPath);
    } catch {
      continue;
    }
    for (const name of names.sort((left, right) => left.localeCompare(right, 'zh-CN'))) {
      if (!/^\d{2}-.+\.md$/u.test(name)) continue;
      const absolutePath = path.join(directoryPath, name);
      const markdown = await fs.readFile(absolutePath, 'utf8');
      const text = contentToPlainText(markdown, '.md');
      const id = name.slice(0, 2);
      entries.push({
        schema_version: '1.0',
        id,
        kind: 'formal-article',
        title: extractMarkdownTitle(markdown, deriveTitleFromPath(name)),
        canonical_path: relative(absolutePath),
        text_path: relative(absolutePath),
        source_url: null,
        status: 'formal-article',
        fingerprint: buildFingerprint(text)
      });
    }
  }
  return entries;
}

async function listExternalEntries() {
  const entries = [];
  let names = [];
  try {
    names = await fs.readdir(externalRoot, { withFileTypes: true });
  } catch {
    return entries;
  }
  for (const entry of names.filter((item) => item.isDirectory()).sort((left, right) => left.name.localeCompare(right.name, 'zh-CN'))) {
    const metadataPath = path.join(externalRoot, entry.name, 'metadata.json');
    try {
      const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf8'));
      const textPath = path.join(repoRoot, metadata.archive.normalized_text_path);
      const text = await fs.readFile(textPath, 'utf8');
      entries.push({
        schema_version: '1.0',
        id: metadata.archive.id,
        kind: 'external-archive',
        title: metadata.archive.title,
        canonical_path: metadata.archive.source_html_path,
        text_path: metadata.archive.normalized_text_path,
        source_url: metadata.sources?.[0]?.url ?? null,
        status: metadata.archive.status,
        rights: metadata.rights?.classification ?? 'unspecified',
        fingerprint: buildFingerprint(text)
      });
    } catch (error) {
      throw new Error(`无法读取外部归档 ${entry.name}：${error.message}`);
    }
  }
  return entries;
}

const formalEntries = await listFormalEntries();
const externalEntries = await listExternalEntries();
const entries = [...formalEntries, ...externalEntries].sort((left, right) => left.id.localeCompare(right.id, 'zh-CN'));
await fs.writeFile(outputPath, `${entries.map((entry) => JSON.stringify(entry)).join('\n')}\n`, 'utf8');
console.log(`内容库索引已更新：正式文章 ${formalEntries.length} 篇，外部原文 ${externalEntries.length} 篇，共 ${entries.length} 条。`);