"""
QR Code Utility Module

Provides high-performance QR code generation with memory-efficient operations.
Supports various output formats and includes utility functions for common operations.
"""

import io
import functools
from typing import Optional, Union, Tuple, Literal, Dict, Any
from pathlib import Path
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer
)
from qrcode.image.styles.colormasks import (
    SolidFillColorMask,
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    HorizontalGradiantColorMask,
    VerticalGradiantColorMask
)
from PIL import Image, ImageDraw

# Type aliases for better code readability
OutputFormat = Literal['png', 'svg', 'pil', 'bytes', 'file']
ModuleDrawerType = Union[
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer
]
ColorMaskType = Union[
    SolidFillColorMask,
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    HorizontalGradiantColorMask,
    VerticalGradiantColorMask
]

class QRCodeGenerator:
    """
    High-performance QR code generator with memory-efficient operations.

    Features:
    - Optimized QR code generation with configurable error correction
    - Multiple output formats (PNG, SVG, PIL Image, bytes)
    - Styling options for visual customization
    - Caching mechanism for repeated operations
    - Memory-efficient handling of large data
    - Thread-safe operations
    """

    def __init__(self):
        self._cache = {}
        self._qr_factory = qrcode.QRCode
        # Pre-initialize common module drawers to avoid repeated instantiation
        self._common_drawers = {
            'square': SquareModuleDrawer(),
            'gapped_square': GappedSquareModuleDrawer(),
            'circle': CircleModuleDrawer(),
            'rounded': RoundedModuleDrawer(),
            'vertical_bars': VerticalBarsDrawer(),
            'horizontal_bars': HorizontalBarsDrawer()
        }

    @functools.lru_cache(maxsize=256)
    def generate_qr(
        self,
        data: str,
        error_correction: qrcode.constants.ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_M,
        box_size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        optimize: int = 0,
        version: Optional[int] = None
    ) -> qrcode.QRCode:
        """
        Generate a QR code with caching for repeated operations.

        Args:
            data: Data to encode in the QR code
            error_correction: Error correction level (L, M, Q, H)
            box_size: Size of each box in pixels
            border: Border size in boxes
            fill_color: Color of the QR code modules
            back_color: Background color
            optimize: Optimize data by trying to reduce the version
            version: Force a specific version (1-40)

        Returns:
            QRCode instance
        """
        qr = self._qr_factory(
            version=version,
            error_correction=error_correction,
            box_size=box_size,
            border=border,
            optimize=optimize
        )
        qr.add_data(data)
        qr.make(fit=True)
        return qr

    def _get_module_drawer(self, module_drawer: Optional[ModuleDrawerType] = None) -> ModuleDrawerType:
        """Helper to get module drawer with fallback to default square drawer."""
        if module_drawer is None:
            return self._common_drawers['square']
        return module_drawer

    def to_pil_image(
        self,
        qr: qrcode.QRCode,
        fill_color: str = "black",
        back_color: str = "white",
        module_drawer: Optional[ModuleDrawerType] = None,
        color_mask: Optional[ColorMaskType] = None,
        embed_image: Optional[Union[str, Image.Image]] = None,
        embed_image_size_ratio: float = 0.2,
        embed_image_border: int = 0
    ) -> Image.Image:
        """
        Convert QR code to PIL Image with styling options.

        Args:
            qr: QRCode instance
            fill_color: Color of the QR code modules
            back_color: Background color
            module_drawer: Module drawer for styling
            color_mask: Color mask for advanced coloring
            embed_image: Image to embed in the center
            embed_image_size_ratio: Size ratio of embedded image
            embed_image_border: Border around embedded image

        Returns:
            PIL Image of the QR code
        """
        module_drawer = self._get_module_drawer(module_drawer)

        img = qr.make_image(
            fill_color=fill_color,
            back_color=back_color,
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            color_mask=color_mask
        )

        if embed_image is not None:
            self._embed_image(
                img,
                embed_image,
                size_ratio=embed_image_size_ratio,
                border=embed_image_border
            )

        return img

    def _embed_image(
        self,
        qr_img: StyledPilImage,
        image: Union[str, Image.Image],
        size_ratio: float = 0.2,
        border: int = 0
    ) -> None:
        """Embed an image in the center of the QR code."""
        if isinstance(image, str):
            # Use lazy loading for file paths to avoid unnecessary I/O
            with Image.open(image) as img:
                self._paste_embedded_image(qr_img, img, size_ratio, border)
        else:
            self._paste_embedded_image(qr_img, image, size_ratio, border)

    def _paste_embedded_image(
        self,
        qr_img: StyledPilImage,
        image: Image.Image,
        size_ratio: float,
        border: int
    ) -> None:
        """Helper method to paste embedded image with proper resource handling."""
        # Calculate the size of the embedded image
        qr_width, qr_height = qr_img.size
        img_size = int(min(qr_width, qr_height) * size_ratio)

        # Resize the image with memory-efficient settings
        image = image.resize((img_size, img_size), Image.Resampling.LANCZOS)

        # Create a white background with border if needed
        if border > 0:
            bg_size = img_size + 2 * border
            bg = Image.new('RGB', (bg_size, bg_size), 'white')
            bg.paste(image, (border, border))
            image = bg

        # Calculate position to center the image
        pos = (
            (qr_width - image.size[0]) // 2,
            (qr_height - image.size[1]) // 2
        )

        # Paste the image onto the QR code
        qr_img.paste(image, pos)

    def generate(
        self,
        data: str,
        output_format: OutputFormat = 'pil',
        error_correction: qrcode.constants.ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_M,
        **kwargs
    ) -> Union[Image.Image, bytes, str, None]:
        """
        Generate a QR code in the specified format.

        Args:
            data: Data to encode in the QR code
            output_format: Output format ('pil', 'png', 'svg', 'bytes', 'file')
            error_correction: Error correction level (L, M, Q, H)
            **kwargs: Additional arguments for specific output formats

        Returns:
            QR code in the requested format
        """
        # Generate the QR code with caching
        qr = self.generate_qr(data, error_correction=error_correction)

        if output_format == 'pil':
            return self.to_pil_image(qr, **kwargs)
        elif output_format == 'png':
            img = self.to_pil_image(qr, **kwargs)
            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True, compress_level=9)
            return output.getvalue()
        elif output_format == 'svg':
            return qr.make_image(image_factory=qrcode.image.svg.SvgImage).to_string()
        elif output_format == 'bytes':
            img = self.to_pil_image(qr, **kwargs)
            output = io.BytesIO()
            img_format = kwargs.get('format', 'PNG')
            save_kwargs = {'format': img_format}
            if img_format.lower() == 'png':
                save_kwargs.update({'optimize': True, 'compress_level': 9})
            img.save(output, **save_kwargs)
            return output.getvalue()
        elif output_format == 'file':
            img = self.to_pil_image(qr, **kwargs)
            file_path = kwargs.get('file_path')
            if not file_path:
                raise ValueError("file_path must be provided for 'file' output format")
            img.save(file_path)
            return None
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def get_qr_metrics(
        self,
        data: str,
        error_correction: qrcode.constants.ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_M
    ) -> Dict[str, Any]:
        """
        Get metrics about the QR code that would be generated.

        Args:
            data: Data to encode
            error_correction: Error correction level

        Returns:
            Dictionary containing:
            - version: QR code version (1-40)
            - size: Size in modules (including border)
            - data_capacity: Maximum data capacity in bytes
            - error_correction_level: Error correction level
            - modules_count: Number of modules in the QR code
            - data_utilization: Percentage of data capacity used
        """
        qr = self.generate_qr(data, error_correction=error_correction)
        data_capacity = qr.get_data_capacity()
        data_length = len(data.encode('utf-8'))
        utilization = (data_length / data_capacity) * 100 if data_capacity > 0 else 0

        return {
            'version': qr.version,
            'size': qr.modules_count + (2 * qr.border),
            'data_capacity': data_capacity,
            'error_correction_level': error_correction,
            'modules_count': qr.modules_count,
            'data_utilization': round(utilization, 2)
        }

    def validate_data(
        self,
        data: str,
        error_correction: qrcode.constants.ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_M
    ) -> bool:
        """
        Validate if data can be encoded in a QR code with given error correction.

        Args:
            data: Data to validate
            error_correction: Error correction level

        Returns:
            True if data can be encoded, False otherwise
        """
        try:
            qr = self.generate_qr(data, error_correction=error_correction)
            return qr.version is not None
        except Exception:
            return False

    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about supported output formats and their options.

        Returns:
            Dictionary containing format information and available options
        """
        return {
            'pil': {
                'description': 'Returns a PIL Image object',
                'options': ['fill_color', 'back_color', 'module_drawer', 'color_mask', 'embed_image']
            },
            'png': {
                'description': 'Returns PNG image as bytes',
                'options': ['fill_color', 'back_color', 'module_drawer', 'color_mask', 'embed_image']
            },
            'svg': {
                'description': 'Returns SVG XML as string',
                'options': []
            },
            'bytes': {
                'description': 'Returns image as bytes in specified format',
                'options': ['format', 'fill_color', 'back_color', 'module_drawer', 'color_mask', 'embed_image']
            },
            'file': {
                'description': 'Saves image to file',
                'required': ['file_path'],
                'options': ['fill_color', 'back_color', 'module_drawer', 'color_mask', 'embed_image']
            }
        }

# Singleton instance for easy access
qr_generator = QRCodeGenerator()

def generate_qr(
    data: str,
    output_format: OutputFormat = 'pil',
    **kwargs
) -> Union[Image.Image, bytes, str, None]:
    """
    Convenience function to generate a QR code.

    Args:
        data: Data to encode in the QR code
        output_format: Output format ('pil', 'png', 'svg', 'bytes', 'file')
        **kwargs: Additional arguments passed to QRCodeGenerator.generate()

    Returns:
        QR code in the requested format
    """
    return qr_generator.generate(data, output_format, **kwargs)

def get_qr_metrics(
    data: str,
    error_correction: qrcode.constants.ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_M
) -> Dict[str, Any]:
    """
    Get metrics about the QR code that would be generated.

    Args:
        data: Data to encode
        error_correction: Error correction level

    Returns:
        Dictionary of QR code metrics
    """
    return qr_generator.get_qr_metrics(data, error_correction)

def validate_qr_data(
    data: str,
    error_correction: qrcode.constants.ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_M
) -> bool:
    """
    Validate if data can be encoded in a QR code.

    Args:
        data: Data to validate
        error_correction: Error correction level

    Returns:
        True if data can be encoded, False otherwise
    """
    return qr_generator.validate_data(data, error_correction)

def get_supported_formats() -> Dict[str, Dict[str, Any]]:
    """
    Get information about supported output formats and their options.

    Returns:
        Dictionary containing format information and available options
    """
    return qr_generator.get_supported_formats()

# Predefined module drawers for convenience
SQUARE_DRAWER = SquareModuleDrawer()
GAPPED_SQUARE_DRAWER = GappedSquareModuleDrawer()
CIRCLE_DRAWER = CircleModuleDrawer()
ROUNDED_DRAWER = RoundedModuleDrawer()
VERTICAL_BARS_DRAWER = VerticalBarsDrawer()
HORIZONTAL_BARS_DRAWER = HorizontalBarsDrawer()

# Predefined color masks for convenience
SOLID_FILL_MASK = SolidFillColorMask()
RADIAL_GRADIENT_MASK = RadialGradiantColorMask()
SQUARE_GRADIENT_MASK = SquareGradiantColorMask()
HORIZONTAL_GRADIENT_MASK = HorizontalGradiantColorMask()
VERTICAL_GRADIENT_MASK = VerticalGradiantColorMask()