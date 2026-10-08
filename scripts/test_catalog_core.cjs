'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const C = require('../catalog-core.js');

// Deliberately mix exact release dates, year-only records, and malformed dates.
// updated/added dates must never manufacture new releases in the charts.
const papers = [
  {
    id: 'visual', title: 'Visual Hand Policy', authors: ['Alice Chen'],
    tldr: 'Controls a hand with images.', tldr_zh: '根据图像控制灵巧手。',
    category: 'Dexterous Manipulation', date: '2024-02-28', year: 2024,
    updated: '2026-10-08', added_date: '2026-10-08',
    tags: ['Reinforcement learning', 'Vision'], sensing: ['Vision'],
    hand: ['Allegro'], task: ['In-hand reorientation'],
    method: ['Reinforcement learning'], links: {code: 'https://example.org/visual'},
  },
  {
    id: 'touch', title: 'Touch Hand Policy', authors: ['Bo Li'],
    category: 'Tactile Dexterous Manipulation', date: '2024-02-29', year: 2024,
    updated: '2026-10-08', tags: ['Reinforcement learning', 'Tactile feedback'],
    sensing: ['Tactile'], hand: ['Allegro'], task: ['In-hand reorientation'],
    method: ['Reinforcement learning'], links: {},
  },
  {
    id: 'sensor', title: 'Touch Sensor', category: 'Tactile Sensing & Representation',
    date: '2024-03-01', year: 2024, tags: ['Hardware / sensor'], links: {},
  },
  {
    id: 'general', title: 'General Policy Learning',
    category: 'Policy Optimization', date: '2023-12-31', year: 2023,
    tags: ['Reinforcement learning', 'Dataset / benchmark'],
    links: {code: 'https://example.org/general'},
  },
  {
    id: 'year-only', title: 'Early Imitation',
    category: 'Dexterous Manipulation', year: 2022,
    updated: '2026-10-08', added_date: '2026-10-08',
    tags: ['Imitation learning', 'Vision'], links: {},
  },
  {
    id: 'bad-date', title: 'Invalid Date Record',
    category: 'Dexterous Manipulation', date: '2024-02-30', year: 2024,
    tags: ['Vision'], links: {},
  },
  {
    id: 'unknown', title: 'Undated Record',
    category: 'Policy Optimization', date: 'unknown', tags: [], links: {},
  },
];
const ids = rows => rows.map(p => p.id);
const count = (rows, label) => rows.find(row => row.label === label)?.count;

test('exact dates accept leap days and reject invalid, partial, or timestamp values', () => {
  assert.equal(C.exactDate('2024-02-29'), Date.UTC(2024, 1, 29));
  for (const value of [undefined, null, '', '2023-02-29', '2024-02-30',
    '2024-13-01', '2024-00-01', '2024-01-00', '2024-2-29', '2024',
    '2024-02', '2024-02-29T00:00:00Z']) {
    assert.equal(C.exactDate(value), null, String(value));
  }
});

test('selected research areas use OR while selected topic tags use AND', () => {
  assert.deepEqual(ids(C.filter(papers, {
    categories: ['Dexterous Manipulation', 'Tactile Dexterous Manipulation'],
    tags: ['Reinforcement learning'],
  })), ['visual', 'touch']);
  assert.deepEqual(ids(C.filter(papers, {
    categories: ['Dexterous Manipulation', 'Tactile Dexterous Manipulation'],
    tags: ['Reinforcement learning', 'Vision'],
  })), ['visual']);
  assert.deepEqual(C.filter(papers, {
    tags: ['Vision', 'Tactile feedback'],
  }), []);
});

test('search covers names, Chinese summaries, and metadata without case sensitivity', () => {
  assert.deepEqual(ids(C.filter(papers, {query: ' ALICE CHEN '})), ['visual']);
  assert.deepEqual(ids(C.filter(papers, {query: '根据图像'})), ['visual']);
  assert.deepEqual(ids(C.filter(papers, {query: 'allegro'})), ['visual', 'touch']);
});

test('code and facet filters combine with topics instead of replacing them', () => {
  assert.deepEqual(ids(C.filter(papers, {
    tags: ['Reinforcement learning'], codeOnly: true,
    facets: {hand: 'Allegro', sensing: 'Vision', task: '', method: ''},
  })), ['visual']);
  assert.deepEqual(C.filter(papers, {facets: {hand: 'Unknown hand'}}), []);
  assert.equal(C.filter(papers, {facets: {hand: '', sensing: ''}}).length, papers.length);
});

test('date boundaries are inclusive and exclude absent or impossible release dates', () => {
  assert.deepEqual(ids(C.filter(papers, {
    start: '2024-02-28', end: '2024-02-29',
  })), ['visual', 'touch']);
  assert.deepEqual(ids(C.filter(papers, {start: '2024-02-29'})), ['touch', 'sensor']);
  assert.deepEqual(ids(C.filter(papers, {end: '2024-02-28'})), ['visual', 'general']);
  assert.deepEqual(C.filter(papers, {start: '2024-03-02', end: '2024-03-01'}), []);
  assert.equal(C.filter(papers).length, papers.length, 'no date constraint keeps undated works');
});

