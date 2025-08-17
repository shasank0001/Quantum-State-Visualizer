# Changes to Make in Frontend

Based on the analysis of the current frontend implementation against `frontend_plan.md` and `dev_plane.md`, here are the required changes to fully align with the planned architecture and specifications:

## 1. Missing Core Dependencies & Setup

### 1.1 Package Dependencies
**Status:** ❌ **Missing Critical Dependencies**

**Missing packages that need to be installed:**
- `monaco-editor` or `@monaco-editor/react` - For advanced QASM editor with syntax highlighting
- `reconnecting-websocket` - For robust WebSocket connections as specified in plans
- `react-window` or `react-virtualized` - For virtualized grid rendering for large n (>8 qubits)
- `@types/three` - Already installed ✅

**Action Required:**
```bash
npm install @monaco-editor/react reconnecting-websocket react-window @types/react-window
```

### 1.2 Missing API Integration
**Status:** ❌ **Critical Missing Implementation**

**Current Issue:** `src/lib/api.ts` is completely empty
**Required:** Complete API client implementation with TanStack Query integration

**Missing API Functions:**
- REST API client for `/simulate` endpoint
- WebSocket client for real-time streaming
- Error handling and retry logic
- Request/response type definitions

## 2. EditorPanel Enhancements

### 2.1 Advanced QASM Editor
**Status:** ❌ **Using Basic Textarea Instead of Monaco**

**Current Implementation:** Basic HTML textarea
**Plan Requirement:** Monaco Editor or CodeMirror with syntax highlighting

**Changes Needed:**
- Replace `Textarea` component with Monaco Editor
- Add QASM syntax highlighting
- Implement real-time validation with error indicators
- Add line numbers and code folding

### 2.2 Drag-and-Drop Circuit Builder
**Status:** ❌ **Completely Missing**

**Plan Requirement:** "Graphical editor: Basic drag-and-drop for essential gates"
**Missing Features:**
- Visual circuit builder interface  
- Gate palette (H, X, Y, Z, CNOT, etc.)
- Drag-and-drop functionality
- Circuit-to-QASM conversion

### 2.3 Enhanced Validation
**Status:** ⚠️ **Basic Implementation Only**

**Current:** Simple regex-based validation
**Plan Requirement:** Comprehensive validation including:
- Security validation (gate whitelist)
- Qubit count analysis
- Operation count limits
- Unitary vs non-unitary classification
- Real-time feedback

## 3. Bloch Sphere Rendering Optimizations

### 3.1 Performance Issues for Large n
**Status:** ❌ **Missing Critical Optimizations**

**Plan Requirement:** "For n>8, enable subset selection", "Use virtualized grid"
**Missing Features:**
- Virtualized rendering with `react-window`
- Subset selection dropdown for qubits
- Tabbed groups (Q0-7, Q8-15, etc.)
- Performance monitoring and auto-degradation
- Single Canvas consolidation for WebGL efficiency

### 3.2 Enhanced Bloch Sphere Features
**Status:** ⚠️ **Partially Implemented**

**Missing from Plan:**
- Hover tooltips showing quick rho coordinates
- Dynamic camera synchronization across spheres
- 2D fallback mode for extreme cases (n>16)
- Instanced rendering for shared geometries
- Frameloop optimization ("demand" mode)

### 3.3 Mixedness Visualization
**Status:** ⚠️ **Basic Implementation**

**Current:** Simple translucent ring
**Plan Enhancement:** "translucent shell for mixedness" with proper purity scaling

## 4. WebSocket Integration

### 4.1 Real-Time Communication
**Status:** ❌ **Completely Missing**

**Plan Requirement:** "WebSocket listeners in ControlsBar", "reconnecting WebSocket client"
**Missing Implementation:**
- WebSocket connection management
- Real-time progress updates
- Step-by-step execution support
- Connection error handling
- Automatic reconnection logic

### 4.2 Streaming Features
**Status:** ❌ **Placeholder Only**

**Missing Features:**
- Step-by-step simulation controls
- Real-time state updates
- Progress indicators during simulation
- Background process handling

## 5. State Management Enhancements

### 5.1 Missing Store Features
**Status:** ⚠️ **Partially Complete**

**Plan Requirements Not Implemented:**
- Pipeline progress tracking
- WebSocket connection state
- Performance monitoring state
- URL parameter parsing for shareable links
- Conditioned state view support (stretch goal placeholder)

