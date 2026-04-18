# Changelog

All notable changes to this project will be documented in this file.

The format is based (but not strictly) on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Since this is a game project, we also use a "Play" category among the existing types of changes ("Added", "Changed", etc.), shown before every other change category (unless, of course, for versions that don't change play, as we'll explain next).

This project adheres to the numbering scheme of [Semantic Versioning](https://semver.org/spec/v2.0.0.html), that is, the **X**.**Y**.**Z** scheme.

However, we use different meanings for the numbers: every time meaningful/playable content is added, we increase the minor number. If such addition completes the game, we set the major number to 1.

All other changes are indicated in what would normally be the numbering for indicating patches/fixes, including additions/improvements/removals in code or game design. This is so because in a game project, we assume people are more eager for changes in play.

In other words, it is a content-centric/play-centric approach which I think is more suited to game projects.

This way is also simpler for players to follow the project: they can focus their attention on the leading numbering (major and minor). The major one to know when the game is completed or not and the minor one to know when to look forward to new playable content on the game.

If we add content after completing the game (major version 1), like DLCs or extra stuff, we also increase the minor number, but never touch the major number again. After all, it is still the same game. If we were to make a sequel or prequel, etc., rather than increasing the major number, we would create a new repository altogether, since we'd consider it different project.

Another slight difference is that for pre-releases we don't use separators between the patch number and the pre-release letters (for instance, we use `0.13.0rc1` rather than `0.13.0-rc1`, which seems to be the recommended format for Python projects uploaded to the Python Package Index).


## [0.13.0rc1] - 2026-04-17

This is a very substantial pre-release which consists, above all else, of the addition of the first complete playable mission of the game. This represents at least a few months of content creation and layout plus more than a year of game systems development to support that content.

### Play

- First mission is fully available (resist the temptation to click the spoilers below before playing this content)

<details>
  <summary>Click to reveal spoiler on first mission (namely a brief synopsis of the actual content)</summary>

  The first mission consists of a level 25 screens wide (with varying heights that span 6 screens in height). It has scripted scenes/dialogues, including an optional one where you get a powerup for the duration of the level. It has new enemies and a new hazard (spikes) and, at the end, a boss fight.
</details>


### Added

- This CHANGELOG to help people track changes as new version are released
- support for different languages/locales
- Brazilian portuguese translation (by me)
- several new system subsystems and interfaces:
  - pause menu
  - load game screen (can load, rename and erase save slots)
  - credits screen with links to external assets used in the game
  - links screen with links to follow/donate to the project
  - data screen with convenience utilities related to game user data
  - prompt screen to show prompts in various main menu screens
  - a locale prompt shown to user the very first time the game is launched
  - an in-game prompt for play-related info
  - a report system used to deliver lore to players or developer messages to users

### Changed

- finished and improved play logging: a custom log system for actions and states during a play session for the purpose of playtesting and debugging


## 0.12.2 and previous versions

All these versions up to 0.12.2 represent the early versions of the game as a prototype. The playable content consisted only of a small area a couple of screens wide with a few stationary enemies. Once that content was added, subsequent changes within those versions consisted only of code/system improvements.


[0.13.0rc1]: https://github.com/IndieSmiths/bionicblue/releases/tag/v0.13.0rc1
