"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, ShieldCheck } from "lucide-react";
import { register } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const prefillDomain = params.get("domain") ?? "";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => register(email, password),
    onSuccess: () => {
      const q = prefillDomain ? `?domain=${encodeURIComponent(prefillDomain)}` : "";
      router.push(`/dashboard/scans/new${q}`);
    },
  });

  return (
    <div className="w-full max-w-md rounded-xl2 border border-line bg-cream-card p-8 shadow-pop">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-lime-soft">
        <ShieldCheck className="h-5 w-5 text-ink" />
      </div>
      <h1 className="mt-5 font-serif text-2xl text-ink">Create your account</h1>
      <p className="mt-1.5 text-sm text-ink-secondary">
        {prefillDomain ? (
          <>
            We&rsquo;ll scan <span className="font-medium text-ink">{prefillDomain}</span> right after this.
          </>
        ) : (
          "Free to start — first scan included."
        )}
      </p>

      <form
        className="mt-7 space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div>
          <label className="mb-1.5 block text-[13px] font-medium text-ink-secondary">Email</label>
          <Input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-[13px] font-medium text-ink-secondary">Password</label>
          <Input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
        </div>

        {mutation.isError && (
          <div className="flex items-center gap-2 rounded-lg bg-status-critical/10 px-3.5 py-2.5 text-sm text-status-critical">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {mutation.error instanceof Error ? mutation.error.message : "Something went wrong"}
          </div>
        )}

        <Button type="submit" variant="accent" size="lg" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating account…" : "Create account"}
          {!mutation.isPending && <ArrowRight className="h-4 w-4" />}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-ink-secondary">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-ink hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
