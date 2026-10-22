const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Dynamically locate the apps/web directory from any starting context
let webDir;
const candidates = [
  path.resolve(__dirname, '../apps/web'),
  path.resolve(__dirname, '../web'),
  path.resolve(__dirname, '../../apps/web'),
  path.resolve(process.cwd(), 'apps/web'),
  path.resolve(process.cwd(), 'web'),
  process.cwd(),
];

for (const candidate of candidates) {
  const pkgPath = path.join(candidate, 'package.json');
  if (fs.existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
      if (pkg.name === 'web' || fs.existsSync(path.join(candidate, 'src/app'))) {
        webDir = candidate;
        break;
      }
    } catch (_) {}
  }
}

if (!webDir) {
  webDir = path.resolve(__dirname, '../apps/web');
}

console.log(`[build-web] Building Next.js application in: ${webDir}`);
execSync('npm run build', { cwd: webDir, stdio: 'inherit' });

// Ensure .next output exists at current working directory for Vercel
const srcNext = path.join(webDir, '.next');
const destNext = path.join(process.cwd(), '.next');

if (srcNext !== destNext && fs.existsSync(srcNext)) {
  console.log(`[build-web] Syncing build artifacts to: ${destNext}`);
  fs.cpSync(srcNext, destNext, { recursive: true });

  // Repair Node File Trace (.nft.json) relative traversal paths
  console.log('[build-web] Adjusting NFT trace paths for deployment packaging...');
  adjustNftTraces(srcNext, destNext);
}

console.log('[build-web] Build completed successfully.');

function adjustNftTraces(srcDir, destDir) {
  function walk(currentDest) {
    const entries = fs.readdirSync(currentDest, { withFileTypes: true });
    for (const entry of entries) {
      const destFullPath = path.join(currentDest, entry.name);
      if (entry.isDirectory()) {
        walk(destFullPath);
      } else if (entry.name.endsWith('.nft.json')) {
        try {
          const relFromDest = path.relative(destDir, destFullPath);
          const srcFullPath = path.join(srcDir, relFromDest);
          const destFileDir = path.dirname(destFullPath);
          const srcFileDir = path.dirname(srcFullPath);

          const raw = fs.readFileSync(destFullPath, 'utf8');
          const json = JSON.parse(raw);
          if (Array.isArray(json.files)) {
            let modified = false;
            json.files = json.files.map((fileEntry) => {
              const absTarget = path.resolve(srcFileDir, fileEntry);
              const relToSrc = path.relative(srcDir, absTarget);
              // If target is internal to .next, preserve the existing relative path
              if (!relToSrc.startsWith('..') && !path.isAbsolute(relToSrc)) {
                return fileEntry;
              }
              // If target is external (e.g. node_modules), recompute relative from new location
              const newRel = path.relative(destFileDir, absTarget).replace(/\\/g, '/');
              if (newRel !== fileEntry) {
                modified = true;
              }
              return newRel;
            });
            if (modified) {
              fs.writeFileSync(destFullPath, JSON.stringify(json));
            }
          }
        } catch (err) {
          console.warn(`[build-web] Warning adjusting NFT trace at ${destFullPath}:`, err.message);
        }
      }
    }
  }

  walk(destDir);
}
