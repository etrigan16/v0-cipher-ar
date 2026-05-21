'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle, Shield } from 'lucide-react';

interface Question {
  id: string;
  question: string;
  options: { label: string; score: number }[];
}

const questions: Question[] = [
  {
    id: 'firewall',
    question: '¿Tienen firewall configurado y actualizado?',
    options: [
      { label: 'Sí, con reglas personalizadas', score: 0 },
      { label: 'Sí, configuración básica', score: 1 },
      { label: 'No estoy seguro', score: 2 },
      { label: 'No tenemos firewall', score: 3 },
    ],
  },
  {
    id: 'updates',
    question: '¿Con qué frecuencia actualizan sistemas y software?',
    options: [
      { label: 'Automáticamente o semanalmente', score: 0 },
      { label: 'Mensualmente', score: 1 },
      { label: 'Ocasionalmente', score: 2 },
      { label: 'Raramente o nunca', score: 3 },
    ],
  },
  {
    id: 'backup',
    question: '¿Realizan copias de seguridad de datos críticos?',
    options: [
      { label: 'Diariamente con pruebas de restauración', score: 0 },
      { label: 'Semanalmente', score: 1 },
      { label: 'Mensualmente', score: 2 },
      { label: 'No tenemos backups', score: 3 },
    ],
  },
  {
    id: 'mfa',
    question: '¿Utilizan autenticación multifactor (MFA)?',
    options: [
      { label: 'Sí, en todos los sistemas críticos', score: 0 },
      { label: 'Solo en algunos sistemas', score: 1 },
      { label: 'No, pero conocemos MFA', score: 2 },
      { label: 'No sabemos qué es MFA', score: 3 },
    ],
  },
  {
    id: 'monitoring',
    question: '¿Monitorean logs y alertas de seguridad?',
    options: [
      { label: 'Sí, continuamente con SIEM', score: 0 },
      { label: 'Sí, periodicamente manualmente', score: 1 },
      { label: 'Ocasionalmente', score: 2 },
      { label: 'No monitoreamos', score: 3 },
    ],
  },
  {
    id: 'training',
    question: '¿Capacitan al equipo sobre seguridad?',
    options: [
      { label: 'Sí, anualmente con simulaciones', score: 0 },
      { label: 'Sí, ocasionalmente', score: 1 },
      { label: 'No, pero lo consideramos importante', score: 2 },
      { label: 'No hay capacitación', score: 3 },
    ],
  },
];

interface RiskLevel {
  level: string;
  color: string;
  bgColor: string;
  recommendations: string[];
}

const riskLevels: Record<string, RiskLevel> = {
  critical: {
    level: 'CRÍTICO',
    color: 'text-foreground',
    bgColor: 'bg-background',
    recommendations: [
      'Contactar a Cipher.ar URGENTEMENTE para auditoría de emergencia',
      'Implementar firewall y segmentación de red inmediatamente',
      'Establecer plan de backup diario con almacenamiento seguro',
      'Implementar MFA en todos los accesos administrativos',
      'Activar monitoreo continuo de logs',
    ],
  },
  high: {
    level: 'ALTO',
    color: 'text-foreground',
    bgColor: 'bg-background',
    recommendations: [
      'Agendar auditoría de seguridad completa en los próximos 30 días',
      'Revisar y fortalecer configuración de firewall',
      'Implementar MFA como prioridad',
      'Establecer ciclo de actualizaciones automatizado',
      'Iniciar programa de capacitación en seguridad',
    ],
  },
  medium: {
    level: 'MEDIO',
    color: 'text-foreground',
    bgColor: 'bg-background',
    recommendations: [
      'Realizar auditoría de seguridad en próximos 60 días',
      'Expandir MFA a todos los sistemas relevantes',
      'Mejorar frecuencia de backups',
      'Implementar monitoreo de logs centralizado',
      'Planificar capacitaciones regulares',
    ],
  },
  low: {
    level: 'BAJO',
    color: 'text-foreground',
    bgColor: 'bg-background',
    recommendations: [
      'Mantener vigilancia continua de su postura de seguridad',
      'Realizar auditoría anual como validación',
      'Considerar implementar SIEM para mayor visibilidad',
      'Continuar con capacitaciones regulares',
      'Mantenerse actualizado sobre nuevas amenazas',
    ],
  },
};