### 5.2 Store Actions Missing
**Status:** ⚠️ **Basic Actions Only**

**Missing Actions:**
- `updateSimulationProgress()`
- `setWebSocketStatus()`
- `parseUrlParams()` for shareable links
- `applyPerformanceSettings()`

## 6. Inspector Panel Issues

### 6.1 Numerical Display Problems
**Status:** ⚠️ **Inconsistent Implementation**

**Plan Requirement:** "clip tiny negatives in display (e.g., ≤1e-12 shown as 0)"
**Current Issue:** Basic formatting without proper numerical stability

**Required Changes:**
- Implement proper negative clipping
- Consistent 3-decimal precision for purity
- Complex number formatting improvements
- Scientific notation for very small numbers

### 6.2 Missing Inspector Features
**Status:** ❌ **Basic Implementation Only**

**Missing from Plan:**
- Uncertainty indicators (e.g., error ~1/sqrt(S))
- Pipeline badges in inspector
- Copy functionality for matrix elements
- Proper complex number display

## 7. Controls Bar Enhancements

### 7.1 Missing Control Features  
**Status:** ⚠️ **Static Implementation**

**Plan Requirements Missing:**
- Functional speed sliders for animations
- Step/Previous buttons for gate-by-gate execution
- Shots slider for trajectory mode
- Accuracy vs. speed presets
- Pipeline selection controls

### 7.2 Settings Modal
**Status:** ❌ **Completely Missing**

**Plan Requirement:** "Settings modal: Endianness, precision, WebSocket endpoints"
**Missing Features:**
- Settings dialog/modal
- WebSocket endpoint configuration
- Precision settings
- Compact view controls

## 8. Performance & UX Issues

### 8.1 Large Dataset Handling
**Status:** ❌ **No Optimization**

**Plan Requirement:** ">30 FPS on mid-range devices, tested via monitoring tools"
**Missing:**
- Performance monitoring integration
- FPS tracking
- Memory usage monitoring
- Automatic quality degradation

### 8.2 Loading States & Feedback
**Status:** ⚠️ **Basic Loading Only**

**Plan Requirements:**
- Progress indicators with estimated times
- Spinner on spheres during simulation
- Better error states and user feedback
- Toast notifications for actions

## 9. Stretch Goal Placeholders

### 9.1 Step-by-Step Execution
**Status:** ❌ **No Placeholder Implementation**

**Required Placeholders:**
- Step mode flag in store
- WebSocket message handlers for snapshots
- Incremental rendering capability
- Gate-by-gate state tracking

### 9.2 Shareable Links
**Status:** ❌ **No URL Parsing**

**Plan Requirement:** "Parse URL params in App on mount"
**Missing:**
- URL parameter parsing
- Circuit serialization/deserialization
- Link generation functionality

### 9.3 Conditioned View Support
**Status:** ❌ **No Placeholder**

**Required:**
- Condition toggle in UI
- WebSocket condition message support
- Store fields for conditioned outcomes

## 10. Testing Infrastructure

### 10.1 Missing Test Setup
**Status:** ❌ **No Tests Implemented**

**Plan Requirements:**
- Unit tests for components
- Integration tests for data flows  
- Performance monitoring in dev mode
- Golden tests for known circuits

## 11. Implementation Priority

### Phase 1: Critical (Immediate)
1. Install missing dependencies
2. Implement complete API client (`lib/api.ts`)
3. Replace textarea with Monaco Editor
4. Add WebSocket integration basics

### Phase 2: Core Features (Next)
1. Performance optimizations for large n
2. Enhanced numerical display formatting
3. Settings modal implementation
4. Complete controls functionality

### Phase 3: Advanced Features
1. Drag-and-drop circuit builder
2. Virtualized grid rendering
3. Step-by-step execution
4. Performance monitoring

### Phase 4: Polish & Testing
1. Comprehensive test suite
2. Error handling improvements
3. UX enhancements
4. Stretch goal placeholders

## Summary

**Current Completion Status:** ~60% of planned features implemented
**Critical Missing:** API integration, Monaco editor, WebSocket support, performance optimizations
**Architecture Status:** ✅ Good foundation with proper component structure and state management
**UI/UX Status:** ⚠️ Good styling but missing interactive features
**Performance Status:** ❌ Not optimized for large qubit counts as required by plans

The frontend has a solid foundation but needs significant additions to meet the full specifications outlined in the plans, particularly around API integration, performance optimization, and advanced editor features.
