// Backend API Types

export interface HealthResponse {
  status: 'ok';
  version: string;
  ollama_available: boolean;
}

export interface Course {
  id: number;
  code: string;
  name: string;
  keywords?: string[];
}

export interface FileRecord {
  id: number;
  name: string;
  course: string;
  material_type: string;
  week?: number;
  confidence: number;
  status: 'PENDING' | 'AUTO_MOVED' | 'CONFIRMED' | 'REJECTED';
  snippet?: string;
}

export interface Settings {
  id: number;
  semester_name: string;
  organization_style: 'week' | 'type';
  downloads_path: string;
  confidence_auto: number;
  confidence_suggest: number;
}

export interface QueueStats {
  total_pending: number;
  total_confirmed: number;
  total_rejected: number;
  avg_confidence: number;
}

export interface ProcessingResult {
  status: 'auto_moved' | 'suggest' | 'review_queue' | 'error';
  file_id?: number;
  course?: string;
  confidence?: number;
  message?: string;
}

export interface WatchFolder {
  id: number;
  path: string;
  semester_id: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface WatchFolderStatus {
  id: number;
  path: string;
  accessible: boolean;
  enabled: boolean;
  file_count: number;
  last_checked: string;
}

export interface Session {
  id: string;
  created_at: string;
  last_activity: string;
  valid?: boolean;
}
