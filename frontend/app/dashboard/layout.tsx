import { TopNav } from "@/components/dashboard/topnav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-cream">
      <TopNav />
      <main className="container py-10">{children}</main>
    </div>
  );
}
