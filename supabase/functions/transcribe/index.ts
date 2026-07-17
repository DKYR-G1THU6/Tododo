// Edge Function: transcribe
// 把任务的录音转成文字。流程：
//   接收 { uuid, audio_url } -> 从 voice 桶下载录音 -> 调 Groq whisper-large-v3
//   -> 把 transcript + transcribe_status='done' 写回 tasks 行（并更新 updated_at 以便同步下发）
//
// 用调用者的 JWT 建 client，全程受 RLS 约束（只能碰自己的行/录音）。
// GROQ_API_KEY 存为 Edge Function secret，绝不下发到客户端。

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions";
const GROQ_MODEL = "whisper-large-v3";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

// audio_url 约定为 voice 桶内对象路径 {user_id}/{uuid}.{ext}；容错去掉可能的前缀
function toObjectPath(audioUrl: string): string {
  let p = audioUrl.trim();
  const marker = "/voice/";
  const idx = p.indexOf(marker);
  if (idx >= 0) p = p.slice(idx + marker.length);
  if (p.startsWith("voice/")) p = p.slice("voice/".length);
  return p;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);

  const authHeader = req.headers.get("Authorization");
  if (!authHeader) return json({ error: "missing Authorization header" }, 401);

  const groqKey = Deno.env.get("GROQ_API_KEY");
  if (!groqKey) return json({ error: "GROQ_API_KEY not configured" }, 500);

  let uuid: string | undefined;
  let audioUrl: string | undefined;
  try {
    const body = await req.json();
    uuid = body.uuid;
    audioUrl = body.audio_url;
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }
  if (!uuid || !audioUrl) return json({ error: "uuid and audio_url are required" }, 400);

  // 以调用者身份建 client（受 RLS 约束）
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } },
  );

  const objectPath = toObjectPath(audioUrl);

  try {
    // 1) 下载录音
    const { data: file, error: dlErr } = await supabase.storage.from("voice").download(objectPath);
    if (dlErr || !file) throw new Error(`download failed: ${dlErr?.message ?? "no file"}`);

    // 2) 调 Groq（OpenAI 兼容的 audio/transcriptions 接口）
    const form = new FormData();
    form.append("file", file, objectPath.split("/").pop() ?? "audio");
    form.append("model", GROQ_MODEL);
    form.append("response_format", "json");

    const groqResp = await fetch(GROQ_URL, {
      method: "POST",
      headers: { Authorization: `Bearer ${groqKey}` },
      body: form,
    });
    if (!groqResp.ok) {
      const detail = await groqResp.text();
      throw new Error(`groq ${groqResp.status}: ${detail}`);
    }
    const { text } = await groqResp.json();

    // 3) 写回任务行（更新 updated_at 让转写结果通过同步下发到两端）
    const { error: upErr } = await supabase
      .from("tasks")
      .update({
        transcript: text,
        transcribe_status: "done",
        updated_at: new Date().toISOString(),
      })
      .eq("uuid", uuid);
    if (upErr) throw new Error(`db update failed: ${upErr.message}`);

    return json({ ok: true, uuid, transcript: text });
  } catch (err) {
    // 失败：标记 transcribe_status='failed'，方便客户端展示/重试
    await supabase
      .from("tasks")
      .update({ transcribe_status: "failed", updated_at: new Date().toISOString() })
      .eq("uuid", uuid);
    return json({ ok: false, uuid, error: String(err) }, 500);
  }
});
