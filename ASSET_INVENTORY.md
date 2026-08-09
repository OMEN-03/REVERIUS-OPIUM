# REVERIUS OPIUM - Asset Inventory & Organization Guide

## Asset Directory Structure

### /assets/images/logos/
- **reverius_opium_main_logo.png** - Central emblem with "REVERIUS OPIUM" text and subtitle
- **reverius_opium_logo_clean.svg** - Vector version for scaling
- **favicon.ico** - Multi-size favicon for browser tabs

**Icon Variants** (in `/logos/icon_variants/`):
- icon_minimal.png - Minimal geometric variant
- icon_titan.png - Titan variant (double-pointed)
- icon_core.png - Core variant (golden multi-pointed)

### /assets/images/icons/
**System Icon Set**:
- app_icon.png - Main application icon
- system_tray.png - System tray icon (small format)
- loading_icon.png - Animated loading spinner
- folder_icon.png - Folder/directory icon
- boot_screen.png - Boot/startup screen icon
- monochrome.png - Monochrome variant
- light_mode.png - Light theme icon variant
- favicon_variations/ - Multiple favicon sizes (16x16, 32x32, 64x64, 128x128, 256x256)

**Color Palette** (in `/icons/color_palette/`):
- icon_gold.png - Gold variant
- icon_silver.png - Silver variant
- icon_black.png - Black variant
- icon_white.png - White variant
- icon_glowing.png - Glowing/neon variant
- icon_neon_blue.png - Neon blue variant
- icon_monochrome.png - Monochrome variant
- icon_outline.png - Outline/wireframe variant

### /assets/images/wallpapers/
- wallpaper_forest_golden.png - Golden architectural theme
- wallpaper_night_tower.png - Dark tower/cityscape
- wallpaper_core_golden.png - Core icon with golden aura
- wallpaper_energy_burst.png - Energy/particle effect
- wallpaper_dark_abstract.png - Dark abstract background

### /assets/themes/
- brand_style_guide.png - Complete brand identity document
- color_palette.json - Color definitions (RGB, HEX, HSV)
- typography.json - Font definitions and hierarchy
- texture_materials.json - Texture and material specifications

### /assets/docs/
- BRAND_GUIDE.md - Typography, colors, textures & materials specifications
- ASSET_STANDARDS.md - Technical specifications for all asset types
- ICON_GUIDELINES.md - Icon design and usage guidelines

---

## Color Palette (RGB/HEX)

| Color | Name | Hex | RGB |
|-------|------|-----|-----|
| ⭐ | Gold | #D4AF37 | (212, 175, 55) |
| ⭐ | Silver | #C0C0C0 | (192, 192, 192) |
| ⭐ | Black | #0A0E27 | (10, 14, 39) |
| ⭐ | White | #FFFFFF | (255, 255, 255) |
| ⭐ | Neon Blue | #00D9FF | (0, 217, 255) |
| ⭐ | Glowing Orange | #FF6B00 | (255, 107, 0) |

---

## Typography

**Primary Font**: Consolas (monospace, used throughout UI)
- Headline: 24-26px, bold
- Body: 12-16px, regular
- Display: 18-22px, bold

---

## Textures & Materials

- Brushed Metal
- Polished Gold
- Matte Black
- Carbon Fiber
- Neon Glow
- Holographic

---

## Asset Naming Convention

All assets follow the pattern: `{category}_{variant}_{color/style}.{extension}`

Examples:
- `icon_minimal_gold.png`
- `wallpaper_forest_golden.png`
- `logo_reverius_opium_clean.svg`

---

## Integration with AssetManager

All assets are accessed through the centralized AssetManager:

```python
from utils.asset_manager import AssetManager

# Load specific assets
logo = AssetManager.logo("reverius_opium_main_logo.png")
icon = AssetManager.icon("icon_gold.png")
wallpaper = AssetManager.wallpaper("wallpaper_forest_golden.png")
theme = AssetManager.theme("brand_style_guide.png")
```
