"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, ArrowRight, Users, ShieldCheck, BarChart3, Clock, BookOpen, Phone } from "lucide-react"
import Link from "next/link"
import { Navigation } from "@/components/navigation"

const pricingPlans = [
  {
    name: "Shield HR Essentials",
    description: "Fractional HR for Less Than the Cost of One Hire!",
    subtitle: "Companies with 1–49 employees",
    monthlyPrice: "1,500+",
    icon: ShieldCheck,
    color: "blue",
    features: [
      "4–6 hours of HR consulting per month",
      "On-call HR support for day-to-day HR questions",
      "Quarterly check-in meetings",
      "Unlimited electronic compliance training",
      "Ongoing handbook review and updates",
      "Standard HR templates (job descriptions, offer letters, termination checklists)",
      "Compliance email updates",
      "Customized onboarding platform",
    ],
  },
  {
    name: "Elevate HR Essentials",
    description: "Fractional HR for Less Than the Cost of One Hire!",
    subtitle: "Businesses with 25–99 employees",
    monthlyPrice: "2,000+",
    icon: Users,
    color: "primary",
    popular: true,
    features: [
      "8–12 hours of HR consulting per month",
      "Everything in Shield",
      "Monthly check-in meetings",
      "Recruitment support (job postings, screening, interview guidance)",
      "Performance management (reviews, performance improvement plans)",
      "Benefits administration support",
      "Proactive compliance audits and updates",
      "Two customized training sessions annually",
    ],
  },
  {
    name: "Strategic HR Partner",
    description: "Fractional HR for Less Than the Cost of One Hire!",
    subtitle: "Companies with 75–250+ employees",
    monthlyPrice: "2,500+",
    icon: BarChart3,
    color: "gray",
    features: [
      "12–20+ hours of consulting and executive advising per month",
      "Everything in Elevate & Shield",
      "HRIS or ATS implementation and/or support",
      "Quarterly leadership strategy sessions",
      "Succession planning, compensation benchmarking, org development",
      "Employee engagement surveys with action planning",
      "Monthly onsite or virtual executive coaching",
      "Four customized training sessions annually",
      "State and Federal leave management and tracking",
    ],
  },
]

const addOnServices = [
  {
    name: "Customized Employee Handbook Build",
    price: "$1,500",
    type: "one-time fee",
  },
  {
    name: "Additional HR Consulting or Project Support",
    price: "$175",
    type: "per hour",
  },
  {
    name: "Payroll Processing",
    price: "$250–$1,000",
    type: "per month",
    note: "Based on company size and complexity – Proposal Required",
  },
  {
    name: "Leave Management Administration",
    price: "Proposal required",
    type: "",
  },
  {
    name: "Workplace Investigations",
    price: "Proposal Required",
    type: "",
  },
  {
    name: "Benefits Administration & Technology Services",
    price: "Proposal required",
    type: "",
  },
]

