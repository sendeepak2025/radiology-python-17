# DICOM Viewer Debugging Guide

## Quick 3-Line Summary

**Root Causes:** Async lifecycle race conditions, missing error boundaries, inadequate retry logic, and improper cornerstone initialization sequence.

**Immediate Fix:** Use the corrected `AdvancedDicomViewer_Fixed.tsx` with enhanced initialization flow and debug panel.

**Final Fix Location:** Replace original component with fixed version, ensure proper DICOM service configuration, and implement comprehensive error handling.

## Critical Issues Analysis

### 🔴 Critical Issues

1. **Async Initialization Race Conditions**
   - **Problem:** `useEffect` dependencies causing multiple initialization attempts
   - **Symptoms:** "Initializing DICOM viewer..." hang, inconsistent loading
   - **Code Location:** Main `useEffect` hook in initialization
   - **Fix:** Proper dependency management and mounted ref guards

2. **Missing Error Boundaries**
   - **Problem:** Unhandled promise rejections causing silent failures
   - **Symptoms:** White screen, no error feedback to user
   - **Code Location:** Image loading and element enablement functions
   - **Fix:** Comprehensive try/catch blocks and error state management

3. **Inadequate Element Enablement**
   - **Problem:** No retry logic for cornerstone element enablement failures
   - **Symptoms:** "Element not enabled" errors, viewer not responding
   - **Code Location:** Element enablement without validation
   - **Fix:** Retry logic with exponential backoff and validation

### 🟡 Major Issues

4. **Timeout Handling**
   - **Problem:** No timeout mechanism for image loading
   - **Symptoms:** Indefinite loading states
   - **Code Location:** Image loading promises
   - **Fix:** Promise.race with timeout and proper cleanup

5. **Cleanup on Unmount**
   - **Problem:** Memory leaks and dangling event listeners
   - **Symptoms:** Performance degradation, console errors
   - **Code Location:** Component unmount lifecycle
   - **Fix:** Proper cleanup in useEffect return function

6. **State Management**
   - **Problem:** Inconsistent state updates and race conditions
   - **Symptoms:** UI not reflecting actual viewer state
   - **Code Location:** Multiple setState calls without proper sequencing
   - **Fix:** Centralized state management with proper sequencing

### 🟢 Minor Issues

7. **Debug Information**
   - **Problem:** Insufficient logging for troubleshooting
   - **Symptoms:** Difficult to diagnose issues in production
   - **Code Location:** Throughout component lifecycle
   - **Fix:** Comprehensive debug state and logging

8. **User Feedback**
   - **Problem:** Poor loading state communication
   - **Symptoms:** User confusion about loading progress
   - **Code Location:** Loading UI components
   - **Fix:** Detailed progress indicators and status messages

## Import & Bundling Analysis

### ESM/Bundler Environment (Recommended)

```typescript
// Correct imports for bundler environment
import cornerstone from 'cornerstone-core';
import cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader';
import dicomParser from 'dicom-parser';

// Configure external dependencies
cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
cornerstoneWADOImageLoader.external.dicomParser = dicomParser;

// Configure web workers
cornerstoneWADOImageLoader.configure({
  useWebWorkers: true,
  decodeConfig: {
    convertFloatPixelDataToInt: false,
    use16BitDataType: true
  }
});
```

### Global Script Environment (Alternative)

```html
<!-- Load dependencies in correct order -->
<script src="https://unpkg.com/cornerstone-core@2.6.1/dist/cornerstone.min.js"></script>
<script src="https://unpkg.com/dicom-parser@1.8.21/dist/dicomParser.min.js"></script>
<script src="https://unpkg.com/cornerstone-wado-image-loader@4.13.2/dist/cornerstoneWADOImageLoader.bundle.min.js"></script>

<script>
  // Dependencies are automatically wired in global environment
  // Configure after loading
  cornerstoneWADOImageLoader.configure({
    useWebWorkers: true,
    decodeConfig: {
      convertFloatPixelDataToInt: false
    }
  });
</script>
```

### Dependency Wiring Issues

**Problem:** `cornerstoneWADOImageLoader.external` not available in some module configurations

