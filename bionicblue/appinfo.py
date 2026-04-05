
TITLE = "Bionic Blue"

ABBREVIATED_TITLE = "BB"

ORG_DIR_NAME = 'IndieSmiths'
APP_DIR_NAME = 'bionicblue'

### play versioning;
###
###
### there are 02 measures of play data compatibility for this
### game and the play data it produces;
###
### the first is this number below and it indicates the version of the
### overall play experience of this game; changes that affect this
### play for two or more levels cause this number to be incremented;
###
### for instance, if the height of the playable character's jump
### changes, it will affect the overall play experience, so this
### number is incremented
OVERALL_PLAY_VERSION = 1

### the other measure of play data compatibility is a dedicated version
### assigned to each level, defined below;
###
### for instance, if an enemy that is featured only in that level has its
### behaviour changed, this merits an increase in that level play version;
INTRO_LEVEL_PLAY_VERSION = 1

### all those play versioning measures are used to ensure compatibility
### of play data logged, mostly for the sake of playtesting and debugging;
###
### for instance, say one person has version "n" of this game and another
### person has a newer version "n+1" of this game (I'm talking about the
### game version, that is, the package version, not the play version explained
### here); even though their game versions are different, perhaps they
### still have the same play version, because the changes between the
### versions may be only in the underlying systems, not the playable
### content; this means both their play data are compatible, despite the
### difference in the underlying software;
###
### that is precisely why this play versioning is needed and important;

### just to be clear, play data is stored locally and no one has access to
### it but you; the only way for anyone else to have access to such data
### is if you share it on your own (which, as the developer, I, Kennedy,
### would appreciated if you'd do, so that I can improved the game; just reach
### out to me on the social networks or other channels of the project)

### these custom versions are important because over time the play data
### system may change and it may not be able to read play data produced
### by previous versions of such system; likewise, the specific versions
### for the levels displayed here exists to indicate changes in the level
### content that make it incompatible with replaying play data produced
### in a previous version of such level;
###
### put simply, the play data system or any other factor that influences it
### may change and require different data to replay a play session; this
### also includes changes that are not related to the play data system, but
### the overall play, things that affect more than one level; for instance,
### if the height of the playable character's jump is changed, this will
### affect all play; if an enemy that is featured in more than one level is
### changed, this will also change play in a more broad way than the level
### version defined here
###
### likewise, a level playable content may also change in a number of ways
### (enemies with different stats, abilities, perhaps to balance the play
### experience in favor of more fun, new areas introduced, etc.), all this
### also would make reproducing a play session created in a previous version
### of that level difficult or, likely more often, impossible;
###
### for instance, if play data from a previous version of the level was
### recorded when a chasm was smaller, a new version of that level where the
### chasm was made larger may cause the playable character to fall when the
### inputs are reproduced;
