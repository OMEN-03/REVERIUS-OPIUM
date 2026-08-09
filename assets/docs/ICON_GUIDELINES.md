# REVERIUS OPIUM - Icon Usage Guidelines

## Icon System Overview

The REVERIUS OPIUM icon system consists of three design variants (Minimal, Titan, Core) in eight color options, providing flexibility for different UI contexts and themes.

---

## Variant Selection Guide

### Minimal Icon
**When to use:**
- System taskbar (16x16)
- Browser tabs/favicon
- Small toolbar buttons
- Tight spaces

**Characteristics:**
- Simplified, geometric
- Clean lines
- Recognizable at small sizes
- Less detail

**Example sizes:**
- 16x16 - System tray
- 24x24 - Toolbar
- 32x32 - Small buttons
- 48x48 - Medium buttons

---

### Titan Icon
**When to use:**
- Application launcher icons
- Dock/panel icons
- Medium UI buttons
- Standard application branding

**Characteristics:**
- Double-pointed variant
- Medium complexity
- Professional appearance
- Balanced proportions

**Example sizes:**
- 48x48 - Button icons
- 64x64 - Launcher icons
- 128x128 - Application shortcuts
- 256x256 - Dialog/window icons

---

### Core Icon
**When to use:**
- Primary branding
- Splash screens
- Large backgrounds
- Premium features
- High-resolution displays

**Characteristics:**
- Multi-pointed star/crown
- Complex detail
- Premium appearance
- Rich visual impact

**Example sizes:**
- 256x256 - High-DPI displays
- 512x512 - Large buttons
- 1024x1024 - Wallpaper elements
- 2048x2048 - Print materials

---

## Color Selection Guide

### By Context

#### Professional/Corporate
- **Gold** - Premium applications, first impressions
- **Silver** - Neutral, technical applications
- **Black** - Dark mode, maximum contrast

#### Technical/System
- **Neon Blue** - Network, system, tech elements
- **Black** - Dark backgrounds, system icons
- **White** - Light backgrounds, inverted themes

#### Active/Alert
- **Glowing Orange** - Warnings, alerts, active states
- **Neon Blue** - Processing, active operations
- **Gold** - Important, emphasized

#### Accessibility
- **Monochrome** - Color-blind safe
- **Outline** - High contrast mode
- **White on Black** - Maximum accessibility

### By Feature Type

| Feature | Primary | Secondary | Alert |
|---------|---------|-----------|-------|
| AI Assistant | Gold | Neon Blue | Glowing Orange |
| Security | Silver | Black | Neon Blue |
| Processing | Neon Blue | Gold | Glowing Orange |
| System Status | Silver | White | Glowing Orange |
| User Interface | Gold | Silver | Glowing Orange |

---

## Size Specifications

### Web Usage
```
Favicon:        16x16, 32x32
Buttons:        24x24, 32x32, 48x48
Toolbar:        16x16, 24x24
Avatar/Profile: 48x48, 64x64, 128x128
Header Logo:    64x64, 128x128
Banner:         256x256, 512x512
```

### UI Integration
```
Menu Icons:           16x16
Toolbar Icons:        24x24
Button Icons:         32x32
Status Indicators:    16x16, 24x24
Dialog Icons:         48x48, 64x64
Modal Headers:        64x64, 128x128
```

### Print Usage
```
Business Card:        128x128
Logo Application:     256x256, 512x512
Poster/Banner:        512x512, 1024x1024
Print Document:       300 DPI
Embossing:           512x512+
```

---

## Color Pair Combinations

### Recommended Combinations

**Premium (Gold + Silver)**
```
Gold icon on Black background
Silver icon on Gold background
Recommended for: Luxury features, primary UI
```

**Technical (Neon Blue + Black)**
```
Neon Blue icon on Black background
Neon Blue icon on White background
Recommended for: System, network, tech
```

**Alert (Orange + Dark)**
```
Glowing Orange icon on Black background
Glowing Orange icon on Dark Blue background
Recommended for: Warnings, active states
```

**Professional (Silver + White)**
```
Silver icon on Black background
Silver icon on Gray background
Recommended for: Enterprise, neutral UI
```