**Solution 1 - Check and Wire:**
```typescript
if (cornerstoneWADOImageLoader.external) {
  cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
  cornerstoneWADOImageLoader.external.dicomParser = dicomParser;
} else {
  // Use setter-based API if available
  if (cornerstoneWADOImageLoader.setExternalLibraries) {
    cornerstoneWADOImageLoader.setExternalLibraries({
      cornerstone,
      dicomParser
    });
  }
}
```

**Solution 2 - Dynamic Import:**
```typescript
const initializeDependencies = async () => {
  const [cornerstone, dicomParser, wadoLoader] = await Promise.all([
    import('cornerstone-core'),
    import('dicom-parser'),
    import('cornerstone-wado-image-loader')
  ]);
  
  if (wadoLoader.external) {
    wadoLoader.external.cornerstone = cornerstone;
    wadoLoader.external.dicomParser = dicomParser;
  }
  
  return { cornerstone, dicomParser, wadoLoader };
};
```

## Lifecycle & Async Flow

### Corrected Initialization Sequence

1. **Phase 1: Dependency Wiring**
   ```typescript
   // Wire external dependencies
   cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
   cornerstoneWADOImageLoader.external.dicomParser = dicomParser;
   ```

2. **Phase 2: WADO Loader Configuration**
   ```typescript
   // Configure web workers and decode settings
   cornerstoneWADOImageLoader.configure({
     useWebWorkers: true,
     decodeConfig: {
       convertFloatPixelDataToInt: false,
       use16BitDataType: true
     },
     webWorkerPath: workerPath || '/cornerstoneWADOImageLoaderWebWorker.js'
   });
   ```

3. **Phase 3: Element Preparation**
   ```typescript
   // Ensure element is ready and attached to DOM
   if (!element || !element.parentNode) {
     throw new Error('Element not ready');
   }
   ```

4. **Phase 4: Element Enablement with Retry**
   ```typescript
   // Enable with exponential backoff retry
   await enableElementWithRetry(element, maxRetries);
   ```

5. **Phase 5: Image Loading with Timeout**
   ```typescript
   // Load image with timeout protection
   await Promise.race([
     cornerstone.loadAndCacheImage(imageId),
     timeoutPromise(30000)
   ]);
   ```

### Race Condition Prevention

```typescript
// Use mounted ref to prevent state updates after unmount
const mountedRef = useRef(true);

useEffect(() => {
  return () => {
    mountedRef.current = false;
  };
}, []);

// Check before state updates
const safeSetState = (updater) => {
  if (mountedRef.current) {
    setState(updater);
  }
};
```

### Missing .catch() Handling

```typescript
// Before (problematic)
loadImage(imageId).then(handleSuccess);

// After (corrected)
loadImage(imageId)
  .then(handleSuccess)
  .catch(handleError);

// Or with async/await
try {
  await loadImage(imageId);
  handleSuccess();
} catch (error) {
  handleError(error);
}
```

## Error Handling & Logging

### Robust Error Handling Pattern

```typescript
const handleError = useCallback((error: any, context: string, canRetry: boolean = false) => {
  const errorMessage = error instanceof Error ? error.message : String(error);
  const fullError = `${context}: ${errorMessage}`;
  
  // Log with context
  console.error(`❌ [AdvancedDicomViewer] ${fullError}`, {
    error,
    context,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    canRetry
  });
  
  // Update debug state
  setDebugState(prev => ({
    ...prev,
    lastError: fullError,
    timestamp: new Date().toISOString()
  }));
  
  // Update UI state
  setError(fullError);
  setInitState('error');
  
  // Notify parent
  onError?.(fullError);
}, [onError]);
```

### Debug Panel Implementation

```typescript
const [debugState, setDebugState] = useState({
  step: 'Starting initialization',
  timestamp: new Date().toISOString(),
  cornerstoneInitialized: false,
  elementEnabled: false,
  imageLoaded: false,
  retryCount: 0,
  lastError: null
});

const updateDebugState = useCallback((step: string, additionalData = {}) => {
  const timestamp = new Date().toISOString();
  console.log(`🔍 [AdvancedDicomViewer] ${step} at ${timestamp}`);
  
  setDebugState(prev => ({
    ...prev,
    step,
    timestamp,
    ...additionalData
  }));
}, []);
```

