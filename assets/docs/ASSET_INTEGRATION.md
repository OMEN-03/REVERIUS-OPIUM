# Asset Integration & Best Practices Guide

## Quick Start: Using Assets in Code

### Python - Load an Image

```python
from utils.asset_manager import AssetManager
from PIL import Image, ImageTk

# Get asset path
icon_path = AssetManager.icon("icon_gold.png")

# Verify it exists
if icon_path.exists():
    # Load with PIL
    img = Image.open(str(icon_path))
    
    # Convert for Tkinter
    photo = ImageTk.PhotoImage(img)
    
    # Use in widget
    label = tk.Label(root, image=photo)
    label.image = photo  # Keep reference!
    label.pack()
else:
    print(f"Asset not found: {icon_path}")
```

### Python - Load Multiple Assets

```python
from utils.asset_manager import AssetManager

# Icon variants
icons = {
    'gold': AssetManager.icon("icon_gold.png"),
    'silver': AssetManager.icon("icon_silver.png"),
    'blue': AssetManager.icon("icon_neon_blue.png"),
}

# All exist and are ready to use
for name, path in icons.items():
    print(f"{name}: {path}")
```

### Accessing Different Asset Types

```python
from utils.asset_manager import AssetManager

# Images
logo = AssetManager.logo("reverius_opium_main_logo.png")
wallpaper = AssetManager.wallpaper("wallpaper_core_golden.png")
background = AssetManager.image("some_image.png")

# Audio
startup_sound = AssetManager.sound("startup.wav")
notification = AssetManager.sound("notification.mp3")

# Other assets
font = AssetManager.font("Consolas.ttf")
model = AssetManager.model("ai_model.onnx")
prompt = AssetManager.prompt("system_prompt.txt")
config = AssetManager.config("app_config.json")
```

---

## Directory Organization Quick Reference

| Asset Type | Location | Usage |
|------------|----------|-------|
| Logos | `assets/images/logos/` | Branding, primary identification |
| Icons | `assets/images/icons/` | UI elements, buttons |
| Icon Colors | `assets/images/icons/color_palette/` | Variant-specific icons |
| Wallpapers | `assets/images/wallpapers/` | Background images |
| Sounds | `assets/audio/` | UI feedback, notifications |
| Fonts | `assets/fonts/` | Typography assets |
| Models | `assets/models/` | AI/ML models |
| Prompts | `assets/prompts/` | AI prompt templates |
| Config | `assets/configs/` | Configuration files |

---

## Asset Management Workflow

### 1. Adding a New Asset

```python
# Step 1: Determine asset type
# Is it an image? → logo, icon, wallpaper, or background?
# Is it audio? → startup, notification, music, or voice?
# Is it other? → font, model, prompt, config, etc.

# Step 2: Get the correct directory
path = AssetManager.image("my_new_image.png")
# OR
path = AssetManager.icon("my_icon.png")
# OR other methods

# Step 3: Copy/save your asset to that location
# (Can be done through file explorer or programmatically)

# Step 4: Update assets_manifest.json with the new file
# (Add entry to the appropriate category)

# Step 5: Test loading
if path.exists():
    print(f"✓ Asset found at {path}")
else:
    print(f"✗ Asset not found at {path}")
```

### 2. Organizing Asset Variants

```python
# For icon color variants:
# Use AssetManager.icon() with descriptive names
icon_paths = {
    'gold': AssetManager.icon("icon_gold.png"),
    'silver': AssetManager.icon("icon_silver.png"),
    'blue': AssetManager.icon("icon_neon_blue.png"),
    'dark': AssetManager.icon("icon_black.png"),
}

# All resolve to: assets/images/icons/icon_*.png
```

### 3. Removing Unused Assets

```python
import os
from utils.asset_manager import AssetManager

# Get path
icon_path = AssetManager.icon("old_icon.png")

# Verify it exists and is not used elsewhere
if icon_path.exists():
    # Check codebase for references first!
    # Then remove
    os.remove(str(icon_path))
    
    # Update assets_manifest.json
    # Remove from tracking
```

