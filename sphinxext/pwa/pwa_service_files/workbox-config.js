module.exports = {
	globDirectory: '.',
	globPatterns: [
		'**/*.{png,jpg,svg,css,webmanifest,eot,ttf,woff,woff2,js,ico,html,inv,webp}'
	],
	swDest: 'sw.js',
	ignoreURLParametersMatching: [
		/^utm_/,
		/^fbclid$/
	]
};