export function PricingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
      <Navigation />

      <main className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <Badge variant="outline" className="mb-6 bg-primary/10 text-primary border-primary/20 animate-fadeIn">
              HR Subscription Packages
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 animate-fadeIn">
              Choose Your Envision HR Plan
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8 animate-fadeIn">
              Fractional HR for less than the cost of one hire! Dependent upon state(s), complexity and number of employees.
            </p>
          </div>

          {/* Pricing Cards */}
          <div className="grid lg:grid-cols-3 gap-8 mb-16 items-start">
            {pricingPlans.map((plan, index) => {
              const IconComponent = plan.icon
              
              return (
                <Card
                  key={plan.name}
                  className={`relative shadow-lg border-0 hover:shadow-xl transition-all duration-300 hover:-translate-y-2 animate-fadeIn ${
                    plan.popular ? "ring-2 ring-primary scale-105" : ""
                  }`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-primary hover:bg-primary text-primary-foreground px-4 py-1">Most Popular</Badge>
                    </div>
                  )}

                  <CardHeader className="text-center pb-6">
                    <div
                      className={`w-12 h-12 mx-auto mb-4 rounded-lg flex items-center justify-center bg-primary/10`}
                    >
                      <IconComponent
                        className={`h-6 w-6 text-primary`}
                      />
                    </div>
                    <CardTitle className="text-xl font-bold">{plan.name}</CardTitle>
                    <CardDescription className="text-gray-600 font-medium mb-2">{plan.description}</CardDescription>
                    <CardDescription className="text-gray-500 text-sm">{plan.subtitle}</CardDescription>
                    <div className="mt-6">
                      <div className="flex items-baseline justify-center">
                        <span className="text-3xl font-bold">Starting at ${plan.monthlyPrice}</span>
                        <span className="text-gray-500 ml-1">/month</span>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-6">
                    <Button
                      asChild
                      className={`w-full transition-all duration-200 hover:scale-105 ${
                        plan.popular
                          ? "bg-primary hover:bg-primary/90"
                          : "bg-gray-800 hover:bg-gray-900"
                      }`}
                    >
                      <Link href="/auth/signup">
                        Get Started <ArrowRight className="ml-2 h-4 w-4" />
                      </Link>
                    </Button>

                    <div className="space-y-3">
                      <h4 className="font-semibold text-gray-900">What's included:</h4>
                      <ul className="space-y-2">
                        {plan.features.map((feature, idx) => (
                          <li key={idx} className="flex items-start gap-3">
                            <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-gray-600">{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Add-On Services Section */}
          <div className="mb-16">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Optional Add-On Services</h2>
              <p className="text-xl text-gray-600">
                These services can be added to any tier for additional customization
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {addOnServices.map((service, index) => (
                <Card key={service.name} className="border-0 shadow-md hover:shadow-lg transition-shadow">
                  <CardHeader className="text-center pb-4">
                    <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                      <BookOpen className="h-5 w-5 text-accent" />
                    </div>
                    <CardTitle className="text-lg">{service.name}</CardTitle>
                    <div className="mt-3">
                      <span className="text-2xl font-bold text-primary">{service.price}</span>
                      {service.type && <span className="text-gray-500 text-sm ml-1">{service.type}</span>}
                    </div>
                    {service.note && (
                      <p className="text-xs text-gray-500 mt-2">{service.note}</p>
                    )}
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>

          {/* Contact Banner */}
          <div className="bg-gradient-to-r from-primary to-blue-800 rounded-2xl p-8 text-center text-white mb-16 animate-fadeIn">
            <h3 className="text-2xl font-bold mb-4">Ready to Get Started?</h3>
            <p className="text-lg mb-6 opacity-90">
              Contact our HR experts to discuss which plan is right for your business and get a customized proposal.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild variant="secondary">
                <Link href="/contact">
                  Contact Sales <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" className="border-white text-white hover:bg-white hover:text-primary">
                <Link href="/auth/signup">
                  Get Started Now
                </Link>
              </Button>
            </div>
          </div>

          {/* FAQ Section */}
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">Pricing FAQ</h2>
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="font-semibold mb-2">How is pricing determined?</h3>
                <p className="text-gray-600">
                  Pricing is dependent upon your state(s), business complexity, and number of employees. The listed prices are starting points, and we'll provide a customized proposal based on your specific needs.
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="font-semibold mb-2">What's included in all tiers?</h3>
                <p className="text-gray-600">
                  All tiers include leave management & tracking, customized onboarding platform, ongoing employee handbook updates, benefits administration support, recruitment support, and performance management assistance.
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="font-semibold mb-2">Can I add services later?</h3>
                <p className="text-gray-600">
                  Yes! You can upgrade your plan or add any of our optional services at any time. We'll work with you to adjust your package as your business grows and your HR needs evolve.
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="font-semibold mb-2">What kind of support do I get?</h3>
                <p className="text-gray-600">
                  All plans include on-call HR support for day-to-day questions. Higher tiers include more consulting hours, regular check-ins, and strategic guidance from certified HR professionals.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
