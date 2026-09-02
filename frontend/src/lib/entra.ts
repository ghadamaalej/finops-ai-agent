import { PublicClientApplication, type AccountInfo } from "@azure/msal-browser";

const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID ?? "efca227f-fc70-4c52-bade-e36ada2a3a40";
const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID ?? "ca0d73b8-e582-45fe-829d-8213bb022801";
const redirectUri = import.meta.env.VITE_ENTRA_REDIRECT_URI ?? "http://localhost:5173/signin";
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const identityTokenKey = "finops.identity.id_token";

export const identityScopes = ["openid", "profile", "email"];
export const armScopes = ["https://management.azure.com/user_impersonation"];
export const msalInstance = new PublicClientApplication({
  auth: { clientId, authority: `https://login.microsoftonline.com/${tenantId}`, redirectUri },
  cache: { cacheLocation: "sessionStorage" },
});

export async function establishFinopsSession(account: AccountInfo) {
  // This token is requested only for OIDC identity and sent only to /auth/session.
  const identity = await msalInstance.acquireTokenSilent({ account, scopes: identityScopes });
  if (!identity.idToken) throw new Error("Microsoft did not return an ID token.");
  const response = await fetch(`${apiBaseUrl}/auth/session`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id_token: identity.idToken }) });
  if (!response.ok) throw new Error("FinOps AI could not establish your session.");
  const data = await response.json();
  sessionStorage.setItem(identityTokenKey, identity.idToken);
  sessionStorage.setItem("finops.user", JSON.stringify(data.user));
  return data.user;
}

export async function getAzureManagementAccessToken(account: AccountInfo) {
  // Separate ARM token. An ID token and Graph token are never accepted here.
  return (await msalInstance.acquireTokenSilent({ account, scopes: armScopes })).accessToken;
}

export function getIdentityToken() {
  const token = sessionStorage.getItem(identityTokenKey);
  if (!token) throw new Error("Your FinOps AI identity session expired. Please sign in again.");
  return token;
}

// The identity token represents the application's authenticated session.  ARM
// credentials are never written here, so selecting a subscription must not
// clear this token.
export function clearConnectionTokens() {}
