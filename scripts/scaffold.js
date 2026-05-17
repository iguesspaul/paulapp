import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.join(__dirname, '..');

const featureArg = process.argv[2];

if (!featureArg) {
    console.error("Usage: npm run scaffold <feature-name>");
    process.exit(1);
}

const feature = featureArg.toLowerCase();
const Feature = feature.charAt(0).toUpperCase() + feature.slice(1);

// 1. Create Route
const routeDir = path.join(rootDir, 'src', 'routes', feature);
fs.mkdirSync(routeDir, { recursive: true });
const svelteTemplate = `<script lang="ts">
    import { onMount } from "svelte";
    import { load${Feature} } from "../../lib/${feature}/api";

    let isLoading = true;

    onMount(async () => {
        try {
            await load${Feature}();
        } catch (error) {
            console.error("Failed to load ${feature}:", error);
        } finally {
            isLoading = false;
        }
    });
</script>

<div class="h-full w-full flex flex-col p-8 gap-8 overflow-hidden font-mono">
    <div class="flex flex-row justify-between items-end shrink-0">
        <h1 class="text-4xl text-text-primary tracking-widest drop-shadow uppercase">${feature}</h1>
    </div>
    
    {#if isLoading}
        <div class="text-text-primary/60">Loading...</div>
    {:else}
        <div class="text-text-primary/80">
            ${Feature} content goes here.
        </div>
    {/if}
</div>
`;
fs.writeFileSync(path.join(routeDir, '+page.svelte'), svelteTemplate);

// 2. Create API Facade
const apiDir = path.join(rootDir, 'src', 'lib', feature);
fs.mkdirSync(apiDir, { recursive: true });
const apiTemplate = `import { invoke } from "@tauri-apps/api/core";

export async function load${Feature}(): Promise<any> {
    return await invoke("load_${feature}");
}
`;
fs.writeFileSync(path.join(apiDir, 'api.ts'), apiTemplate);

// 3. Create Rust Module
const rustModulePath = path.join(rootDir, 'src-tauri', 'src', `${feature}.rs`);
const rustTemplate = `use serde::{Deserialize, Serialize};

pub fn load_data() -> Result<String, String> {
    eprintln!("[${feature}] Loading data");
    Ok("Data loaded successfully".to_string())
}
`;
fs.writeFileSync(rustModulePath, rustTemplate);

// 4. Auto-wire lib.rs
const libPath = path.join(rootDir, 'src-tauri', 'src', 'lib.rs');
let libContent = fs.readFileSync(libPath, 'utf8');

// Add mod declaration
const modStatement = `mod ${feature};`;
if (!libContent.includes(modStatement)) {
    const modRegex = /^mod \w+;/gm;
    let match;
    let lastIndex = -1;
    while ((match = modRegex.exec(libContent)) !== null) {
        lastIndex = match.index + match[0].length;
    }
    
    if (lastIndex !== -1) {
        libContent = libContent.slice(0, lastIndex) + "\n" + modStatement + libContent.slice(lastIndex);
    } else {
        libContent = modStatement + "\n" + libContent;
    }
}

// Add tauri::command function
const commandFunc = `\n#[tauri::command]\nfn load_${feature}() -> Result<String, String> {\n    ${feature}::load_data()\n}\n`;
if (!libContent.includes(`fn load_${feature}()`)) {
    const entryPointMatch = libContent.match(/#\[cfg_attr\(mobile, tauri::mobile_entry_point\)\]/);
    if (entryPointMatch) {
        libContent = libContent.slice(0, entryPointMatch.index) + commandFunc + "\n" + libContent.slice(entryPointMatch.index);
    }
}

// Add to generate_handler!
if (!libContent.includes(`load_${feature}`)) {
    const handlerRegex = /tauri::generate_handler\!\[([\s\S]*?)\]/;
    const match = handlerRegex.exec(libContent);
    if (match) {
        let handlers = match[1];
        if (!handlers.includes(`load_${feature}`)) {
            if (handlers.trim().length > 0 && !handlers.trim().endsWith(',')) {
                handlers += ',';
            }
            handlers += `\n            load_${feature}`;
            const newHandlerBlock = `tauri::generate_handler![\n${handlers.trim()}\n        ]`;
            libContent = libContent.replace(handlerRegex, newHandlerBlock);
        }
    }
}

fs.writeFileSync(libPath, libContent);

console.log(`Successfully scaffolded ${feature}!`);
console.log(`- Created src/routes/${feature}/+page.svelte`);
console.log(`- Created src/lib/${feature}/api.ts`);
console.log(`- Created src-tauri/src/${feature}.rs`);
console.log(`- Auto-wired into src-tauri/src/lib.rs`);
