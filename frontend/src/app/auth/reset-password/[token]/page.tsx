"use client"

import { ResetPasswordForm } from "@/components/auth/reset-password-form"

export default function ResetPasswordPage({
  params
}: {
  params: { token: string }
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-emerald-50 flex items-center justify-center p-4">
      <ResetPasswordForm token={params.token} />
    </div>
  )
} 