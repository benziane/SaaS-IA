/**
 * Middleware - Grade S++
 * Route protection and authentication
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/* ========================================================================
   CONFIGURATION
   ======================================================================== */

// Public routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/register'];

// Routes that require authentication
const PROTECTED_ROUTES = ['/dashboard', '/transcription'];

/* ========================================================================
   MIDDLEWARE
   ======================================================================== */

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  
  // Redirect root to login
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Allow public routes without any check
  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route));
  if (isPublicRoute) {
    return NextResponse.next();
  }
  
  // Check if route is protected
  const isProtectedRoute = PROTECTED_ROUTES.some(route => pathname.startsWith(route));
  
  // Get auth token from cookie
  const token = request.cookies.get('auth_token')?.value;
  
  // Redirect to login if accessing protected route without token
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  return NextResponse.next();
}

/* ========================================================================
   CONFIGURATION
   ======================================================================== */

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)',
  ],
};

