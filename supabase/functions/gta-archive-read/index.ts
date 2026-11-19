import { createClient } from "npm:@supabase/supabase-js@2";
Deno.serve(async (req) => {
  const raw = req.headers.get("Authorization") ?? "";
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(raw.replace(/^Bearer /, "")));
  const hex = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2,"0")).join("");
  if (hex !== "47458214eb25f45266ff688eb0cef84e9890526004fa541bd89f554f74381161") return new Response(null,{status:401});
  const id = new URL(req.url).searchParams.get("id") ?? "";
  if (req.method !== "GET" || !/^[A-Za-z0-9_-]{11}$/.test(id)) return new Response(null,{status:400});
  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const {data,error} = await db.storage.from("gta-originals").createSignedUrl(id+".mp4",900);
  if(error) return new Response(null,{status:/not found|does not exist/i.test(error.message)?404:503});
  return Response.json({url:data.signedUrl},{headers:{"Cache-Control":"no-store"}});
});
