# JP2Forge Architecture Documentation

## 1. System Overview

JP2Forge is a comprehensive image processing system designed to convert standard image formats to JPEG2000 with specialized support for BnF (Bibliothèque nationale de France) compliance. The architecture follows a modular design that separates concerns between core functionality, workflow orchestration, and utility components.

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       CLI Layer                          │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Workflow Layer                        │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ BaseWorkflow  │  │StandardWrkflw│  │ParallelWrkflw│  │
│  └───────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└──────────┼────────────────┼────────────────┼────────────┘
           │                │                │
           ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                      Core Layer                          │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │  Compressor  │  │  Analyzer   │  │  Metadata      │  │
│  │              │  │             │  │  ├─BaseHandler │  │
│  │              │  │             │  │  └─BnFHandler  │  │
│  └──────────────┘  └─────────────┘  └────────────────┘  │
│  ┌──────────────┐                                       │
│  │ TIFFHandler  │                                       │
│  └──────────────┘                                       │
└────────────┬────────────┬────────────────┬──────────────┘
             │            │                │
             ▼            ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                    Utilities Layer                       │
│  ┌───────────┐ ┌──────────┐ ┌───────┐ ┌───────────────┐ │
│  │Configuration│ │  XML    │ │Imaging│ │ Parallel Proc.│ │
│  └───────────┘ └──────────┘ └───────┘ └───────────────┘ │
│  ┌───────────┐ ┌──────────┐ ┌───────────────────────┐  │
│  │Color Prof.│ │Tool Mgr. │ │Resource Monitoring    │  │
│  └───────────┘ └──────────┘ └───────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Key Components

The system is organized into several logical layers:

1. **CLI Layer**: Provides command-line interface for user interaction
2. **Workflow Layer**: Orchestrates the processing pipeline
3. **Core Layer**: Implements the core JPEG2000 conversion functionality
4. **Utilities Layer**: Provides supporting functionality across the system

## 2. Data Flow

### 2.1 Standard Workflow Data Flow

```
┌─────────────┐      ┌───────────────┐     ┌───────────────┐    ┌───────────────┐
│ Input Image ├─────►│ Pre-processing├────►│  Compression  ├───►│Quality Analysis│
└─────────────┘      └───────────────┘     └───────────────┘    └───────┬───────┘
                                                                        │
┌───────────────┐    ┌───────────────┐     ┌───────────────┐    ┌──────▼────────┐
│Final JP2 Image│◄───┤Metadata Inject.│◄────┤  Validation   │◄───┤Decision Logic │
└───────────────┘    └───────────────┘     └───────────────┘    └───────────────┘
```

### 2.2 BnF Workflow Data Flow

```
┌─────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Input Image ├───►│Color Profile  ├───►│  Compression  ├───►│Ratio Validation│
└─────────────┘    │  Handling     │    │  (Kakadu)     │    └───────┬───────┘
                   └───────────────┘    └───────────────┘            │
                                                                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌────────────┐
│Final JP2 Image│◄───┤ XMP Metadata  │◄───┤BnF Compliance │◄───┤Compression │
└───────────────┘    │  Injection    │    │  Validation   │    │  Decision  │
                     └───────────────┘    └───────────────┘    └────────────┘
```

### 2.3 Multi-page TIFF Workflow Data Flow

```
┌─────────────┐    ┌───────────────┐    ┌──────────────────┐    ┌───────────────┐
│ Multi-page  ├───►│ TIFF Handler  ├───►│  Page Extraction ├───►│ Page Iteration │
│    TIFF     │    │               │    │                  │    └───────┬───────┘
└─────────────┘    └───────────────┘    └──────────────────┘            │
                                                                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Page Results  │◄───┤ Process Each  │◄───┤Standard or BnF │◄───┤Configuration  │
│ Collection    │    │     Page      │    │   Workflow     │    │   Options     │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

### 2.4 Parallel Processing Data Flow

```
                     ┌────────────────────┐
                     │  Input Directory   │
                     └──────────┬─────────┘
                                │
                                ▼
