# JP2Forge Visual Workflow

This document provides visual diagrams of the JP2Forge processing workflows.

## Standard Processing Workflow

```mermaid
flowchart TD
    A[Input Files] --> B[File Processing]
    B --> C{Multi-page TIFF?}
    C -->|Yes| D[Extract Pages]
    C -->|No| E[Process as Single Image]
    D --> F[Process Each Page]
    E --> G[Compress to JP2]
    F --> G
    G --> H[Quality Analysis]
    H --> I[Metadata Handling]
    I --> J[Generate Reports]
    J --> K[Output JP2 Files]
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:1px
    style K fill:#f9f9f9,stroke:#333,stroke-width:1px
    style G fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style I fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style H fill:#fff3e0,stroke:#ff9800,stroke-width:1px
```

## BnF Compliance Workflow

```mermaid
flowchart TD
    A[Input Files] --> B[Document Type Selection]
    B --> C[Set BnF Parameters]
    C --> D[Apply Compression Ratio]
    D --> E[BnF-Compliant JP2 Generation]
    E --> F[Embed BnF Metadata]
    F --> G[Validate BnF Compliance]
    G --> H[Output JP2 Files]
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:1px
    style H fill:#f9f9f9,stroke:#333,stroke-width:1px
    style D fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style F fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style G fill:#fff3e0,stroke:#ff9800,stroke-width:1px
```

## Memory-Efficient Processing

Memory-efficient processing is available in both standard and parallel workflows to handle large images and multi-page TIFFs.

```mermaid
flowchart TD
    A[Input File] --> B[Memory Estimation]
    B --> C{Exceeds Memory Limit?}
    C -->|No| D[Standard Processing]
    C -->|Yes| E[Setup Chunking]
    E --> F[Process in Chunks]
    F --> G[Generate JP2]
    D --> G
    G --> H[Output JP2 File]
    
    C --> |Multi-page TIFF?| I{Check Page Size}
    I -->|All Pages Fit In Memory| J[Process All Pages Sequentially]
    I -->|Some Pages Too Large| K[Process Large Pages in Chunks]
    J --> L[Combine Results]
    K --> L
    L --> H
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:1px
    style H fill:#f9f9f9,stroke:#333,stroke-width:1px
    style E fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style F fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style G fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style K fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
```

### Memory-Efficient Configuration Options

The memory-efficient processing can be controlled with these configuration parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--memory-limit-mb` | Maximum memory to use (MB) | 4096 |
| `--chunk-size` | Chunk size in pixels | 1000000 |
| `--force-chunking` | Force chunked processing | False |
| `--min-chunk-height` | Minimum chunk height | 32 |

## Parallel Processing Workflow

```mermaid
flowchart TD
    A[Input Directory] --> B[Resource Monitoring]
    B --> C[Create Worker Pool]
    C --> D[Distribute Work]
    D --> E[Worker 1]
    D --> F[Worker 2]
    D --> G[Worker N]
    E --> E1{Large File?}
    F --> F1{Large File?}
    G --> G1{Large File?}
    E1 -->|Yes| E2[Memory-Efficient Processing]
    E1 -->|No| E3[Standard Processing]
    F1 -->|Yes| F2[Memory-Efficient Processing]
    F1 -->|No| F3[Standard Processing]
    G1 -->|Yes| G2[Memory-Efficient Processing]
    G1 -->|No| G3[Standard Processing]
    E2 --> H[Results Collection]
    E3 --> H
    F2 --> H
    F3 --> H
    G2 --> H
    G3 --> H
    H --> I[Generate Summary Report]
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:1px
    style I fill:#f9f9f9,stroke:#333,stroke-width:1px
    style C fill:#bbdefb,stroke:#1976d2,stroke-width:1px
    style D fill:#bbdefb,stroke:#1976d2,stroke-width:1px
    style E fill:#bbdefb,stroke:#1976d2,stroke-width:1px
    style F fill:#bbdefb,stroke:#1976d2,stroke-width:1px
    style G fill:#bbdefb,stroke:#1976d2,stroke-width:1px
    style E2 fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style F2 fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style G2 fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
```