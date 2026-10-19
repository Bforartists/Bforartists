# Bforartists Online Essentials: changes on top of Blender's

The Online Essentials at `https://assets.bforartists.com/essentials/` are Blender's Online Essentials plus the changes in this folder. Blender's `.blend` files are never edited, so new Blender assets keep arriving with every update.

| What | How |
|---|---|
| 🖼️ New thumbnail | Put a `.webp` in `thumbnails/` at the path `find` prints |
| 🗂️ Rename / reorder categories | Copy Blender's `blender_assets.cats.txt` here and edit it |
| ↪️ Move an asset to another category | Add a line to `catalog_map.json` |
| 🏷️ Library name | `library.json` |

```sh
python tools/utils/bforartists_online_essentials.py find "clay strips"   # where its thumbnail goes
python tools/utils/bforartists_online_essentials.py build                # build + test locally
python tools/utils/bforartists_online_essentials.py update               # pull Blender, build, upload (asks first)
```

Full guide: [Online Essentials Asset Library](https://github.com/Bforartists/Bforartists/wiki/Online-Essentials-Asset-Library) · Issue #6728
