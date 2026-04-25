"use client"

import { useState } from "react"
import { Shield, AlertTriangle, CheckCircle, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface Question {
  id: string
  question: string
  options: { label: string; score: number }[]
}

const questions: Question[] = [
  {
    id: "firewall",
    question: "Tienen un firewall configurado y actualizado?",
    options: [
      { label: "Si, con reglas personalizadas", score: 0 },
      { label: "Si, configuracion basica", score: 1 },
      { label: "No estoy seguro", score: 2 },
      { label: "No tenemos firewall", score: 3 }
    ]
  },
  {
    id: "updates",
    question: "Con que frecuencia actualizan sistemas y software?",
    options: [
      { label: "Automaticamente o semanalmente", score: 0 },
      { label: "Mensualmente", score: 1 },
      { label: "Ocasionalmente", score: 2 },
      { label: "Raramente o nunca", score: 3 }
    ]
  },
  {
    id: "backup",
    question: "Realizan copias de seguridad de datos criticos?",
    options: [
      { label: "Diariamente con pruebas de restauracion", score: 0 },
      { label: "Semanalmente", score: 1 },
      { label: "Mensualmente", score: 2 },
      { label: "No tenemos backups", score: 3 }
    ]
  },
  {
    id: "mfa",
    question: "Utilizan autenticacion multifactor (MFA)?",
    options: [
      { label: "Si, en todos los sistemas criticos", score: 0 },
      { label: "Solo en algunos sistemas", score: 1 },
      { label: "Solo para correo electronico", score: 2 },
      { label: "No usamos MFA", score: 3 }
    ]
  },
  {
    id: "training",
    question: "El personal recibe capacitacion en seguridad?",
    options: [
      { label: "Si, regularmente con simulaciones", score: 0 },
      { label: "Si, una vez al ano", score: 1 },
      { label: "Solo al ingresar a la empresa", score: 2 },
      { label: "No hay capacitacion", score: 3 }
    ]
  },
  {
    id: "wifi",
    question: "Como esta configurada su red WiFi?",
    options: [
      { label: "Redes separadas para empleados e invitados", score: 0 },
      { label: "Una red con contrasena fuerte", score: 1 },
      { label: "Una red con contrasena simple", score: 2 },
      { label: "Red abierta o sin segmentacion", score: 3 }
    ]
  }
]

interface RiskLevel {
  level: string
  color: string
  bgColor: string
  borderColor: string
  icon: typeof Shield
  description: string
  recommendations: string[]
}

function getRiskLevel(score: number): RiskLevel {
  if (score <= 4) {
    return {
      level: "Bajo",
      color: "text-green-400",
      bgColor: "bg-green-500/10",
      borderColor: "border-green-500/30",
      icon: CheckCircle,
      description: "Tu empresa tiene buenas practicas de seguridad. Sin embargo, siempre hay espacio para mejorar.",
      recommendations: [
        "Mantener las practicas actuales",
        "Considerar auditorias periodicas",
        "Evaluar nuevas amenazas emergentes"
      ]
    }
  } else if (score <= 9) {
    return {
      level: "Medio",
      color: "text-yellow-400",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/30",
      icon: AlertTriangle,
      description: "Existen areas de mejora que deberian atenderse para reducir la exposicion a amenazas.",
      recommendations: [
        "Implementar autenticacion multifactor",
        "Revisar politicas de actualizacion",
        "Capacitar al personal regularmente",
        "Evaluar segmentacion de red"
      ]
    }
  } else {
    return {
      level: "Alto",
      color: "text-red-400",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/30",
      icon: AlertTriangle,
      description: "Tu empresa tiene vulnerabilidades significativas que requieren atencion inmediata.",
      recommendations: [
        "Auditoria de seguridad urgente",
        "Implementar controles basicos de seguridad",
        "Establecer politica de copias de seguridad",
        "Capacitacion inmediata del personal",
        "Revision completa de infraestructura"
      ]
    }
  }
}

export function RiskCalculatorSection() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [showResults, setShowResults] = useState(false)

  const handleAnswer = (questionId: string, score: number) => {
    const newAnswers = { ...answers, [questionId]: score }
    setAnswers(newAnswers)

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    } else {
      setShowResults(true)
    }
  }

  const resetCalculator = () => {
    setCurrentQuestion(0)
    setAnswers({})
    setShowResults(false)
  }

  const totalScore = Object.values(answers).reduce((sum, score) => sum + score, 0)
  const riskLevel = getRiskLevel(totalScore)
  const progress = ((currentQuestion + 1) / questions.length) * 100

  return (
    <section id="calculadora" className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border bg-card">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
            Evaluacion Gratuita
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance">
            Calculadora de Riesgo de Seguridad
          </h2>
          <p className="text-muted-foreground text-lg">
            Responde estas preguntas para evaluar el nivel de riesgo de tu empresa.
          </p>
        </div>

        <div className="bg-background border border-border rounded-lg p-6 md:p-8">
          {!showResults ? (
            <>
              {/* Progress bar */}
              <div className="mb-8">
                <div className="flex justify-between text-sm text-muted-foreground mb-2">
                  <span>Pregunta {currentQuestion + 1} de {questions.length}</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Question */}
              <div>
                <h3 className="text-xl font-medium text-foreground mb-6">
                  {questions[currentQuestion].question}
                </h3>
                
                <div className="space-y-3">
                  {questions[currentQuestion].options.map((option, index) => (
                    <button
                      key={index}
                      onClick={() => handleAnswer(questions[currentQuestion].id, option.score)}
                      className="w-full text-left p-4 rounded-lg border border-border bg-card hover:border-primary/50 hover:bg-card/80 transition-colors"
                    >
                      <span className="text-foreground">{option.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : (
            /* Results */
            <div className="text-center">
              <div className={`w-20 h-20 rounded-full ${riskLevel.bgColor} border ${riskLevel.borderColor} flex items-center justify-center mx-auto mb-6`}>
                <riskLevel.icon className={`w-10 h-10 ${riskLevel.color}`} />
              </div>

              <h3 className="text-2xl font-bold text-foreground mb-2">
                Nivel de Riesgo: <span className={riskLevel.color}>{riskLevel.level}</span>
              </h3>
              
              <p className="text-muted-foreground mb-8">
                {riskLevel.description}
              </p>

              <div className="text-left bg-card border border-border rounded-lg p-6 mb-8">
                <h4 className="font-medium text-foreground mb-4">
                  Recomendaciones:
                </h4>
                <ul className="space-y-2">
                  {riskLevel.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-2 text-muted-foreground">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button 
                  variant="outline" 
                  onClick={resetCalculator}
                  className="border-border text-foreground hover:bg-card"
                >
                  Repetir evaluacion
                </Button>
                <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90">
                  <Link href="#contacto">
                    Solicitar auditoria completa
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
