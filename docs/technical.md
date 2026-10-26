# Technical notes

## Reproduced failure

The setup used Windows 11, an AMD Radeon RX 9070 XT, Foundation Sunshine and Zako VDD 100.0.18.1. The virtual display was the sole active primary output and ran at 3840×2160, 60 Hz. Windows enumerated supported modes including 3840×2160.

The built-in EDID's first detailed timing reported 1920×1080. Changing that timing to 4K in an earlier diagnostic test unlocked the game's 4K menu. For this patch test, the original EDID was restored and verified against the original file's complete SHA-256. The driver was not replaced.

Oblivion Remastered Performance Fix 1.1.0 was disabled by renaming its proxy DLL. Loaded-module inspection showed the system VERSION.dll only, and the mod's log did not change. The original fullscreen menu was still limited to 1080p, so that mod is not required to reproduce this failure.

## Causal path

Function names below are Ghidra-generated labels for this exact executable, not developer-provided symbols.

1. `FUN_141172db0` reads the monitor's EDID with SetupAPI and RegEnumValueW. It extracts native width/height from the first detailed timing and stores them at monitor-record offsets `+0x20/+0x24`. It also builds a Windows-supported mode list and a separate maximum-resolution pair.
2. `FUN_141183fb0` rebuilds display metrics. `FUN_1431aa020` provides the metrics used by the game's settings code.
3. `FUN_1431ab020` builds a monitor's resolution list. In fullscreen mode, it removes modes with a different aspect ratio and modes wider than the EDID-native width.
4. Menu builders `FUN_1448efac0` and `FUN_1448e62f0` consume that list. Validation functions `FUN_14319c280` and `FUN_1431bdc00` use it too, choosing the last list entry if a requested resolution is missing.
5. The subsequent `FUN_1431a4980` fullscreen limit uses the separately enumerated maximum when available. No additional change there was required in the observed test.

Conceptually, the fullscreen filter changes from:

```text
keep supported_mode if
    aspect_ratio_matches_native(supported_mode)
    and supported_mode.width <= edid_native_width
```

to:

```text
keep supported_mode if
    aspect_ratio_matches_native(supported_mode)
```

The earlier minimum-height filter and the Windows-supported mode list are retained. Modes above a panel's native timing that Windows exposes, such as supersampling modes, may consequently appear too. This is the intended policy change; the patch does not add arbitrary modes or a fixed 4K value.

## Patch

Image base: `0x140000000`. All addresses are specific to the accepted file hash.

| Field | Value |
|---|---|
| Instruction VA | `0x1431ab536` |
| Instruction RVA | `0x031ab536` |
| File offset | `0x031aab36` |
| Section | `.text` |
| Original | `7E 2C`: JLE `0x1431ab564` |
| Patched | `EB 2C`: JMP to the same target |
| Single changed byte | `7E` → `EB` |
| EXE size | 160654648 bytes |

The preceding aspect-ratio check still branches to the removal path on a mismatch. The changed instruction therefore preserves a same-aspect supported mode even when it exceeds the native width. The borderless and windowed branches do not execute this instruction.

Original SHA-256:

```text
b7be7e6ebe9424f6fdf274f5e7a59372de103e043ab5b66c60e021c0c89df457
```

Patched SHA-256:

```text
302c436781814c561813ae8bb482dd54d934807da4a9459726755d2869e56682
```

## Validation and limits

The full original and patched files differed at exactly one byte. Read-only inspection of the running game confirmed `EB 2C` at the expected RVA. With original EDID and no PerfFix, the menu changed from a user-confirmed maximum of 1920×1080 to 3840×2160. Applying 4K succeeded; host source and signal were 3840×2160. The user confirmed that 4K remained selected after a normal exit and relaunch.

This was an original/patched comparison followed by a second patched launch, not an A/B/A reversal test. The game changed INI resolution fields from 4K to 1080p in the control run; those fields were not manually reset before the patched run. The saved `r.SetRes` entry still contained 4K. The static filter and loaded instruction provide additional direct evidence for the menu change.

Display polling still captured a roughly one-second 1080p startup transient on the repeated patched launch. Polling alone does not identify the API caller; removing that transient requires separate initialization tracing.

Borderless obtains its single menu entry from the native EDID dimensions and remains unmodified. The user reported that the image remained 4K despite the disabled 1080p label. Host/signal dimensions were verified, but swap-chain and internal render-target dimensions were not directly measured.

Compatibility with other game builds, other patches, and PerfFix enabled has not been established. The patcher accepts only the two complete hashes above.

The distribution tool additionally checks instruction context, verifies a separate original backup, is idempotent, supports restoration and attempts rollback if post-write verification fails. Local release checks use private working copies of the real EXE; no game executable or diagnostic dump is included in this repository.
