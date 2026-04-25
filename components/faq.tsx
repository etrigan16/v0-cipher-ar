"use client"

import { useState } from "react"
import { ChevronDown } from "lucide-react"

const faqs = [
  {
    question: "Que incluye una auditoria de seguridad?",
    answer: "Una auditoria completa incluye: analisis de vulnerabilidades de red e infraestructura, revision de configuraciones de seguridad, pruebas de penetracion controladas, evaluacion de politicas de acceso, revision de cumplimiento normativo, y un informe detallado con recomendaciones priorizadas por nivel de riesgo."
  },
  {
    question: "Cuanto tiempo toma implementar mejoras de seguridad?",
    answer: "El tiempo varia segun el alcance. Una configuracion basica de firewall y segmentacion de red puede completarse en 1-2 semanas. Proyectos mas complejos como hardening de servidores o implementacion de monitoreo continuo pueden tomar 4-8 semanas. Siempre proporcionamos un cronograma detallado antes de comenzar."
  },
  {
    question: "Trabajaban con empresas de mi tamano?",
    answer: "Si, nos especializamos en PyMEs. Entendemos que las pequenas y medianas empresas tienen presupuestos diferentes a las grandes corporaciones, por eso ofrecemos soluciones escalables que se adaptan a tus necesidades y recursos actuales, con posibilidad de crecer conforme tu empresa lo haga."
  },
  {
    question: "Que pasa si ya sufrimos un ataque?",
    answer: "Ofrecemos servicios de respuesta a incidentes. Esto incluye: contencion inmediata del ataque, analisis forense para determinar el alcance, recuperacion de sistemas afectados, y recomendaciones para prevenir futuros incidentes. Cuanto antes nos contactes, menor sera el impacto."
  },
  {
    question: "Ofrecen soporte continuo despues de la implementacion?",
    answer: "Si, tenemos planes de soporte y monitoreo continuo. Estos incluyen: supervision 24/7 de alertas de seguridad, actualizaciones periodicas de sistemas, respuesta rapida ante nuevas amenazas, y revisiones trimestrales de tu postura de seguridad."
  },
  {
    question: "Como garantizan la confidencialidad de mi informacion?",
    answer: "Firmamos acuerdos de confidencialidad (NDA) con todos nuestros clientes. Nuestro equipo sigue estrictos protocolos de manejo de informacion sensible, y toda la documentacion generada durante los proyectos se almacena de forma segura con acceso limitado."
  },
  {
    question: "Que certificaciones tienen?",
    answer: "Nuestro equipo cuenta con certificaciones reconocidas en la industria incluyendo: CISSP, CEH (Certified Ethical Hacker), CompTIA Security+, y certificaciones especificas de fabricantes como Cisco y Microsoft. Mantenemos nuestras certificaciones actualizadas mediante formacion continua."
  },
  {
    question: "Pueden ayudarme con el cumplimiento de normativas?",
    answer: "Si, asesoramos en cumplimiento de diversas normativas como GDPR, ISO 27001, PCI-DSS, y regulaciones locales de proteccion de datos. Realizamos analisis de brechas de cumplimiento y te ayudamos a implementar los controles necesarios para alcanzar y mantener la conformidad."
  }
]

function FAQItem({ question, answer, isOpen, onClick }: { 
  question: string
  answer: string
  isOpen: boolean
  onClick: () => void 
}) {
  return (
    <div className="border-b border-border last:border-b-0">
      <button
        onClick={onClick}
        className="w-full flex items-center justify-between py-5 text-left"
      >
        <span className="font-medium text-foreground pr-4">
          {question}
        </span>
        <ChevronDown 
          className={`w-5 h-5 text-muted-foreground shrink-0 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`} 
        />
      </button>
      <div 
        className={`overflow-hidden transition-all duration-200 ${
          isOpen ? "max-h-96 pb-5" : "max-h-0"
        }`}
      >
        <p className="text-muted-foreground leading-relaxed">
          {answer}
        </p>
      </div>
    </div>
  )
}

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  return (
    <section id="faq" className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
            Preguntas Frecuentes
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance">
            Resolvemos tus dudas
          </h2>
          <p className="text-muted-foreground text-lg">
            Las preguntas mas comunes sobre nuestros servicios.
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg px-6">
          {faqs.map((faq, index) => (
            <FAQItem
              key={index}
              question={faq.question}
              answer={faq.answer}
              isOpen={openIndex === index}
              onClick={() => setOpenIndex(openIndex === index ? null : index)}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
