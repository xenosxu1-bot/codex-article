import crypto from 'node:crypto';
import path from 'node:path';

export const MAX_ALLOWED_REPEAT_PERCENT = 50;

export function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

export function decodeHtmlEntities(value) {
  return value
    .replace(/&#(x[0-9a-f]+|\d+);/gi, (_, code) => String.fromCodePoint(code[0].toLowerCase() === 'x' ? parseInt(code.slice(1), 16) : parseInt(code, 10)))
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&apos;/gi, "'");
}

export function htmlToPlainText(html) {
  return decodeHtmlEntities(
    html
      .replace(/<(script|style|noscript)[\s\S]*?<\/\1>/gi, '')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/(p|div|section|li|h[1-6]|blockquote|figcaption|tr)>/gi, '\n')
      .replace(/<[^>]+>/g, '')
  )
    .replace(/\r/g, '')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function markdownToPlainText(markdown) {
  return markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/^#\s+/gm, '')
    .replace(/^>\s?/gm, '')
    .replace(/[`*_~|]/g, ' ')
    .replace(/\r/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function contentToPlainText(content, extension = '') {
  const ext = extension.toLowerCase();
  if (ext === '.html' || ext === '.htm') return htmlToPlainText(content);
  if (ext === '.md' || ext === '.markdown') return markdownToPlainText(content);
  return content.replace(/\r/g, '').trim();
}

export function normalizeText(text) {
  return text
    .normalize('NFKC')
    .toLocaleLowerCase('zh-CN')
    .replace(/[^0-9A-Za-z一-龥]/g, '');
}

export function toShingleSet(text, size) {
  const chars = Array.from(normalizeText(text));
  if (!chars.length) return new Set();
  if (chars.length <= size) return new Set([chars.join('')]);
  const shingles = new Set();
  for (let index = 0; index <= chars.length - size; index += 1) {
    shingles.add(chars.slice(index, index + size).join(''));
  }
  return shingles;
}

export function diceSimilarityPercent(leftSet, rightSet) {
  if (!leftSet.size || !rightSet.size) return 0;
  let shared = 0;
  for (const item of leftSet) if (rightSet.has(item)) shared += 1;
  return Number(((2 * shared / (leftSet.size + rightSet.size)) * 100).toFixed(2));
}

export function buildFingerprint(text) {
  const normalized = normalizeText(text);
  return {
    normalized_chars: Array.from(normalized).length,
    normalized_sha256: sha256(normalized),
    five_char_shingle_count: toShingleSet(normalized, 5).size
  };
}

export function extractMarkdownTitle(markdown, fallback = '') {
  const match = markdown.match(/^#\s+(.+)$/m);
  return (match?.[1] || fallback).trim();
}

export function deriveTitleFromPath(filePath) {
  return path.basename(filePath, path.extname(filePath)).replace(/^\d{2}-/, '').trim();
}

export function compareContent(candidate, reference) {
  const body = diceSimilarityPercent(toShingleSet(candidate.text, 5), toShingleSet(reference.text, 5));
  const title = diceSimilarityPercent(toShingleSet(candidate.title, 2), toShingleSet(reference.title, 2));
  const repeat = Number((body * 0.85 + title * 0.15).toFixed(2));
  const sameTitle = normalizeText(candidate.title) === normalizeText(reference.title);
  const sameHash = sha256(normalizeText(candidate.text)) === sha256(normalizeText(reference.text));
  return {
    body_similarity_percent: body,
    title_similarity_percent: title,
    repeat_percent: repeat,
    same_normalized_title: sameTitle,
    same_normalized_text: sameHash,
    exceeds_limit: sameHash || sameTitle || repeat >= MAX_ALLOWED_REPEAT_PERCENT
  };
}

export function slugify(value) {
  return value
    .normalize('NFKC')
    .replace(/[^0-9A-Za-z一-龥]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48) || 'content';
}