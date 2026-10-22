const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Dynamically locate apps/web directory
let webDir;
if (fs.existsSync(path.resolve(__dirname, '../apps/web/package.json'))) {
  webDir = path.resolve(__dirname, '../apps/web');
} else if (fs.existsSync(path.resolve(process.cwd(), 'apps/web/package.json'))) {
  webDir = path.resolve(process.cwd(), 'apps/web');
} else if (fs.existsSync(path.resolve(process.cwd(), 'web/package.json'))) {
  webDir = path.resolve(process.cwd(), 'web');
} else {
  webDir = process.cwd();
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
