import { Navbar } from "@/components/navbar"
import { HeroSection, TrustedBySection } from "@/components/hero"
import { ServicesSection } from "@/components/services"
import { IntelligenceSection } from "@/components/intelligence"
import { AuditExpressSection } from "@/components/audit-express"
import { AttackSurfaceSection } from "@/components/attack-surface"
import { PhishingSection } from "@/components/phishing"
import { PricingSection } from "@/components/pricing"
import { ContactSection } from "@/components/contact"
import { Footer } from "@/components/footer"

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <HeroSection />
      <TrustedBySection />
      <ServicesSection />
      <IntelligenceSection />
      <AuditExpressSection />
      <AttackSurfaceSection />
      <PhishingSection />
      <PricingSection />
      <ContactSection />
      <Footer />
    </main>
  )
}
