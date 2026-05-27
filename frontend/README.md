# AcadSort Frontend - Wave 6.1 Complete ✅

**Status**: React + TypeScript + Tailwind scaffold complete with full API integration

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

This will:
1. Start Vite dev server on `http://localhost:5173`
2. Backend must be running on `http://127.0.0.1:8765`
3. App will poll backend health every 2 seconds

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # Main app with health check loop
│   ├── index.css             # Tailwind + custom animations
│   │
│   ├── components/
│   │   ├── Header.tsx        # Navigation bar
│   │   └── HealthCheck.tsx   # Backend status indicator
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx     # Accomplishment-driven stats page
│   │   ├── FileProcessor.tsx # Real-time file review page
│   │   └── Settings.tsx      # Configuration page
│   │
│   ├── hooks/
│   │   └── useBackendAPI.ts  # Custom hook for all API calls
│   │
│   └── types/
│       └── api.ts            # TypeScript interfaces
│
├── index.html                # HTML template
├── package.json              # Dependencies
├── vite.config.ts            # Vite config
├── tailwind.config.ts        # Tailwind config
├── postcss.config.ts         # PostCSS config
├── tsconfig.json             # TypeScript config
└── tauri.conf.json           # Tauri desktop config
```

## Features

### 🎯 Dashboard
- Progress bar showing organization percentage
- Weekly stats (files organized, pending, accuracy)
- Recently organized files list
- Call-to-action for new users

### ⚙️ File Processor
- Real-time file review interface
- Confidence visualization (color-coded bars)
- Course dropdown for manual selection
- Queue preview showing next files
- Celebration animation on confirm
- Empty state when all files processed

### ⚙️ Settings
- Organization style toggle (Week vs Type)
- Confidence threshold sliders:
  - Auto-move threshold (for automatic organization)
  - Suggest threshold (for user confirmation)
- Courses list display
- Semester information
- Save with success feedback

## API Integration

The `useBackendAPI` hook provides these functions:

```typescript
// Health & Status
checkHealth()                    // GET /health

// Courses
getCoursesList()                // GET /api/courses/list

// Settings
getSettings()                   // GET /api/settings/current
updateSettings(updates)         // PUT /api/settings/current

// Queue & Stats
getQueueStats()                // GET /api/queue/stats
getPendingFiles()              // GET /api/queue/pending

// Files
getRecentFiles()               // GET /api/files/list?limit=10
confirmFile(fileId, courseCode) // POST /api/files/confirm
rejectFile(fileId)             // POST /api/files/reject
```

## Styling

- **Framework**: Tailwind CSS 3.4.0
- **Colors**: Indigo-based palette with amber, green, red accents
- **Animations**: Custom pulse, slide-in, grow animations
- **Responsive**: Mobile-first design (Grid + Flexbox)

## Development

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

### Run Tauri Desktop App
```bash
npm run tauri dev
```

## Browser Requirements

- ES2020 support
- Modern CSS Grid/Flexbox
- Fetch API
- localStorage (future)

## Next Steps

1. **Wave 6.2**: Install dependencies and test health check
2. **Wave 6.3**: Add animations and toast notifications
3. **Wave 6.4**: Implement Filipino UX elements
4. **Wave 6.5**: Mobile responsiveness and accessibility

## Architecture Notes

**Health Check Loop**:
- Polls `/health` every 2 seconds in App component
- Shows loading state until first response
- Displays error state if backend unavailable

**API Error Handling**:
- useBackendAPI hook catches all errors
- Returns default values on failure
- Sets error state for debugging

**Component State**:
- Local state for UI interactions
- Auto-refresh every 3-5 seconds for data
- Clean interval cleanup on unmount

## Troubleshooting

### "Backend connection failed"
- Ensure backend is running: `python -m backend.main` or `./backend/bin/backend`
- Backend must be on port 8765
- Check CORS is enabled in FastAPI

### Files not loading
- Clear browser cache
- Check browser console for API errors
- Verify backend endpoints are responding

### Styling not working
- Run `npm install` to get Tailwind CSS
- Rebuild with `npm run build`
- Check browser dev tools for CSS loading
