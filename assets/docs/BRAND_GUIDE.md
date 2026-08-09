# REVERIUS OPIUM - Brand Style Guide

## Brand Identity

**Name:** REVERIUS OPIUM  
**Tagline:** "I AM NOT A MACHINE. I AM REVERIUS."  
**Nature:** Advanced AI Assistant with tactical and covert operations capabilities  
**Brand Personality:** Elite, mysterious, powerful, intelligent, precision-focused

---

## Logo System

### Primary Logo
The main REVERIUS OPIUM logo features:
- Central geometric emblem (multi-pointed star/crown)
- Gold and silver metallic accents
- Dark background integration
- Accompanied by text: "REVERIUS OPIUM" with subtitle

**Usage Rules:**
- Minimum size: 64x64 pixels
- Maintain clear space around logo (equal to 1/2 logo width)
- Never rotate or distort
- Use on both dark and light backgrounds

### Icon Variants

#### Minimal Icon
- Geometric, simplified version
- Best for small sizes (16x16, 32x32)
- Use in taskbars and tabs

#### Titan Icon  
- Double-pointed variant
- Medium complexity
- Suitable for 48x48 to 256x256
- Professional applications

#### Core Icon
- Multi-pointed golden variant
- Most detailed version
- Best for large formats
- Primary visual representation

---

## Color Palette

### Primary Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **Gold** | #D4AF37 | Primary accents, highlights, premium elements |
| **Silver** | #C0C0C0 | Secondary accents, borders, refinement |

### Neutral Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **Deep Black** | #0A0E27 | Background, dark theme base |
| **White** | #FFFFFF | Text, highlights, contrast |

### Accent Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **Neon Blue** | #00D9FF | UI elements, interactive states, data visualization |
| **Glowing Orange** | #FF6B00 | Alerts, emphasis, energy states |

### Icon Color Variants

Use the following icon variants for different contexts:

- **Gold** - Luxurious, premium contexts
- **Silver** - Professional, neutral contexts
- **Black** - Dark mode, high contrast
- **White** - Light mode, inverted backgrounds
- **Glowing** - Active/emphasized states
- **Neon Blue** - System/tech states
- **Monochrome** - Accessibility, print
- **Outline** - Wireframe, conceptual

---

## Typography

### Font Family
**Primary:** Consolas (Monospace)

```
REVERIUS OPIUM
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789!@#$%^&*()
```

### Hierarchy

#### Display (26px, Bold)
Used for main headers and prominent UI elements.

```
REVERIUS OPIUM
```

#### Headline (24px, Bold)
Used for page titles and major sections.

#### Subheading (18-22px, Bold)
Used for section headers and secondary titles.

#### Body Text (12-16px, Regular)
Used for all content and UI labels.

#### Caption (11px, Regular)
Used for small text, hints, and metadata.

---

## Textures & Materials

### Visual Effects

1. **Brushed Metal**
   - Subtle directional lines
   - Used for toolbar backgrounds
   - Creates industrial feel

2. **Polished Gold**
   - Reflective highlights
   - Used for premium UI elements
   - Adds luxury appeal

3. **Matte Black**
   - Flat, non-reflective
   - Primary background texture
   - Professional foundation

4. **Carbon Fiber**
   - Diagonal weave pattern
   - Used for technical elements
   - Emphasizes precision

5. **Neon Glow**
   - Soft luminescent effect
   - Used for interactive elements
   - Indicates interactivity

6. **Holographic**
   - Color-shifting gradient
   - Used for premium features
   - Creates futuristic feel

---

## UI Element Examples

### Buttons
```
┌─────────────────────────────────┐
│  EXECUTE COMMAND                │  (Neon Blue)
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  INITIALIZE SYSTEM              │  (Gold accent)
└─────────────────────────────────┘
```

### Status Indicators
- **ONLINE:** Neon Blue (#00D9FF)
- **ACTIVE:** Glowing Orange (#FF6B00)
- **STANDBY:** Silver (#C0C0C0)
- **OFFLINE:** Dark (#0A0E27)

### Data Visualization
- Use Neon Blue for primary data
- Use Gold for highlights/peaks
- Use Glowing Orange for warnings
- Use Silver for reference lines

---

## Wallpaper Specifications

### Forest Golden
- Architectural elements with golden lighting
- Use for professional/command contexts
- Dimensions: 2560x1440 (16:9)

### Night Tower
- Dark cityscape with tower silhouette
- Use for security/covert contexts
- Dimensions: 2560x1440 (16:9)

### Core Golden
- Core icon central, golden aura
- Use for startup/presentation
- Dimensions: 2560x1440 (16:9)

### Energy Burst
- Particle effects radiating outward
- Use for active/processing states
- Dimensions: 2560x1440 (16:9)

### Dark Abstract
- Minimalist dark patterns
- Use for default/clean contexts
- Dimensions: 2560x1440 (16:9)

---

## Integration Guidelines

### Web Integration
```html
<!-- Logo -->
<img src="/assets/images/logos/reverius_opium_main_logo.png" alt="REVERIUS OPIUM">

<!-- Favicon -->
<link rel="icon" type="image/png" href="/assets/images/icons/favicon.png">

<!-- Icon -->
<img src="/assets/images/icons/icon_gold.png" class="app-icon" alt="App Icon">
```

### Python Integration
```python
from utils.asset_manager import AssetManager

# Load logo
logo_path = AssetManager.logo("reverius_opium_main_logo.png")

# Load icon variants
icon_gold = AssetManager.icon("icon_gold.png")
icon_neon_blue = AssetManager.icon("icon_neon_blue.png")

# Load wallpapers
wallpaper = AssetManager.wallpaper("wallpaper_core_golden.png")
```

---

## Brand Voice & Tone

- **Formal but approachable**
- **Confident and authoritative**
- **Technical precision with elegance**
- **Mysterious yet transparent**

### Example Messaging
- ✅ "REVERIUS OPIUM INITIALIZED"
- ✅ "SYSTEM ONLINE - READY FOR COMMANDS"
- ✅ "ENCRYPTION ACTIVE - YOUR DATA IS SECURE"
- ❌ "Hiya! REVERIUS here!" (too casual)
- ❌ "SYSTEM IS NOW SUPER AWESOME!" (too informal)

---

## Accessibility Considerations

1. **Color Blindness:** Use icon outlines in addition to color
2. **Monochrome Mode:** Provide grayscale alternatives
3. **High Contrast:** Ensure 4.5:1 contrast ratio minimum
4. **Font:** Consolas is readable at all sizes

---

## Files & Resources

| File | Location | Use |
|------|----------|-----|
| Main Logo | `assets/images/logos/` | Primary branding |
| Icon Set | `assets/images/icons/color_palette/` | UI elements |
| Wallpapers | `assets/images/wallpapers/` | Backgrounds |
| Brand Guide | `assets/images/brand_guide/` | Reference |

---

## Questions?

Refer to `ASSET_INVENTORY.md` for complete file listing and `AssetManager` API documentation.

