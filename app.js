/* Static reading desk; discovery candidates never become curated papers automatically. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const C = window.DexCatalog;
  const categories = C.categories, tagGroups = C.groups;
  const facets = ['sensing', 'hand', 'task', 'method'];
  const facetNames = {sensing:'Sensing', hand:'Hand / platform', task:'Task', method:'Learning method'};
  const selectedCategories = new Set(), selectedTags = new Set();
  const desktop = window.matchMedia('(min-width: 1151px)');
  let papers = [], shown = [], view = 'cards', panel = 'papers', selectedId = '', detailEnabled = true, chinese = false, timelineMode = 'year';
  let snapshotDate = '', selectedYear = '';
  function state() { return {query:$('search').value.trim(),year:selectedYear,categories:[...selectedCategories],tags:[...selectedTags],codeOnly:$('code-only').checked,start:$('date-start').value,end:$('date-end').value,facets:Object.fromEntries(facets.map(f=>[f,$(f).value]))}; }
  function saveURL() { history.replaceState(null,'',location.pathname + C.writeURL(state(),panel)); }
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeURL = s => { try { const u = new URL(s); return ['https:', 'http:'].includes(u.protocol) ? esc(u.href) : '#'; } catch { return '#'; } };
  const external = (url, label) => `<a href="${safeURL(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`;
  const authors = p => Array.isArray(p.authors) ? p.authors.join(', ') : p.authors || '';
  const categoryButton = (c, count) => `<button class="category-tag" data-category="${esc(c)}" aria-pressed="${selectedCategories.has(c)}">${esc(c)}${count === undefined ? '' : `<span>${count}</span>`}</button>`;
  const tagGroup = t => tagGroups.find(g=>g.tags.includes(t))?.id || 'resource';
  const tags = p => (p.tags || []).map(t => `<button class="tag" data-group="${tagGroup(t)}" data-tag="${esc(t)}" aria-pressed="${selectedTags.has(t)}">${esc(t)}</button>`).join('');
  function links(p) { return Object.entries(p.links || {}).filter(([,u]) => u).map(([k,u]) => external(u, p.link_labels?.[k] || {paper:'Paper ↗',project:'Project ↗',code:'Code ↗'}[k] || k)).join(''); }
  function card(p) {
    return `<article class="paper${selectedId === p.id && $('paper-detail').open ? ' selected' : ''}" data-paper-id="${esc(p.id)}"><div class="paper-top"><time datetime="${esc(p.date || '')}">${esc(p.date || p.year)}</time><button class="paper-category${p.scope === 'adjacent' ? ' adjacent' : ''}" data-category="${esc(p.category)}" aria-pressed="${selectedCategories.has(p.category)}">${esc(p.category)}</button></div><h3><button class="paper-title" data-open-paper="${esc(p.id)}" aria-haspopup="${desktop.matches ? 'false' : 'dialog'}">${esc(p.title)}</button></h3><p class="insight">${esc(p.tldr)}</p><div class="tags">${tags(p)}</div><div class="links">${links(p)}</div></article>`;
  }
  function renderDetail(p) {
    $('detail-content').innerHTML = `<h2 id="detail-title">${esc(p.title)}</h2>${authors(p) ? `<p class="detail-authors">${esc(authors(p))}</p>` : ''}<p class="detail-date">${esc(p.date || p.year)} · ${p.scope === 'adjacent' ? 'Related resource' : 'Dexterous manipulation'}</p><div class="primary-actions">${links(p)}</div><section class="detail-section"><div class="section-heading"><h3>At a glance</h3>${p.tldr_zh ? `<button id="detail-language" class="language-toggle" aria-label="${chinese ? 'Read English summary' : 'Read Chinese summary'}">${chinese ? 'English' : '中文'}</button>` : ''}</div><p>${esc(chinese && p.tldr_zh ? p.tldr_zh : p.tldr)}</p></section><section class="detail-section"><h3>Research context</h3><dl class="detail-facets">${facets.map(f => `<div><dt>${facetNames[f]}</dt><dd>${esc((p[f] || []).join(', ') || 'Not recorded')}</dd></div>`).join('')}</dl></section><section class="detail-section"><h3>Topics</h3>${categoryButton(p.category)}<div class="tags">${tags(p)}</div>${p.scope === 'adjacent' ? '<p class="detail-scope">An adjacent resource: included for context, rather than counted as a core dexterous manipulation policy.</p>' : ''}${p.notes_zh ? `<p class="detail-scope">${esc(p.notes_zh)}</p>` : ''}</section><section class="detail-section provenance"><h3>Source notes</h3><p>${esc(p.summary_basis || 'Curated paper summary')}</p>${p.bib_keys?.length ? '<p>From your imported bibliography.</p>' : ''}<div class="links">${external(p.source_url || p.links.paper,'Original source ↗')}</div></section>`;
  }
  function syncDetail(autoSelect = true) {
    const dialog = $('paper-detail');
    const enabled = panel === 'papers' && view === 'cards' && detailEnabled && shown.length > 0;
    $('desk').classList.toggle('detail-closed', !enabled || !desktop.matches);
    if (!enabled) { if (dialog.open) dialog.close(); return; }
    if (!shown.some(p => p.id === selectedId)) selectedId = autoSelect && desktop.matches ? shown[0].id : '';
    const paper = papers.find(p => p.id === selectedId);
    if (!paper) { if (dialog.open) dialog.close(); return; }
    renderDetail(paper);
    if (desktop.matches && !dialog.open) dialog.show();
  }
  function render() {
    const invalidDates = $('date-start').value && $('date-end').value && $('date-start').value > $('date-end').value;
    $('date-error').hidden = !invalidDates;
    shown = C.filter(papers, state());
    const sort = $('sort').value;
    if (sort === 'newest' || sort === 'oldest') shown.sort((a,b) => String(a.date || a.year).localeCompare(String(b.date || b.year)) * (sort === 'newest' ? -1 : 1));
    if (sort === 'title') shown.sort((a,b) => a.title.localeCompare(b.title));
    $('result-count').textContent = `${shown.length} of ${papers.length} curated papers`;
    // Keep the original tag buttons focused while updating their pressed state.
    if (!$('categories').children.length) $('categories').innerHTML = categories.map(c => categoryButton(c, papers.filter(p=>p.category===c).length)).join('');
    $('categories').querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(selectedCategories.has(b.dataset.category))));
    const active = [...selectedTags].map(t => `<button class="active-tag" data-tag="${esc(t)}">${esc(t)} ×</button>`);
    facets.filter(f => $(f).value).forEach(f => active.push(`<button class="active-tag" data-clear-facet="${f}">${esc($(f).value)} ×</button>`));
    if ($('code-only').checked) active.push('<button class="active-tag" data-clear-code>With code ×</button>');
    if ($('date-start').value || $('date-end').value) active.push(`<button class="active-tag" data-clear-dates>${esc($('date-start').value || 'Any date')} → ${esc($('date-end').value || 'Any date')} ×</button>`);
    if(selectedYear) active.push(`<button class="active-tag" data-clear-year>Year ${esc(selectedYear)} ×</button>`);
    $('active-filters').innerHTML = active.join('');
    const filterCount = facets.filter(f=>$(f).value).length + Number($('code-only').checked) + selectedTags.size + Number(Boolean(selectedYear)) + Number(Boolean($('date-start').value || $('date-end').value));
    $('filter-count').textContent = filterCount ? `(${filterCount})` : '';
    $('cards-view').setAttribute('aria-pressed', String(view === 'cards'));
    $('table-view').setAttribute('aria-pressed', String(view === 'table'));
    $('desk').classList.toggle('table-mode', view === 'table');
    syncDetail();
    if (!shown.length) $('results').innerHTML = '<p class="empty">No papers match this combination.<br>Try another term or reset the filters.</p>';
    else if (view === 'table') $('results').innerHTML = `<div class="table-wrap"><table><thead><tr><th>Paper</th><th>Date</th><th>Research area</th><th>Sensing</th><th>Links</th></tr></thead><tbody>${shown.map(p=>`<tr><td>${external(p.links.paper,p.title)}</td><td>${esc(p.date || p.year)}</td><td>${esc(p.category)}</td><td>${esc((p.sensing||[]).join(', '))}</td><td><div class="links">${links(p)}</div></td></tr>`).join('')}</tbody></table></div>`;
    else $('results').innerHTML = shown.map(card).join('');
    $('results').setAttribute('aria-busy', 'false');
    renderFilterTags(); renderStats(); saveURL();
  }
  function openPaper(id) {
    selectedId = id; detailEnabled = true; syncDetail(false);
    const dialog = $('paper-detail');
    if (!desktop.matches && !dialog.open) dialog.showModal();
    document.querySelectorAll('[data-paper-id]').forEach(el => el.classList.toggle('selected', el.dataset.paperId === id));
  }
  function showPanel(next) {
    panel = next;
    ['papers','stats','watch'].forEach(name=>$(name+'-panel').hidden = next !== name);
    ['papers','stats','watch'].forEach(name => { if (next === name) $(`${name}-nav`).setAttribute('aria-current','page'); else $(`${name}-nav`).removeAttribute('aria-current'); });
    $('desk').classList.toggle('watch-mode', next === 'watch');
    $('desk').classList.toggle('stats-mode', next === 'stats');
    closeFilters(); syncDetail(); if(next === 'stats') renderStats(); saveURL(); $('collection').scrollTop = 0;
  }
  function closeFilters() { $('filter-panel').hidden = true; $('toggle-filters').setAttribute('aria-expanded','false'); }
  async function loadWatch() {
    try {
      const [wr, cr] = await Promise.all([fetch('./watch.json'), fetch('./candidates.json')]);
      if (!wr.ok || !cr.ok) throw new Error('Watch unavailable');
      const w = await wr.json(), queue = await cr.json();
      const rawItems = Array.isArray(queue) ? queue : queue.candidates || queue.items || [];
      const known = new Set(papers.map(p=>p.links?.paper?.match(/arxiv\.org\/abs\/(\d{4}\.\d{4,5})/)?.[1]).filter(Boolean));
      const items = rawItems.filter(p=>!known.has((p.links?.paper || p.id || '').match(/(\d{4}\.\d{4,5})/)?.[1]));
      const checked = w.last_successful_run || w.last_checked_at;
      $('queue-count').textContent = `${items.length} candidates`;
      $('watch-status').textContent = checked ? 'Last successful search' : 'Awaiting first search';
      document.querySelector('.status-dot').classList.toggle('ok', Boolean(checked));
      $('last-search').textContent = checked ? new Date(checked).toLocaleString('en-GB',{timeZone:'Asia/Shanghai',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}) + ' · Beijing' : 'Enable the repository workflow to begin.';
      $('watch-detail').textContent = checked ? `Last search: ${$('last-search').textContent}. ${items.length} candidates await review. Search window: ${w.lookback_days || 7} days.` : 'No completed search is recorded yet.';
      $('candidate-list').innerHTML = items.length ? items.map(p=>`<li><h4>${external(p.links?.paper || p.url || `https://arxiv.org/abs/${p.arxiv_id}`,p.title)}</h4><div class="candidate-meta"><span>Published ${esc((p.published || '').slice(0,10))}</span><span>Updated ${esc((p.updated || '').slice(0,10))}</span></div>${p.summary || p.abstract ? `<p>${esc(p.summary || p.abstract)}</p>` : ''}</li>`).join('') : '<li>No candidates awaiting review.</li>';
    } catch {
      $('watch-status').textContent = 'Status unavailable'; $('last-search').textContent = 'The latest search status could not be loaded.';
      $('watch-detail').textContent = 'Watch data could not be loaded. Try reloading this page.'; $('candidate-list').innerHTML='<li>The candidate queue is unavailable.</li>';
    }
  }
  function renderFilterTags() {
    if (!$('filter-tags').children.length) $('filter-tags').innerHTML = tagGroups.map(g=>`<section class="tag-group" data-group="${g.id}"><h4>${g.label}</h4><p>${g.description}</p><div class="tag-grid">${g.tags.map(t=>`<button class="filter-tag" data-tag="${esc(t)}" aria-pressed="false"><span>${esc(t)}</span><span class="tag-count"></span></button>`).join('')}</div></section>`).join('');
    $('filter-tags').querySelectorAll('[data-tag]').forEach(button=>{
      const t=button.dataset.tag, selected=selectedTags.has(t);
      const count=C.filter(papers,{...state(),tags:[...[...selectedTags].filter(v=>v!==t),t]}).length;
      button.setAttribute('aria-pressed',String(selected)); button.querySelector('.tag-count').textContent=count;
      button.disabled=!count && !selected;
    });
  }
  function bars(rows, kind, total) {
    return rows.filter(row=>row.count).sort((a,b)=>b.count-a.count).map(row=>`<button class="distribution-row" data-explore="${kind}" data-value="${esc(row.label)}" aria-label="Explore ${esc(row.label)}: ${row.count} papers"><span class="distribution-label">${esc(row.label)}</span><span class="distribution-track"><span style="width:${total?row.count/total*100:0}%"></span></span><strong>${row.count}</strong></button>`).join('') || '<p class="chart-empty">No matching records.</p>';
  }
  function renderStats() {
    const d=C.stats(shown), f=state();
    const filtered=Boolean(f.query || f.categories.length || f.tags.length || f.codeOnly || f.start || f.end || f.year || Object.values(f.facets).some(Boolean));
    $('stats-scope').textContent=!filtered ? `${d.total} curated papers · full collection` : `${d.total} of ${papers.length} papers · current search and filters`;
    $('stats-reset').hidden=!filtered;
    $('stats-metrics').innerHTML=[['Curated papers',d.total,'Core works and adjacent resources'],['Tactile dexterity',d.tactile,'Core works using tactile sensing'],['With code',d.withCode,'Linked implementation or hardware'],['Latest release',d.latest || '—','First public release in this selection']].map(([label,value,note])=>`<div><dt>${label}</dt><dd${label==='Latest release'?' class="date-metric"':''}>${value}</dd><dd class="metric-note">${note}</dd></div>`).join('');
    const rows=timelineMode==='year'?d.yearly:d.monthly, max=Math.max(1,...rows.map(r=>r.count));
    $('release-chart').innerHTML=rows.length?rows.map(row=>`<button class="year-column" data-explore="${timelineMode}" data-value="${row.label}" aria-label="Explore ${row.label}: ${row.count} papers" ${row.count?'':'disabled'}><span class="bar-stage"><span class="year-bar" style="height:${row.count/max*100}%"><span>${row.count || ''}</span></span></span><span class="year-label">${timelineMode==='year'?row.label:new Date(row.label+'-01T00:00:00Z').toLocaleDateString('en-US',{month:'short',timeZone:'UTC'})}</span></button>`).join(''):'<p class="chart-empty">No publication dates in this selection.</p>';
    $('timeline-description').textContent=timelineMode==='year'?'First public release year. Select a bar to read the papers.':`Monthly releases in ${d.latestYear || 'the latest year'}.`;
    $('date-coverage').textContent=timelineMode==='year'?`${d.total-d.unknownYears} papers have a recorded year. ${d.unknownYears ? d.unknownYears+' unknown years excluded.' : 'Revision dates are not counted as new releases.'}`:`${d.unknownDates ? d.unknownDates+' records without an exact date are excluded.' : 'All records have exact publication dates.'}`;
    $('annual-chart').setAttribute('aria-pressed',String(timelineMode==='year')); $('monthly-chart').setAttribute('aria-pressed',String(timelineMode==='month'));
    $('category-chart').innerHTML=bars(d.categories,'category',d.total);
    ['policy','transfer','capability'].forEach(id=>$(id+'-chart').innerHTML=bars(d.groups.find(g=>g.id===id).counts,'tag',d.total));
  }
  function restoreURL() {
    const saved=C.readURL(location.search,location.hash), params=new URLSearchParams(location.search);
    selectedYear=saved.year; selectedCategories.clear();saved.categories.forEach(c=>selectedCategories.add(c)); selectedTags.clear();saved.tags.forEach(t=>selectedTags.add(t));
    $('search').value=saved.query;$('date-start').value=saved.start;$('date-end').value=saved.end;$('code-only').checked=saved.codeOnly;
    facets.forEach(f=>$(f).value=params.get(f)||''); panel=saved.panel;render();showPanel(saved.panel);
  }
  window.addEventListener('popstate',restoreURL);
  window.addEventListener('hashchange',()=>{const next=location.hash==='#stats'?'stats':location.hash==='#watch'?'watch':'papers';showPanel(next);});
  document.addEventListener('click', e => {
    const c = e.target.closest('[data-category]'); if (c) { const value = c.dataset.category; selectedCategories.has(value) ? selectedCategories.delete(value) : selectedCategories.add(value); render(); }
    const t = e.target.closest('[data-tag]'); if (t) { const value = t.dataset.tag; selectedTags.has(value) ? selectedTags.delete(value) : selectedTags.add(value); render(); }
    const f = e.target.closest('[data-clear-facet]'); if (f) { $(f.dataset.clearFacet).value = ''; render(); }
    if (e.target.closest('[data-clear-dates]')) { $('date-start').value=''; $('date-end').value=''; render(); }
    if(e.target.closest('[data-clear-year]')) {selectedYear='';render();}
    const explore = e.target.closest('[data-explore]');
    if (explore) {
      if(explore.dataset.explore === 'category') { selectedCategories.clear(); selectedCategories.add(explore.dataset.value); }
      if(explore.dataset.explore === 'tag') selectedTags.add(explore.dataset.value);
      if(explore.dataset.explore === 'year') selectedYear=explore.dataset.value;
      if(explore.dataset.explore === 'month') { $('date-start').value=explore.dataset.value+'-01'; const [y,m]=explore.dataset.value.split('-').map(Number); $('date-end').value=new Date(Date.UTC(y,m,0)).toISOString().slice(0,10); }
      showPanel('papers'); render();
    }
    if (e.target.closest('[data-clear-code]')) { $('code-only').checked = false; render(); }
    const p = e.target.closest('[data-open-paper]'); if (p) openPaper(p.dataset.openPaper);
    if (e.target.id === 'detail-language') { chinese = !chinese; renderDetail(papers.find(p=>p.id === selectedId)); $('detail-language')?.focus(); }
    if (!$('filter-panel').hidden && !e.target.closest('#filter-panel, #toggle-filters')) closeFilters();
  });
  $('toggle-filters').onclick = () => { const open = $('filter-panel').hidden; $('filter-panel').hidden = !open; $('toggle-filters').setAttribute('aria-expanded', String(open)); if (open) $('close-filters').focus(); };
  $('close-filters').onclick = () => { closeFilters(); $('toggle-filters').focus(); };
  document.addEventListener('keydown', e=>{ if (e.key === 'Escape' && !$('filter-panel').hidden) { closeFilters(); $('toggle-filters').focus(); } });
  function resetFilters() { selectedYear='';selectedCategories.clear(); selectedTags.clear(); $('search').value=''; $('code-only').checked=false; $('date-start').value=''; $('date-end').value=''; facets.forEach(f=>$(f).value=''); render(); }
  $('reset').onclick = $('reset-filter-panel').onclick = $('stats-reset').onclick = resetFilters;
  $('clear-dates').onclick = () => { $('date-start').value=''; $('date-end').value=''; render(); };
  ['search','sort','code-only','date-start','date-end',...facets].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));
  $('cards-view').onclick = () => { view='cards'; render(); };
  $('table-view').onclick = () => { view='table'; render(); };
  $('papers-nav').onclick = () => showPanel('papers');
  $('stats-nav').onclick = () => showPanel('stats');
  $('annual-chart').onclick = () => {timelineMode='year';renderStats();};
  $('monthly-chart').onclick = () => {timelineMode='month';renderStats();};
  $('watch-nav').onclick = $('review-candidates').onclick = () => showPanel('watch');
  $('close-detail').onclick = () => { detailEnabled=false; $('paper-detail').close(); $('desk').classList.add('detail-closed'); document.querySelectorAll('.paper.selected').forEach(el=>el.classList.remove('selected')); };
  $('paper-detail').addEventListener('cancel', () => { detailEnabled=false; });
  desktop.addEventListener('change', () => { $('paper-detail').close(); syncDetail(); });
  $('theme').onclick = () => { const dark=document.documentElement.dataset.theme !== 'dark'; document.documentElement.dataset.theme=dark?'dark':'light'; $('theme').setAttribute('aria-label',`Switch to ${dark?'light':'dark'} mode`); $('theme').title=`Switch to ${dark?'light':'dark'} mode`; };
  fetch('./papers.json').then(r=>{ if(!r.ok) throw new Error('Catalog unavailable'); return r.json(); }).then(data=>{
    papers=data.papers; if(!Array.isArray(papers)) throw new Error('Invalid catalog');
    snapshotDate=data.updated; $('stats-snapshot').textContent=data.updated;
    $('updated').textContent=`Updated ${data.updated}`;
    facets.forEach(f=>{const values=[...new Set(papers.flatMap(p=>p[f] || []))].sort(); $(f).innerHTML += values.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');}); restoreURL(); loadWatch();
  }).catch(()=>{ $('result-count').textContent='Catalog unavailable'; $('results').innerHTML='<p class="empty">The catalog could not be loaded. Please reload the page.</p>'; $('results').setAttribute('aria-busy','false'); });
})();
