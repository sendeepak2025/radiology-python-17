# DICOM Viewer Import & Bundling Analysis

## Executive Summary

This document provides comprehensive analysis and solutions for importing and bundling DICOM-related libraries in both modern ESM/bundler environments and legacy global script environments. The analysis covers cornerstone-core, cornerstone-wado-image-loader, and dicom-parser integration patterns.

## Current Environment Analysis

### Detected Configuration

Based on the codebase structure, you're using:
- **Build System:** Create React App / Webpack
- **Module System:** ES Modules (ESM)
- **TypeScript:** Yes
- **Package Manager:** npm
- **Target Environment:** Modern browsers with bundler support

### Dependency Versions

Recommended versions for compatibility:
```json
{
  "cornerstone-core": "^2.6.1",
  "cornerstone-wado-image-loader": "^4.13.2",
  "dicom-parser": "^1.8.21",
  "cornerstone-tools": "^6.0.10"
}
```

## Import Patterns Analysis

### ✅ Correct ESM/Bundler Pattern (Recommended)

```typescript
// File: src/services/dicomService.ts
import cornerstone from 'cornerstone-core';
import cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader';
import dicomParser from 'dicom-parser';

// Type definitions (if using TypeScript)
import type { EnabledElement, Viewport, Image } from 'cornerstone-core';

class DicomService {
  private initialized = false;
  
  async initialize(): Promise<void> {
    if (this.initialized) return;
    
    try {
      // Wire external dependencies
      if (cornerstoneWADOImageLoader.external) {
        cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
        cornerstoneWADOImageLoader.external.dicomParser = dicomParser;
      } else {
        // Fallback for different module configurations
        this.wireExternalDependencies();
      }
      
      // Configure WADO loader
      cornerstoneWADOImageLoader.configure({
        useWebWorkers: true,
        decodeConfig: {
          convertFloatPixelDataToInt: false,
          use16BitDataType: true
        },
        webWorkerPath: '/cornerstoneWADOImageLoaderWebWorker.js'
      });
      
      // Initialize web workers
      const maxWebWorkers = Math.min(navigator.hardwareConcurrency || 4, 8);
      cornerstoneWADOImageLoader.webWorkerManager.initialize({
        maxWebWorkers,
        startWebWorkersOnDemand: true
      });
      
      this.initialized = true;
      console.log('✅ DICOM service initialized successfully');
      
    } catch (error) {
      console.error('❌ Failed to initialize DICOM service:', error);
      throw new Error(`DICOM service initialization failed: ${error.message}`);
    }
  }
  
  private wireExternalDependencies(): void {
    // Alternative wiring methods for different module configurations
    const loader = cornerstoneWADOImageLoader as any;
    
    // Method 1: Direct assignment
    if (loader.setExternalLibraries) {
      loader.setExternalLibraries({
        cornerstone,
        dicomParser
      });
      return;
    }
    
    // Method 2: Global assignment (for UMD builds)
    if (typeof window !== 'undefined') {
      (window as any).cornerstone = cornerstone;
      (window as any).dicomParser = dicomParser;
    }
    
    // Method 3: Module-level assignment
    try {
      Object.assign(loader, {
        cornerstone,
        dicomParser
      });
    } catch (error) {
      console.warn('Could not wire external dependencies:', error);
    }
  }
}

export const dicomService = new DicomService();
```

### ❌ Problematic Patterns to Avoid

```typescript
// DON'T: Dynamic imports without proper error handling
import('cornerstone-core').then(cornerstone => {
  // This can cause race conditions
});

// DON'T: Mixing import styles
import cornerstone from 'cornerstone-core';
const wadoLoader = require('cornerstone-wado-image-loader'); // Mixed syntax

// DON'T: Assuming external object exists
cornerstoneWADOImageLoader.external.cornerstone = cornerstone; // May throw

// DON'T: Global pollution in modules
window.cornerstone = cornerstone; // Avoid in ESM environment
```

## Bundler Configuration

### Webpack Configuration (Create React App)

