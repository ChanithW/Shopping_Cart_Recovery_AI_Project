#!/usr/bin/env python3
"""
Script to create the missing hero image for the homepage.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_hero_image(filename, width=800, height=400):
    """Create a hero image for the homepage"""
    
    # Create image with a nice gradient background
    image = Image.new('RGB', (width, height), color='#007bff')
    draw = ImageDraw.Draw(image)
    
    # Create gradient background from blue to lighter blue
    for y in range(height):
        blue_val = int(0 + (y / height) * 50)  # From dark blue to lighter
        green_val = int(123 + (y / height) * 50) 
        color_val = int(255 - (y / height) * 50)
        for x in range(width):
            draw.point((x, y), fill=(blue_val, green_val, color_val))
    
    # Try to load a font
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            title_font = ImageFont.truetype("/Windows/Fonts/arial.ttf", 48)
            subtitle_font = ImageFont.truetype("/Windows/Fonts/arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
    
    # Add text
    title_text = "Welcome to ECommerceStore"
    subtitle_text = "Your trusted online shopping destination"
    text_color = 'white'
    
    # Draw title
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = bbox[2]
    x = (width - title_width) // 2
    y = height // 2 - 60
    draw.text((x, y), title_text, fill=text_color, font=title_font)
    
    # Draw subtitle
    bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = bbox[2]
    x = (width - subtitle_width) // 2
    y = height // 2 + 20
    draw.text((x, y), subtitle_text, fill=text_color, font=subtitle_font)
    
    return image

def main():
    try:
        # Create hero image
        images_dir = os.path.join('static', 'images')
        hero_path = os.path.join(images_dir, 'hero-image.jpg')
        
        if not os.path.exists(hero_path):
            print("Creating hero image...")
            img = create_hero_image('hero-image.jpg')
            img.save(hero_path, 'JPEG', quality=85)
            print(f"✅ Hero image created: {hero_path}")
        else:
            print("Hero image already exists")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()