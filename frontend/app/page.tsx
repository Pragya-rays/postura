import { Navbar } from "@/components/marketing/navbar";
import { Hero } from "@/components/marketing/hero";
import { ScrollReset } from "@/components/marketing/scroll-reset";
import { SocialProof } from "@/components/marketing/social-proof";
import { HowItWorks } from "@/components/marketing/how-it-works";
import { SampleReport } from "@/components/marketing/sample-report";
import { ChecksGrid } from "@/components/marketing/checks-grid";
import { PricingSection } from "@/components/marketing/pricing-section";
import { Footer } from "@/components/marketing/footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-cream text-ink">
      <ScrollReset />
      <Navbar />
      <Hero />
      <SocialProof />
      <HowItWorks />
      <SampleReport />
      <ChecksGrid />
      <PricingSection />
      <Footer />
    </main>
  );
}
