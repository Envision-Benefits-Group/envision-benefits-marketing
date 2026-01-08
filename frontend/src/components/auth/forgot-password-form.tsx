"use client"

import type React from "react"
import { useState } from "react"
import axios from "axios"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { ShieldCheck, Loader2 } from "lucide-react"
import Link from "next/link"

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("")
  const [error, setError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccessMessage("")
    setLoading(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL
      if (!apiUrl) {
        throw new Error("API URL is not defined")
      }

      const response = await axios.post(
        `${apiUrl}/auth/forgot-password`,
        { email: email.toLowerCase() },
        {
          headers: { "Content-Type": "application/json" },
        }
      )

      // The backend always returns a generic success message, even if user doesn't exist
      setSuccessMessage("If an account with that email exists, an email has been sent.")
      setEmail("")
    } catch (err: any) {
      console.error("Forgot password error:", err)
      if (err.message === "API URL is not defined") {
        setError("Server configuration error. Please contact support.")
      } else if (err.response) {
        const backendMessage = err.response.data?.detail
        setError(backendMessage || "An error occurred. Please try again.")
      } else {
        setError("An error occurred. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md shadow-xl border-0">
      <CardHeader className="text-center pb-6">
        <Link href="/" className="flex justify-center mb-4">
          <img
            src="/logo.png"
            alt="Envision Benefits Group"
            className="h-12 w-auto"
          />
        </Link>
        <CardTitle className="text-2xl font-bold">Forgot Password</CardTitle>
        <CardDescription>Enter your email to receive a password reset link.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {successMessage && (
            <div className="p-3 text-sm text-green-600 bg-green-50 border border-green-200 rounded-md">
              {successMessage}
            </div>
          )}
          
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your account email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <Button type="submit" className="w-full bg-primary hover:bg-primary/90" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              "Send Reset Link"
            )}
          </Button>
        </form>

        <Separator className="my-6" />

        <div className="text-center space-y-4">
          <div>
            <Link href="/auth/login" className="text-sm text-gray-500 hover:text-gray-700 hover:underline font-medium">
              Back to Sign In
            </Link>
          </div>
          
          <div>
            <p className="text-sm text-gray-600">
              Don't have an account?{" "}
              <Link href="/auth/signup" className="text-blue-600 hover:text-blue-800 hover:underline font-medium">
                Sign up
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-700 hover:underline">
            ← Back to home
          </Link>
        </div>
      </CardContent>
    </Card>
  )
} 