```javascript
// File: craco.config.js (if using CRACO)
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Handle cornerstone web workers
      webpackConfig.module.rules.push({
        test: /cornerstoneWADOImageLoaderWebWorker\.js$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
              outputPath: 'workers/'
            }
          }
        ]
      });
      
      // Handle DICOM files
      webpackConfig.module.rules.push({
        test: /\.dcm$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
              outputPath: 'dicom/'
            }
          }
        ]
      });
      
      return webpackConfig;
    }
  }
};
```

### Vite Configuration

```javascript
// File: vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  define: {
    global: 'globalThis'
  },
  optimizeDeps: {
    include: [
      'cornerstone-core',
      'cornerstone-wado-image-loader',
      'dicom-parser'
    ]
  },
  worker: {
    format: 'es'
  },
  assetsInclude: ['**/*.dcm']
});
```

## Web Worker Integration

### Worker File Setup

```typescript
// File: public/cornerstoneWADOImageLoaderWebWorker.js
// This file should be copied from node_modules/cornerstone-wado-image-loader/dist/
// Or served from a CDN

// Option 1: Copy during build
// Add to package.json scripts:
// "postinstall": "cp node_modules/cornerstone-wado-image-loader/dist/cornerstoneWADOImageLoaderWebWorker.js public/"

// Option 2: Serve from CDN
const WORKER_CDN_URL = 'https://unpkg.com/cornerstone-wado-image-loader@4.13.2/dist/cornerstoneWADOImageLoaderWebWorker.js';
```

### Dynamic Worker Loading

```typescript
// File: src/utils/workerUtils.ts
export const getWorkerPath = (): string => {
  // Check if worker exists in public folder
  const localWorkerPath = '/cornerstoneWADOImageLoaderWebWorker.js';
  
  // Fallback to CDN if local worker not available
  const cdnWorkerPath = 'https://unpkg.com/cornerstone-wado-image-loader@4.13.2/dist/cornerstoneWADOImageLoaderWebWorker.js';
  
  return process.env.NODE_ENV === 'development' ? localWorkerPath : cdnWorkerPath;
};

export const checkWorkerAvailability = async (workerPath: string): Promise<boolean> => {
  try {
    const response = await fetch(workerPath, { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
};
```

## Environment-Specific Solutions

### Development Environment

```typescript
// File: src/config/dicom.dev.ts
export const developmentConfig = {
  useWebWorkers: true,
  webWorkerPath: '/cornerstoneWADOImageLoaderWebWorker.js',
  decodeConfig: {
    convertFloatPixelDataToInt: false,
    use16BitDataType: true
  },
  // Enable verbose logging in development
  enableLogging: true,
  // Use local DICOM server
  dicomServerUrl: 'http://localhost:8000'
};
```

### Production Environment

```typescript
// File: src/config/dicom.prod.ts
export const productionConfig = {
  useWebWorkers: true,
  webWorkerPath: 'https://cdn.jsdelivr.net/npm/cornerstone-wado-image-loader@4.13.2/dist/cornerstoneWADOImageLoaderWebWorker.js',
  decodeConfig: {
    convertFloatPixelDataToInt: false,
    use16BitDataType: true
  },
  // Disable logging in production
  enableLogging: false,
  // Use production DICOM server
  dicomServerUrl: process.env.REACT_APP_DICOM_SERVER_URL
};
```

### Test Environment

```typescript
// File: src/config/dicom.test.ts
export const testConfig = {
  useWebWorkers: false, // Disable workers in tests
  webWorkerPath: '',
  decodeConfig: {
    convertFloatPixelDataToInt: false,
    use16BitDataType: false // Simpler config for tests
  },
  enableLogging: false,
  // Use mock server
  dicomServerUrl: 'http://localhost:3001'
};
```

## Legacy Global Script Support

### HTML Template for Global Scripts

