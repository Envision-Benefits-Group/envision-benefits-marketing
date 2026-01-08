"use client"

import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  ArrowRight,
  BarChart3,
  Check,
  ChevronDown,
  ChevronUp,
  FileText,
  Users,
  ShieldCheck,
  BookOpen,
  BotMessageSquare,
  MessageSquare,
} from "lucide-react"
import Link from "next/link"
import { Navigation } from "@/components/navigation"
import { useState } from "react"

const faqData = [
  {
    question: "What types of HR services does the Envision HR Platform provide?",
    answer:
      "Our platform offers comprehensive HR support including compliance management, employee handbook creation, on-call HR support, recruitment assistance, performance management, benefits administration, and customized training programs.",
  },
  {
    question: "How does the AI-powered HR chatbot work?",
    answer:
      "You can ask HR-related questions in plain English and get instant answers based on current labor laws, HR best practices, and your company's specific policies. The chatbot provides guidance while ensuring you have access to human expertise when needed.",
  },
  {
    question: "Is my company data secure on the platform?",
    answer:
      "Absolutely. We use industry-standard encryption and secure cloud infrastructure to protect your sensitive HR data. Our platform includes role-based access controls and complies with all relevant data protection regulations.",
  },
  {
    question: "What's included in the Digital HR Vault?",
    answer:
      "The Digital HR Vault contains essential HR templates including job descriptions, offer letters, termination checklists, employee handbooks, policy templates, and compliance documents. All documents are regularly updated to reflect current legal requirements.",
  },
  {
    question: "How quickly can I get started with HR support?",
    answer:
      "You can get started immediately after signup. Access to the Digital HR Vault and AI chatbot is instant, and we'll schedule your first consultation call within 24-48 hours to begin personalized HR support.",
  },
]

