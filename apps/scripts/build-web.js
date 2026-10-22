/**
 * Build adapter for Vercel configurations targeting /apps as root directory
 */
const path = require('path');
const rootScript = path.resolve(__dirname, '../../scripts/build-web.js');

require(rootScript);