export function RiskCalculatorSection() {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [showResult, setShowResult] = useState(false);

  const handleAnswer = (score: number) => {
    const questionId = questions[currentQuestion].id;
    setScores({ ...scores, [questionId]: score });

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      setShowResult(true);
    }
  };

  const totalScore = Object.values(scores).reduce((a, b) => a + b, 0);
  const maxScore = questions.length * 3;
  const riskPercentage = Math.round((totalScore / maxScore) * 100);

  let riskKey: string;
  if (riskPercentage >= 75) riskKey = 'critical';
  else if (riskPercentage >= 50) riskKey = 'high';
  else if (riskPercentage >= 25) riskKey = 'medium';
  else riskKey = 'low';

  const risk = riskLevels[riskKey];

  return (
    <section id="riesgos" className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">CALCULADORA DE RIESGOS</h2>
        <div className="w-16 h-1 bg-foreground mb-12"></div>

        {!showResult ? (
          <div className="border border-foreground p-8 bg-background">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <p className="font-mono text-sm text-foreground/60">
                  PREGUNTA {currentQuestion + 1} DE {questions.length}
                </p>
                <div className="w-32 h-1 bg-foreground/20 overflow-hidden">
                  <div
                    className="h-full bg-foreground transition-all duration-300"
                    style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <h3 className="text-2xl font-bold text-foreground font-mono mb-8">
              {questions[currentQuestion].question}
            </h3>

            <div className="space-y-3">
              {questions[currentQuestion].options.map((option, i) => (
                <button
                  key={i}
                  onClick={() => handleAnswer(option.score)}
                  className="w-full text-left px-6 py-4 border border-foreground bg-background hover:bg-foreground hover:text-background transition-all font-mono text-sm"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="border border-foreground p-12 bg-background">
            <div className="text-center mb-12">
              <div className="flex justify-center mb-6">
                {riskPercentage >= 50 ? (
                  <AlertTriangle className="w-16 h-16 text-foreground" />
                ) : (
                  <CheckCircle className="w-16 h-16 text-foreground" />
                )}
              </div>

              <p className="text-sm font-mono text-foreground/60 mb-2">NIVEL DE RIESGO</p>
              <h3 className="text-4xl font-bold text-foreground font-mono mb-4">{risk.level}</h3>
              <p className="text-2xl font-mono text-foreground mb-8">{riskPercentage}% de riesgo</p>
            </div>

            <div className="border-t border-b border-foreground py-8 mb-8">
              <h4 className="font-bold font-mono text-foreground mb-6">RECOMENDACIONES INMEDIATAS</h4>
              <ul className="space-y-4">
                {risk.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-3 text-foreground/80 text-sm">
                    <span className="text-foreground font-bold mt-1">→</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>

            <div className="text-center">
              <a
                href="#contacto"
                className="inline-flex items-center gap-2 px-8 py-4 bg-foreground text-background font-bold font-mono border border-foreground hover:opacity-80 transition-opacity"
              >
                <Shield size={20} />
                SOLICITAR AUDITORÍA AHORA
              </a>
            </div>

            <button
              onClick={() => {
                setCurrentQuestion(0);
                setScores({});
                setShowResult(false);
              }}
              className="block mx-auto mt-8 text-foreground/60 hover:text-foreground font-mono text-sm underline transition-colors"
            >
              Hacer el test nuevamente
            </button>
          </div>
        )}
      </div>
    </section>
  );
}


