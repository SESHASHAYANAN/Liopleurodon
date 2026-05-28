import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';

/**
 * OAuth callback handler.
 * After a user signs in via Google/GitHub, Supabase redirects here
 * with a `code` query param. We exchange it for a session, then
 * redirect the user back to the homepage.
 */
export async function GET(request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = searchParams.get('next') || '/';

  if (code) {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    );

    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // If something went wrong, redirect home anyway
  return NextResponse.redirect(`${origin}/`);
}
