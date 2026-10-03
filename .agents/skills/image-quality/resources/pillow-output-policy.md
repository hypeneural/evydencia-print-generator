# Pillow output references

Official docs validated 2026-10-03.

- `ImageOps.exif_transpose` applies EXIF orientation and removes the orientation tag from the result.
  https://pillow.readthedocs.io/en/stable/reference/ImageOps.html
- `Resampling.LANCZOS` is a high-quality resize filter.
  https://pillow.readthedocs.io/en/latest/handbook/concepts.html
- JPEG quality is documented up to 95 as the useful best-quality range; values above 95 should be avoided because 100 greatly increases size for little gain.
- JPEG supports explicit DPI, ICC profile and chroma subsampling including 4:4:4.
  https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html

Project defaults may only become production policy after a physical/lab validation.
