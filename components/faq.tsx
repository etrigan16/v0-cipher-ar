'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

const faqs = [
  {
    question: '¿Qué incluye una auditoría de seguridad?',
    answer: 'Análisis de vulnerabilidades, pruebas de penetración, evaluación de controles, revisión de configuraciones, análisis de cumplimiento normativo, y un informe ejecutivo con recomendaciones priorizadas por riesgo.',
  },
  {
    question: '¿Cuánto tiempo toma implementar mejoras?',
    answer: 'Depende del alcance. Configuraciones básicas: 1-2 semanas. Proyectos complejos (hardening, monitoreo): 4-8 semanas. Proporcionamos cronograma detallado antes de comenzar.',
  },
  {
    question: '¿Trabajan con empresas de mi tamaño?',
    answer: 'Sí, nos especializamos en PyMEs. Ofrecemos soluciones escalables adaptadas a tu presupuesto actual, con posibilidad de crecer conforme tu empresa lo haga.',
  },
  {
    question: '¿Qué pasa si ya sufrimos un ataque?',
    answer: 'Ofrecemos respuesta a incidentes: contención inmediata, análisis forense, recuperación de sistemas, y recomendaciones preventivas. Cuanto antes contactes, menor impacto.',
  },
  {
    question: '¿Ofrecen soporte continuo?',
    answer: 'Sí, planes de monitoreo 24/7, actualizaciones periódicas, respuesta ante nuevas amenazas, y revisiones trimestrales de tu postura de seguridad.',
  },
  {
    question: '¿Cómo garantizan confidencialidad?',
    answer: 'Firmamos NDAs con todos los clientes. Protocolos estrictos de manejo de información sensible, acceso limitado a documentación, almacenamiento seguro.',
  },
  {
    question: '¿Certificaciones del equipo?',
    answer: 'CISSP, CEH, CompTIA Security+, certificaciones de Cisco y Microsoft. Mantenemos certificaciones actualizadas mediante formación continua.',
  },
  {
    question: '¿Ayudan con cumplimiento normativo?',
    answer: 'Sí, asesoramos en GDPR, ISO 27001, PCI-DSS, regulaciones locales. Análisis de brechas y plan de implementación de controles necesarios.',
  },
];

function FAQItem({
  question,
  answer,
  isOpen,
  onClick,
}: {
  question: string;
  answer: string;
  isOpen: boolean;
  onClick: () => void;
}) {
  return (
    <div className="border-b border-foreground last:border-b-0">
      <button onClick={onClick} className="w-full flex items-center justify-between py-5 text-left hover:bg-foreground hover:text-background px-4 -mx-4 transition-all">
        <span className="font-mono font-bold text-foreground">{question}</span>
        <ChevronDown className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="pb-5 px-4 text-sm text-foreground/70 leading-relaxed">
          {answer}
        </div>
      )}
    </div>
  );
}

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="px-4 sm:px-6 lg:px-8 py-20 bg-surface-2">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">PREGUNTAS FRECUENTES</h2>
        <div className="w-16 h-1 bg-foreground mb-12"></div>

        <div className="border border-foreground bg-background">
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
  );
}
