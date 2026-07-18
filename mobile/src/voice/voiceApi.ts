/**
 * 语音任务的云端部分：上传录音 + 触发服务端转写
 *
 * 录音本身是离线可用的（先落地本地文件和任务卡片），
 * 上传和转写需要联网，失败了不影响任务已经存在。
 */
import { SUPABASE_VOICE_BUCKET } from '../config';
import { supabase, ensureSession } from '../sync/supabase';

/**
 * 上传录音到 voice 桶，返回对象路径 `{user_id}/{uuid}.{ext}`。
 * 路径首段必须是 user_id —— Storage 的 RLS 策略就是按这个判断归属的。
 */
export async function uploadRecording(localUri: string, uuid: string): Promise<string> {
  const session = await ensureSession();
  const userId = session.user.id;

  const ext = (localUri.split('.').pop() || 'm4a').split('?')[0];
  const objectPath = `${userId}/${uuid}.${ext}`;

  // RN 里 Blob 支持不稳，用 arrayBuffer 上传是 supabase-js 推荐做法
  const response = await fetch(localUri);
  const bytes = await response.arrayBuffer();

  const { error } = await supabase.storage
    .from(SUPABASE_VOICE_BUCKET)
    .upload(objectPath, bytes, {
      contentType: ext === 'm4a' ? 'audio/mp4' : `audio/${ext}`,
      upsert: true,
    });
  if (error) throw error;

  return objectPath;
}

/** 请求服务端把这段录音转成文字（Edge Function 调 Groq whisper-large-v3） */
export async function requestTranscription(uuid: string, audioUrl: string): Promise<void> {
  const { error } = await supabase.functions.invoke('transcribe', {
    body: { uuid, audio_url: audioUrl },
  });
  if (error) throw error;
}

/** 取录音的可播放地址（私有桶需要签名 URL） */
export async function getPlayableUrl(audioUrl: string): Promise<string | null> {
  const { data, error } = await supabase.storage
    .from(SUPABASE_VOICE_BUCKET)
    .createSignedUrl(audioUrl, 60 * 60);
  if (error) return null;
  return data?.signedUrl ?? null;
}
