import { useEffect, useRef, useState } from "react";
import { InteractionStatus } from "@azure/msal-browser";
import { useMsal } from "@azure/msal-react";
import { useNavigate } from "react-router";
import PageMeta from "../components/common/PageMeta";
import { armScopes, clearConnectionTokens, getAzureManagementAccessToken, getIdentityToken } from "../lib/entra";

type Subscription = { subscription_id: string; subscription_name?: string; state?: string };
type FastApiError = { detail?: string | Array<{ loc?: Array<string | number>; msg?: string }> };
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function apiError(response: Response, fallback: string) {
  const body = await response.json().catch(() => null) as FastApiError | null;
  if (Array.isArray(body?.detail)) {
    return body.detail.map(item => `${item.loc?.join(".") ?? "request"}: ${item.msg ?? "invalid value"}`).join("; ");
  }
  return typeof body?.detail === "string" ? body.detail : fallback;
}

export default function AzureConnect() {
  const { instance, accounts, inProgress } = useMsal();
  const navigate = useNavigate();
  const requested = useRef(false);
  const user = JSON.parse(sessionStorage.getItem("finops.user") ?? "null") as { display_name?: string; email?: string } | null;
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Do not start token acquisition until the provider has processed every redirect.
    if (inProgress !== InteractionStatus.None || requested.current) return;
    const account = accounts[0];
    if (!account) { setError("Your Microsoft sign-in session expired. Please sign in again."); setLoading(false); return; }
    requested.current = true;
    let active = true;
    async function loadSubscriptions() {
      try {
        const idToken = getIdentityToken();
        const azureToken = await getAzureManagementAccessToken(account);
        const response = await fetch(`${apiBaseUrl}/auth/subscriptions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id_token: idToken, azure_access_token: azureToken }) });
        if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "Azure access was not granted or no subscriptions are available."); }
        const data = await response.json() as { subscriptions: Subscription[] };
        if (active) setSubscriptions(data.subscriptions);
      }
      catch (reason)
      {

        const message = reason instanceof Error ? reason.message : "Could not list subscriptions.";
        if (/interaction_required|consent_required|login_required/i.test(message) && inProgress === InteractionStatus.None)
          {
          await instance.acquireTokenRedirect({ account, scopes: armScopes });
          return;
        }
        if (active) setError(message);
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadSubscriptions();
    return () => { active = false; };
  }, [accounts, inProgress, instance]);

  async function selectSubscription(subscription: Subscription) {
    try {
      // FastAPI's two body parameters require named top-level objects:
      // selection: SubscriptionSelection and payload: EntraSession.
      const response = await fetch(`${apiBaseUrl}/auth/azure-connections`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selection: {
            subscription_id: subscription.subscription_id,
            subscription_name: subscription.subscription_name,
            permissions_status: "DELEGATED",
          },
          payload: { id_token: getIdentityToken() },
        }),
      });
      if (!response.ok) throw new Error(await apiError(response, "Could not save the Azure connection."));
      clearConnectionTokens();
      navigate("/");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save the Azure connection."); }
  }

  return <div className="min-h-screen bg-gray-50 p-6 dark:bg-gray-950"><PageMeta title="Connect Azure | FinOps AI" description="Connect an Azure subscription" />
    <main className="mx-auto mt-16 max-w-2xl rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-900"><p className="text-sm font-medium text-brand-500">FINOPS AGENT</p><h1 className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">Connect your Azure environment</h1><p className="mt-4 text-gray-600 dark:text-gray-300">{user?.display_name ?? user?.email ?? "Signed in"}. Choose the subscription FinOps Agent may analyse.</p><div className="my-6 rounded-xl border border-gray-200 p-5 text-sm text-gray-600 dark:border-gray-700 dark:text-gray-300">Microsoft Entra authenticates your account. A separate Azure Resource Manager token is acquired only to list subscriptions and is never persisted.</div>{loading && <p className="text-sm text-gray-500">Loading Azure subscriptions…</p>}{error && <p className="text-sm text-error-500">{error}</p>}<div className="space-y-3">{subscriptions.map(subscription => <div key={subscription.subscription_id} className="flex items-center justify-between rounded-xl border border-gray-200 p-4 dark:border-gray-700"><div><p className="font-medium text-gray-900 dark:text-white">{subscription.subscription_name}</p><p className="text-sm text-gray-500">{subscription.subscription_id} · {subscription.state}</p></div><button onClick={() => void selectSubscription(subscription)} className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white">Select</button></div>)}</div></main>
  </div>;
}
