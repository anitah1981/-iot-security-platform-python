const { getDefaultConfig } = require('@expo/metro-config');

/** @type {import('metro-config').Config} */
const config = getDefaultConfig(__dirname);

// Workaround for axios resolving to its Node build (which requires 'crypto')
// during EAS Android builds. Disabling package exports makes Metro use the
// browser-compatible entry instead, avoiding the missing 'crypto' module.
config.resolver = {
  ...config.resolver,
  unstable_enablePackageExports: false,
};

module.exports = config;