---

## Implementation Examples

### Python/Tkinter
```python
from utils.asset_manager import AssetManager
import tkinter as tk
from PIL import Image, ImageTk

# Load icon
icon_path = AssetManager.icon("icon_gold.png")
img = Image.open(str(icon_path))
img.thumbnail((32, 32))  # Resize for button
photo = ImageTk.PhotoImage(img)

# Use in button
button = tk.Button(frame, image=photo, text="Execute")
button.image = photo  # Keep reference
button.pack()
```

### Web HTML
```html
<!-- Different sizes for different contexts -->
<img src="/assets/images/icons/icon_gold.png" 
     class="app-icon-small" 
     width="32" 
     height="32" 
     alt="REVERIUS">

<!-- Background image -->
<div style="background-image: url('/assets/images/icons/icon_neon_blue.png');
            background-size: contain;
            width: 64px;
            height: 64px;">
</div>

<!-- Favicon -->
<link rel="icon" type="image/png" 
      href="/assets/images/icons/favicon.png" 
      sizes="32x32">
```

### CSS
```css
.app-icon {
  background-image: url('/assets/images/icons/icon_gold.png');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  width: 48px;
  height: 48px;
}

.icon-small {
  width: 24px;
  height: 24px;
  background-size: 100%;
}

.icon-large {
  width: 128px;
  height: 128px;
  background-size: 100%;
}

@media (prefers-color-scheme: dark) {
  .app-icon {
    background-image: url('/assets/images/icons/icon_gold.png');
  }
}

@media (prefers-color-scheme: light) {
  .app-icon {
    background-image: url('/assets/images/icons/icon_black.png');
  }
}
```

---

## Performance Optimization

### Lazy Loading
```python
# Load icons only when needed
icon_cache = {}

def get_icon(icon_name: str, variant: str = "gold"):
    key = f"{icon_name}_{variant}"
    if key not in icon_cache:
        path = AssetManager.icon(f"icon_{variant}.png")
        icon_cache[key] = Image.open(str(path))
    return icon_cache[key]
```

### Format Recommendations

| Usage | Format | Notes |
|-------|--------|-------|
| Web | PNG | Transparency, good compression |
| Web | WebP | Better compression, modern browsers |
| Desktop | PNG | Universal support |
| Print | PDF/SVG | Scalability, quality |
| Mobile | PNG | Wide device support |

---

## Common Mistakes to Avoid

❌ **DON'T:**
- Stretch or distort icons
- Use low-resolution icons in large formats
- Mix unrelated color variants
- Forget to maintain aspect ratio
- Use transparent PNGs on colored backgrounds
- Apply drop shadows/effects to SVG versions

✅ **DO:**
- Use variant appropriate to size
- Maintain clear space around icons
- Test in actual UI context
- Use correct color for theme
- Check accessibility contrast
- Provide multiple size options

---

## Testing & Validation

### Checklist Before Deployment

- [ ] Icon displays correctly at all required sizes
- [ ] Color contrast meets WCAG standards
- [ ] Icon recognizable in actual UI context
- [ ] No pixelation or quality loss
- [ ] Consistent with brand guidelines
- [ ] Works in both dark and light themes
- [ ] Accessible to color-blind users
- [ ] File size optimized
- [ ] Tested across target browsers/platforms
- [ ] Documentation updated

---

## Asset Paths Reference

```
Minimal Icons:  assets/images/icons/color_palette/icon_*.png
Titan Icons:    assets/images/logos/icon_variants/icon_titan.png
Core Icons:     assets/images/logos/icon_variants/icon_core.png
Favicon:        assets/images/icons/favicon.png
System Icons:   assets/images/icons/
Variants:       icon_gold, icon_silver, icon_black, icon_white,
                icon_glowing, icon_neon_blue, icon_monochrome,
                icon_outline
```

---

## Questions?

Refer to:
- `BRAND_GUIDE.md` - Overall brand specifications
- `ASSET_INVENTORY.md` - Complete asset listing
- `AssetManager` API - Programmatic access