┌──────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│Resource      │◄────┤ Adaptive Worker Pool├────►│Progress Tracker │
│Monitor       │     └────────────┬────────┘     └─────────────────┘
└──────────────┘                  │
                                  ▼
                     ┌─────────────────────┐
                     │   Work Distribution │
                     └─────────┬───────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
      ┌────────────────┐┌────────────────┐┌────────────────┐
      │Worker Thread 1 ││Worker Thread 2 ││Worker Thread N │
      └───────┬────────┘└───────┬────────┘└───────┬────────┘
              │                 │                 │
              ▼                 ▼                 ▼
      ┌────────────────┐┌────────────────┐┌────────────────┐
      │Standard Workflow││Standard Workflow││Standard Workflow│
      └───────┬────────┘└───────┬────────┘└───────┬────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │Results Aggregation│
                      └───────────────────┘
```

## 3. Component Descriptions

### 3.1 Core Components

#### 3.1.1 Compressor

The Compressor module handles the actual image conversion to JPEG2000 format:

- Supports both lossless and lossy compression
- Implements BnF-specific compression requirements
- Handles advanced JPEG2000 parameters (resolution levels, progression order, etc.)
- Integrates with external tools like Kakadu when available

Key Classes:
- `core.compressor.JP2Compressor`: Main compression implementation
- `core.compressor.BnFCompressor`: BnF-compliant compression implementation

#### 3.1.2 Analyzer

The Analyzer module performs quality assessment of compressed images:

- Calculates PSNR (Peak Signal-to-Noise Ratio)
- Computes SSIM (Structural Similarity Index)
- Measures MSE (Mean Square Error)
- Validates compression ratios for BnF compliance

Key Classes:
- `core.analyzer.QualityAnalyzer`: Implements quality metric calculations
- `core.analyzer.CompressionRatioValidator`: Validates BnF compression ratios

#### 3.1.3 Metadata

The Metadata module handles metadata embedding in JPEG2000 files:

- Supports XMP metadata injection
- Implements BnF-specific metadata requirements
- Ensures proper XML handling and namespace management
- Validates metadata according to specifications

Key Classes:
- `core.metadata.base_handler.MetadataHandler`: Base metadata handling implementation
- `core.metadata.bnf_handler.BnFMetadataHandler`: BnF-specific metadata implementation
- `core.metadata.xmp_utils`: Utilities for XMP metadata handling

#### 3.1.4 TIFF Handler

The TIFF Handler module is responsible for managing multi-page TIFF files:

- Detects multi-page TIFF files automatically
- Extracts individual pages from multi-page TIFFs
- Manages page numbering and naming conventions
- Applies memory-efficient processing for large files
- Handles metadata tagging with page information

Key Classes:
- `core.tiff_handler.TIFFHandler`: Main implementation for multi-page TIFF processing
- `core.tiff_handler.PageExtractor`: Handles the extraction of individual pages from TIFF
- `core.tiff_handler.TIFFMetadataManager`: Manages page-specific metadata

### 3.2 Workflow Components

#### 3.2.1 BaseWorkflow

The BaseWorkflow provides the foundation for all workflow implementations:

- Defines the common workflow interface
- Handles configuration and parameter validation
- Implements logging and error handling
- Provides progress reporting infrastructure

#### 3.2.2 StandardWorkflow

The StandardWorkflow implements the standard image processing pipeline:

- Orchestrates the core components for single-image processing
- Implements quality-based decision logic
- Handles metadata injection
- Manages temporary files and cleanup

#### 3.2.3 ParallelWorkflow

The ParallelWorkflow extends the standard workflow for batch processing:

- Manages parallel execution of multiple image conversions
- Implements resource-aware work distribution
- Provides progress tracking and ETA estimation
- Handles results aggregation and reporting

### 3.3 Utility Components

#### 3.3.1 Configuration

The Configuration system manages application settings:

- Supports hierarchical configuration
- Implements schema validation
- Handles multiple configuration sources (files, environment variables)
- Provides defaults and fallbacks

Key Classes:
- `utils.config.config_manager.ConfigManager`: Main configuration management
- `utils.config.config_schema.ConfigSchema`: Configuration schema validation

#### 3.3.2 XML Processing

The XML utilities handle proper XML generation and parsing:

- Manages XML namespaces
- Ensures proper XML escaping and formatting
- Validates XML against schemas
- Implements XMP-specific functionality

Key Classes:
- `utils.xml.namespace_registry.NamespaceRegistry`: Manages XML namespaces
- `utils.xml.xmp_manager.XMPManager`: Handles XMP metadata generation

#### 3.3.3 Imaging

The Imaging utilities provide advanced image processing capabilities:

- Implements streaming image processing for large images
- Provides memory usage estimation
- Handles color profile management
- Supports memory-mapped file operations

Key Classes:
- `utils.imaging.streaming_processor.StreamingImageProcessor`: Processes large images
- `utils.imaging.memory_estimator.MemoryEstimator`: Estimates memory requirements

#### 3.3.4 Parallel Processing

The Parallel Processing utilities implement resource-aware parallelism:

- Monitors system resources
- Implements adaptive worker pool
- Provides progress tracking
- Manages work distribution

Key Classes:
- `utils.parallel.adaptive_pool.AdaptiveWorkerPool`: Dynamic worker pool
- `utils.parallel.resource_monitor.ResourceMonitor`: System resource monitoring
- `utils.parallel.progress_tracker.ProgressTracker`: Progress tracking with ETA

#### 3.3.5 External Tool Management

The Tool Management utilities handle external tool integration:

- Detects tool availability
- Provides consistent interfaces
- Implements fallback mechanisms
- Manages tool execution

Key Classes:
- `utils.tools.tool_manager.ToolManager`: Main tool management
- `utils.tools.kakadu_tool.KakaduTool`: Kakadu integration
- `utils.tools.exiftool.ExifTool`: ExifTool integration

## 4. Interactions and Dependencies

### 4.1 Component Interaction Diagram

```
                 ┌───────────────┐
                 │Configuration  │
                 │   System      │
                 └───┬───────────┘
                     │
                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│CLI Interface  ├──►│   Workflow    ├──►│Tool Management│
