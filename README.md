# Oblivion Remastered virtual display fix

A reversible **one-byte patch** for the Windows x64 Steam build of **The Elder Scrolls IV: Oblivion Remastered**. Python 3.8 or newer is required; there are no third-party dependencies.

With a virtual display running at 3840×2160, the game's fullscreen resolution menu can still stop at 1920×1080 when the monitor's EDID reports a 1080p native timing.

The game already knows the modes supported by Windows, but its fullscreen list discards modes wider than that EDID-native width. This patch removes that width ceiling. It preserves the supported-mode source, aspect-ratio filter and minimum-height filter. It does not force a particular resolution.

## Usage

Download [patch.py](patch.py), close the game, and run with Python 3 available as `python`:

```sh
python patch.py "PATH/TO/Oblivion Remastered/OblivionRemastered/Binaries/Win64/OblivionRemastered-Win64-Shipping.exe"
```

Replace the path with your installation. The script verifies the EXE hash, saves an original backup next to it, changes one byte, and verifies the result. Re-running it leaves an already patched file unchanged. Existing backups are verified and never overwritten.

Start the game, select **fullscreen**, and choose a supported resolution such as 3840×2160.

Check without changing any files:

```sh
python patch.py "PATH/TO/OblivionRemastered-Win64-Shipping.exe" --check
```

To undo, close the game and run:

```sh
python patch.py "PATH/TO/OblivionRemastered-Win64-Shipping.exe" --restore
```

Restore requires the verified `OblivionRemastered-Win64-Shipping.exe.oblivion-resolution-fix.original` backup. It changes the byte back and verifies the complete original hash.

Supports only the exact Steam executable identified by the hashes in [patch.py](patch.py). Other builds and other modified EXEs are refused. In-game validation was on Windows 11; Linux/Proton behavior has not been tested.

## Verified behavior and limits

- With the original EDID and original EXE, the reproduced fullscreen menu offered at most 1920×1080.
- With this one-byte change and the same EDID, it offered 3840×2160. The selected 4K setting survived a normal exit and relaunch.
- **A brief switch to 1080p during startup can still occur.** This patch does not fix that transient.
- **Borderless is unchanged:** its disabled resolution field can still show the EDID-native 1080p even when the displayed image remains 4K.
- Testing used Foundation Sunshine and Zako VDD with **Oblivion Remastered Performance Fix disabled**. Compatibility with that mod enabled has not been tested.
- Internal rendering resolution, upscaling and graphics quality are separate settings.

## Disclaimer

Use at your own risk. This patch is provided without warranty; see [LICENSE](LICENSE).

This is an unofficial community project, not affiliated with or endorsed by the game's developers, publishers, or rights holders. Game-related trademarks and copyrights belong to their respective owners. No game binaries or assets are distributed. The MIT license applies only to this project's code and documentation.

[Technical details](docs/technical.md) · [Related Shadow of War fix](https://github.com/asdf-qwert/shadow-of-war-virtual-display-fix) · [MIT license](LICENSE)
