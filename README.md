# Bionic Blue (by Kennedy Guerra)

Bionic Blue is an action platformer game featuring a bionic boy tasked with protecting humanity against dangerous robots. It is a desktop game completely free of charge and dedicated to the public domain.

![Title image](https://i.imgur.com/tjBQKXp.png)

![Screenshot](https://i.imgur.com/Pe9abBl.gif)

> [!NOTE]
> Bionic Blue is currently at an early stage of development and for now works like a demo to showcase gameplay.

This project is part of the [Indie Smiths](https://github.com/IndieSmiths) project (formerly know as Indie Python project) and has a [dedicated website](https://bionicblue.indiesmiths.com) where you can find more info about it.

It is made in [Python](https://github.com/python/cpython)/[pygame-ce](https://github.com/pygame-community/pygame-ce) targeting desktop platforms where Python is available like Windows, Mac and Linux.

This game was created by [Kennedy R. S. Guerra](https://kennedyrichard.com) (me), who also develops/maintains it.


## Support the game

Please, support the Bionic Blue game and other useful software of the Indie Smiths project by becoming our patron on [patreon][]. You can also make recurrent donations using [github sponsors][], [liberapay][] or [Ko-fi][].

Both [github sponsors][] and [Ko-fi][] also accept one-time donations.

Any amount is welcome and helps. Check the project's [donation page][] for all donation methods available.



## Installing & running the game

To run the game, installation is actually optional.


### If you want to install

You can install bionic blue from the Python Package Index with the `pip` command:

```
pip install bionicblue
```

Depending on your system, you might need to use the `pip3` command instead of the `pip` command above. That's all you should need.

This will install the `pygame-ce` library (pygame community edition fork) as well, if not already present. To run the installed game, all you need now is to run the `bionicblue` command.


### If you want to use as a standalone program

Download the `bionicblue` folder in the top of the repository folder. Then, if you have the `pygame-ce` library (pygame community edition fork) installed in the Python instance you'll use to run the game, you just need to execute the command below in the directory where you put the `bionicblue` folder:

```python
python -m bionicblue
```

Depending on your system, you might need to use the `python3` command instead of the `python` command above. That's all you should need.

However, if the pygame installed in the Python instance used to run the game isn't pygame-ce the game won't launch. Instead, a dialog will appear explaining the problem and providing instructions to replace your pygame installation by the community edition fork. Both regular pygame and the community edition fork (pygame-ce) are great, but the game can only run with pygame-ce because it uses services that are available solely in that library.


## Controls

The controls are configurable both for keyboard and gamepad.

Default controls for keyboard are...

| Action | Key |
| --- | --- |
| Movement | w, a, s, d keys |
| Shoot | j |
| Jump | k |

Enter (return) and escape keys are reserved for confirming and exitting/going back, respectively. Arrow keys are used to navigate menus, but can also be configured to be used for moving the character.

Regarding the gamepad, the user doesn't need to configure directional buttons/triggers. Those are detected and managed automatically. The user only needs to configure the gamepad for actions like shooting, jumping, etc.


## Semantic versioning for games

Since [semantic versioning](https://semver.org/spec/v2.0.0.html) doesn't map well to game project versions, this is the meaning I adopt here:

In a **X**.**Y**.**Z** version...

**X** is always either 0 or 1. If it is 0, the game isn't finished, that is, it isn't in the state the creator envisioned for it. If it is 1, then the game is in that state and thus we consider it finished.

Even when the game is finished (X is 1), the game may still get new features, fixes, content, etc., though, in much the same way finished games can still get patches or DLCs. Such additions/changes won't increment X though, only Y and Z, depending on the specific changes.

In semantic versioning, incrementign X indicates breaking changes, but since a game is just an executable, not a library with a public API, there's no reason to think of it like that here, so as we explained, we are only concerned with whether the game is finished or not.

**Y** and **Z** more closely resemble their meaning in semantic versioning. **Y** is incremented whenever new features or content are added to the game or when changes are made. And **Z** is incremented whenever a fix is introduced.


## Contributing

Keep in mind this is a game project, so it has a design and finite set of features defined by its creator (me, Kennedy Guerra) according to his vision. In this sense, it is not much different from a book project, which is usually not a very collaborative project, except for the editor's work.

In other words, as much as we love contributions in general in the Indie Smiths project, for this game project we would like the contributions to be limited to refactoring/optimizing/fixes, rather than changing the design/content of the game.

Additionally, when submitting pull requests (PRs), please, submit them to the `develop` branch, not the `main` branch. This way we can refine/complement the changes before merging them with `main`.

If in doubt, please [start a discussion](https://github.com/IndieSmiths/bionicblue/discussions) first, in order to discuss what you would like to change.


## Issues

Issues are reserved for things that crash the game or otherwise prevent the user from progressing in the game. Please, if you're not certain, [start a discussion](https://github.com/IndieSmiths/bionicblue/discussions) instead. It can always be converted into an issue later if needed.

## Contact

Contact me any time via [Bluesky](https://bsky.app/profile/kennedyrichard.com), [Twitter/X](https://twitter.com/KennedyRichard), [mastodon](https://fosstodon.org/KennedyRichard) or [email](mailto:kennedy@kennedyrichard.com).

You are also welcome on the Indie Smiths's [discord server](https://indiesmiths.com/discord).


## License

Bionic Blue is dedicated to the public domain with [The Unlicense](https://unlicense.org/).


## Why the name on game's title

Making games is arduous and honest work. Musicians, illustrators and many other professionals always sign their works. People who make games should not be afraid of doing so as well. Check [Bennett Foddy and Zach Gage's video](https://www.youtube.com/watch?v=N4UFC0y1tY0) to learn more about this.



<!-- More Links -->

[patreon]: https://patreon.com/KennedyRichard
[github sponsors]: https://github.com/sponsors/KennedyRichard
[liberapay]: https://liberapay.com/KennedyRichard
[Ko-fi]: https://ko-fi.com/kennedyrichard
[donation page]: https://indiesmiths.com/donate