└───────────────┘   │   System      │   └───────────────┘
                    └───┬───┬───┬───┘
                        │   │   │
            ┌───────────┘   │   └────────────┐
            │               │                │
            ▼               ▼                ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  Compressor    │  │    Analyzer    │  │   Metadata     │
└────────┬───────┘  └────────┬───────┘  └────────┬───────┘
         │                   │                   │
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                  Utilities Layer                         │
│   (XML, Imaging, Parallel Processing, Resources, etc.)   │
└─────────────────────────────────────────────────────────┘
           ▲
           │
           │
┌────────────────┐
│  TIFF Handler  │
└────────────────┘
```

### 4.2 Key Dependencies

- Workflow components depend on Core components
- Core components depend on Utility components
- Configuration system is used throughout all components
- Parallel processing system integrates with the Workflow system
- External tool management is used by Compressor and Metadata components
- TIFF Handler depends on Imaging utilities for efficient processing

## 5. Extension Points

### 5.1 Workflow Extensions

New workflow types can be created by extending the BaseWorkflow class:

```python
from workflow.base import BaseWorkflow

class CustomWorkflow(BaseWorkflow):
    def process_file(self, input_path):
        # Custom implementation
        pass
```

### 5.2 Compression Strategy Extensions

New compression strategies can be implemented by extending core compression classes:

```python
from core.compressor import JP2Compressor

class CustomCompressor(JP2Compressor):
    def compress(self, input_path, output_path, params):
        # Custom implementation
        pass
```

### 5.3 Metadata Handler Extensions

Custom metadata handling can be implemented by extending the base metadata handler:

```python
from core.metadata.base_handler import MetadataHandler

class CustomMetadataHandler(MetadataHandler):
    def inject_metadata(self, jp2_path, metadata):
        # Custom implementation
        pass
```

### 5.4 Tool Integration Extensions

Support for additional external tools can be added by extending the tool management system:

```python
from utils.tools.tool_manager import ExternalTool

