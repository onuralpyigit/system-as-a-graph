import type { AuthProvider } from "@refinedev/core";

import { ApiError, authApi } from "./api-client";
import { clearSession, isExpired, readSession, writeSession } from "./session-storage";

// Session & Authentication Manager (SRS VAE-01.3-4), as a Refine AuthProvider.
// LDAP itself is never touched from here: the panel's /session endpoint does
// the bind and hands back a bearer token, which is all this app ever holds.
export const authProvider: AuthProvider = {
  login: async ({ username, password }: { username: string; password: string }) => {
    try {
      const session = await authApi.login({ username, password });
      writeSession(session);
      return { success: true, redirectTo: "/" };
    } catch (error) {
      const message = error instanceof ApiError ? error.detail : "Unable to sign in";
      return {
        success: false,
        error: { name: "LoginError", message },
      };
    }
  },

  logout: async () => {
    clearSession();
    return { success: true, redirectTo: "/login" };
  },

  check: async () => {
    const session = readSession();
    if (!session || isExpired(session)) {
      clearSession();
      return { authenticated: false, redirectTo: "/login" };
    }
    return { authenticated: true };
  },

  onError: async (error) => {
    if (error instanceof ApiError && error.status === 401) {
      clearSession();
      return { logout: true, redirectTo: "/login" };
    }
    return {};
  },

  getIdentity: async () => readSession(),
};
