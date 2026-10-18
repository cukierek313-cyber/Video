# VidCraft AI — Shorts Studio (Stage 2)

Windows desktop MVP for short-form video creators. Dark UI, media import, ordered multi-clip timeline, vertical 9:16 / square 1:1 / horizontal 16:9 output, MP4 export, optional music mix, and AI-generated SRT subtitles.

## Current scope
- Import video/audio/image media into a media bin.
- Preview video by double-clicking it in the media bin.
- Add multiple clips to a timeline and reorder them with drag-and-drop or arrows.
- Export clips sequentially to a common resolution and 30 fps.
- Add optional background music at reduced volume.
- Generate SRT subtitles for the selected timeline clip with Faster-Whisper.
- Build one portable `VidCraftAI.exe` via PyInstaller and GitHub Actions.

## Build locally on Windows
Install Python 3.11, unzip the project, then double-click `build_windows.bat`. Output: `dist\VidCraftAI.exe`.

## GitHub build
1. Create a repository and upload all files.
2. Open **Actions** and run **Build Windows EXE and publish Release** to get the artifact.
3. To publish a Release, push a version tag, e.g. `git tag v0.2.0` then `git push origin v0.2.0`.

## AI subtitles
The first subtitle run downloads the Whisper `small` model. Transcription runs locally on CPU; performance depends on the PC. The rest of the editor does not require an AI service or API key.

## Known MVP limitations
This is a functional foundation, not feature parity with CapCut. It does not yet have frame-accurate clip trimming on the timeline, keyframe animations, transitions, text overlays, waveform visualization, or subtitle burn-in. Timeline reorder is supported; clip boundaries are not yet draggable. Export re-encodes each clip and can take time. Review the code and test on sample media before distributing builds.