### Runtime Probes

```typescript
// Initialization probe
console.log('🚀 [DICOM] Starting initialization', {
  studyUid: study.study_uid,
  patientId: study.patient_id,
  imageUrls: study.image_urls?.length || 0
});

// Element enablement probe
console.log('🔧 [DICOM] Enabling element', {
  element: element.tagName,
  attached: !!element.parentNode,
  dimensions: { width: element.offsetWidth, height: element.offsetHeight }
});

// Image loading probe
console.log('📷 [DICOM] Loading image', {
  imageId,
  cacheSize: cornerstone.imageCache.getCacheInfo(),
  timestamp: Date.now()
});

// Success probe
console.log('✅ [DICOM] Initialization complete', {
  totalTime: Date.now() - startTime,
  viewport: cornerstone.getViewport(element),
  imageCount: imageIds.length
});
```

## Debugging Checklist

### Pre-Flight Checks

- [ ] **Dependencies Loaded**
  ```javascript
  console.log('Cornerstone:', typeof cornerstone);
  console.log('WADO Loader:', typeof cornerstoneWADOImageLoader);
  console.log('DICOM Parser:', typeof dicomParser);
  ```

- [ ] **External Dependencies Wired**
  ```javascript
  console.log('External cornerstone:', cornerstoneWADOImageLoader.external?.cornerstone);
  console.log('External dicomParser:', cornerstoneWADOImageLoader.external?.dicomParser);
  ```

- [ ] **Web Workers Available**
  ```javascript
  console.log('Web Workers supported:', typeof Worker !== 'undefined');
  console.log('Worker path exists:', fetch('/cornerstoneWADOImageLoaderWebWorker.js'));
  ```

### Runtime Checks

- [ ] **Element State**
  ```javascript
  console.log('Element attached:', !!element.parentNode);
  console.log('Element dimensions:', element.offsetWidth, element.offsetHeight);
  console.log('Element enabled:', cornerstone.getEnabledElements().includes(element));
  ```

- [ ] **Image Loading**
  ```javascript
  console.log('Image ID format:', imageId);
  console.log('Cache info:', cornerstone.imageCache.getCacheInfo());
  console.log('Active requests:', /* check network tab */);
  ```

- [ ] **Error States**
  ```javascript
  console.log('Last error:', debugState.lastError);
  console.log('Retry count:', debugState.retryCount);
  console.log('Current state:', initState);
  ```

### Network Debugging

- [ ] **CORS Configuration**
  - Check server CORS headers
  - Verify preflight requests
  - Test with browser dev tools

- [ ] **Image Accessibility**
  ```bash
  curl -I http://localhost:8000/path/to/image.dcm
  ```

- [ ] **Content-Type Headers**
  - Should be `application/dicom` or `application/octet-stream`
  - Check server configuration

## Reproduction Steps

### Scenario 1: "Initializing DICOM viewer..." Hang

1. **Setup:**
   ```bash
   npm start
   # Navigate to viewer page
   ```

2. **Trigger:**
   - Open DICOM viewer component
   - Observe loading state
   - Check browser console for errors

3. **Debug:**
   ```javascript
   // In browser console
   console.log('Cornerstone enabled elements:', cornerstone.getEnabledElements());
   console.log('Image cache:', cornerstone.imageCache.getCacheInfo());
   ```

4. **Expected Fix:**
   - Loading should progress through states
   - Debug panel should show step progression
   - Should complete within 10 seconds

### Scenario 2: Image Loading Timeout

1. **Setup:**
   ```bash
   # Simulate slow network
   # Chrome DevTools > Network > Throttling > Slow 3G
   ```

2. **Trigger:**
   - Load large DICOM image
   - Wait for timeout (30 seconds)

3. **Debug:**
   ```javascript
   // Check network requests
   console.log('Active requests:', performance.getEntriesByType('resource'));
   ```

4. **Expected Fix:**
   - Should show timeout error after 30 seconds
   - Should offer retry option
   - Should not hang indefinitely

### Scenario 3: Element Enablement Failure

1. **Setup:**
   ```javascript
   // Mock cornerstone failure
   const originalEnable = cornerstone.enable;
   cornerstone.enable = () => { throw new Error('Mock failure'); };
   ```