---

## Common Patterns

### Pattern 1: Lazy Loading with Cache

```python
class IconCache:
    _cache = {}
    
    @classmethod
    def get(cls, name: str, color: str = "gold"):
        key = f"{name}_{color}"
        if key not in cls._cache:
            from PIL import Image
            path = AssetManager.icon(f"icon_{color}.png")
            cls._cache[key] = Image.open(str(path))
        return cls._cache[key]
    
    @classmethod
    def clear(cls):
        cls._cache.clear()

# Usage
icon = IconCache.get("app", "gold")
```

### Pattern 2: Theme-Aware Asset Selection

```python
def get_icon_for_theme(icon_name: str, dark_mode: bool = True):
    """Get icon appropriate for current theme."""
    if dark_mode:
        # Use gold/blue for dark backgrounds
        return AssetManager.icon(f"icon_gold.png")
    else:
        # Use black/outline for light backgrounds
        return AssetManager.icon(f"icon_black.png")

# Usage
icon_path = get_icon_for_theme("app", dark_mode=True)
```

### Pattern 3: Fallback Asset Loading

```python
def load_asset_with_fallback(primary: str, fallback: str, 
                             asset_type: str = "icon"):
    """Load asset with automatic fallback."""
    from utils.asset_manager import AssetManager
    
    # Try primary
    if asset_type == "icon":
        path = AssetManager.icon(primary)
    else:
        path = AssetManager.image(primary)
    
    if path.exists():
        return path
    
    # Fall back to secondary
    if asset_type == "icon":
        path = AssetManager.icon(fallback)
    else:
        path = AssetManager.image(fallback)
    
    if path.exists():
        return path
    
    # Both missing - log error
    print(f"WARNING: Neither {primary} nor {fallback} found")
    return None

# Usage
icon = load_asset_with_fallback("icon_gold.png", "icon_silver.png", "icon")
```

### Pattern 4: Batch Asset Operations

```python
from pathlib import Path
from utils.asset_manager import AssetManager

def get_all_icon_variants():
    """Get all color variants of icons."""
    variants = ["gold", "silver", "black", "white", 
                "glowing", "neon_blue", "monochrome", "outline"]
    
    icons = {}
    for variant in variants:
        path = AssetManager.icon(f"icon_{variant}.png")
        if path.exists():
            icons[variant] = path
    
    return icons

# Usage
all_icons = get_all_icon_variants()
for variant, path in all_icons.items():
    print(f"{variant}: {path}")
```

---

## Best Practices

### ✅ DO

1. **Always use AssetManager**
   ```python
   # Good
   path = AssetManager.icon("icon_gold.png")
   
   # Bad
   path = Path("assets/images/icons/icon_gold.png")
   ```

2. **Check existence before loading**
   ```python
   path = AssetManager.icon("my_icon.png")
   if path.exists():
       # Safe to load
   ```

3. **Organize by type**
   ```python
   # Use appropriate method
   logo = AssetManager.logo("logo.png")  # Not icon
   wallpaper = AssetManager.wallpaper("bg.png")  # Not image
   ```

4. **Maintain references in Tkinter**
   ```python
   photo = ImageTk.PhotoImage(image)
   label = tk.Label(root, image=photo)
   label.image = photo  # IMPORTANT
   ```

5. **Use descriptive names**
   ```python
   # Good
   icon_gold_small = AssetManager.icon("icon_gold_small.png")
   
   # Bad
   img1 = AssetManager.icon("i1.png")
   ```

### ❌ DON'T

1. **Don't hardcode paths**
   ```python
   # Bad
   path = "assets/images/icons/icon.png"
   
   # Good
   path = AssetManager.icon("icon.png")
   ```

2. **Don't assume assets exist**
   ```python
   # Bad
   img = Image.open(str(AssetManager.icon("missing.png")))
   
   # Good
   path = AssetManager.icon("icon.png")
   if path.exists():
       img = Image.open(str(path))
   ```

