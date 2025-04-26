# JP2Forge Notation Conventions

## Compression Ratio Notation

There are two common ways to express compression ratios, which can cause confusion:

### BnF Documentation Format (1:N)

In BnF (Bibliothèque nationale de France) documentation, compression ratios are expressed in the format **1:N**, where:
- **1** represents the compressed size
- **N** represents the original size

Examples:
- **1:4** means one part compressed to four parts original
- **1:6** means one part compressed to six parts original
- **1:16** means one part compressed to sixteen parts original

### JP2Forge Implementation Format (N:1)

In JP2Forge code and reports, we use the format **N:1**, where:
- **N** represents the original size
- **1** represents the compressed size

Examples:
- **4:1** or **4.0** means four parts original to one part compressed
- **6:1** or **6.0** means six parts original to one part compressed
- **16:1** or **16.0** means sixteen parts original to one part compressed

Both notations represent the same compression level, just expressed differently.

## Conversion Between Formats

| BnF Format | JP2Forge Format | Document Type       |
|------------|-----------------|---------------------|
| 1:4        | 4:1 or 4.0      | Photograph/Heritage |
| 1:6        | 6:1 or 6.0      | Color               |
| 1:16       | 16:1 or 16.0    | Grayscale           |

## Why We Use N:1 Format

The N:1 format is more common in image processing contexts and matches how compression ratios are typically displayed in file reports (showing by what factor the original is larger than the compressed version).