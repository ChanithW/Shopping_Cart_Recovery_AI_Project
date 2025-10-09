#!/usr/bin/env python3
"""
Script to create sample product images for the e-commerce platform.
This will create placeholder images for all products in the database.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import MySQLdb

# Database configuration
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Empty password for WAMP default
    'database': 'ecommerce'
}

def create_placeholder_image(filename, product_name, width=400, height=400):
    """Create a placeholder image with product name text"""
    
    # Create image with a nice gradient background
    image = Image.new('RGB', (width, height), color='#f8f9fa')
    draw = ImageDraw.Draw(image)
    
    # Create gradient background
    for y in range(height):
        color_val = int(248 - (y / height) * 30)  # Gradient from light to slightly darker
        for x in range(width):
            draw.point((x, y), fill=(color_val, color_val + 5, color_val + 10))
    
    # Add border
    border_color = '#007bff'
    draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=3)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        try:
            font = ImageFont.truetype("/Windows/Fonts/arial.ttf", 24)
            small_font = ImageFont.truetype("/Windows/Fonts/arial.ttf", 16)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
    
    # Add product name text
    text_color = '#333333'
    
    # Split long product names into multiple lines
    words = product_name.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_text = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), line_text, font=font)
        if bbox[2] > width - 40:  # Leave 20px margin on each side
            if len(current_line) > 1:
                current_line.pop()  # Remove the last word
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Calculate total text height
    total_text_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)
    
    # Start position (center vertically)
    y_start = (height - total_text_height) // 2
    
    # Draw each line centered
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2]
        x = (width - text_width) // 2
        y = y_start + i * (bbox[3] + 10)
        draw.text((x, y), line, fill=text_color, font=font)
    
    # Add "Sample Product" text at bottom
    sample_text = "Sample Product Image"
    bbox = draw.textbbox((0, 0), sample_text, font=small_font)
    text_width = bbox[2]
    x = (width - text_width) // 2
    y = height - 50
    draw.text((x, y), sample_text, fill='#666666', font=small_font)
    
    return image

def main():
    try:
        # Create products directory if it doesn't exist
        products_dir = os.path.join('static', 'images', 'products')
        os.makedirs(products_dir, exist_ok=True)
        
        # Connect to database
        connection = MySQLdb.connect(**config)
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all products
        cursor.execute("SELECT id, name, image FROM products")
        products = cursor.fetchall()
        
        print("Creating sample product images...")
        
        for product in products:
            image_path = os.path.join(products_dir, product['image'])
            
            # Only create image if it doesn't exist
            if not os.path.exists(image_path):
                print(f"Creating image for: {product['name']} -> {product['image']}")
                
                # Create placeholder image
                img = create_placeholder_image(product['image'], product['name'])
                
                # Save image
                img.save(image_path, 'JPEG', quality=85)
                print(f"  ✓ Saved: {image_path}")
            else:
                print(f"  - Image already exists: {product['image']}")
        
        cursor.close()
        connection.close()
        
        print("\n✅ Sample product images created successfully!")
        print(f"📁 Images location: {os.path.abspath(products_dir)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()