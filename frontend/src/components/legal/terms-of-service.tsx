"use client"

import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

export function TermsOfService() {
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
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Terms of Service</h1>
            <p className="text-gray-600">Last Updated: July 15th, 2025</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 mb-8 hover:shadow-xl transition-all duration-300">
            <div className="prose max-w-none">
              <h2 className="text-2xl font-semibold text-primary mb-4">1. Introduction</h2>
              <p>
                Welcome to Envision HR Platform. These Terms of Service ("Terms") govern your use of our website, services,
                and applications (collectively, the "Services") provided by Envision Benefits Group ("we," "us," or "our").
              </p>
              <p>
                By accessing or using our Services, you agree to be bound by these Terms. If you disagree with any part
                of the Terms, you may not access the Services.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">2. AI-Generated Content and Service Disclaimer</h2>
              <p>
                <strong>IMPORTANT:</strong> Envision HR Platform utilizes artificial intelligence to provide HR guidance,
                analyze policies, generate responses to HR questions, and facilitate compliance support. By using our
                Services, you acknowledge and agree to the following:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  AI-generated content is for informational purposes only and should not be considered as
                  definitive legal, compliance, or any other form of professional advice.
                </li>
                <li>
                  HR guidance, policy recommendations, and compliance information are based on algorithms and may contain errors, omissions, or inaccuracies.
                </li>
                <li>
                  You must conduct your own due diligence and consult with qualified HR and legal professionals before making any decisions based on information from the Services.
                </li>
                <li>
                  We do not guarantee the accuracy, completeness, or reliability of any AI-generated content. You are solely responsible for verifying all information.
                </li>
                 <li>
                  Our services provide general HR guidance and templates but do not replace the need for qualified HR professionals and legal counsel.
                </li>
              </ul>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">3. User Accounts</h2>
              <p>
                When you create an account with us, you must provide accurate, complete, and current information. You
                are responsible for safeguarding the password and for all activities that occur under your account, including actions taken by users you invite.
              </p>
              <p>
                You agree to notify us immediately of any unauthorized use of your account or any other breach of
                security. We will not be liable for any loss or damage arising from your failure to comply with this
                section.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">4. Subscription and Payments</h2>
              <p>
                Our Services are provided on a subscription basis. By subscribing, you agree to pay all fees in accordance with the pricing and terms in effect.
              </p>
              <p>
                You are responsible for providing complete and accurate billing information. If automatic billing fails,
                we may suspend your access to the Services until payment is received.
              </p>
              <p>
                Subscription fees are non-refundable except as expressly set forth in these Terms or as required by
                applicable law.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">5. Intellectual Property</h2>
              <p>
                The Services and their original content (excluding User Content), features, and functionality are and will remain the exclusive
                property of Envision HR Platform and its licensors. The Services are protected by copyright, trademark, and
                other laws.
              </p>
              <p>
                Our trademarks and trade dress may not be used in connection with any product or service without the
                prior written consent of Envision HR Platform.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">6. User Content and Responsibility</h2>
              <p>
                Our Services allow you to upload, store, and share documents, data, and other information ("User Content") within your HR platform. You are solely responsible for the
                User Content that you post, including its legality, reliability, and appropriateness.
              </p>
              <p>
                You represent and warrant that you have all the necessary rights, licenses, and permissions to upload and share the User Content within the Services. By uploading User Content, you grant us a limited license to use, process, and display such content solely for the purpose of providing the HR Services to you.
              </p>
              <p>We do not claim ownership of your User Content. You retain any and all of your rights to any User Content you submit.</p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">7. Prohibited Uses</h2>
              <p>You agree not to use the Services:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  In any way that violates any applicable federal, state, local, or international law or regulation.
                </li>
                <li>
                  To upload or transmit any material that is illegal, defamatory, or infringes on the rights of any third party.
                </li>
                <li>
                  To impersonate or attempt to impersonate Envision HR Platform, an Envision HR Platform employee, another
                  user, or any other person or entity.
                </li>
                <li>
                  To engage in any other conduct that restricts or inhibits anyone's use or enjoyment of the Services,
                  or which may harm Envision HR Platform or users of the Services.
                </li>
              </ul>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">8. Limitation of Liability</h2>
              <p>
                IN NO EVENT SHALL ENVISION HR PLATFORM, ITS OFFICERS, DIRECTORS, EMPLOYEES, OR AGENTS, BE LIABLE TO YOU FOR
                ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, PUNITIVE, OR CONSEQUENTIAL DAMAGES WHATSOEVER RESULTING FROM
                ANY:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>ERRORS, MISTAKES, OR INACCURACIES IN AI-GENERATED CONTENT OR OTHER CONTENT;</li>
                <li>PERSONAL INJURY OR PROPERTY DAMAGE OF ANY NATURE WHATSOEVER;</li>
                <li>
                  UNAUTHORIZED ACCESS TO OR USE OF OUR SECURE SERVERS AND/OR ANY PERSONAL INFORMATION STORED THEREIN;
                </li>
                <li>INTERRUPTION OR CESSATION OF TRANSMISSION TO OR FROM OUR SERVICES;</li>
                <li>BUGS, VIRUSES, TROJAN HORSES, OR THE LIKE THAT MAY BE TRANSMITTED TO OR THROUGH OUR SERVICES;</li>
                <li>
                  FINANCIAL OR BUSINESS LOSSES INCURRED AS A RESULT OF RELIANCE ON THE SERVICES OR AI-GENERATED CONTENT;
                </li>
                <li>
                  ERRORS OR OMISSIONS IN ANY CONTENT OR FOR ANY LOSS OR DAMAGE INCURRED AS A RESULT OF THE USE OF ANY
                  CONTENT POSTED, TRANSMITTED, OR OTHERWISE MADE AVAILABLE THROUGH THE SERVICES.
                </li>
              </ul>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">9. Indemnification</h2>
              <p>
                You agree to defend, indemnify, and hold harmless Envision HR Platform and its licensees and licensors, and
                their employees, contractors, agents, officers, and directors, from and against any and all claims,
                damages, obligations, losses, liabilities, costs or debt, and expenses (including but not limited to
                attorney's fees) arising from:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Your use of and access to the Services;</li>
                <li>Your violation of any term of these Terms;</li>
                <li>
                  Your violation of any third-party right, including without limitation any copyright, property, or
                  privacy right;
                </li>
                <li>Any claim that your User Content caused damage to a third party.</li>
              </ul>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">10. Termination</h2>
              <p>
                We may terminate or suspend your account and bar access to the Services immediately, without prior
                notice or liability, under our sole discretion, for any reason whatsoever and without limitation,
                including but not limited to a breach of the Terms.
              </p>
              <p>
                If you wish to terminate your account, you may simply discontinue using the Services or contact us to
                request account deletion.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">11. Governing Law</h2>
              <p>
                These Terms shall be governed and construed in accordance with the laws of the State of Delaware, United
                States, without regard to its conflict of law provisions.
              </p>
              <p>
                Our failure to enforce any right or provision of these Terms will not be considered a waiver of those
                rights. If any provision of these Terms is held to be invalid or unenforceable by a court, the remaining
                provisions of these Terms will remain in effect.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">12. Changes to Terms</h2>
              <p>
                We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a
                revision is material, we will provide at least 30 days' notice prior to any new terms taking effect.
                What constitutes a material change will be determined at our sole discretion.
              </p>
              <p>
                By continuing to access or use our Services after any revisions become effective, you agree to be bound
                by the revised terms. If you do not agree to the new terms, you are no longer authorized to use the
                Services.
              </p>

              <h2 className="text-2xl font-semibold text-primary mt-8 mb-4">13. Contact Us</h2>
              <p>
                If you have any questions about these Terms, please contact us at{" "}
                <a href="mailto:legal@envisionbenefitsgroup.com" className="text-primary hover:underline">
                  legal@envisionbenefitsgroup.com
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
