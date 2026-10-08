/* Shared, deterministic catalog operations used by the UI and its checks. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.DexCatalog = api;
})(typeof window === 'undefined' ? this : window, function () {
  'use strict';
  const categories = ['Dexterous Manipulation','Tactile Dexterous Manipulation','Tactile Sensing & Representation','Hand–Object Interaction','Grasp Synthesis','Policy Optimization'];
  const legacyAreas = {
    'Tactile Foundations':['Tactile Sensing & Representation'],
    'Manipulation Foundations':['Hand–Object Interaction', 'Grasp Synthesis', 'Policy Optimization'],
    'Related Methods & Datasets':['Hand–Object Interaction', 'Grasp Synthesis', 'Policy Optimization']
  };
  const groups = [
    {id:'policy',label:'Policy & learning',description:'How the controller is learned or optimized.',tags:['Reinforcement learning','Imitation learning','Vision-language-action','Foundation policy','Diffusion / flow policy','Model-based planning']},
    {id:'transfer',label:'Data & transfer',description:'Where skills come from and how they move between embodiments.',tags:['Human motion transfer','Retargeting','Teleoperation','Sim-to-real','Cross-embodiment','Human-in-the-loop']},
    {id:'capability',label:'Manipulation skills',description:'What the hand is asked to do.',tags:['Dexterous grasping','In-hand manipulation','Bimanual coordination','Tool use','Long-horizon tasks','Articulated objects']},
    {id:'sensing',label:'Sensing & contact',description:'Tactile feedback means touch enters the robot policy at execution time.',tags:['Tactile feedback','Vision','Proprioception','Force control']},
    {id:'resource',label:'Research resources',description:'Supporting datasets, hardware and overviews.',tags:['Dataset / benchmark','Hardware / sensor','Survey']}
  ];
  const day = 86400000;
  function exactDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return null;
    const n = Date.parse(value + 'T00:00:00Z');
    return Number.isFinite(n) && new Date(n).toISOString().slice(0,10) === value ? n : null;
  }
  function filter(papers, state = {}) {
    const query = (state.query || '').trim().toLowerCase();
    const cats = state.categories || [], tags = state.tags || [], facets = state.facets || {};
    return papers.filter(p => {
      const date = exactDate(p.date);
      return (!cats.length || cats.includes(p.category)) && tags.every(t=>(p.tags || []).includes(t)) &&
        (!state.codeOnly || Boolean(p.links?.code)) && (!state.year || Number(p.year) === Number(state.year)) &&
        (!state.start || (date !== null && p.date >= state.start)) &&
        (!state.end || (date !== null && p.date <= state.end)) &&
        Object.entries(facets).every(([f,v])=>!v || (p[f] || []).includes(v)) &&
        (!query || [p.title,p.tldr,p.tldr_zh,p.category,p.authors,...(p.tags || []),...(p.sensing || []),...(p.hand || []),...(p.task || []),...(p.method || [])].join(' ').toLowerCase().includes(query));
    });
  }
  function distribution(papers, values, getValues) {
    return values.map(label=>({label,count:papers.filter(p=>getValues(p).includes(label)).length}));
  }
  function stats(papers) {
    const dated = papers.filter(p=>exactDate(p.date) !== null);
    const years = papers.map(p=>Number(p.year)).filter(y=>Number.isInteger(y) && y>1900 && y<2200);
    const latest = dated.map(p=>p.date).sort().at(-1) || null;
    const latestYear = years.length ? Math.max(...years) : null;
    const minYear = years.length ? Math.min(...years) : null;
    const yearly = minYear === null ? [] : Array.from({length:latestYear-minYear+1},(_,i)=>({label:String(minYear+i),count:papers.filter(p=>Number(p.year)===minYear+i).length}));
    const monthly = latestYear === null ? [] : Array.from({length:12},(_,i)=>({label:`${latestYear}-${String(i+1).padStart(2,'0')}`,count:dated.filter(p=>p.date.startsWith(`${latestYear}-${String(i+1).padStart(2,'0')}`)).length}));
    return {
      total:papers.length,tactile:papers.filter(p=>p.category==='Tactile Dexterous Manipulation').length,
      withCode:papers.filter(p=>p.links?.code).length,latest,latestYear,yearly,monthly,
      unknownDates:papers.length-dated.length,unknownYears:papers.length-years.length,
      recent:latest ? dated.filter(p=>exactDate(p.date)>exactDate(latest)-30*day).length : 0,
      categories:distribution(papers,categories,p=>[p.category]),
      groups:groups.map(g=>({...g,counts:distribution(papers,g.tags,p=>p.tags || [])}))
    };
  }
  function readURL(search, hash) {
    const q = new URLSearchParams(search);
    return {categories:[...new Set(q.getAll('area').flatMap(c=>legacyAreas[c] || [c]).filter(c=>categories.includes(c)))],tags:q.getAll('tag').filter(t=>groups.some(g=>g.tags.includes(t))),query:q.get('q') || '',year:/^\d{4}$/.test(q.get('year') || '') ? q.get('year') : '',facets:Object.fromEntries(['sensing','hand','task','method'].map(f=>[f,q.get(f)||''])),start:exactDate(q.get('from'))===null?'':q.get('from'),end:exactDate(q.get('to'))===null?'':q.get('to'),codeOnly:q.get('code')==='1',panel:['#stats','#watch'].includes(hash)?hash.slice(1):'papers'};
  }
  function writeURL(state, panel) {
    const q = new URLSearchParams();
    (state.categories || []).forEach(c=>q.append('area',c)); (state.tags || []).forEach(t=>q.append('tag',t));
    if (state.year) q.set('year',String(state.year)); if (state.query) q.set('q',state.query); if(state.start)q.set('from',state.start);if(state.end)q.set('to',state.end);if(state.codeOnly)q.set('code','1');
    for(const [f,v] of Object.entries(state.facets || {})) if(v)q.set(f,v);
    return (q.size?'?'+q.toString():'') + (panel==='papers'?'':'#'+panel);
  }
  return {categories,groups,exactDate,filter,distribution,stats,readURL,writeURL};
});
