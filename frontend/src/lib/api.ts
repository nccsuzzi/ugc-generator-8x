import { VideoMetadata, ConversationHistoryResponse } from '../types/chat';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface SendMessageResponse {
  message: string;
  video_id?: string;
  generation_started: boolean;
  conversation_id: string;
}

export async function sendMessage(
  message: string,
  conversationId?: string
): Promise<SendMessageResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId || null,
    }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to send message');
  }

  return res.json();
}

export async function getConversation(
  conversationId: string
): Promise<ConversationHistoryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch conversation history');
  }
  return res.json();
}

export async function getVideoStatus(videoId: string): Promise<VideoMetadata> {
  const res = await fetch(`${API_BASE_URL}/api/v1/videos/${videoId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch video status');
  }
  return res.json();
}

export function getVideoFileUrl(videoId: string): string {
  return `${API_BASE_URL}/api/v1/videos/${videoId}/file`;
}

export function getVideoDownloadUrl(videoId: string): string {
  return `${API_BASE_URL}/api/v1/videos/${videoId}/file?download=true`;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, { method: 'GET' });
    return res.ok;
  } catch {
    return false;
  }
}