```html
<!-- File: public/dicom-global.html -->
<!DOCTYPE html>
<html>
<head>
  <title>DICOM Viewer - Global Scripts</title>
  
  <!-- Load dependencies in correct order -->
  <script src="https://unpkg.com/cornerstone-core@2.6.1/dist/cornerstone.min.js"></script>
  <script src="https://unpkg.com/dicom-parser@1.8.21/dist/dicomParser.min.js"></script>
  <script src="https://unpkg.com/cornerstone-wado-image-loader@4.13.2/dist/cornerstoneWADOImageLoader.bundle.min.js"></script>
  
  <script>
    // Configure after all scripts load
    window.addEventListener('load', function() {
      // Dependencies are automatically wired in global environment
      cornerstoneWADOImageLoader.configure({
        useWebWorkers: true,
        decodeConfig: {
          convertFloatPixelDataToInt: false
        },
        webWorkerPath: 'https://unpkg.com/cornerstone-wado-image-loader@4.13.2/dist/cornerstoneWADOImageLoaderWebWorker.js'
      });
      
      console.log('Global DICOM environment ready');
    });
  </script>
</head>
<body>
  <div id="dicom-viewer" style="width: 512px; height: 512px;"></div>
  
  <script>
    // Example usage in global environment
    function initializeViewer() {
      const element = document.getElementById('dicom-viewer');
      
      // Enable the element
      cornerstone.enable(element);
      
      // Load and display image
      const imageId = 'wadouri:https://example.com/sample.dcm';
      cornerstone.loadImage(imageId).then(function(image) {
        cornerstone.displayImage(element, image);
      });
    }
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', initializeViewer);
  </script>
</body>
</html>
```

### Hybrid Support Component

```typescript
// File: src/components/DICOM/HybridDicomViewer.tsx
import React, { useEffect, useRef, useState } from 'react';

// Conditional imports based on environment
let cornerstone: any;
let cornerstoneWADOImageLoader: any;
let dicomParser: any;

if (typeof window !== 'undefined' && (window as any).cornerstone) {
  // Global environment
  cornerstone = (window as any).cornerstone;
  cornerstoneWADOImageLoader = (window as any).cornerstoneWADOImageLoader;
  dicomParser = (window as any).dicomParser;
} else {
  // Module environment
  try {
    cornerstone = require('cornerstone-core');
    cornerstoneWADOImageLoader = require('cornerstone-wado-image-loader');
    dicomParser = require('dicom-parser');
  } catch (error) {
    console.error('Failed to load DICOM modules:', error);
  }
}

interface HybridDicomViewerProps {
  imageId: string;
  onReady?: () => void;
  onError?: (error: string) => void;
}

const HybridDicomViewer: React.FC<HybridDicomViewerProps> = ({
  imageId,
  onReady,
  onError
}) => {
  const elementRef = useRef<HTMLDivElement>(null);
  const [isGlobalEnv, setIsGlobalEnv] = useState(false);
  
  useEffect(() => {
    // Detect environment
    const globalEnv = typeof window !== 'undefined' && (window as any).cornerstone;
    setIsGlobalEnv(!!globalEnv);
    
    if (!cornerstone) {
      onError?.('Cornerstone not available in current environment');
      return;
    }
    
    const initializeViewer = async () => {
      try {
        if (!elementRef.current) return;
        
        // Wire dependencies if in module environment
        if (!isGlobalEnv && cornerstoneWADOImageLoader.external) {
          cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
          cornerstoneWADOImageLoader.external.dicomParser = dicomParser;
        }
        
        // Enable element
        cornerstone.enable(elementRef.current);
        
        // Load and display image
        const image = await cornerstone.loadImage(imageId);
        cornerstone.displayImage(elementRef.current, image);
        
        onReady?.();
        
      } catch (error) {
        onError?.(error.message);
      }
    };
    
    initializeViewer();
    
    return () => {
      if (elementRef.current && cornerstone) {
        try {
          cornerstone.disable(elementRef.current);
        } catch (error) {
          console.warn('Error disabling element:', error);
        }
      }
    };
  }, [imageId, isGlobalEnv, onReady, onError]);
  
  return (
    <div>
      <div 
        ref={elementRef} 
        style={{ width: '100%', height: '400px', backgroundColor: '#000' }}
      />
      <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
        Environment: {isGlobalEnv ? 'Global Scripts' : 'ES Modules'}
      </div>
    </div>
  );
};

export default HybridDicomViewer;
```

## TypeScript Configuration

### Type Definitions

