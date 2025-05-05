# JP2Forge Technical Glossary

This glossary provides definitions for technical terms used throughout the JP2Forge documentation.

## JPEG2000 Terminology

| Term | Definition |
|------|------------|
| **JP2** | The file format for JPEG2000 images, with extension `.jp2` |
| **Codestream** | The compressed image data within a JP2 file |
| **Tile** | A rectangular region of the image that is independently encoded |
| **Component** | A color channel (e.g., R, G, B) in the image |
| **Resolution level** | A specific scale at which the image can be decoded |
| **Precinct** | A spatial region of the codestream used for organizing packets |
| **Code-block** | The fundamental unit for entropy coding |
| **Progression order** | The order in which compressed data is organized (LRCP, RLCP, RPCL, PCRL, CPRL) |
| **UUID Box** | Container for storing metadata within the JP2 file format |

## BnF Compliance Terminology

| Term | Definition |
|------|------------|
| **BnF** | Bibliothèque nationale de France - French National Library |
| **BnF compliance** | Adherence to BnF technical specifications for digital preservation |
| **Compression ratio** | Ratio between original and compressed file sizes |
| **Compression ratio tolerance** | Acceptable deviation from target compression ratio |
| **Referential** | BnF's reference document defining technical requirements |

## Image Quality Metrics

| Term | Definition |
|------|------------|
| **PSNR** | Peak Signal-to-Noise Ratio - Measures image quality (higher is better) |
| **SSIM** | Structural Similarity Index - Measures perceived quality (higher is better) |
| **MSE** | Mean Square Error - Average of squared differences between original and compressed pixels |

## Processing Terminology

| Term | Definition |
|------|------------|
| **Chunking** | Processing large images in smaller pieces to manage memory usage |
| **Streaming processor** | Component that processes images in a memory-efficient way |
| **Memory mapping** | Technique for accessing files without loading them entirely into memory |
| **Adaptive worker pool** | System that adjusts the number of worker threads based on system resources |
| **Memory-efficient processing** | Techniques to minimize memory usage during image processing |

## Document Types

| Term | Definition |
|------|------------|
| **Photograph** | Standard photographic images (default compression ratio: 4:1) |
| **Heritage document** | Historical documents with high-quality settings (compression ratio: 4:1) |
| **Color** | General color images (compression ratio: 6:1) |
| **Grayscale** | Grayscale images (compression ratio: 16:1) |

## Compression Modes

| Term | Definition |
|------|------------|
| **Supervised** | Quality-controlled compression with analysis |
| **Lossless** | Compression without loss of information |
| **Lossy** | Compression that discards some information |
| **BnF compliant** | Compression following BnF technical specifications |

## Metadata Terminology

| Term | Definition |
|------|------------|
| **XMP** | Extensible Metadata Platform - Adobe's standard for metadata |
| **Exif** | Exchangeable Image File Format - Standard for metadata in images |
| **ExifTool** | External program used for reading and writing metadata |
| **Metadata embedding** | Process of adding metadata to JP2 files |
| **UUID box** | Container for XMP metadata in JP2 files |

## JP2Forge-specific Terms

| Term | Definition |
|------|------------|
| **Workflow** | The sequence of operations performed on an image |
| **Standard workflow** | Sequential processing of individual files |
| **Parallel workflow** | Concurrent processing of multiple files |
| **BnF mode** | Processing configuration that follows BnF specifications |
| **Normal mode** | Standard processing without BnF compliance |