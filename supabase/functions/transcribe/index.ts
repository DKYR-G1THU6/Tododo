// Edge Function: transcribe
// 把任务的录音转成文字。流程：
//   接收 { uuid, audio_url } -> 从 voice 桶下载录音 -> 调 Groq whisper-large-v3
//   -> 把 transcript + transcribe_status='done' 写回 tasks 行（并更新 updated_at 以便同步下发）
//
// 用调用者的 JWT 建 client，全程受 RLS 约束（只能碰自己的行/录音）。
// GROQ_API_KEY 存为 Edge Function secret，绝不下发到客户端。

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions";

// 默认 whisper-large-v3：待办都是几秒的短句，turbo 的速度优势体感不到，
// 而中英混说正是 turbo 退化最明显的地方，转错了还要手动改标题。
// 想对比 whisper-large-v3-turbo 时，在 Edge Function Secrets 里加 GROQ_MODEL 即可，不用改代码。
const GROQ_MODEL = Deno.env.get("GROQ_MODEL") ?? "whisper-large-v3";

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

/**
 * 取用于建 client 的 API key。
 *
 * SUPABASE_ANON_KEY 已被标记 deprecated，新项目改用 SUPABASE_PUBLISHABLE_KEYS
 * （一个 JSON 字典/数组）。这里优先读新的、回退到旧的，两种项目都能跑。
 */
function resolveApiKey(): string {
  const raw = Deno.env.get("SUPABASE_PUBLISHABLE_KEYS");
  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      const candidates: unknown[] = Array.isArray(parsed) ? parsed : Object.values(parsed);
      for (const c of candidates) {
        if (typeof c === "string" && c.length > 0) return c;
        // 也可能是 { name, api_key } 这类对象
        if (c && typeof c === "object") {
          for (const v of Object.values(c as Record<string, unknown>)) {
            if (typeof v === "string" && v.startsWith("sb_publishable_")) return v;
          }
        }
      }
    } catch {
      // 解析失败就当它本身就是一个 key
      if (raw.startsWith("sb_")) return raw;
    }
  }

  const legacy = Deno.env.get("SUPABASE_ANON_KEY");
  if (legacy) return legacy;

  throw new Error("no publishable/anon key available in the function environment");
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
  let supabase;
  try {
    supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      resolveApiKey(),
      { global: { headers: { Authorization: authHeader } } },
    );
  } catch (e) {
    return json({ error: String(e) }, 500);
  }

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
    // title 也一并写成转写文本：语音任务创建时只有占位标题，
    // 用户要的就是「说了什么，任务就叫什么」，两端都直接显示。
    const cleaned = (text ?? "").trim();

    // 静音/杂音也会被转出个 "." 之类的东西。这种情况不该把任务标题改成标点，
    // 而应标记失败并保留占位标题，让用户知道要重录。
    const hasSpeech = cleaned.replace(/[\s.,;:!?'"，。、；：！？…·—\-]/g, "").length > 0;

    const patch: Record<string, unknown> = {
      transcript: cleaned,
      transcribe_status: hasSpeech ? "done" : "failed",
      updated_at: new Date().toISOString(),
    };
    if (hasSpeech) patch.title = cleaned;

    const { error: upErr } = await supabase.from("tasks").update(patch).eq("uuid", uuid);
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
