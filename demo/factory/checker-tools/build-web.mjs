// Supervisor-owned tool: never load candidate Vite/TypeScript configuration or npm scripts.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
const toolRoot=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(process.argv[2] || '/workspace/demo/forum-web');
const dependencies=path.resolve(process.argv[3] || toolRoot);
const require=createRequire(path.join(dependencies,'package.json'));
const ts=require('typescript');
const { build }=await import(pathToFileURL(require.resolve('vite')).href);
const files=[];
function collect(directory) {
  for (const entry of fs.readdirSync(directory,{withFileTypes:true})) {
    const name=path.join(directory,entry.name);
    if (entry.isSymbolicLink()) throw new Error('WEB_SOURCE_SYMLINK');
    if (entry.isDirectory()) collect(name);
    else if (/\.(?:ts|tsx)$/.test(name)) files.push(name);
  }
}
collect(path.join(root,'src'));
if (!files.length) throw new Error('WEB_TYPESCRIPT_SOURCE_MISSING');
const program=ts.createProgram(files,{noEmit:true,strict:true,jsx:ts.JsxEmit.ReactJSX,
  target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext,moduleResolution:ts.ModuleResolutionKind.Bundler,
  esModuleInterop:true,skipLibCheck:true,lib:['lib.es2022.d.ts','lib.dom.d.ts','lib.dom.iterable.d.ts']});
const errors=ts.getPreEmitDiagnostics(program);
if (errors.length) {
  process.stdout.write(JSON.stringify({status:'failed',errors:errors.slice(0,20).map(e=>({
    code:e.code,file:e.file ? path.relative(root,e.file.fileName):null,
    line:e.file&&e.start!==undefined?e.file.getLineAndCharacterOfPosition(e.start).line+1:0}))})+'\n');
  process.exit(1);
}
if (process.argv.includes('--check-only')) {
  process.stdout.write(JSON.stringify({status:'passed',typechecked_files:files.length})+'\n');
  process.exit(0);
}
await build({configFile:false,envDir:false,tsconfig:path.join(toolRoot,'tsconfig.web.json'),root,base:'/',logLevel:'silent',
  css:{postcss:{plugins:[]}},
  build:{outDir:'dist',emptyOutDir:true,assetsInlineLimit:0}});
process.stdout.write(JSON.stringify({status:'passed',typechecked_files:files.length})+'\n');
