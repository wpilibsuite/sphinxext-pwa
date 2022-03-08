module.exports = {
  globDirectory: ".",
  globPatterns: [
    "**/*.{csv,vi,pdf,zip,png,jpg,svg,css,json,txt,webmanifest,eot,ttf,woff,woff2,js,ico,html,inv}",
  ],
  swDest: "sw.js",
  ignoreURLParametersMatching: [/^utm_/, /^fbclid$/],
};