```typescript
// File: src/types/cornerstone.d.ts
declare module 'cornerstone-core' {
  export interface EnabledElement {
    element: HTMLElement;
    image?: Image;
    viewport?: Viewport;
    canvas?: HTMLCanvasElement;
    invalid: boolean;
    needsRedraw: boolean;
  }
  
  export interface Viewport {
    scale: number;
    translation: { x: number; y: number };
    voi: {
      windowWidth: number;
      windowCenter: number;
    };
    invert: boolean;
    pixelReplication: boolean;
    rotation: number;
    hflip: boolean;
    vflip: boolean;
  }
  
  export interface Image {
    imageId: string;
    minPixelValue: number;
    maxPixelValue: number;
    slope: number;
    intercept: number;
    windowCenter: number;
    windowWidth: number;
    render: any;
    getPixelData: () => Uint8Array | Uint16Array | Int16Array | Float32Array;
    rows: number;
    columns: number;
    height: number;
    width: number;
    color: boolean;
    columnPixelSpacing: number;
    rowPixelSpacing: number;
    invert: boolean;
    sizeInBytes: number;
  }
  
  export function enable(element: HTMLElement): void;
  export function disable(element: HTMLElement): void;
  export function displayImage(element: HTMLElement, image: Image, viewport?: Partial<Viewport>): void;
  export function loadImage(imageId: string): Promise<Image>;
  export function loadAndCacheImage(imageId: string): Promise<Image>;
  export function getViewport(element: HTMLElement): Viewport;
  export function setViewport(element: HTMLElement, viewport: Partial<Viewport>): void;
  export function resize(element: HTMLElement, forcedResize?: boolean): void;
  export function reset(element: HTMLElement): void;
  export function getEnabledElements(): EnabledElement[];
  export function getEnabledElement(element: HTMLElement): EnabledElement;
  
  export const imageCache: {
    getCacheInfo(): any;
    setMaximumSizeBytes(bytes: number): void;
    purgeCache(): void;
  };
  
  export const events: {
    IMAGE_RENDERED: string;
    NEW_IMAGE: string;
    PRE_RENDER: string;
  };
}

declare module 'cornerstone-wado-image-loader' {
  export interface External {
    cornerstone: any;
    dicomParser: any;
  }
  
  export interface DecodeConfig {
    convertFloatPixelDataToInt?: boolean;
    use16BitDataType?: boolean;
  }
  
  export interface Config {
    useWebWorkers?: boolean;
    decodeConfig?: DecodeConfig;
    webWorkerPath?: string;
  }
  
  export const external: External;
  export function configure(config: Config): void;
  
  export const webWorkerManager: {
    initialize(config?: { maxWebWorkers?: number; startWebWorkersOnDemand?: boolean }): void;
    terminate(): void;
  };
}

declare module 'dicom-parser' {
  export interface DataSet {
    byteArray: Uint8Array;
    elements: { [tag: string]: any };
    string(tag: string): string | undefined;
    uint16(tag: string): number | undefined;
    int16(tag: string): number | undefined;
    uint32(tag: string): number | undefined;
    int32(tag: string): number | undefined;
    float(tag: string): number | undefined;
    double(tag: string): number | undefined;
    numStringValues(tag: string): number;
    floatString(tag: string): string | undefined;
    intString(tag: string): string | undefined;
  }
  
  export function parseDicom(byteArray: Uint8Array, options?: any): DataSet;
}
```

### TSConfig Updates

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": [
      "dom",
      "dom.iterable",
      "es6",
      "webworker"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "typeRoots": [
      "node_modules/@types",
      "src/types"
    ]
  },
  "include": [
    "src",
    "src/types"
  ]
}
```

## Performance Optimization

### Code Splitting

```typescript
// File: src/components/DICOM/LazyDicomViewer.tsx
import React, { lazy, Suspense } from 'react';
import { CircularProgress, Box } from '@mui/material';

// Lazy load the DICOM viewer to reduce initial bundle size
const AdvancedDicomViewer = lazy(() => 
  import('./AdvancedDicomViewer_Fixed').then(module => ({
    default: module.default
  }))
);

// Lazy load DICOM dependencies
const loadDicomDependencies = lazy(() => 
  Promise.all([
    import('cornerstone-core'),
    import('cornerstone-wado-image-loader'),
    import('dicom-parser')
  ]).then(([cornerstone, wadoLoader, dicomParser]) => ({
    default: { cornerstone, wadoLoader, dicomParser }
  }))
);

