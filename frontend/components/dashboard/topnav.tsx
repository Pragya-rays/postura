"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LogOut, Plus } from "lucide-react";
import { Logo } from "@/components/marketing/logo";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { logout, me } from "@/lib/api";

const links = [{ href: "/dashboard", label: "Domains" }];

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Doubles as the dashboard's auth guard: an unauthenticated visitor gets a
  // 401 here and is bounced to /login. Every dashboard page renders under
  // this layout, so this one check covers all of them.
  const meQuery = useQuery({ queryKey: ["me"], queryFn: me, retry: false });

  useEffect(() => {
    if (meQuery.isError) router.replace("/login");
  }, [meQuery.isError, router]);

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
      router.push("/");
    },
  });

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-cream/85 backdrop-blur-md">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/dashboard">
            <Logo />
          </Link>
          <nav className="hidden items-center gap-1 sm:flex">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors",
                  pathname === l.href ? "bg-ink/5 text-ink" : "text-ink-secondary hover:text-ink"
                )}
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/dashboard/scans/new">
            <Button variant="accent" size="sm">
              <Plus className="h-3.5 w-3.5" />
              New scan
            </Button>
          </Link>
          <div className="hidden items-center gap-2 border-l border-line pl-3 sm:flex">
            <span className="text-[13px] text-ink-secondary">{meQuery.data?.email ?? ""}</span>
            <button
              type="button"
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
              className="text-ink-muted transition-colors hover:text-ink disabled:opacity-50"
              title="Log out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
