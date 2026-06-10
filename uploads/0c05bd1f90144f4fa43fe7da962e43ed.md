---
name: Academic Nexus
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#44474e'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#465f88'
  primary: '#000a1e'
  on-primary: '#ffffff'
  primary-container: '#002147'
  on-primary-container: '#708ab5'
  inverse-primary: '#aec7f6'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#000a22'
  on-tertiary: '#ffffff'
  tertiary-container: '#00204d'
  on-tertiary-container: '#4086fa'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#aec7f6'
  on-primary-fixed: '#001b3d'
  on-primary-fixed-variant: '#2d476f'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#d8e2ff'
  tertiary-fixed-dim: '#adc6ff'
  on-tertiary-fixed: '#001a42'
  on-tertiary-fixed-variant: '#004395'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 40px
  max-width: 1280px
---

## Brand & Style

The brand personality is authoritative yet facilitating—a bridge between rigorous academic discipline and cutting-edge artificial intelligence. It targets university students, researchers, and lifelong learners who value efficiency and intellectual growth. The UI must evoke a sense of clarity, focus, and reliability.

This design system utilizes a **Corporate / Modern** aesthetic with **Minimalist** leanings. It emphasizes a "structured-tech" feel: everything is aligned to a strict grid to reflect organizational logic, while subtle depth and refined typography ensure the interface feels sophisticated and premium rather than purely utilitarian. The emotional response should be one of "calm productivity."

## Colors

The palette is anchored by **Oxford Blue**, providing a traditional academic foundation of trust and intelligence. 

- **Primary (Oxford Blue):** Used for navigation, headers, and primary actions to establish authority.
- **Secondary (Emerald Green):** Reserved for "Match Found" states, success indicators, and positive growth metrics.
- **Tertiary (Electric Blue):** Used for interactive links, progress bars, and AI-driven insights to signal technological sophistication.
- **Neutral (Slate Grays):** A scale of grays facilitates a clear information hierarchy without distracting from the content.
- **Background:** High-purity white (#FFFFFF) for the primary canvas, with very light gray (#F8FAFC) for secondary containers and surface separation.

## Typography

The typography system relies on **Inter** for its exceptional readability and neutral, professional character across all weights. For technical data and UI metadata, **Geist** is introduced to provide a "developer-friendly" precision that complements the AI-driven nature of the application.

Large headlines use tighter letter-spacing and heavier weights to feel impactful and grounded. Body text maintains generous line heights to ensure long-form reading—such as study group descriptions or research goals—remains effortless. Labels and captions utilize Geist to distinguish metadata from content.

## Layout & Spacing

This design system employs a **Fluid Grid** with fixed maximum constraints. 

- **Desktop:** 12-column grid with 20px gutters and 40px side margins. 
- **Tablet:** 8-column grid with 16px gutters and 24px side margins.
- **Mobile:** 4-column grid with 12px gutters and 16px side margins.

The spacing rhythm is based on a **4px baseline**, ensuring all vertical and horizontal gaps are multiples of four. This mathematical consistency reinforces the organized, "data-driven" aesthetic requested. Containers should use `lg` (24px) padding for standard content and `xl` (32px) for hero sections to maintain an open, airy feel.

## Elevation & Depth

To maintain an "Academic-Tech" feel, depth is created through **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows.

- **Level 0 (Base):** #FFFFFF.
- **Level 1 (Cards/Containers):** White background with a 1px border in #E2E8F0.
- **Level 2 (Interactive/Hover):** A subtle ambient shadow (0px 4px 12px rgba(0, 33, 71, 0.05)) is added to indicate interactivity.
- **Level 3 (Modals):** High-diffusion shadow (0px 12px 32px rgba(0, 0, 0, 0.1)) to separate critical tasks from the background.

Surfaces should feel "sheet-like"—stacked neatly rather than floating in 3D space. Use subtle background tints (#F1F5F9) to define section headers or sidebar areas.

## Shapes

The shape language is **Soft (0.25rem)**. This provides a professional balance: the corners are soft enough to feel approachable and modern, but sharp enough to maintain a sense of precision and structure.

- **Standard Elements (Buttons, Inputs):** 4px (0.25rem).
- **Match Cards / Metric Blocks:** 8px (0.5rem).
- **Outer Modals:** 12px (0.75rem).

Avoid fully rounded "pill" shapes for primary actions to maintain the formal academic tone; reserve pill shapes exclusively for small status tags or "chips."

## Components

### Match Cards
The central component of the system. Match Cards use a Level 1 elevation (1px border). They feature a header with the group name in `headline-md`, a sub-header for the academic subject in `label-sm`, and a "Match Percentage" badge in the top-right corner using the secondary (Emerald) color.

### Metric Blocks
Used for data-heavy views. These are small, non-elevated containers with a light gray fill (#F8FAFC). They display a large numerical value in `headline-lg` and a descriptive label in `label-sm`.

### Tabbed Navigation
Tabs are strictly horizontal with a 2px bottom border indicator in Primary Oxford Blue for the active state. Inactive tabs use Neutral Slate Gray. No background fills on tab triggers to keep the UI clean.

### Buttons
- **Primary:** Solid Oxford Blue with white text. High-contrast.
- **Secondary:** Transparent background with a 1px Oxford Blue border.
- **AI/Match:** Solid Electric Blue for actions specifically involving AI generation or matching.

### Input Fields
Strict rectangular fields with 4px corner radius. Focus states use a 2px Electric Blue ring with 0% offset to highlight the active "data entry" mode.

### Chips/Tags
Small, pill-shaped markers for "Skills" or "Topics." Use a light tint of the primary color (#E0E7FF) with dark blue text for high legibility at small sizes.