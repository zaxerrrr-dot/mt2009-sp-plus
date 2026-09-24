// Rebuilds the search index (lunr, the same fields as the MT2009 wiki's)
// from search-docs.json that build.py writes: node lunr-build.js DOCS LUNR OUT
const fs = require('fs');
const vm = require('vm');
const [docsPath, lunrPath, outPath] = process.argv.slice(2);
const mod = { exports: {} };
const ctx = { console, window: {}, self: {}, module: mod, exports: mod.exports };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(lunrPath, 'utf8'), ctx);
const lunr = (typeof mod.exports === 'function' ? mod.exports : null) || ctx.lunr || ctx.window.lunr || ctx.self.lunr;
const data = JSON.parse(fs.readFileSync(docsPath, 'utf8'));
const idx = lunr(function () {
  this.ref('url');
  this.field('title', { boost: 10 });
  this.field('headings', { boost: 5 });
  this.field('keywords', { boost: 5 });
  this.field('category', { boost: 2 });
  this.field('content');
  data.pages.forEach(p => this.add(p));
});
fs.writeFileSync(outPath, JSON.stringify({ version: data.version, generated: new Date().toISOString(),
  pages: data.pages, lunrIndex: idx.toJSON() }));
console.log('search index:', data.pages.length, 'documents');
