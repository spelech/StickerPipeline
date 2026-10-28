# Changelog

## [1.1.0](https://github.com/spelech/StickerPipeline/compare/v1.0.1...v1.1.0) (2026-10-28)


### Features

* add Cricut Joy 2 sheet presets (4.5x6.5 mat & 8.5x11 letter) with registration box and web configurator ([4a3a934](https://github.com/spelech/StickerPipeline/commit/4a3a934c3ee47d78c40266643b3d9e4449ab6606))
* add sample sticker output artifacts and update README ([c3d954e](https://github.com/spelech/StickerPipeline/commit/c3d954e4c95f6f501b64611359c525c25311a2e0))
* add web dashboard studio UI at root path with drag-and-drop upload and gallery ([5248cde](https://github.com/spelech/StickerPipeline/commit/5248cde22498e4ac9da8dcc85fcb19fe0039b342))


### Bug Fixes

* add graceful exception skip handling for live generation timeouts ([bb19e6a](https://github.com/spelech/StickerPipeline/commit/bb19e6af5ae3df99c261102eb88835258506c98e))
* update Dockerfile libgl1 dependency for Debian slim ([52adacf](https://github.com/spelech/StickerPipeline/commit/52adacfae76398072458c480c251e3fbdb574e9d))


### Performance Improvements

* lazy load rembg session to prevent startup blocking ([a8b731c](https://github.com/spelech/StickerPipeline/commit/a8b731c2091aac5ae786a9d42990a040bdf85fd3))
* lazy-import rembg module to prevent import hang on container startup ([e8c2fa5](https://github.com/spelech/StickerPipeline/commit/e8c2fa5997c2032f5caaf72c93daab599ea8c7fd))


### Documentation

* add custom 1280x640 social preview card (.github/social-preview.svg) ([29a2912](https://github.com/spelech/StickerPipeline/commit/29a2912e8cffe9803f02274f535846d31151a977))
