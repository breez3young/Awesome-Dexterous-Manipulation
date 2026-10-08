#!/usr/bin/env node
'use strict';

// Refresh catalog-derived README sections without touching editorial content.
const fs = require('node:fs');
const path = require('node:path');
const C = require('../catalog-core.js');
const root = path.resolve(__dirname, '..');
const file = path.join(root, 'README.md');
const {papers} = JSON.parse(fs.readFileSync(path.join(root, 'papers.json'), 'utf8'));
const website = 'https://breez3young.github.io/Awesome-Dexterous-Manipulation/';
const begin = '<!-- BEGIN GENERATED CATALOG: update with node scripts/build_readme.cjs -->';
const end = '<!-- END GENERATED CATALOG -->';
const readme = fs.readFileSync(file, 'utf8');
if (readme.split(begin).length !== 2 || readme.split(end).length !== 2 || readme.indexOf(begin) > readme.indexOf(end)) {
  throw new Error('README must contain exactly one ordered catalog marker pair.');
}
const esc = value => String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/\|/g,'&#124;').replace(/[\r\n]+/g,' ');
const link = (url, label) => {
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password) throw new Error('Invalid README link');
  return `<a href="${esc(url)}">${esc(label)}</a>`;
};
const resources = p => Object.entries({paper:'Paper',project:'Project',code:'Code'}).filter(([k])=>p.links?.[k]).map(([k,label])=>link(p.links[k],label)).join(' · ');
const routes = [
  ['dactyl-2018','Learning in-hand control'],
  ['dexpilot-2019','Human-to-robot teleoperation'],
  ['digit-2020','Fingertip tactile hardware'],
  ['tacto-2020','Tactile simulation'],
  ['touch-dexterity-2023','Manipulation through touch'],
  ['t-rex','Tactile-reactive policies'],
  ['morphometric-imitation','Contact-aware motion transfer'],
];
if (!Array.isArray(papers) || papers.some(p=>!C.categories.includes(p.category))) throw new Error('Invalid catalog area');
const stats = C.stats(papers);
const lines = [
  '## At a glance','',
  `<p align="center"><b>${stats.total} papers</b> · <b>${stats.tactile} tactile dexterity papers</b> · <b>${stats.withCode} code links</b> · ${C.categories.length} research areas · ${link(website,'browse the collection')}</p>`,'',
  '| Research area | Papers |','|:--|--:|',
  ...stats.categories.map(row=>`| ${link(website+'?area='+encodeURIComponent(row.label),row.label)} | ${row.count} |`),'',
  'Counts describe this curated collection. Code links may cover data tools, simulation, or hardware rather than a complete policy implementation. Explore release trends and tag distributions in [Stats]('+website+'#stats).','',
  '## Start here','',
  'Seven reading routes through the collection, spanning robot control, touch, and human-to-robot transfer.','',
  '| Reading route | Paper | Year | Resources |','|:--|:--|:--:|:--|',
  ...routes.map(([id,theme])=>{
    const p=papers.find(p=>p.id===id);
    if(!p)throw new Error('Missing reading-route paper: '+id);
    return `| ${theme} | <b>${esc(p.title)}</b> | ${p.year} | ${resources(p)} |`;
  }),'',
  '## Recent papers','',
  'The most recent first releases in the curated catalog. Dates below are publication dates, not dates added to this repository.','',
  '| First released | Paper | Research area | Resources |','|:--|:--|:--|:--|',
  ...papers.filter(p=>C.exactDate(p.date)!==null).sort((a,b)=>b.date.localeCompare(a.date)||a.id.localeCompare(b.id)).slice(0,8).map(p=>`| ${p.date} | <b>${esc(p.title)}</b> | ${esc(p.category)} | ${resources(p)} |`),'',
  '[View the full catalog]('+website+') for summaries, evaluation context, and combinations of learning, sensing, and task tags.','',
];
const start = readme.indexOf(begin) + begin.length;
const rendered = readme.slice(0,start) + '\n\n' + lines.join('\n') + readme.slice(readme.indexOf(end));
if (process.argv.includes('--check')) {
  if (rendered !== readme) { console.error('README catalog sections are stale. Run node scripts/build_readme.cjs.'); process.exitCode=1; }
  else console.log('README catalog sections match papers.json.');
} else {
  if(rendered!==readme)fs.writeFileSync(file,rendered);
  console.log(`README refreshed: ${stats.total} papers across ${C.categories.length} research areas.`);
}
