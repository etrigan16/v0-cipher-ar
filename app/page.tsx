import { Navbar } from "@/components/navbar"
import { HeroSection, TrustedBySection } from "@/components/hero"
import { ServicesSection } from "@/components/services"
import { AboutSection, TeamSection } from "@/components/about"
import { CaseStudiesSection } from "@/components/case-studies"
import { ThreatsSection } from "@/components/threats"
import { FAQSection } from "@/components/faq"
import { TestimonialsSection } from "@/components/testimonials"
import { RiskCalculatorSection } from "@/components/risk-calculator"
import { NewsletterSection } from "@/components/newsletter"
import { ContactSection } from "@/components/contact"
import { Footer } from "@/components/footer"

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <HeroSection />
      <TrustedBySection />
      <ServicesSection />
      <CaseStudiesSection />
      <ThreatsSection />
      <RiskCalculatorSection />
      <AboutSection />
      <TeamSection />
      <TestimonialsSection />
      <FAQSection />
      <NewsletterSection />
      <ContactSection />
      <Footer />
    </main>
  )
}
