import { fileURLToPath } from 'node:url';
export default {envDir:false,cacheDir:'/tmp/aeion-vite-cache',tsconfig:fileURLToPath(new URL('./tsconfig.web.json',import.meta.url)),
  css:{postcss:{plugins:[]}},test:{include:['src/**/*.test.ts','src/**/*.test.tsx'],
  environment:'node',passWithNoTests:false,testTimeout:10000,hookTimeout:10000,
  maxWorkers:1,reporters:['json'],outputFile:'/tmp/vitest-results.json'}};
