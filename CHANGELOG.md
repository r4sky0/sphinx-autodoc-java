# Changelog

## [0.6.0](https://github.com/r4sky0/sphinx-java-autodoc/compare/v0.5.0...v0.6.0) (2026-10-15)


### Features

* support Sphinx 8.2 ([#54](https://github.com/r4sky0/sphinx-java-autodoc/issues/54)) ([cde6519](https://github.com/r4sky0/sphinx-java-autodoc/commit/cde6519e44d10f73a2a409fd84af1156fd447be5))

## [0.5.0](https://github.com/r4sky0/sphinx-java-autodoc/compare/v0.4.0...v0.5.0) (2026-10-14)


### ⚠ BREAKING CHANGES

* use readable HTML anchors for Java declarations ([#50](https://github.com/r4sky0/sphinx-java-autodoc/issues/50))

### Features

* declare packages on their pages, as Javadoc does ([#51](https://github.com/r4sky0/sphinx-java-autodoc/issues/51)) ([f24dfc1](https://github.com/r4sky0/sphinx-java-autodoc/commit/f24dfc13956a924d4f25b3a4465e07e45a93579f))
* use readable HTML anchors for Java declarations ([#50](https://github.com/r4sky0/sphinx-java-autodoc/issues/50)) ([f75278e](https://github.com/r4sky0/sphinx-java-autodoc/commit/f75278e719775eeeb7d81b521eddce4e59c1733a))

## [0.4.0](https://github.com/r4sky0/sphinx-java-autodoc/compare/v0.3.0...v0.4.0) (2026-10-13)


### Features

* note overridden methods and summarize members with their modifiers and type ([#47](https://github.com/r4sky0/sphinx-java-autodoc/issues/47)) ([9ae1723](https://github.com/r4sky0/sphinx-java-autodoc/commit/9ae172326f597af89e5967cc791200a3b08223dd))


### Bug Fixes

* render links, throws, type parameters, annotations and quotes as the standard doclet does ([#46](https://github.com/r4sky0/sphinx-java-autodoc/issues/46)) ([0c91ca9](https://github.com/r4sky0/sphinx-java-autodoc/commit/0c91ca9ed5dfe65c5f6fcefa000b7e25c8d13e41))

## [0.3.0](https://github.com/r4sky0/sphinx-java-autodoc/compare/v0.2.1...v0.3.0) (2026-10-13)


### Features

* configure the source encoding and exclude packages ([#40](https://github.com/r4sky0/sphinx-java-autodoc/issues/40)) ([de8ba9c](https://github.com/r4sky0/sphinx-java-autodoc/commit/de8ba9c527ab8abe53e1ec9c6b203c74d2864b11))
* link declarations to their source through sphinx.ext.linkcode ([#41](https://github.com/r4sky0/sphinx-java-autodoc/issues/41)) ([d9d017f](https://github.com/r4sky0/sphinx-java-autodoc/commit/d9d017f118601461af0ea54e88b847fef68af36e))
* render JDK note tags and omit author, version and serial tags ([#39](https://github.com/r4sky0/sphinx-java-autodoc/issues/39)) ([f51b7f0](https://github.com/r4sky0/sphinx-java-autodoc/commit/f51b7f026363799018912d81398e27cfd94507cc))


### Documentation

* add a feature gallery and source links in the showcase ([#43](https://github.com/r4sky0/sphinx-java-autodoc/issues/43)) ([d73a96b](https://github.com/r4sky0/sphinx-java-autodoc/commit/d73a96bda1b2ebf14cf1625516a0a1b46efa9da7))
* shorten the guides, fix stale claims and organize navigation by task ([#45](https://github.com/r4sky0/sphinx-java-autodoc/issues/45)) ([d55214f](https://github.com/r4sky0/sphinx-java-autodoc/commit/d55214fa90688d2dcb8b1fe50a7bf46572479a1c))

## [0.2.1](https://github.com/r4sky0/sphinx-java-autodoc/compare/v0.2.0...v0.2.1) (2026-10-12)


### Documentation

* install the extension from PyPI ([#35](https://github.com/r4sky0/sphinx-java-autodoc/issues/35)) ([e281edc](https://github.com/r4sky0/sphinx-java-autodoc/commit/e281edce9f5cf5e8e06c49b8973c9756a3689d6a))
* link the README to PyPI with a version badge ([#37](https://github.com/r4sky0/sphinx-java-autodoc/issues/37)) ([c69d0dd](https://github.com/r4sky0/sphinx-java-autodoc/commit/c69d0dd9dcb91f0623095784c963869ed1356c41))

## [0.2.0](https://github.com/r4sky0/sphinx-java-autodoc/compare/v0.1.0...v0.2.0) (2026-10-12)


### Features

* build the showcase in four themes and check layouts across themes ([#23](https://github.com/r4sky0/sphinx-java-autodoc/issues/23)) ([1b337ff](https://github.com/r4sky0/sphinx-java-autodoc/commit/1b337ff938dd6529c51aa881d68b901b45e7aa5d))
* navigate generated API pages with summaries, sections and page TOC entries ([#18](https://github.com/r4sky0/sphinx-java-autodoc/issues/18)) ([c2e2af9](https://github.com/r4sky0/sphinx-java-autodoc/commit/c2e2af91407b83b73478fe72dd02f6819d48eb8d))
* render Java signatures with Sphinx's signature nodes and linked types ([#20](https://github.com/r4sky0/sphinx-java-autodoc/issues/20)) ([c828610](https://github.com/r4sky0/sphinx-java-autodoc/commit/c82861037dbdb94d3192f6164dc8b670567933f4))
* render Javadoc HTML tables and {[@value](https://github.com/value)} constants natively ([#14](https://github.com/r4sky0/sphinx-java-autodoc/issues/14)) ([27053e0](https://github.com/r4sky0/sphinx-java-autodoc/commit/27053e01cf40469047a0bf589e08ee3e1e4c4ce9))
* render plain inline Javadoc snippets as native code blocks ([#7](https://github.com/r4sky0/sphinx-java-autodoc/issues/7)) ([7d288cc](https://github.com/r4sky0/sphinx-java-autodoc/commit/7d288cc7270c0df5f85c0313a96cb046a0b931ff))
* separate source lookup and preserve inline return documentation ([#17](https://github.com/r4sky0/sphinx-java-autodoc/issues/17)) ([e9aab5d](https://github.com/r4sky0/sphinx-java-autodoc/commit/e9aab5deab33108f312fffea1aaff97e0cc9908c))
* short type titles, search in every theme and an Alabaster showcase ([#28](https://github.com/r4sky0/sphinx-java-autodoc/issues/28)) ([c59fe7f](https://github.com/r4sky0/sphinx-java-autodoc/commit/c59fe7f02a7a71c1257c029e7e82a2811220ecdc))


### Bug Fixes

* clarify Sphinx installation and wrap Java signatures on mobile ([#1](https://github.com/r4sky0/sphinx-java-autodoc/issues/1)) ([d1e0965](https://github.com/r4sky0/sphinx-java-autodoc/commit/d1e0965e8b1cb86dc0121113491acc73e2d46b84))
* mark only declaration annotations as deprecated and act on the repository audit ([#27](https://github.com/r4sky0/sphinx-java-autodoc/issues/27)) ([8485d86](https://github.com/r4sky0/sphinx-java-autodoc/commit/8485d86e90025a438a6b44aac671fa0d4e0e0d28))
* refresh incremental Java docs and preserve Javadoc content ([#6](https://github.com/r4sky0/sphinx-java-autodoc/issues/6)) ([5793822](https://github.com/r4sky0/sphinx-java-autodoc/commit/57938223a3f522a841ebec265050ed5c4956f89e))
* validate API models and recover interrupted page generation ([#13](https://github.com/r4sky0/sphinx-java-autodoc/issues/13)) ([066c53a](https://github.com/r4sky0/sphinx-java-autodoc/commit/066c53a835d1172ee1c83f16f45f5ba1b0ca9feb))


### Documentation

* add repository guidance for coding agents ([#2](https://github.com/r4sky0/sphinx-java-autodoc/issues/2)) ([9fe39b7](https://github.com/r4sky0/sphinx-java-autodoc/commit/9fe39b70b71a0bc2f940689c64bc5f4c702224c1))
* clarify tested Java releases and improve README ([#4](https://github.com/r4sky0/sphinx-java-autodoc/issues/4)) ([bf50251](https://github.com/r4sky0/sphinx-java-autodoc/commit/bf50251861d61c5dafdacfef8e31f21a86173b11))
* compare alternatives to help users choose a tool ([#29](https://github.com/r4sky0/sphinx-java-autodoc/issues/29)) ([8739d1d](https://github.com/r4sky0/sphinx-java-autodoc/commit/8739d1dcf2ef53646a6f928167ddececaf221d7e))
* record verified CI and installation results ([#3](https://github.com/r4sky0/sphinx-java-autodoc/issues/3)) ([d69f3f8](https://github.com/r4sky0/sphinx-java-autodoc/commit/d69f3f86045233e9e255caadff782208728a1232))
* restructure guides around the maintainer journey and drop ballast ([#8](https://github.com/r4sky0/sphinx-java-autodoc/issues/8)) ([18d33d8](https://github.com/r4sky0/sphinx-java-autodoc/commit/18d33d89351f54c40303d7802210eb7cf34c6e3a))
* set up agent skill configuration and move ADR into docs/adr/ ([#25](https://github.com/r4sky0/sphinx-java-autodoc/issues/25)) ([67f6ee4](https://github.com/r4sky0/sphinx-java-autodoc/commit/67f6ee4070f0054f820067ae640df333309a3bba))
* show the Apache Commons Lang API as the documentation example ([#16](https://github.com/r4sky0/sphinx-java-autodoc/issues/16)) ([10c0836](https://github.com/r4sky0/sphinx-java-autodoc/commit/10c08364e35c54bcc88f82f4ed8cc7e7445b3a3e))
