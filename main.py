import argparse
import sys
from pathlib import Path
from PIL import Image

# Force UTF-8 output for Windows consoles
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def pixelate(image_path: Path, output_dir: Path, sizes: list[int]) -> None:
    """
    Reads an image, pixelates it to the specified sizes, and saves the results.
    """
    try:
        # Open image
        with Image.open(image_path) as img:
            print(f"Processing {image_path.name} (Original size: {img.size})")

            for size in sizes:
                try:
                    # Calculate new dimensions preserving aspect ratio
                    # 'size' will be the maximum dimension
                    width, height = img.size
                    aspect_ratio = width / height

                    if width > height:
                        new_width = size
                        new_height = int(size / aspect_ratio)
                    else:
                        new_height = size
                        new_width = int(size * aspect_ratio)
                    
                    # Ensure dimensions are at least 1x1
                    new_width = max(1, new_width)
                    new_height = max(1, new_height)

                    # Resize smoothly down to calculated dimensions
                    img_small = img.resize((new_width, new_height), resample=Image.Resampling.BILINEAR)
                    
                    # Scale back up using NEAREST to original size
                    result = img_small.resize(img.size, Image.Resampling.NEAREST)
                    
                    # Construct output filename
                    output_filename = f"{image_path.stem}_{size}_pixelated.png"
                    output_path = output_dir / output_filename
                    
                    result.save(output_path)
                    print(f"  Saved: {output_path}")
                except Exception as e:
                    print(f"  Error processing size {size} for {image_path.name}: {e}")

    except Exception as e:
        print(f"Error opening {image_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Pixelate images in a directory.")
    parser.add_argument("--input", type=str, default="images", help="Input directory containing images")
    parser.add_argument("--output", type=str, default="output", help="Output directory for processed images")
    parser.add_argument("--sizes", type=int, nargs="+", default=[16, 32, 64], help="List of pixelation sizes (e.g., 16 32 64)")
    
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    sizes = args.sizes

    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Supported image extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}

    files = [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]

    if not files:
        print(f"No image files found in '{input_dir}'.")
        return

    for file in files:
        pixelate(file, output_dir, sizes)

if __name__ == '__main__':
    main()
