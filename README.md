# CBRE Lab Safety Induction — WebXR

A browser-based 3D / VR lab safety induction. Walk a two-room laboratory, spot
seven safety hazards, and make each one safe. Runs on PC (mouse + WASD) and
Meta Quest 2/3 (WebXR — teleport + laser pointer).

## Live site

Deployed automatically to GitHub Pages from the `web/` folder on every push to
`main` (see `.github/workflows/deploy-pages.yml`).

- **PC**: open the Pages URL in Chrome/Edge, click Start. WASD to move,
  hold-left-mouse-drag to look, click a hazard to flag it.
- **Quest**: open the same URL in the Quest browser and press **Enter VR**.
  Trigger on a hazard flags and fixes it; trigger on the floor teleports.

## Project layout

| Path | Purpose |
|---|---|
| `web/` | The deployable site (Three.js viewer + `assets/lab.glb`) |
| `blender/build_lab.py` | Procedural environment generator — rebuilds `lab.glb` |
| `build.bat` | Run the Blender build headless (requires Blender 5.x) |
| `serve.bat` | Local dev server at http://localhost:8000 |

## Rebuilding the environment

```
build.bat
```

Regenerates `web/assets/lab.glb` from `blender/build_lab.py`. All hazard mesh
names (`HAZARD_NN_*`) are contract API for `web/main.js` — do not rename them.

## The seven hazards

1. Fume hood sash left fully raised (main lab)
2. Eyewash station blocked (main lab)
3. Unlabelled chemical bottle (main lab)
4. Extension lead across walkway (main lab)
5. Compressed gas cylinder unsecured (main lab)
6. Sharps in general waste (main lab, bins under the window)
7. Lab coat sharing a hook with street clothing (prep room)
