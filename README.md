# Pixelize

A Python tool that applies a stylish pixelation effect to your images. It downsizes images to specific dimensions and then scales them back up using nearest-neighbor interpolation to create a retro, blocky look.

## Features

- **Pixelation**: Automatically pixelates images to multiple sizes (default: 16, 32, 64 pixels on the longest side), preserving aspect ratio.
- **Batch Processing**: Processes all images in a specified directory.
- **Customizable**: Configure input/output directories and pixelation sizes via the command line.
- **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) (Fast Python package installer and resolver)

## Installation

1.  Clone this repository:
    ```bash
    git clone <repository-url>
    cd pixelize
    ```

2.  Install dependencies using `uv`:
    ```bash
    uv sync
    ```

## Usage

You can run the script directly using `uv run`.

### Basic Usage
Process images from the default `images/` directory and save them to `output/` with default sizes (16, 32, 64):

```bash
uv run main.py
```

### Custom Usage
Specify custom input/output directories and pixel sizes:

```bash
uv run main.py --input ./my_photos --output ./pixel_art --sizes 128 256
```

### CLI Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `--input` | `images` | Directory containing input images. |
| `--output` | `output` | Directory where processed images will be saved. |
| `--sizes` | `16 32 64` | List of target pixel sizes for the maximum dimension (integers). |

## Example

To pixelate all images in `photos/` to 10x10 and 20x20 blocks and save them to `results/`:

```bash
uv run main.py --input photos --output results --sizes 10 20
```
