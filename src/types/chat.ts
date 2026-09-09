export type MessageRole = 'user' | 'assistant';

export type VideoGenerationStatus =
  | 'pending'
  | 'extracting'
  | 'planning'
  | 'rendering'
  | 'completed'
  | 'failed'
  | 'expired';

export interface VideoMetadata {
  id: string;
  status: VideoGenerationStatus;
  current_stage?: string;
  stage_message?: string;
  duration?: number;
  concept?: string;
  text_overlay?: string;
  background_asset_id?: string;
  gif_asset_id?: string;
  audio_asset_id?: string;
  video_url?: string;
  download_url?: string;
  is_expired?: boolean;
  error?: string;
  licensing_tier?: string;
  asset_sources?: any;
  qa_metadata?: any;
  created_at?: string;
  completed_at?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  videoId?: string;
  videoMetadata?: VideoMetadata;
  createdAt: Date;
}

export interface MessageItemDTO {
  id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  video_id?: string;
  video_metadata?: VideoMetadata;
}

export interface ConversationHistoryResponse {
  conversation_id: string;
  created_at: string;
  messages: MessageItemDTO[];
  active_video_id?: string;
}
