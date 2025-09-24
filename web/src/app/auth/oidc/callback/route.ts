import { getDomain } from "@/lib/redirectSS";
import { buildUrl } from "@/lib/utilsSS";
import { NextRequest, NextResponse } from "next/server";

export const GET = async (request: NextRequest) => {
  // Wrapper around the FastAPI endpoint /auth/oidc/default/callback,
  // which adds back a redirect to the main app.
  const url = new URL(buildUrl("/auth/oidc/default/callback"));
  url.search = request.nextUrl.search;
  
  console.log('OIDC Callback received with query params:', request.nextUrl.search);
  console.log('Forwarding to backend URL:', url.toString());
  
  try {
    // Set 'redirect' to 'manual' to prevent automatic redirection
    const response = await fetch(url.toString(), { redirect: "manual" });
    console.log('Backend response status:', response.status);
    
    const setCookieHeader = response.headers.get("set-cookie");
    console.log('Set-Cookie header present:', Boolean(setCookieHeader));
    
    // Log all response headers for debugging
    const headersObj: Record<string, string> = {};
    response.headers.forEach((value, name) => {
      headersObj[name] = value;
    });
    console.log('Response headers:', headersObj);

  if (response.status === 401) {
    return NextResponse.redirect(
      new URL("/auth/create-account", getDomain(request))
    );
  }

  if (!setCookieHeader) {
    console.log('No set-cookie header found, redirecting to error page');
    return NextResponse.redirect(new URL("/auth/error", getDomain(request)));
  }

  // Get the redirect URL from the backend's 'Location' header, or default to '/'
  const redirectUrl = response.headers.get("location") || "/";
  console.log('Redirect URL from backend:', redirectUrl);

  const redirectResponse = NextResponse.redirect(
    new URL(redirectUrl, getDomain(request))
  );

  redirectResponse.headers.set("set-cookie", setCookieHeader);
  console.log('Final redirect response prepared with cookies');
  return redirectResponse;
  } catch (error) {
    console.error('Error in OIDC callback handler:', error);
    return NextResponse.redirect(new URL("/auth/error?reason=callback-error", getDomain(request)));
  }
};
