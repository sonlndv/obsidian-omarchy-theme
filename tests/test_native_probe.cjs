'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {probeFormatting} = require('./native_formatting_probe.cjs');
test('probe rejects unrelated vault or file before reading DOM; no native rendering claim', () => {
  const document = new Proxy({}, {get(){ throw new Error('DOM must not be inspected'); }});
  const args={document,expectedVaultPath:'/explicit/synthetic',expectedFile:'Formatting checks.md',mode:'source',scheme:'dark',layer:'theme-only'};
  assert.throws(()=>probeFormatting({...args,app:{vault:{adapter:{getBasePath:()=>'/unrelated'}}}}),{code:'VAULT_MISMATCH'});
  assert.throws(()=>probeFormatting({...args,app:{vault:{adapter:{getBasePath:()=>'/explicit/synthetic'}},workspace:{activeLeaf:{view:{getViewType:()=> 'markdown',file:{path:'Other.md'},getMode:()=> 'source'}}}}}),{code:'FILE_OR_MODE_MISMATCH'});
});