3. **Don't store file paths directly**
   ```python
   # Bad
   self.icon_path = "C:\\Users\\...\\assets\\images\\icons\\icon.png"
   
   # Good
   self.get_icon_path = lambda: AssetManager.icon("icon.png")
   ```

4. **Don't mix asset types**
   ```python
   # Bad
   path = AssetManager.image("icon_gold.png")  # Is an icon
   
   # Good
   path = AssetManager.icon("icon_gold.png")
   ```

5. **Don't forget to maintain manifest**
   ```python
   # When adding assets:
   # 1. Save file to correct directory
   # 2. Update assets_manifest.json
   # 3. Update ASSET_INVENTORY.md if significant
   # 4. Test loading
   ```

---

## Troubleshooting

### Asset Not Found

```python
from utils.asset_manager import AssetManager

# Debug missing asset
icon_path = AssetManager.icon("icon_gold.png")
print(f"Expected path: {icon_path}")
print(f"Exists: {icon_path.exists()}")
print(f"Parent exists: {icon_path.parent.exists()}")

# List available icons
import os
icon_dir = icon_path.parent
if icon_dir.exists():
    files = os.listdir(str(icon_dir))
    print(f"Available files: {files}")
```

### Image Not Displaying in Tkinter

```python
# Common issue: reference is garbage collected
# WRONG:
label = tk.Label(root, image=ImageTk.PhotoImage(image))

# RIGHT:
photo = ImageTk.PhotoImage(image)
label = tk.Label(root, image=photo)
label.image = photo  # Store reference
```

### Path Resolution Issues

```python
from utils.asset_manager import AssetManager
from pathlib import Path

# Verify project root
print(f"Project root: {AssetManager.project_root}")
print(f"Assets root: {AssetManager.assets_root}")

# Manually verify path
icon_path = AssetManager.icon("icon_gold.png")
print(f"Full path: {icon_path.absolute()}")
print(f"Is absolute: {icon_path.is_absolute()}")
```

---

## Asset Manifest Entry Template

When adding new assets, update `assets_manifest.json`:

```json
{
  "file": "icon_new_variant.png",
  "path": "assets/images/icons/color_palette",
  "type": "icon",
  "color": "new_variant",
  "description": "Brief description of the icon",
  "size": "recommended pixels (e.g., 256x256)",
  "status": "EXPECTED or COMPLETED"
}
```

---

## Performance Tips

1. **Lazy load large assets**
   ```python
   # Load wallpaper only when needed
   wallpaper_cache = None
   
   def get_wallpaper():
       global wallpaper_cache
       if wallpaper_cache is None:
           path = AssetManager.wallpaper("wallpaper.png")
           wallpaper_cache = Image.open(str(path))
       return wallpaper_cache
   ```

2. **Resize before conversion to Tkinter**
   ```python
   img = Image.open(str(AssetManager.icon("icon.png")))
   img.thumbnail((32, 32))  # Resize first
   photo = ImageTk.PhotoImage(img)
   ```

3. **Cache frequently used assets**
   ```python
   @functools.lru_cache(maxsize=32)
   def get_cached_icon(name: str):
       return Image.open(str(AssetManager.icon(f"{name}.png")))
   ```

---

## File Size Optimization

| Asset Type | Recommended Size | Format | Quality |
|------------|------------------|--------|---------|
| Icon | 256x256 | PNG | High (lossless) |
| Wallpaper | 2560x1440 | PNG/WebP | High |
| Logo | 512x512 | PNG/SVG | Lossless |
| Thumbnail | 128x128 | JPEG | Medium |
| Audio | - | OGG/MP3 | 128-192 kbps |
| Model | - | ONNX/PT | As-is |

---

## Questions?

Refer to:
- `assets_manifest.json` - Complete asset catalog
- `BRAND_GUIDE.md` - Brand specifications
- `ASSET_INVENTORY.md` - Asset directory guide