export function LandingPage() {
  const [openFAQ, setOpenFAQ] = useState<number | null>(null)

  const toggleFAQ = (index: number) => {
    setOpenFAQ(openFAQ === index ? null : index)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
      <Navigation />

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="text-left">
              <Badge variant="outline" className="mb-6 bg-primary/10 text-primary border-primary/20 animate-fadeIn">
                SCALABLE HR PARTNERSHIP
              </Badge>
              <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 animate-fadeIn">
                Your Scalable,
                <span className="block text-primary">Outsourced HR Partner.</span>
              </h1>
              <p className="text-xl md:text-2xl text-gray-600 mb-8 leading-relaxed animate-fadeIn">
                Empower your SMB with self-service HR resources, AI-powered assistance, and on-demand access to human expertise—all through one intuitive platform.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-12 animate-fadeIn">
                <Button
                  asChild
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-lg px-8 py-6 transform hover:scale-105 transition-all duration-200"
                >
                  <Link href="/auth/signup">
                    Get Started Today <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="text-lg px-8 py-6 hover:bg-primary/5 transition-all duration-200"
                >
                  <Link href="/auth/login">Sign In</Link>
                </Button>
              </div>
            </div>

            <div className="relative animate-fadeIn">
              <div className="relative bg-gradient-to-br from-gray-100 to-blue-100 rounded-2xl p-8 shadow-2xl transform hover:scale-105 transition-all duration-300">
                <img
                  src="/hero.jpg"
                  alt="Envision HR Platform Preview"
                  className="w-full h-auto rounded-lg shadow-lg"
                />
                <div className="absolute -top-4 -right-4 bg-white rounded-full p-3 shadow-lg animate-pulse">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <div className="absolute -bottom-4 -left-4 bg-white rounded-full p-3 shadow-lg animate-pulse">
                  <ShieldCheck className="h-6 w-6 text-primary" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Everything Your Business Needs for HR Success</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Reduce compliance risks, streamline operations, and focus on growing your business with our comprehensive HR platform.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Digital HR Vault</CardTitle>
                <CardDescription>
                  Access essential HR templates, policies, and documents. Download job descriptions, offer letters, handbooks, and compliance materials anytime.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <BotMessageSquare className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>AI-Powered HR Assistance</CardTitle>
                <CardDescription>
                  Get instant answers to HR questions with our intelligent chatbot. Access guidance on compliance, policies, and best practices 24/7.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>On-Demand Human Expertise</CardTitle>
                <CardDescription>
                  Schedule calls with certified HR professionals. Get personalized guidance for complex situations and strategic HR decisions.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <MessageSquare className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Support Ticketing System</CardTitle>
                <CardDescription>
                  Submit HR questions and requests through our integrated ticketing system. Track your inquiries and get expert responses.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <BookOpen className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Training & Development</CardTitle>
                <CardDescription>
                  Access unlimited electronic compliance training and customized training sessions to keep your team informed and compliant.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <ShieldCheck className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Compliance Management</CardTitle>
                <CardDescription>
                  Stay up-to-date with labor laws and regulations. Receive proactive compliance updates and audit support to minimize risks.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Pricing Preview Section */}
      <section className="py-20 px-4 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Fractional HR for Less Than the Cost of One Hire</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Choose the HR support level that fits your business size and needs.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {/* Shield HR Essentials */}
            <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <ShieldCheck className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle className="text-xl">Shield HR Essentials</CardTitle>
                <CardDescription>For companies with 1–49 employees</CardDescription>
                <div className="mt-4">
                  <span className="text-3xl font-bold">$1,500+</span>
                  <span className="text-gray-500">/month</span>
                </div>
              </CardHeader>
              <CardContent className="text-center">
                <ul className="space-y-3 text-gray-600 mb-6">
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />4–6 hours HR consulting
                  </li>
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />On-call HR support
                  </li>
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />Unlimited compliance training
                  </li>
                </ul>
                <Button asChild className="w-full">
                  <Link href="/auth/signup">Get Started</Link>
                </Button>
              </CardContent>
            </Card>

            {/* Elevate HR Essentials (Highlighted) */}
            <Card className="border-2 border-primary shadow-2xl hover:shadow-primary/20 transition-all duration-300 hover:-translate-y-1 relative">
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary">Most Popular</Badge>
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">Elevate HR Essentials</CardTitle>
                <CardDescription>For businesses with 25–99 employees</CardDescription>
                <div className="mt-4">
                  <span className="text-3xl font-bold">$2,000+</span>
                  <span className="text-gray-500">/month</span>
                </div>
              </CardHeader>
              <CardContent className="text-center">
                <ul className="space-y-3 text-gray-600 mb-6">
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />
                    8–12 hours HR consulting
                  </li>
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />
                    Recruitment support
                  </li>
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />
                    Performance management
                  </li>
                </ul>
                <Button asChild className="w-full bg-primary hover:bg-primary/90">
                  <Link href="/auth/signup">Choose Plan</Link>
                </Button>
              </CardContent>
            </Card>

            {/* Strategic HR Partner */}
            <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle className="text-xl">Strategic HR Partner</CardTitle>
                <CardDescription>For companies with 75–250+ employees</CardDescription>
                <div className="mt-4">
                  <span className="text-3xl font-bold">$2,500+</span>
                  <span className="text-gray-500">/month</span>
                </div>
              </CardHeader>
              <CardContent className="text-center">
                <ul className="space-y-3 text-gray-600 mb-6">
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />
                    12–20+ hours consulting
                  </li>
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />
                    HRIS implementation
                  </li>
                  <li className="flex items-center justify-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />
                    Strategic leadership
                  </li>
                </ul>
                <Button asChild variant="outline" className="w-full">
                  <Link href="/contact">Contact Sales</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
          <div className="text-center">
            <Link href="/pricing" className="text-primary hover:underline">
              See all features and compare plans <ArrowRight className="inline h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Get Started in Minutes</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Experience the complete HR platform workflow from signup to expert consultation.
            </p>
          </div>
          <div className="relative">
            <div
              className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-200"
              style={{ transform: "translateX(-50%)" }}
            ></div>
            <div className="space-y-16">
              <div className="flex items-center justify-between">
                <div className="w-5/12">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">1. Sign Up & Access Resources</h3>
                  <p className="text-gray-600">Create your account and immediately access the Digital HR Vault with essential templates and documents.</p>
                </div>
                <div className="w-2/12 flex justify-center">
                  <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center z-10">1</div>
                </div>
                <div className="w-5/12"></div>
              </div>
              <div className="flex items-center justify-between">
                <div className="w-5/12"></div>
                <div className="w-2/12 flex justify-center">
                  <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center z-10">2</div>
                </div>
                <div className="w-5/12 text-right">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">2. Get AI-Powered Answers</h3>
                  <p className="text-gray-600">Ask the AI chatbot any HR questions and receive instant guidance based on current laws and best practices.</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="w-5/12">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">3. Schedule Expert Consultation</h3>
                  <p className="text-gray-600">Book a call with certified HR professionals for personalized guidance and strategic planning.</p>
                </div>
                <div className="w-2/12 flex justify-center">
                  <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center z-10">3</div>
                </div>
                <div className="w-5/12"></div>
              </div>
              <div className="flex items-center justify-between">
                <div className="w-5/12"></div>
                <div className="w-2/12 flex justify-center">
                  <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center z-10">4</div>
                </div>
                <div className="w-5/12 text-right">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">4. Submit Support Requests</h3>
                  <p className="text-gray-600">Use the ticketing system for ongoing HR support and track your requests through our admin dashboard.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h2>
            <p className="text-xl text-gray-600">
              Have questions? We've got answers. If you can't find what you're looking for, feel free to contact us.
            </p>
          </div>
          <div className="space-y-4">
            {faqData.map((faq, index) => (
              <Collapsible key={index} onOpenChange={() => toggleFAQ(index)}>
                <CollapsibleTrigger className="w-full">
                  <Card className="flex items-center justify-between p-6 hover:bg-gray-100 transition-colors">
                    <h3 className="text-lg font-semibold text-left">{faq.question}</h3>
                    {openFAQ === index ? (
                      <ChevronUp className="h-6 w-6" />
                    ) : (
                      <ChevronDown className="h-6 w-6" />
                    )}
                  </Card>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <CardContent className="p-6">
                    <p className="text-gray-600">{faq.answer}</p>
                  </CardContent>
                </CollapsibleContent>
              </Collapsible>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-primary">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-4">Ready to Transform Your HR Operations?</h2>
          <p className="text-xl text-primary-foreground/80 mb-8">
            Join hundreds of SMBs who trust Envision HR Platform for their human resources needs.
          </p>
          <Button asChild size="lg" variant="secondary" className="text-lg px-8 py-6">
            <Link href="/auth/signup">
              Get Started Now <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <h3 className="text-2xl font-bold">Envision HR Platform</h3>
            <p className="text-gray-400">Your Scalable, Outsourced HR Partner</p>
          </div>
          <div className="flex space-x-6">
            <Link href="/terms" className="hover:text-primary">
              Terms
            </Link>
            <Link href="/privacy" className="hover:text-primary">
              Privacy
            </Link>
            <Link href="/contact" className="hover:text-primary">
              Contact
            </Link>
          </div>
        </div>
        <div className="mt-8 text-center text-gray-500 border-t border-gray-700 pt-4">
          <p>&copy; {new Date().getFullYear()} Envision Benefits Group. All Rights Reserved.</p>
        </div>
      </footer>
    </div>
  )
}
