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
}

console.log('[build-web] Build completed successfully.');
