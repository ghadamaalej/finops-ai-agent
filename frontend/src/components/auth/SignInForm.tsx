import { useEffect, useRef, useState } from "react";
import { InteractionStatus } from "@azure/msal-browser";
import { useMsal } from "@azure/msal-react";
import { Link, useNavigate } from "react-router";
import { ChevronLeftIcon } from "../../icons";
import { establishFinopsSession, identityScopes } from "../../lib/entra";

export default function SignInForm() {
  const { instance, accounts, inProgress } = useMsal();
  const navigate = useNavigate();
  const processed = useRef(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // MsalProvider processes the redirect once. This page only consumes the
  // settled account after MSAL reports no interaction in progress.
  useEffect(() => {
    if (inProgress !== InteractionStatus.None || !accounts[0] || processed.current) return;
    processed.current = true;
    setLoading(true);
    void establishFinopsSession(accounts[0])
      .then(() => navigate("/connect-azure", { replace: true }))
      .catch((reason: unknown) => { processed.current = false; setError(reason instanceof Error ? reason.message : "Sign-in failed."); })
      .finally(() => setLoading(false));
  }, [accounts, inProgress, navigate]);

  function signIn() {
    if (inProgress !== InteractionStatus.None) return;
    setError("");
    setLoading(true);
    void instance.loginRedirect({ scopes: identityScopes });
  }

  return <div className="flex flex-col flex-1">
    <div className="w-full max-w-md pt-10 mx-auto"><Link to="/" className="inline-flex items-center text-sm text-gray-500 transition-colors hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"><ChevronLeftIcon className="size-5" />Back to dashboard</Link></div>
    <div className="flex flex-col justify-center flex-1 w-full max-w-md mx-auto"><div><div className="mb-5 sm:mb-8"><h1 className="mb-2 font-semibold text-gray-800 text-title-sm dark:text-white/90 sm:text-title-md">Sign in to FinOps App</h1><p className="text-sm text-gray-500 dark:text-gray-400">Use your organization&apos;s Microsoft Entra ID account.</p></div>
      <button
  disabled={loading || inProgress !== InteractionStatus.None}
  onClick={signIn}
  className="inline-flex w-full items-center justify-center gap-3 rounded-lg bg-gray-100 px-7 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200 disabled:opacity-50 dark:bg-white/5 dark:text-white/90"
>
  <svg
    width="20"
    height="20"
    viewBox="0 0 23 23"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <rect x="1" y="1" width="10" height="10" fill="#F25022" />
    <rect x="12" y="1" width="10" height="10" fill="#7FBA00" />
    <rect x="1" y="12" width="10" height="10" fill="#00A4EF" />
    <rect x="12" y="12" width="10" height="10" fill="#FFB900" />
  </svg>

  {loading || inProgress !== InteractionStatus.None
    ? "Signing in…"
    : "Continue with Microsoft"}
</button>
{error && (
  <div className="mt-4 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
    <span className="mt-0.5" aria-hidden="true">
      ⚠️
    </span>
    <p>{error}</p>
  </div>
)}

<p className="mt-5 text-center text-xs leading-5 text-gray-500 dark:text-gray-400">
  <span className="inline-flex items-center gap-1.5">
    <span aria-hidden="true"></span>
    Secure authentication powered by Microsoft
  </span>
</p>    </div></div>
  </div>;
}
