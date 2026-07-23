import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  MAX_ALLOWED_REPEAT_PERCENT,
  compareContent,
  contentToPlainText,
  deriveTitleFromPath,
  extractMarkdownTitle,
  slugify
} from './内容去重工具.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const defaultCatalogPath = path.join(repoRoot, '07-资料与流程', '内容库索引.jsonl');
const defaultReportDirectory = path.join(repoRoot, '07-资料与流程', '内容去重报告');

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

function dateStamp() {
  return new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').slice(0, 19);
}

function toMarkdown(report) {
  const lines = [
    `# 内容重复度检查：${report.candidate.title}`,
    '',
    `- 候选文件：\`${report.candidate.path}\``,
    `- 判定标准：${report.policy.formula}`,
    `- 强制阈值：重复度必须 **低于 ${MAX_ALLOWED_REPEAT_PERCENT}%**；规范化标题或正文完全一致时直接阻止。`,
    `- 检查结果：**${report.result.toUpperCase()}**`,
    ''
  ];
  if (!report.matches.length) {
    lines.push('未找到可比较的内容条目。');
  } else {
    lines.push('| 参考条目 | 类型 | 正文相似度 | 标题相似度 | 重复度 | 结果 |', '| --- | --- | ---: | ---: | ---: | --- |');
    for (const match of report.matches) {
      lines.push(`| ${match.reference.id} ${match.reference.title} | ${match.reference.kind} | ${match.comparison.body_similarity_percent}% | ${match.comparison.title_similarity_percent}% | ${match.comparison.repeat_percent}% | ${match.result} |`);
    }
  }
  return `${lines.join('\n')}\n`;
}

const args = parseArgs(process.argv.slice(2));
if (!args.candidate) {
  console.error('用法：node 09-工具脚本/检查内容重复度.mjs --candidate <文件路径> [--title 标题] [--exclude-id ID] [--catalog 索引路径] [--report-dir 输出目录]');
  process.exitCode = 1;
} else {
  const candidatePath = path.resolve(args.candidate);
  const rawCandidate = await fs.readFile(candidatePath, 'utf8');
  const candidate = {
    path: relative(candidatePath),
    title: args.title || (path.extname(candidatePath).toLowerCase() === '.md' ? extractMarkdownTitle(rawCandidate, deriveTitleFromPath(candidatePath)) : deriveTitleFromPath(candidatePath)),
    text: contentToPlainText(rawCandidate, path.extname(candidatePath))
  };
  if (Array.from(candidate.text).length < 200) throw new Error('候选内容不足 200 个字符，不能给出可信的重复度结论。');
  const catalogPath = path.resolve(args.catalog || defaultCatalogPath);
  const catalog = (await fs.readFile(catalogPath, 'utf8'))
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const matches = [];
  for (const reference of catalog) {
    if (reference.id === args['exclude-id']) continue;
    const referencePath = path.join(repoRoot, reference.text_path);
    const referenceText = await fs.readFile(referencePath, 'utf8');
    const comparison = compareContent(candidate, { title: reference.title, text: referenceText });
    let result = '通过';
    if (comparison.exceeds_limit) result = '阻止';
    else if (comparison.repeat_percent >= 30 || comparison.title_similarity_percent >= 50) result = '人工复核';
    matches.push({ reference: { id: reference.id, kind: reference.kind, title: reference.title, path: reference.text_path }, comparison, result });
  }
  matches.sort((left, right) => right.comparison.repeat_percent - left.comparison.repeat_percent || right.comparison.body_similarity_percent - left.comparison.body_similarity_percent);
  const blocked = matches.filter((match) => match.result === '阻止');
  const report = {
    schema_version: '1.0',
    checked_at: new Date().toISOString(),
    candidate: { path: candidate.path, title: candidate.title, characters: Array.from(candidate.text).length },
    policy: {
      max_allowed_repeat_percent: MAX_ALLOWED_REPEAT_PERCENT,
      formula: '重复度 = 正文五字片段 Dice 相似度 × 85% + 标题二字片段 Dice 相似度 × 15%',
      required: `所有非豁免条目的重复度必须低于 ${MAX_ALLOWED_REPEAT_PERCENT}%`,
      hard_blocks: ['规范化正文完全一致', '规范化标题完全一致', `重复度大于或等于 ${MAX_ALLOWED_REPEAT_PERCENT}%`]
    },
    result: blocked.length ? 'blocked' : matches.some((match) => match.result === '人工复核') ? 'review' : 'pass',
    matches
  };
  const reportDirectory = path.resolve(args['report-dir'] || defaultReportDirectory);
  await fs.mkdir(reportDirectory, { recursive: true });
  const reportName = `${dateStamp()}-${slugify(candidate.title)}`;
  await fs.writeFile(path.join(reportDirectory, `${reportName}.json`), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  await fs.writeFile(path.join(reportDirectory, `${reportName}.md`), toMarkdown(report), 'utf8');
  console.log(`内容重复度检查：${report.result}；最高重复度 ${matches[0]?.comparison.repeat_percent ?? 0}%；报告：${relative(reportDirectory)}/${reportName}.{json,md}`);
  if (blocked.length) process.exitCode = 2;
}