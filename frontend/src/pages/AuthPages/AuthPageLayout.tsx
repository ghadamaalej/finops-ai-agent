import React from "react";
import GridShape from "../../components/common/GridShape";
import { Link } from "react-router";
import ThemeTogglerTwo from "../../components/common/ThemeTogglerTwo";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative z-1 bg-white p-6 dark:bg-gray-900 sm:p-0">
      <div className="relative flex h-screen w-full flex-col justify-center dark:bg-gray-900 sm:p-0 lg:flex-row">

        {children}

        <div className="hidden h-full w-full items-center justify-center bg-brand-950 lg:flex lg:w-1/2 dark:bg-white/5">
          <div className="relative flex h-full w-full items-center justify-center">
            <GridShape />

            <div className="relative z-10 flex max-w-md flex-col items-center px-8 text-center">

  {/* Logo + Brand */}
  <Link
    to="/"
    className="mb-8 flex items-center justify-center gap-3"
  >
    <img
      src="/images/logo/logo-icon.svg"
      alt="FinOps App"
      width={231}
      height={48}
      className="h-12 w-auto"
    />

    <span className="text-2xl font-semibold text-white">
      FinOps App
    </span>
  </Link>

  {/* Description */}
  <p className="max-w-sm text-center text-base leading-7 text-gray-300 dark:text-white/70">
    AI-Powered Cloud Cost Optimization & FinOps Management Platform
  </p>

  {/* Status */}
  <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-blue-200">
    <span className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
    <span>Real-time Cost Monitoring & Optimization</span>
  </div>

</div>
          </div>
        </div>

        <div className="fixed bottom-6 right-6 z-50 hidden sm:block">
          <ThemeTogglerTwo />
        </div>

      </div>
    </div>
  );
}