test('year drilldown includes year-only works and composes with exact-date constraints', () => {
  assert.deepEqual(ids(C.filter(papers, {year: '2022'})), ['year-only']);
  assert.deepEqual(ids(C.filter(papers, {year: '2024'})),
    ['visual', 'touch', 'sensor', 'bad-date']);
  assert.deepEqual(ids(C.filter(papers, {year: '2024', end: '2024-02-29'})),
    ['visual', 'touch']);
  assert.deepEqual(C.filter(papers, {year: '2022', start: '2022-01-01'}), []);
});

test('filtering does not mutate the input records or their order', () => {
  const before = JSON.stringify(papers);
  C.filter(papers, {tags: ['Vision'], start: '2020-01-01'});
  C.stats(papers);
  assert.equal(JSON.stringify(papers), before);
});

test('multi-label topic counts retain the paper denominator and count a paper once per tag', () => {
  const selected = [
    {category: 'Dexterous Manipulation', tags: ['Reinforcement learning', 'Imitation learning', 'Imitation learning']},
    {category: 'Dexterous Manipulation', tags: ['Imitation learning']},
  ];
  const d = C.stats(selected);
  const policy = d.groups.find(g => g.id === 'policy').counts;
  assert.equal(d.total, 2);
  assert.equal(count(policy, 'Reinforcement learning'), 1);
  assert.equal(count(policy, 'Imitation learning'), 2);
  assert.equal(policy.reduce((sum, row) => sum + row.count, 0), 3,
    'topic counts can exceed the number of papers because labels overlap');
  assert.equal(count(policy, 'Imitation learning') / d.total, 1,
    'the UI percentage uses papers, not the sum of topic occurrences');
  assert.equal(d.categories.reduce((sum, row) => sum + row.count, 0), d.total);
});

test('annual releases use recorded publication years, never ingestion or update dates', () => {
  const d = C.stats(papers);
  assert.deepEqual(d.yearly, [
    {label: '2022', count: 1}, {label: '2023', count: 1}, {label: '2024', count: 4},
  ]);
  assert.equal(d.unknownYears, 1);
  assert.equal(d.latestYear, 2024);
  assert.equal(d.yearly.some(row => row.label === '2026'), false);
});

test('monthly releases use exact first-release dates and omit undated or invalid records', () => {
  const d = C.stats(papers);
  assert.equal(d.monthly.length, 12);
  assert.equal(count(d.monthly, '2024-02'), 2);
  assert.equal(count(d.monthly, '2024-03'), 1);
  assert.equal(count(d.monthly, '2024-10'), 0);
  assert.equal(d.monthly.reduce((sum, row) => sum + row.count, 0), 3);
  assert.equal(d.unknownDates, 3);
  assert.equal(d.latest, '2024-03-01');
  assert.equal(d.withCode, 2);
  assert.equal(d.tactile, 1);
});

test('empty and fully undated selections do not invent timeline dates', () => {
  for (const selection of [[], [{title: 'Unknown', tags: [], updated: '2026-10-08'}]]) {
    const d = C.stats(selection);
    assert.equal(d.latest, null);
    assert.equal(d.latestYear, null);
    assert.deepEqual(d.yearly, []);
    assert.deepEqual(d.monthly, []);
    assert.equal(d.recent, 0);
    assert.equal(d.unknownDates, selection.length);
    assert.equal(d.unknownYears, selection.length);
  }
});

test('recent release count uses a 30-day window ending at the latest release', () => {
  const d = C.stats([
    {date: '2024-03-01', year: 2024},
    {date: '2024-02-01', year: 2024},
    {date: '2024-01-31', year: 2024},
    {date: 'bad', year: 2024, updated: '2024-03-01'},
  ]);
  assert.equal(d.recent, 2, 'the exact 30-day-old lower boundary is excluded');
});

test('URL roundtrip preserves combined filters, unicode, facets, year, and selected panel', () => {
  const original = {
    categories: ['Dexterous Manipulation', 'Tactile Dexterous Manipulation'],
    tags: ['Tactile feedback', 'Diffusion / flow policy'],
    query: '手 & touch + force', start: '2024-02-29', end: '2024-12-31',
    year: '2024', codeOnly: true,
    facets: {sensing: 'Vision + tactile', hand: 'Sharpa Wave', task: 'In-hand rotation', method: 'Diffusion / flow policy'},
  };
  const url = new URL(C.writeURL(original, 'stats'), 'https://example.org/catalog/index.html');
  const restored = C.readURL(url.search, url.hash);
  for (const key of Object.keys(original)) assert.deepEqual(restored[key], original[key], key);
  assert.equal(restored.panel, 'stats');
  assert.equal(C.writeURL(restored, restored.panel), url.search + url.hash);
});

test('URL import ignores unknown topic/area values and malformed date or year filters', () => {
  const saved = C.readURL('?area=Unlisted&tag=Unknown&from=2024-02-30&to=oops&year=oops&code=true', '#other');
  assert.deepEqual(saved.categories, []);
  assert.deepEqual(saved.tags, []);
  assert.equal(saved.start, '');
  assert.equal(saved.end, '');
  assert.equal(saved.year, '');
  assert.equal(saved.codeOnly, false);
  assert.equal(saved.panel, 'papers');
  assert.equal(C.readURL('', '#watch').panel, 'watch');
  assert.equal(C.writeURL({}, 'papers'), '');
});
