import { getDomain } from "@/lib/redirectSS";
import { buildUrl } from "@/lib/utilsSS";
import { NextRequest, NextResponse } from "next/server";

const SEE_OTHER_REDIRECT_STATUS = 303;

export const GET = async (request: NextRequest) => {
  // This is a custom handler for the Authentik OIDC callback
  // We need to make sure we properly handle the authentication flow
  // and fix the issue where scopes are being sent as the provider name
  
  console.log("OIDC Callback received:", request.url);
  
  // Get the code and state from the query parameters
  const params = request.nextUrl.searchParams;
  const code = params.get("code");
  const state = params.get("state");
  
  
  if (!code || !state) {
    return NextResponse.redirect(
      new URL("/auth/error", getDomain(request)),
      { status: SEE_OTHER_REDIRECT_STATUS }
    );
  }
  
  // Forward the request to the backend's default callback endpoint
  const url = new URL(buildUrl("/auth/oidc/default/callback"));
  // Make sure to keep all the original query parameters
  url.search = request.nextUrl.search;
  console.log("Forwarding to backend URL:", url.toString());
  
  // Set 'redirect' to 'manual' to prevent automatic redirection
  console.log("Sending fetch request to backend");
  let response;
  let setCookieHeader;
  
  try {
    response = await fetch(url.toString(), { redirect: "manual" });
    console.log("Response received:", response.status, response.statusText);
    
    // Log headers safely
    const headerObj: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      headerObj[key] = value;
    });
    console.log("Response headers:", JSON.stringify(headerObj));
    
    setCookieHeader = response.headers.get("set-cookie");

    if (response.status === 401) {
      console.log("Received 401, redirecting to create-account");
      return NextResponse.redirect(
        new URL("/auth/create-account", getDomain(request)),
        { status: SEE_OTHER_REDIRECT_STATUS }
      );
    }

    if (!setCookieHeader) {
      return NextResponse.redirect(
        new URL("/auth/error", getDomain(request)),
        { status: SEE_OTHER_REDIRECT_STATUS }
      );
    }
  } catch (error) {
    return NextResponse.redirect(
      new URL("/auth/error", getDomain(request)),
      { status: SEE_OTHER_REDIRECT_STATUS }
    );
  }

  // Get the redirect URL from the backend's 'Location' header, or default to '/'
  const redirectUrl = response?.headers.get("location") || "/";
  console.log("Redirect URL from backend:", redirectUrl);

  const redirectResponse = NextResponse.redirect(
    new URL(redirectUrl, getDomain(request)),
    { status: SEE_OTHER_REDIRECT_STATUS }
  );

  // Only set cookie header if it exists
  if (setCookieHeader) {
    redirectResponse.headers.set("set-cookie", setCookieHeader);
    console.log("Added Set-Cookie header to response");
  }
  
  console.log("Returning redirect response to:", redirectUrl);
  return redirectResponse;
};
