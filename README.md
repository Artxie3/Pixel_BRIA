# 🎨 FIBO Pixel Lab

> **Transform AI-generated images into authentic pixel art using BRIA FIBO's JSON-native structured prompts**

[![FIBO Hackathon](https://img.shields.io/badge/FIBO-Hackathon%202025-6366f1?style=for-the-badge)](https://bria-ai.devpost.com/)
[![BRIA API](https://img.shields.io/badge/Powered%20by-BRIA%20FIBO-00d4aa?style=for-the-badge)](https://bria.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](#license)

---

## 🏆 Hackathon Submission

**Categories:** 
- 🥇 **Best JSON-Native or Agentic Workflow** — Full structured prompt pipeline with automated style enforcement
- 🎨 **Best Controllability** — Precise pixel art style control (8-bit, 16-bit, 32-bit, Modern) with color palette limits
- 🛠️ **Best New User Experience** — End-to-end professional tool for digital artists and content creators

---

## 🌟 What is FIBO Pixel Lab?

**FIBO Pixel Lab** is a complete pixel art generation pipeline that leverages BRIA FIBO's unique **JSON-native structured prompts** to create authentic, production-ready pixel art.

### The Problem

Traditional AI image generators produce "pseudo pixel art" — images that look pixelated but lack the authentic characteristics of real pixel art:
- ❌ Inconsistent block sizes
- ❌ Anti-aliasing and gradients within pixels
- ❌ Too many colors for retro aesthetics
- ❌ No transparent backgrounds for assets

### Our Solution: The 3-Stage Pipeline

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  1. GENERATE    │ →  │  2. PERFECT      │ →  │  3. EXTRACT     │
│  Pseudo Pixel   │    │  True Pixel Art  │    │  Remove BG      │
│  via FIBO API   │    │  via Block SVG   │    │  via BRIA API   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ↓                      ↓                      ↓
   Structured JSON         Auto Block            Transparent
   Style Enforcement       Detection             PNG Asset
```

---

## ✨ Key Innovation: FIBO Structured Prompt Engineering

The core innovation of FIBO Pixel Lab is how we leverage BRIA FIBO's **structured prompt system** to enforce authentic pixel art characteristics at the generation level.

### How It Works

1. **User enters a natural language prompt** → *"a warrior with a sword"*

2. **FIBO's LLM translates it to structured JSON** → Rich semantic description with objects, lighting, composition

3. **We inject pixel art style overrides** → Modify `style_medium`, `artistic_style`, `color_scheme`, and `photographic_characteristics` to enforce pixel art rules

4. **FIBO generates with enforced constraints** → The structured prompt ensures consistent pixel art output

5. **Perfect Pixel Process transforms the result** → Our algorithm converts pseudo pixel art into authentic, scalable assets

6. **Background removal extracts clean assets** → BRIA's RMBG API produces transparent PNGs ready for use

---

## 🔬 Perfect Pixel Process: From Pseudo to Authentic

This is where the magic happens. FIBO generates excellent "pseudo pixel art" — but it still contains artifacts like anti-aliasing, micro-gradients, and inconsistent block sizes. Our **Perfect Pixel Process** transforms this into authentic pixel art:

### Step 1: Intelligent Block Detection
Our algorithm scans the image to find the true pixel block size:
- Analyzes color uniformity within candidate block sizes (8px, 16px, 32px, etc.)
- Calculates boundary contrast between adjacent blocks
- Scores each candidate and selects the optimal block size

### Step 2: Block-by-Block Color Extraction
For each detected block, we:
- Sample all pixels within the block
- Count color occurrences and find the dominant color
- Handle transparency with configurable alpha thresholds

### Step 3: SVG Vectorization
Convert the analyzed blocks into a clean SVG:
- Each block becomes a single `<rect>` element with the dominant color
- No anti-aliasing, no gradients — pure pixel-perfect vectors
- Infinitely scalable while maintaining authenticity

### Step 4: Re-rasterization
Render the SVG back to PNG at any desired resolution:
- Perfect 1:1 pixel mapping
- Crisp edges at any zoom level
- Ready for use in any application

---

## 🎯 Why FIBO?

FIBO Pixel Lab showcases what makes BRIA FIBO unique:

| FIBO Capability | How We Use It |
|-----------------|---------------|
| **JSON-Native Generation** | Full structured prompt pipeline, not just text prompts |
| **Deterministic Control** | Style overrides always produce consistent results |
| **Disentangled Parameters** | Separate control over color, detail, composition |
| **Professional Quality** | Licensed training data, production-ready output |
| **LLM Translator** | Natural language → structured JSON automatically |

---

## 🚀 Live Demo

**Try it now:** [https://fibo-pixel-lab.vercel.app](https://fibo-pixel-lab.vercel.app)

### Quick Start
1. Enter a prompt: *"a brave knight in shining armor"*
2. Select a style: **16-bit**
3. Click **Generate** → FIBO creates pseudo pixel art with structured prompts
4. Click **Convert** → Algorithm perfects the pixels
5. Click **Remove Background** → Get transparent asset
6. **Download** your production-ready pixel art!

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- BRIA API Token ([Get one free](https://bria.ai/))

### Local Development

```bash
# Clone the repository
git clone https://github.com/Artxie3/Pixel_BRIA.git
cd Pixel_BRIA

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-web.txt

# Set environment variables
cp .env.example .env
# Edit .env with your BRIA API token

# Run the server
cd webapp
uvicorn server:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

---

## 📊 Judging Criteria Alignment

### ✅ Usage of BRIA FIBO
- **JSON-Native Generation**: Complete structured prompt pipeline
- **Pro Parameters**: Style-specific color limits, artistic style overrides
- **Controllability**: 4 distinct pixel art styles with precise characteristics
- **Disentangled Generation**: Separate control over colors, detail, composition

### ✅ Potential Impact
- **Real Production Problem**: Digital artists need authentic pixel art assets
- **Enterprise Scalability**: API-first architecture, stateless design
- **Professional Workflows**: Reproducible results via structured prompts

### ✅ Innovation & Creativity
- **Novel Approach**: Combining FIBO's structured prompts with algorithmic perfection
- **Unexpected Combination**: AI generation + block detection + vectorization + background removal
- **Significant Improvement**: From "pseudo pixel art" to authentic, scalable assets

---

## 🎬 Demo Video

[![FIBO Pixel Lab Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

*Click to watch the 3-minute demo*

---

## 📁 Project Structure

```
Pixel_BRIA/
├── frontend/               # Web interface
├── webapp/                 # API server
├── pixel_playground.py     # Core FIBO integration & style engine
├── png_to_svg.py           # Block detection & vectorization
├── requirements-web.txt
└── DEPLOYMENT.md
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[BRIA AI](https://bria.ai/)** - For the incredible FIBO API and this hackathon opportunity

---

<p align="center">
  <b>Built with ❤️ for the FIBO Hackathon 2025</b>
  <br>
  <a href="https://bria-ai.devpost.com/">FIBO Hackathon</a> • 
  <a href="https://bria.ai/">BRIA AI</a> • 
  <a href="https://github.com/Artxie3/Pixel_BRIA">GitHub</a>
</p>
