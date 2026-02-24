"""
Generate Android app icons from SAS logo for all required densities.
"""
import os
from PIL import Image

# Android icon sizes for different densities
ICON_SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

# Splash screen sizes (optional, but good to have)
SPLASH_SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

def generate_icons():
    """Generate all required icon sizes from SAS logo."""
    # Get the logo path (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up: android_webview_app -> android_app -> "sas management system" (root)
    # Structure: root/android_app/android_webview_app/generate_icons.py
    project_root = os.path.dirname(os.path.dirname(script_dir))
    logo_path = os.path.join(project_root, 'sas_logo.png')
    
    # Debug: print paths
    print(f"Script dir: {script_dir}")
    print(f"Project root: {project_root}")
    print(f"Logo path: {logo_path}")
    print(f"Logo exists: {os.path.exists(logo_path)}")
    
    # If not found, try common locations
    if not os.path.exists(logo_path):
        possible_paths = [
            os.path.join(project_root, 'sas_logo.png'),
            os.path.join(project_root, 'sas_management', 'static', 'images', 'ssas_logo.png'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                logo_path = path
                print(f"Found logo at: {logo_path}")
                break
    
    if not os.path.exists(logo_path):
        print(f"Error: Logo not found at {logo_path}")
        return False
    
    # Load the logo
    logo = Image.open(logo_path)
    
    # Convert RGBA to RGB if needed, or keep RGBA for transparency
    if logo.mode == 'RGBA':
        # Create a white background for the icon
        background = Image.new('RGB', logo.size, (255, 255, 255))
        background.paste(logo, mask=logo.split()[3])  # Use alpha channel as mask
        logo = background
    
    # Resize to square if needed
    if logo.size[0] != logo.size[1]:
        size = max(logo.size)
        new_logo = Image.new('RGB', (size, size), (255, 255, 255))
        new_logo.paste(logo, ((size - logo.size[0]) // 2, (size - logo.size[1]) // 2))
        logo = new_logo
    
    # Generate icons for each density
    res_dir = os.path.join(script_dir, 'app', 'src', 'main', 'res')
    
    for density, size in ICON_SIZES.items():
        density_dir = os.path.join(res_dir, density)
        os.makedirs(density_dir, exist_ok=True)
        
        # Resize logo to required size
        icon = logo.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save as ic_launcher.png
        icon_path = os.path.join(density_dir, 'ic_launcher.png')
        icon.save(icon_path, 'PNG')
        print(f"Generated {icon_path} ({size}x{size})")
        
        # Also create round and foreground versions for adaptive icons
        icon_round = icon.copy()
        icon_foreground = icon.copy()
        
        icon_round_path = os.path.join(density_dir, 'ic_launcher_round.png')
        icon_foreground_path = os.path.join(density_dir, 'ic_launcher_foreground.png')
        
        icon_round.save(icon_round_path, 'PNG')
        icon_foreground.save(icon_foreground_path, 'PNG')
        
        print(f"Generated {icon_round_path}")
        print(f"Generated {icon_foreground_path}")
    
    print("\nAll icons generated successfully!")
    return True

if __name__ == '__main__':
    generate_icons()