2. **Trigger:**
   - Initialize viewer
   - Observe retry behavior

3. **Debug:**
   ```javascript
   // Check retry attempts
   console.log('Debug state:', debugState);
   ```

4. **Expected Fix:**
   - Should retry 3 times with exponential backoff
   - Should show clear error message after max retries
   - Should not cause infinite loops

### Scenario 4: Memory Leak on Unmount

1. **Setup:**
   ```javascript
   // Monitor memory usage
   console.log('Initial memory:', performance.memory);
   ```

2. **Trigger:**
   - Mount/unmount viewer multiple times
   - Check for memory growth

3. **Debug:**
   ```javascript
   // After each unmount
   console.log('Memory after unmount:', performance.memory);
   console.log('Enabled elements:', cornerstone.getEnabledElements().length);
   ```

4. **Expected Fix:**
   - Memory should not grow significantly
   - No enabled elements should remain
   - No console errors on unmount

## Performance Optimization

### Image Caching Strategy

```typescript
// Configure cache size based on available memory
const configureCache = () => {
  const memoryMB = (performance as any).memory?.usedJSHeapSize / 1024 / 1024 || 512;
  const maxCacheSize = Math.min(memoryMB * 0.3, 1024); // 30% of memory, max 1GB
  
  cornerstone.imageCache.setMaximumSizeBytes(maxCacheSize * 1024 * 1024);
};
```

### Web Worker Configuration

```typescript
// Optimize worker count based on CPU cores
const configureWorkers = () => {
  const workerCount = Math.min(navigator.hardwareConcurrency || 4, 8);
  
  cornerstoneWADOImageLoader.webWorkerManager.initialize({
    maxWebWorkers: workerCount,
    startWebWorkersOnDemand: true,
    webWorkerPath: '/cornerstoneWADOImageLoaderWebWorker.js'
  });
};
```

### Lazy Loading Implementation

```typescript
// Load images on demand
const loadImageOnDemand = useCallback(async (index: number) => {
  if (loadedImages.has(index)) return;
  
  try {
    const imageId = imageIds[index];
    await cornerstone.loadAndCacheImage(imageId);
    setLoadedImages(prev => new Set([...prev, index]));
  } catch (error) {
    console.warn(`Failed to preload image ${index}:`, error);
  }
}, [imageIds, loadedImages]);
```

## Security Considerations

### HIPAA Compliance

```typescript
// Sanitize logs for HIPAA compliance
const sanitizeForLogging = (data: any) => {
  const sanitized = { ...data };
  
  // Remove PII
  delete sanitized.patientName;
  delete sanitized.patientId;
  delete sanitized.studyDescription;
  
  // Hash identifiers
  if (sanitized.studyUid) {
    sanitized.studyUid = hashString(sanitized.studyUid);
  }
  
  return sanitized;
};

// Use in logging
console.log('DICOM event:', sanitizeForLogging(eventData));
```

### Secure Image Loading

```typescript
// Validate image URLs
const validateImageUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url);
    
    // Only allow specific protocols
    if (!['http:', 'https:', 'wadouri:'].includes(parsed.protocol)) {
      return false;
    }
    
    // Validate domain whitelist
    const allowedDomains = ['localhost', 'your-dicom-server.com'];
    if (!allowedDomains.includes(parsed.hostname)) {
      return false;
    }
    
    return true;
  } catch {
    return false;
  }
};
```

## Troubleshooting Common Issues

### Issue: "cornerstone is not defined"
**Solution:** Ensure proper import order and dependency wiring

### Issue: "Failed to fetch" errors
**Solution:** Check CORS configuration and network connectivity

### Issue: Images appear corrupted
**Solution:** Verify DICOM file format and transfer syntax support

### Issue: Memory usage grows over time
**Solution:** Implement proper cache management and cleanup

### Issue: Slow image loading
**Solution:** Enable web workers and optimize cache configuration

### Issue: Touch/mobile interactions not working
**Solution:** Configure touch event handlers and viewport scaling

This debugging guide provides comprehensive coverage of common DICOM viewer issues and their solutions. Use the checklist systematically to identify and resolve problems efficiently.