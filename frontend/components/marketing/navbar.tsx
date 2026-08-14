import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Logo } from "./logo";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-[rgba(5,19,29,0.85)] backdrop-blur-md">
      <div className="container flex h-[72px] items-center justify-between">
        <Link href="/">
          <Logo dark />
        </Link>

        <nav className="hidden items-center gap-10 md:flex">
          <Link href="/pricing" className="text-[16px] font-medium text-ink-muted transition-colors hover:text-ink">
            Pricing
          </Link>
          <Link href="/login" className="text-[16px] font-medium text-ink-muted transition-colors hover:text-ink">
            Log in
          </Link>
          <Link href="/register">
            <Button variant="accent" size="sm">
              Get started
            </Button>
          </Link>
        </nav>

        <nav className="flex items-center gap-2 md:hidden">
          <Link href="/login" className="text-[13px] font-medium text-ink-muted transition-colors hover:text-ink">
            Log in
          </Link>
          <Link href="/register">
            <Button variant="accent" size="sm" className="h-8 px-3 text-[12px]">
              Start
            </Button>
          </Link>
        </nav>
      </div>
    </header>
  );
}
