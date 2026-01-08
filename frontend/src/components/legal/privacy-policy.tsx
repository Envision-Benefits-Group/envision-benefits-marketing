"use client"

import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

export function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
      <Navigation />

      <main className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <Button asChild variant="ghost" size="sm" className="mb-4 hover:bg-primary/10 transition-colors">
              <Link href="/">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Home
              </Link>
            </Button>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Privacy Policy</h1>
            <p className="text-gray-600">Last Updated: July 26, 2025</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 mb-8 hover:shadow-xl transition-all duration-300">
            <div className="prose max-w-none">
              <h2 className="text-2xl font-semibold text-primary mb-4">1. Introduction</h2>
              <p>
                Envision Benefits Group ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy
                explains how we collect, use, disclose, and safeguard your information when you use our website,
                services, and applications (collectively, the "Services").
              </p>
              <p>
                Please read this Privacy Policy carefully. By accessing or using our Services, you acknowledge that you
                have read, understood, and agree to be bound by all the terms of this Privacy Policy. If you do not
                agree, please do not access or use our Services.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">2. Information We Collect</h2>
              <p>We may collect several types of information from and about users of our Services, including:</p>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">2.1 Personal Information</h3>
              <p>
                Personal information is data that can be used to identify you individually, such as your name, email
                address, postal address, phone number, and payment information. We collect personal information when
                you:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Register for an account</li>
                <li>Subscribe to our HR Services</li>
                <li>Request HR consultation or support</li>
                <li>Contact our HR experts</li>
                <li>Participate in surveys or feedback sessions</li>
              </ul>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">2.2 Usage and HR Document Information</h3>
              <p>We may collect information about how you interact with our Services, including:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Log data (IP address, browser type, pages visited, time spent)</li>
                <li>Device information (hardware model, operating system)</li>
                <li>HR documents you upload, access, or share (including content, to the extent necessary to provide the service)</li>
                <li>Search queries within the HR vault and chatbot interactions</li>
                <li>Features you use and HR services you access</li>
              </ul>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">2.3 Service Improvement Data</h3>
              <p>To improve our AI models and platform functionality, we may analyze on an aggregated and anonymized basis:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Your interactions with HR platform features</li>
                <li>Feedback you provide on AI-generated HR guidance</li>
                <li>General usage patterns and HR workflows</li>
              </ul>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">3. How We Use Your Information</h2>
              <p>We may use the information we collect for various purposes, including to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Provide, maintain, and improve our HR Services</li>
                <li>Process transactions and manage your account</li>
                <li>Provide HR consultation and support</li>
                <li>Send you HR compliance updates and important notifications</li>
                <li>Respond to your HR questions and requests</li>
                <li>Personalize your HR experience and deliver relevant content</li>
                <li>Monitor and analyze trends, usage, and activities in connection with our Services</li>
                <li>Train and improve our artificial intelligence algorithms for HR guidance in an anonymized, privacy-preserving manner</li>
                <li>Detect, investigate, and prevent fraudulent transactions and other illegal activities</li>
                <li>Comply with legal obligations</li>
              </ul>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">4. AI and Data Processing</h2>
              <p>
                Envision HR Platform uses artificial intelligence to provide HR guidance, analyze policies, and
                generate responses to user queries. By using our Services, you
                acknowledge and consent to:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>The use of AI algorithms to process and analyze HR-related content and questions</li>
                <li>
                  Automated processing to provide HR guidance and policy recommendations
                </li>
                <li>The collection and use of your interaction data to improve our AI models and algorithms as described above</li>
              </ul>
              <p>
                <strong>Important:</strong> We do not use your confidential HR documents or proprietary data to train models for other customers. Our AI model training is limited to aggregated, anonymized data for service improvement.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">5. How We Share Your Information</h2>
              <p>We may share your information in the following circumstances:</p>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">5.1 Service Providers</h3>
              <p>
                We may share your information with third-party vendors, service providers, contractors, or agents who
                perform services for us or on our behalf, such as payment processing (e.g., Stripe), data analysis, AI model hosting (e.g., OpenAI),
                vector databases (e.g., Qdrant), and hosting services (e.g., AWS).
              </p>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">5.2 Business Transfers</h3>
              <p>
                If we are involved in a merger, acquisition, or sale of all or a portion of our assets, your information
                may be transferred as part of that transaction.
              </p>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">5.3 Legal Requirements</h3>
              <p>
                We may disclose your information if required to do so by law or in response to valid requests by public
                authorities (e.g., a court or government agency).
              </p>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">5.4 Protection of Rights</h3>
              <p>
                We may disclose your information to protect and defend the rights, property, or safety of Envision
                Benefits Group, our users, or the public.
              </p>

              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">5.5 With Your Consent</h3>
              <p>We may share your information with third parties when we have your consent to do so, such as when you invite other users into a deal room.</p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">6. Data Security</h2>
              <p>
                We implement appropriate technical and organizational measures to protect the security of your personal
                information. However, please be aware that no method of transmission over the Internet or electronic
                storage is 100% secure, and we cannot guarantee absolute security.
              </p>
              <p>
                We urge you to take steps to keep your personal information safe, including choosing a strong password
                for your account and keeping it private.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">7. Your Data Protection Rights</h2>
              <p>
                Depending on your location, you may have certain rights regarding your personal information, including:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>The right to access your personal information</li>
                <li>The right to rectify inaccurate personal information</li>
                <li>The right to request the deletion of your personal information</li>
                <li>The right to restrict or object to the arocessing of your personal information</li>
                <li>The right to data portability</li>
                <li>The right to withdraw consent</li>
              </ul>
              <p>
                To exercise these rights, please contact us using the information provided in the "Contact Us" section
                below.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">8. Cookies and Tracking Technologies</h2>
              <p>
                We use cookies and similar tracking technologies to track activity on our Services and hold certain
                information. Cookies are files with a small amount of data that may include an anonymous unique
                identifier.
              </p>
              <p>
                You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent. However,
                if you do not accept cookies, you may not be able to use some portions of our Services.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">9. Children's Privacy</h2>
              <p>
                Our Services are not intended for children under the age of 18. We do not knowingly collect personal
                information from children under 18. If you are a parent or guardian and you are aware that your child
                has provided us with personal information, please contact us.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">10. Changes to This Privacy Policy</h2>
              <p>
                We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new
                Privacy Policy on this page and updating the "Last Updated" date.
              </p>
              <p>
                You are advised to review this Privacy Policy periodically for any changes. Changes to this Privacy
                Policy are effective when they are posted on this page.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">11. Contact Us</h2>
              <p>
                If you have any questions about this Privacy Policy, please contact us at{" "}
                <a href="mailto:privacy@envisionbenefitsgroup.com" className="text-primary hover:underline">
                  privacy@envisionbenefitsgroup.com
                </a>
                .
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
