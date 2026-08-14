"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, Lock } from "lucide-react";
import { login } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: () => router.push("/dashboard"),
  });

  return (
    <div className="w-full max-w-md rounded-xl2 border border-line bg-cream-card p-8 shadow-pop">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-ink/5">
        <Lock className="h-5 w-5 text-ink" />
      </div>
      <h1 className="mt-5 font-serif text-2xl text-ink">Welcome back</h1>
      <p className="mt-1.5 text-sm text-ink-secondary">Log in to see your scan history and grades.</p>

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
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        {mutation.isError && (
          <div className="flex items-center gap-2 rounded-lg bg-status-critical/10 px-3.5 py-2.5 text-sm text-status-critical">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {mutation.error instanceof Error ? mutation.error.message : "Something went wrong"}
          </div>
        )}

        <Button type="submit" variant="primary" size="lg" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Logging in…" : "Log in"}
          {!mutation.isPending && <ArrowRight className="h-4 w-4" />}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-ink-secondary">
        New to Postura?{" "}
        <Link href="/register" className="font-medium text-ink hover:underline">
          Create an account
        </Link>
      </p>

      <p className="mt-4 text-center text-[12px] text-ink-muted">
        Sessions live in httpOnly, Secure cookies. Passwords hashed with argon2.
      </p>
    </div>
  );
}
