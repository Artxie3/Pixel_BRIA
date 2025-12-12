#!/usr/bin/env python3
"""
BRIA Pixel Playground v2
Enhanced with better style prompts and robust block detection.

"""

import os
import sys
import json
import subprocess
import base64
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

load_dotenv()

# Optional imports for pixel art processing
try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    import skimage.metrics as metrics
    from skimage import color
    import cairosvg
    HAS_COMPARISON = True
except ImportError:
    HAS_COMPARISON = False


class BriaPixelPlaygroundV2:
    
    # Improved style definitions with explicit visual characteristics
    PIXEL_STYLES = {
        "8bit": {
            "name": "8-bit Retro (Chunky Pixels)",
            "description": "NES-era style with large, clearly visible pixels",
            "prompt_enhancement": (
                "extremely chunky blocky pixel art, very low resolution style, "
                "NES 8-bit era graphics, only 8-16 colors maximum, "
                "each pixel should be LARGE and clearly visible as a square block, "
                "very simplified shapes with minimal detail, "
                "coarse pixelation like classic Nintendo games"
            ),
            "structured_overrides": {
                "artistic_style": (
                    "8-bit NES-style pixel art, VERY LARGE visible pixel blocks, "
                    "extremely low resolution aesthetic, strictly 8-16 colors, "
                    "coarse chunky pixelation, simplified blocky shapes, "
                    "no fine details, no anti-aliasing, no gradients"
                ),
                "color_limit": "strictly 8-16 distinct flat colors only",
                "detail_level": "very low detail, extremely simplified"
            },
            "negative_prompt": (
                "smooth gradients, anti-aliasing, blur, soft edges, "
                "high detail, fine lines, realistic, photographic, "
                "small pixels, high resolution"
            )
        },
        "16bit": {
            "name": "16-bit Retro (Medium Pixels)",
            "description": "SNES/Genesis style with balanced detail",
            "prompt_enhancement": (
                "16-bit retro pixel art style, medium-sized visible pixels, "
                "SNES or Sega Genesis era graphics, 24-32 colors, "
                "clear pixel grid visible, moderate detail level, "
                "classic 16-bit console game aesthetic"
            ),
            "structured_overrides": {
                "artistic_style": (
                    "16-bit SNES-style pixel art, medium-sized pixel blocks, "
                    "32 color palette maximum, visible pixel grid, "
                    "moderate detail, no anti-aliasing, flat solid colors"
                ),
                "color_limit": "24-32 distinct flat colors",
                "detail_level": "moderate detail, clear shapes"
            },
            "negative_prompt": (
                "smooth gradients, anti-aliasing, blur, soft edges, "
                "photorealistic, 3D rendering"
            )
        },
        "32bit": {
            "name": "32-bit Style (Fine Pixels)",
            "description": "PS1/Saturn era with detailed pixel work",
            "prompt_enhancement": (
                "32-bit era detailed pixel art, fine small pixels, "
                "PlayStation 1 or Saturn style sprites, up to 64 colors, "
                "refined detailed pixel work, smaller pixel size, "
                "high detail retro game aesthetic"
            ),
            "structured_overrides": {
                "artistic_style": (
                    "32-bit era pixel art, fine detailed pixel blocks, "
                    "64 color palette, detailed pixel work, "
                    "small visible pixels, refined shapes, no anti-aliasing"
                ),
                "color_limit": "up to 64 distinct flat colors",
                "detail_level": "high detail, refined shapes"
            },
            "negative_prompt": (
                "blur, soft edges, photorealistic, 3D, gradients within pixels"
            )
        },
        "modern": {
            "name": "Modern Pixel Art",
            "description": "Contemporary indie game style",
            "prompt_enhancement": (
                "modern indie game pixel art, crisp clean pixels, "
                "rich color palette, highly detailed pixel work, "
                "contemporary pixel art aesthetic, sharp edges"
            ),
            "structured_overrides": {
                "artistic_style": (
                    "modern indie pixel art, crisp clean pixels, "
                    "rich vibrant colors, detailed work, sharp edges"
                ),
                "color_limit": "rich color palette",
                "detail_level": "high detail"
            },
            "negative_prompt": "blur, soft edges, photorealistic, 3D"
        }
    }
    
    def __init__(self, api_token: str = None):

        self.api_token = api_token or os.getenv("BRIA_API_TOKEN")
        if not self.api_token:
            raise ValueError("BRIA_API_TOKEN not found. Set it in .env or pass it directly.")
        
        self.base_url = "https://engine.prod.bria-api.com/v2"
        self.headers = {
            "Content-Type": "application/json",
            "api_token": self.api_token
        }
        
        self.session = {
            "prompt": None,
            "style": None,
            "structured_prompt_original": None,
            "structured_prompt_edited": None,
            "generated_image_file": None,
            "svg_file": None,
            "rasterized_png_file": None,
            "editable_png_file": None,
            "nobg_image_file": None,
            "detected_block_size": None,
            "comparison_results": None
        }
    
    def build_enhanced_prompt(self, user_prompt: str, style_key: str = "16bit") -> str:
        """
        Build an enhanced prompt with style-specific characteristics.
        
        Args:
            user_prompt: User's original description
            style_key: One of '8bit', '16bit', '32bit', 'modern'
        
        Returns:
            Enhanced prompt string
        """
        style = self.PIXEL_STYLES.get(style_key, self.PIXEL_STYLES["16bit"])
        
        enhanced = f"{user_prompt}, {style['prompt_enhancement']}"
        
        print(f"   Enhanced prompt for {style['name']}:")
        print(f"   Original: {user_prompt}")
        print(f"   Style: {style_key}")
        
        return enhanced
    
    def generate_structured_prompt(self, prompt: str, seed: int = None) -> Dict[str, Any]:
        """Generate structured prompt from Bria VLM."""
        endpoint = f"{self.base_url}/structured_prompt/generate"
        
        payload = {"prompt": prompt, "sync": True}
        if seed is not None:
            payload["seed"] = seed
        
        print(f" Generating structured prompt from Bria VLM...")
        response = requests.post(endpoint, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f" Structured prompt generated!")
            return result
        else:
            print(f" Error: {response.status_code}")
            response.raise_for_status()
    
    def edit_structured_prompt(
        self,
        structured_prompt: Dict[str, Any],
        style_key: str = "16bit"
    ) -> Dict[str, Any]:
        """
        Edit structured prompt to enforce pixel art style.
        
        This applies style-specific overrides to ensure consistent pixel art output.
        """
        style = self.PIXEL_STYLES.get(style_key, self.PIXEL_STYLES["16bit"])
        overrides = style["structured_overrides"]
        
        # Deep copy
        edited = json.loads(json.dumps(structured_prompt))
        
        print(f"\n Editing structured prompt for {style['name']}...")
        
        # 1. Override style_medium
        edited["style_medium"] = "pixel art"
        print(f"   ✓ style_medium: pixel art")
        
        # 2. Override artistic_style
        edited["artistic_style"] = overrides["artistic_style"]
        print(f"   ✓ artistic_style: {style_key} pixel art")
        
        # 3. Modify aesthetics
        if "aesthetics" not in edited:
            edited["aesthetics"] = {}
        
        aesthetics = edited["aesthetics"]
        
        # Color scheme with limits
        original_colors = aesthetics.get("color_scheme", "vibrant colors")
        aesthetics["color_scheme"] = (
            f"{original_colors}, {overrides['color_limit']}, "
            "no gradients within pixels, high contrast between color blocks"
        )
        print(f"   ✓ color_scheme: {overrides['color_limit']}")
        
        # Mood
        original_mood = aesthetics.get("mood_atmosphere", "")
        if original_mood:
            aesthetics["mood_atmosphere"] = f"{original_mood}, retro gaming nostalgia"
        else:
            aesthetics["mood_atmosphere"] = "retro gaming nostalgia"
        
        # 4. Modify photographic characteristics for 2D
        if "photographic_characteristics" not in edited:
            edited["photographic_characteristics"] = {}
        
        photo = edited["photographic_characteristics"]
        photo["depth_of_field"] = "infinite (2D pixel art, no depth blur)"
        photo["focus"] = "perfectly sharp across entire image"
        photo["camera_angle"] = "orthographic or isometric"
        print(f"   ✓ photographic: 2D flat projection")
        
        # 5. Modify lighting for flat shading
        if "lighting" not in edited:
            edited["lighting"] = {}
        
        lighting = edited["lighting"]
        lighting["conditions"] = "flat, even lighting with cel-shaded shadows"
        lighting["direction"] = "top-left (classic pixel art convention)"
        lighting["shadows"] = "hard-edged, single-color shadows with no gradients"
        print(f"   ✓ lighting: flat pixel art style")
        
        # 6. Add detail level to objects (Option 2 feature)
        if "objects" in edited and isinstance(edited["objects"], list):
            detail_level = overrides.get("detail_level", "moderate detail")
            for obj in edited["objects"]:
                if isinstance(obj, dict):
                    # Append detail instruction to description
                    orig_desc = obj.get("description", "")
                    obj["description"] = f"{orig_desc} Rendered with {detail_level}."
                    
                    # Add pixel-specific appearance
                    orig_appearance = obj.get("appearance_details", "")
                    obj["appearance_details"] = (
                        f"{orig_appearance}, clean pixel art with visible pixel blocks, "
                        f"limited color dithering if needed, sharp silhouette"
                    )
            print(f"   ✓ objects: added {detail_level} instructions")
        
        # 7. Modify background
        if "background_setting" in edited:
            detail = overrides.get("detail_level", "moderate detail")
            edited["background_setting"] = (
                f"{edited['background_setting']} "
                f"Rendered in pixel art style with {detail}."
            )
            print(f"   ✓ background: pixel art style")
        
        # 8. Add context
        original_context = edited.get("context", "")
        edited["context"] = (
            f"A pixel art image in {style_key} style. Clean visible pixels with sharp edges. "
            f"Original context: {original_context}"
        )
        
        print(f"    Structured prompt editing complete!")
        
        return edited
    
    def generate_image(
        self,
        structured_prompt: Dict[str, Any],
        seed: int = None,
        negative_prompt: str = None,
        aspect_ratio: str = "1:1",
        steps_num: int = 50
    ) -> Dict[str, Any]:
        """Generate image with Bria API."""
        endpoint = f"{self.base_url}/image/generate"
        
        payload = {
            "structured_prompt": json.dumps(structured_prompt),
            "sync": True,
            "aspect_ratio": aspect_ratio,
            "steps_num": steps_num,
            "guidance_scale": 5
        }
        
        if seed is not None:
            payload["seed"] = seed
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        print(f" Generating image...")
        if negative_prompt:
            print(f"   Negative prompt: {negative_prompt[:50]}...")
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            image_url = result.get("result", {}).get("image_url")
            print(f" Image generated!")
            
            # Download
            request_id = result.get("request_id", "")
            date_str = datetime.now().strftime("%Y%m%d")
            id_prefix = request_id[:4] if request_id else "0000"
            filename = f"{date_str}_{id_prefix}_image.png"
            
            self._download_image(image_url, filename)
            result["local_image_path"] = filename
            
            return result
        else:
            print(f" Error: {response.status_code}")
            response.raise_for_status()
    
    def generate_pixel_art(
        self,
        prompt: str,
        style: str = "16bit",
        seed: int = None,
        save_prompts: bool = True
    ) -> Dict[str, Any]:
        """Complete pipeline: generate pseudo pixel art via BRIA."""
        style_info = self.PIXEL_STYLES.get(style, self.PIXEL_STYLES["16bit"])

        print("\n" + "=" * 70)
        print(f"[Generate] {style_info['name']} - {style_info['description']}")
        print("=" * 70)
        print(f"Prompt: {prompt}")
        print(f"Style: {style}")
        print("-" * 70)

        self.session["prompt"] = prompt
        self.session["style"] = style

        enhanced_prompt = self.build_enhanced_prompt(prompt, style)

        sp_result = self.generate_structured_prompt(enhanced_prompt, seed=seed)
        sp_data = sp_result.get("result", {})
        sp_str = sp_data.get("structured_prompt", "{}")
        sp_seed = sp_data.get("seed")
        request_id = sp_result.get("request_id", "")
        date_str = datetime.now().strftime("%Y%m%d")
        id_prefix = request_id[:4] if request_id else "0000"

        sp_parsed = json.loads(sp_str)
        self.session["structured_prompt_original"] = sp_parsed

        edited_sp = self.edit_structured_prompt(sp_parsed, style)
        self.session["structured_prompt_edited"] = edited_sp

        if save_prompts:
            orig_file = f"{date_str}_{id_prefix}_original_structured_prompt.json"
            with open(orig_file, "w", encoding="utf-8") as f:
                json.dump(sp_parsed, f, indent=2, ensure_ascii=False)
            print(f"Saved original prompt: {orig_file}")

            edited_file = f"{date_str}_{id_prefix}_edited_structured_prompt.json"
            with open(edited_file, "w", encoding="utf-8") as f:
                json.dump(edited_sp, f, indent=2, ensure_ascii=False)
            print(f"Saved edited prompt: {edited_file}")

        negative = style_info.get("negative_prompt", "")
        img_result = self.generate_image(
            structured_prompt=edited_sp,
            seed=sp_seed,
            negative_prompt=negative,
        )

        img_request_id = img_result.get("request_id", "")
        img_id_prefix = img_request_id[:4] if img_request_id else "0000"
        result_file = f"{date_str}_{img_id_prefix}_generation_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(img_result, f, indent=2, ensure_ascii=False)
        print(f"Saved generation result: {result_file}")

        self.session["generated_image_file"] = img_result.get("local_image_path")

        print("\n" + "-" * 70)
        print("NOTE: AI generates approximate pixel art.")
        print("Use 'Convert to perfect pixels' to detect actual block size and refine.")
        print("-" * 70)

        return {
            "image_file": img_result.get("local_image_path"),
            "image_url": img_result.get("result", {}).get("image_url"),
            "seed": sp_seed,
            "style": style,
            "style_name": style_info["name"],
            "structured_prompt": edited_sp,
        }
    # =========================================================================
    # BLOCK SIZE DETECTION - Pattern-based algorithm
    # =========================================================================
    # BLOCK SIZE DETECTION - Improved algorithm
    # =========================================================================
    
    def _compute_gradient_at_positions(self, img: np.ndarray, block_size: int) -> Tuple[float, float]:
        """
        Compute average gradient magnitude AT block boundaries vs INSIDE blocks.
        
        For correct block size:
        - Gradients AT boundaries should be HIGH (color changes between blocks)
        - Gradients INSIDE blocks should be LOW (uniform colors within blocks)
        
        Returns (boundary_gradient, inside_gradient)
        """
        h, w = img.shape[:2]
        
        # Convert to grayscale for gradient calculation
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(float)
        else:
            gray = img.astype(float)
        
        # Compute gradients (Sobel)
        grad_x = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))
        grad_y = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Separate gradients at boundaries vs inside
        boundary_gradients = []
        inside_gradients = []
        
        for y in range(h):
            for x in range(w):
                # Check if this pixel is on a block boundary
                on_x_boundary = (x % block_size == 0) or (x % block_size == block_size - 1)
                on_y_boundary = (y % block_size == 0) or (y % block_size == block_size - 1)
                
                if on_x_boundary or on_y_boundary:
                    boundary_gradients.append(grad_magnitude[y, x])
                else:
                    inside_gradients.append(grad_magnitude[y, x])
        
        avg_boundary = np.mean(boundary_gradients) if boundary_gradients else 0
        avg_inside = np.mean(inside_gradients) if inside_gradients else 0
        
        return avg_boundary, avg_inside
    
    def _compute_block_uniformity_score(self, img: np.ndarray, block_size: int) -> float:
        """
        Compute how uniform colors are WITHIN each block.
        
        For correct block size, blocks should have very uniform colors.
        Returns a score where HIGHER = more uniform = better.
        """
        h, w = img.shape[:2]
        blocks_y = h // block_size
        blocks_x = w // block_size
        
        if blocks_x == 0 or blocks_y == 0:
            return 0.0
        
        uniformity_scores = []
        
        for by in range(blocks_y):
            for bx in range(blocks_x):
                y1, y2 = by * block_size, (by + 1) * block_size
                x1, x2 = bx * block_size, (bx + 1) * block_size
                block = img[y1:y2, x1:x2].astype(float)
                
                # Calculate standard deviation within block
                # Lower std = more uniform
                block_std = np.std(block)
                
                # Convert to uniformity score (inverse of std)
                # Max std for RGB is ~147, so normalize
                uniformity = 1.0 - min(block_std / 100.0, 1.0)
                uniformity_scores.append(uniformity)
        
        return np.mean(uniformity_scores)
    
    def _compute_boundary_contrast(self, img: np.ndarray, block_size: int) -> float:
        """
        Compute how much color CHANGES at block boundaries.
        
        For correct block size, there should be significant color changes
        at the boundaries between blocks.
        
        Returns ratio of boundary gradients to inside gradients.
        Higher = more contrast at boundaries = better match.
        """
        avg_boundary, avg_inside = self._compute_gradient_at_positions(img, block_size)
        
        if avg_inside < 0.001:
            # Avoid division by zero; if inside is very uniform, that's good
            return avg_boundary / 0.001 if avg_boundary > 0 else 1.0
        
        # Ratio: how much stronger are gradients at boundaries vs inside?
        ratio = avg_boundary / avg_inside
        
        return ratio
    
    def _analyze_block_size(self, img: np.ndarray, block_size: int) -> Dict[str, float]:
        """
        Analyze how well an image matches a specific block size.
        
        Key insight: The correct block size will have:
        1. HIGH uniformity within blocks (low variance inside)
        2. HIGH contrast at boundaries (color changes between blocks)
        3. High boundary/inside gradient ratio
        """
        # Get gradient analysis
        avg_boundary, avg_inside = self._compute_gradient_at_positions(img, block_size)
        
        # Compute uniformity within blocks
        uniformity = self._compute_block_uniformity_score(img, block_size)
        
        # Compute boundary contrast ratio
        boundary_ratio = self._compute_boundary_contrast(img, block_size)
        
        return {
            'block_size': block_size,
            'uniformity': uniformity,
            'boundary_gradient': avg_boundary,
            'inside_gradient': avg_inside,
            'boundary_ratio': boundary_ratio
        }
    
    def find_best_block_size(
        self,
        input_png: str,
        block_sizes: List[int] = None,
        output_dir: str = "block_tests"
    ) -> Dict[str, Any]:
        """
        Detect the natural block size in a pixel art image.
        
        Strategy: Find the block size where:
        - Blocks have uniform colors INSIDE (high uniformity)
        - There's high gradient/contrast AT boundaries (boundary_ratio)
        
        The correct block size will maximize: uniformity × boundary_ratio
        """
        if not HAS_COMPARISON:
            print(" Comparison libraries not available.")
            return None
        
        if block_sizes is None:
            block_sizes = [8, 16, 24, 32]
        
        block_sizes = sorted(block_sizes)
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "="*70)
        print(" BLOCK SIZE DETECTION")
        print("="*70)
        print(f"Testing block sizes: {block_sizes}")
        
        # Load image
        img = np.array(Image.open(input_png).convert('RGB'))
        print(f"Image size: {img.shape[1]}x{img.shape[0]}")
        
        # Analyze each block size
        results = []
        for bs in block_sizes:
            result = self._analyze_block_size(img, bs)
            results.append(result)
        
        # Print raw metrics
        print("\n" + "-"*75)
        print(f"{'Block':<8} {'Uniformity':<12} {'Boundary Grad':<14} {'Inside Grad':<12} {'Ratio':<10}")
        print("-"*75)
        
        for r in results:
            print(f"{r['block_size']:<8} {r['uniformity']:<12.4f} "
                  f"{r['boundary_gradient']:<14.2f} {r['inside_gradient']:<12.2f} "
                  f"{r['boundary_ratio']:<10.3f}")
        
        print("-"*75)
        
        # Calculate combined score
        # Key insight: We want HIGH uniformity AND HIGH boundary ratio
        # Combined score = uniformity × boundary_ratio
        # This rewards block sizes where blocks are solid AND boundaries have contrast
        
        print(f"\n Scoring (uniformity × boundary_ratio):")
        
        scored_results = []
        for r in results:
            # Combined score: multiply uniformity by boundary ratio
            # This way, we need BOTH good uniformity AND good boundary contrast
            combined = r['uniformity'] * r['boundary_ratio']
            
            scored_results.append({
                **r,
                'combined_score': combined
            })
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        print(f"\n   {'Block':<8} {'Uniformity':<12} {'Boundary Ratio':<14} {'Score':<12}")
        print(f"   " + "-"*46)
        
        for i, r in enumerate(scored_results):
            marker = " ← BEST" if i == 0 else ""
            print(f"   {r['block_size']:<8} {r['uniformity']:<12.4f} "
                  f"{r['boundary_ratio']:<14.3f} {r['combined_score']:<12.4f}{marker}")
        
        # Select best
        best_result = scored_results[0]
        best_block_size = best_result['block_size']
        
        print(f"\n DETECTED BLOCK SIZE: {best_block_size}px")
        print(f"   Uniformity: {best_result['uniformity']:.3f}")
        print(f"   Boundary ratio: {best_result['boundary_ratio']:.3f}")
        
        self.session["detected_block_size"] = best_block_size
        self.session["comparison_results"] = results
        
        # Generate SVG for visualization
        svg_path = os.path.join(output_dir, f"detected_{best_block_size}px.svg")
        self._generate_svg(input_png, best_block_size, svg_path)
        
        return {
            "results": results,
            "best_block_size": best_block_size,
            "analysis": best_result
        }
    
    def convert_to_perfect_pixelart(
        self,
        input_png: str = None,
        block_size: int = None,
        auto_detect: bool = True
    ) -> Dict[str, Any]:

        if input_png is None:
            input_png = self.session.get("generated_image_file")
        
        if not input_png or not os.path.exists(input_png):
            print(f" Image not found: {input_png}")
            return None
        
        print("\n" + "="*60)
        print(" PERFECT PIXEL ART CONVERSION")
        print("="*60)
        
        # Auto-detect if needed
        if block_size is None and auto_detect:
            detection = self.find_best_block_size(input_png)
            if detection:
                block_size = detection["best_block_size"]
        
        if block_size is None:
            block_size = 16
            print(f"  Using default: {block_size}px")
        
        print(f"\n Converting with block size: {block_size}px")
        
        # Generate outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        svg_file = f"{timestamp}_perfect_{block_size}px.svg"
        raster_file = f"{timestamp}_perfect_{block_size}px_rasterized.png"
        edit_file = f"{timestamp}_perfect_{block_size}px_editable.png"
        
        svg_generated = self._generate_svg(input_png, block_size, svg_file)
        print(f"   SVG generation result: {svg_generated}, file exists: {os.path.exists(svg_file)}")
        
        if svg_generated:
            print(f" SVG: {svg_file}")
            self.session["svg_file"] = svg_file
            
            if HAS_COMPARISON:
                try:
                    orig = Image.open(input_png)
                    
                    # Rasterized PNG
                    svg_abs_path = Path(svg_file).resolve()
                    print(f"   Rasterizing SVG from: {svg_abs_path}")
                    uri = svg_abs_path.as_uri()
                    cairosvg.svg2png(url=uri, write_to=raster_file,
                                   output_width=orig.width, output_height=orig.height)
                    print(f" Rasterized PNG: {raster_file}")
                    self.session["rasterized_png_file"] = raster_file
                    
                    # Editable PNG
                    editable = self._svg_to_editable_png(svg_file, block_size)
                    if editable:
                        editable.save(edit_file)
                        print(f" Editable PNG: {edit_file} ({editable.width}x{editable.height})")
                        self.session["editable_png_file"] = edit_file
                    
                    return {
                        "svg_file": svg_file,
                        "rasterized_png_file": raster_file,
                        "editable_png_file": edit_file,
                        "detected_block_size": block_size
                    }
                except Exception as e:
                    print(f"   Error during conversion: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            else:
                print("   HAS_COMPARISON is False, cannot complete conversion")
        
        return None
    
    # =========================================================================
    # BACKGROUND REMOVAL
    # =========================================================================
    
    def remove_background(self, input_image: str = None) -> Dict[str, Any]:
        """Remove background using Bria RMBG 2.0."""
        if input_image is None:
            # Prefer the perfect editable image over the original generated image
            input_image = self.session.get("editable_png_file") or self.session.get("generated_image_file")
        
        if not input_image:
            print(" No image specified")
            return None
        
        print("\n" + "="*60)
        print(" REMOVING BACKGROUND")
        print("="*60)
        
        endpoint = f"{self.base_url}/image/edit/remove_background"
        
        # Convert to base64 if local file
        if os.path.exists(input_image):
            with open(input_image, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        else:
            image_data = input_image
        
        payload = {
            "image": image_data,
            "preserve_alpha": True,
            "sync": True
        }
        
        print(" Processing...")
        response = requests.post(endpoint, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            image_url = result.get("result", {}).get("image_url")
            
            request_id = result.get("request_id", "")
            date_str = datetime.now().strftime("%Y%m%d")
            id_prefix = request_id[:4] if request_id else "0000"
            filename = f"{date_str}_{id_prefix}_nobg.png"
            
            self._download_image(image_url, filename)
            result["local_image_path"] = filename
            self.session["nobg_image_file"] = filename
            
            # Save result
            result_file = f"{date_str}_{id_prefix}_nobg_result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            
            print(f" Background removed: {filename}")
            return result
        else:
            print(f" Error: {response.status_code}")
            response.raise_for_status()
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _download_image(self, url: str, filename: str) -> str:
        """Download image from URL."""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f" Downloaded: {filename}")
        return filename
    
    def _generate_svg(self, input_png: str, block_size: int, output_svg: str) -> bool:
        """Generate SVG using png_to_svg.py."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        png_to_svg_path = os.path.join(script_dir, "png_to_svg.py")
        
        cmd = [
            sys.executable,
            png_to_svg_path,
            '--image', input_png,
            '--emit-all-rows',
            '--block-size', str(block_size),
            '--svg-out', output_svg
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  SVG generation error: {result.stderr}")
        return os.path.exists(output_svg)
    
    def _svg_to_editable_png(self, svg_path: str, block_size: int) -> Optional[Image.Image]:
        """Convert SVG to editable PNG where 1 block = 1 pixel."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            
            viewbox = root.get('viewBox')
            if not viewbox:
                return None
            
            vb_parts = viewbox.split()
            vb_width = int(float(vb_parts[2]))
            vb_height = int(float(vb_parts[3]))
            
            img = Image.new('RGB', (vb_width, vb_height), color='white')
            pixels = img.load()
            
            rects = root.findall('.//svg:rect', ns) or root.findall('.//rect')
            
            for rect in rects:
                try:
                    x = int(float(rect.get('x', 0)))
                    y = int(float(rect.get('y', 0)))
                    w = int(float(rect.get('width', 1)))
                    h = int(float(rect.get('height', 1)))
                    fill = rect.get('fill', '#000000')
                    
                    if fill.startswith('#') and len(fill) == 7:
                        r = int(fill[1:3], 16)
                        g = int(fill[3:5], 16)
                        b = int(fill[5:7], 16)
                        color = (r, g, b)
                    else:
                        color = (0, 0, 0)
                    
                    for py in range(y, min(y + h, vb_height)):
                        for px in range(x, min(x + w, vb_width)):
                            pixels[px, py] = color
                except:
                    continue
            
            return img
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary."""
        return {k: v for k, v in self.session.items() if v is not None}


def main():
    """Interactive CLI."""
    print("\n" + "="*70)
    print(" BRIA PIXEL PLAYGROUND v2")
    print("   Enhanced Style Prompts + Robust Block Detection")
    print("="*70)
    
    try:
        playground = BriaPixelPlaygroundV2()
    except ValueError as e:
        print(f" {e}")
        return
    
    while True:
        print("\n" + "-"*70)
        print("MENU")
        print("-"*70)
        print("1. Generate pixel art (with style selection)")
        print("2. Convert to perfect pixels (auto-detect block size)")
        print("3. Remove background")
        print("4. Full pipeline")
        print("5. View session")
        print("6. Exit")
        print("-"*70)
        
        choice = input("Select (1-6): ").strip()
        
        if choice == "1":
            prompt = input("\n Enter description: ").strip()
            if not prompt:
                continue
            
            print("\n Select style:")
            print("   1. 8-bit  (chunky pixels, NES-style)")
            print("   2. 16-bit (medium pixels, SNES-style) [DEFAULT]")
            print("   3. 32-bit (fine pixels, PS1-style)")
            print("   4. Modern (contemporary indie)")
            
            style_choice = input("Style [2]: ").strip() or "2"
            style_map = {"1": "8bit", "2": "16bit", "3": "32bit", "4": "modern"}
            style = style_map.get(style_choice, "16bit")
            
            seed_input = input(" Seed (Enter for random): ").strip()
            seed = int(seed_input) if seed_input.isdigit() else None
            
            result = playground.generate_pixel_art(prompt, style=style, seed=seed)
            print(f"\n Generated: {result['image_file']}")
        
        elif choice == "2":
            current = playground.session.get("generated_image_file")
            img_path = input(f"Image [{current}]: ").strip().strip('"') or current
            
            if img_path and os.path.exists(img_path):
                result = playground.convert_to_perfect_pixelart(img_path)
                if result:
                    print(f"\n Perfect pixel art created!")
                    print(f"   SVG: {result['svg_file']}")
                    print(f"   Detected block size: {result['detected_block_size']}px")
        
        elif choice == "3":
            # Prefer the perfect editable image over the original generated image
            current = playground.session.get("editable_png_file") or playground.session.get("generated_image_file")
            img_path = input(f"Image [{current}]: ").strip().strip('"') or current
            
            if img_path:
                result = playground.remove_background(img_path)
        
        elif choice == "4":
            prompt = input("\n Description: ").strip()
            if not prompt:
                continue
            
            print("\n Style: 1=8bit, 2=16bit, 3=32bit, 4=modern")
            style_choice = input("Style [2]: ").strip() or "2"
            style_map = {"1": "8bit", "2": "16bit", "3": "32bit", "4": "modern"}
            style = style_map.get(style_choice, "16bit")
            
            seed_input = input(" Seed: ").strip()
            seed = int(seed_input) if seed_input.isdigit() else None
            
            # Generate
            gen_result = playground.generate_pixel_art(prompt, style=style, seed=seed)
            
            # Convert
            if input("\nConvert to perfect pixels? (Y/n): ").strip().lower() != 'n':
                playground.convert_to_perfect_pixelart()
            
            # Remove BG
            if input("Remove background? (Y/n): ").strip().lower() != 'n':
                playground.remove_background()
            
            print("\n" + "="*70)
            print(" PIPELINE COMPLETE")
            print("="*70)
            print(json.dumps(playground.get_session_summary(), indent=2))
        
        elif choice == "5":
            print("\n" + json.dumps(playground.get_session_summary(), indent=2))
        
        elif choice == "6":
            print("\n Goodbye!")
            break


if __name__ == "__main__":
    main()