class NewExternalTool(ExternalTool):
    def detect(self):
        # Tool detection logic
        pass
        
    def execute(self, *args, **kwargs):
        # Tool execution logic
        pass
```

### 5.5 Multi-page Format Extensions

Support for additional multi-page formats can be implemented by extending the base page handler:

```python
from core.tiff_handler import MultiPageHandler

class PDFHandler(MultiPageHandler):
    def detect_multi_page(self, file_path):
        # PDF detection logic
        pass
        
    def extract_pages(self, input_path, output_dir):
        # PDF page extraction logic
        pass
```

## 6. Threading and Concurrency Model

JP2Forge uses a carefully designed concurrency model to ensure reliable parallel processing:

### 6.1 Worker Pool

The AdaptiveWorkerPool manages a pool of worker threads that:
- Automatically scales based on system resources
- Prevents resource exhaustion
- Handles work distribution
- Collects results from workers

### 6.2 Resource Monitoring

The ResourceMonitor runs in a dedicated thread to:
- Monitor CPU and memory usage
- Signal the worker pool to scale as needed
- Prevent system overload
- Detect resource constraints

### 6.3 Progress Tracking

The ProgressTracker maintains processing state:
- Tracks completed items
- Estimates remaining time
- Provides progress updates
- Handles status reporting

### 6.4 Synchronization

The system uses various synchronization mechanisms:
- Thread pools for worker management
- Locks for shared resource access
- Queues for work distribution
- Events for signaling between components

## 7. Failure Handling

JP2Forge implements a comprehensive failure handling strategy:

### 7.1 Exception Hierarchy

The system uses a structured exception hierarchy:
- Base exceptions for general errors
- Specialized exceptions for specific error types
- Context-rich exception messages
- Traceback information preservation

### 7.2 Recovery Strategies

Different failure recovery strategies are implemented:
- Automatic retry for transient failures
- Graceful degradation for non-critical components
- Fallback mechanisms for external tool failures
- Safe cleanup of temporary resources

### 7.3 Error Reporting

Failures are reported through multiple channels:
- Detailed logs with context information
- Structured error objects in results
- Progress updates with error counts
- Summary reports with failure analysis

## 8. Performance Considerations

Several design decisions target optimal performance:

### 8.1 Memory Management

- Streaming processing for large images
- Chunk-based processing to control memory usage
- Memory mapping for efficient file access
- Automatic cleanup of temporary resources
- Page-by-page processing for multi-page documents

### 8.2 CPU Utilization

- Adaptive parallel processing based on CPU availability
- Optimal worker count determination
- Work distribution based on estimated complexity
- Process priority management

### 8.3 I/O Optimization

- Minimization of temporary file creation
- Efficient file handling with proper buffering
- Batched metadata operations
- Stream-based processing where possible

## 9. Security Considerations

JP2Forge implements several security measures:

### 9.1 Input Validation

- Thorough validation of all input parameters
- Safe handling of file paths to prevent path traversal
- Sanitization of metadata values
- Protection against malformed input files

### 9.2 External Tool Execution

- Secure execution of external tools
- Proper escaping of command-line arguments
- Controlled environment for subprocess execution
- Validation of external tool outputs

### 9.3 Resource Protection

- Limits on resource consumption
- Timeouts for long-running operations
- Cleanup of temporary files
- Protection against resource exhaustion attacks

## 10. Future Architecture Evolution

The JP2Forge architecture is designed to evolve in several directions:

### 10.1 Planned Extensions

- Web service API for remote processing
- Distributed processing across multiple machines
- Container-based deployment for easy installation
- Integration with workflow management systems

### 10.2 Scalability Improvements

- Enhanced data partitioning for very large datasets
- Improved memory management for extreme size images
- Support for cloud-based processing
- Distributed worker architecture

### 10.3 Feature Roadmap

- Support for additional image formats
- Support for additional multi-page document formats (PDF, DjVu)
- Advanced image pre-processing capabilities
- Enhanced reporting and visualization
- Integration with digital asset management systems