interface LazyDicomViewerProps {
  study: any;
  onReady?: () => void;
  onError?: (error: string) => void;
}

const LazyDicomViewer: React.FC<LazyDicomViewerProps> = (props) => {
  return (
    <Suspense 
      fallback={
        <Box 
          display="flex" 
          justifyContent="center" 
          alignItems="center" 
          height="400px"
        >
          <CircularProgress />
        </Box>
      }
    >
      <AdvancedDicomViewer {...props} />
    </Suspense>
  );
};

export default LazyDicomViewer;
```

### Bundle Analysis

```bash
# Analyze bundle size
npm install --save-dev webpack-bundle-analyzer

# Add to package.json scripts
"analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js"

# Run analysis
npm run analyze
```

## Troubleshooting Guide

### Common Import Issues

1. **"Module not found" errors**
   ```bash
   # Install missing dependencies
   npm install cornerstone-core cornerstone-wado-image-loader dicom-parser
   ```

2. **"external is undefined" errors**
   ```typescript
   // Check if external object exists before using
   if (cornerstoneWADOImageLoader.external) {
     cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
   }
   ```

3. **Web worker loading failures**
   ```typescript
   // Verify worker path and accessibility
   const workerExists = await fetch('/cornerstoneWADOImageLoaderWebWorker.js')
     .then(r => r.ok)
     .catch(() => false);
   ```

4. **TypeScript compilation errors**
   ```bash
   # Install type definitions
   npm install --save-dev @types/cornerstone-core
   
   # Or create custom type definitions
   # See TypeScript Configuration section above
   ```

### Environment Detection

```typescript
// File: src/utils/environmentDetection.ts
export const detectEnvironment = () => {
  const isNode = typeof process !== 'undefined' && process.versions?.node;
  const isBrowser = typeof window !== 'undefined';
  const isWebWorker = typeof importScripts === 'function';
  const isGlobalCornerstone = isBrowser && (window as any).cornerstone;
  const isESM = typeof module === 'undefined';
  
  return {
    isNode,
    isBrowser,
    isWebWorker,
    isGlobalCornerstone,
    isESM,
    supportsWebWorkers: isBrowser && typeof Worker !== 'undefined'
  };
};

export const getOptimalImportStrategy = () => {
  const env = detectEnvironment();
  
  if (env.isGlobalCornerstone) {
    return 'global';
  }
  
  if (env.isESM && env.isBrowser) {
    return 'esm';
  }
  
  if (env.isNode) {
    return 'commonjs';
  }
  
  return 'unknown';
};
```

## Migration Guide

### From Global Scripts to ESM

1. **Install npm packages**
   ```bash
   npm install cornerstone-core cornerstone-wado-image-loader dicom-parser
   ```

2. **Replace script tags with imports**
   ```typescript
   // Before (HTML)
   // <script src="cornerstone.min.js"></script>
   
   // After (TypeScript)
   import cornerstone from 'cornerstone-core';
   ```

3. **Update initialization code**
   ```typescript
   // Before (Global)
   cornerstoneWADOImageLoader.configure({...});
   
   // After (ESM)
   cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
   cornerstoneWADOImageLoader.configure({...});
   ```

### From CommonJS to ESM

1. **Update import syntax**
   ```typescript
   // Before (CommonJS)
   const cornerstone = require('cornerstone-core');
   
   // After (ESM)
   import cornerstone from 'cornerstone-core';
   ```

2. **Update export syntax**
   ```typescript
   // Before (CommonJS)
   module.exports = DicomService;
   
   // After (ESM)
   export default DicomService;
   export { DicomService };
   ```

## Best Practices Summary

1. **Always check for external object existence**
2. **Use proper error handling for import failures**
3. **Implement fallback strategies for different environments**
4. **Optimize bundle size with code splitting**
5. **Use TypeScript for better development experience**
6. **Test in multiple environments (dev, prod, test)**
7. **Monitor bundle size and performance impact**
8. **Keep dependencies up to date**
9. **Use CDN fallbacks for web workers**
10. **Implement proper cleanup and memory management**

This comprehensive analysis provides all necessary information for successfully integrating DICOM libraries in various environments and build configurations.