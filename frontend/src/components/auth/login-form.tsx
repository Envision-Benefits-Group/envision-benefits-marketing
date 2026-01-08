"use client"

import type React from "react"
import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { userAPI } from "@/lib/api";
import { setTokens } from "@/lib/auth";

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { ShieldCheck, Eye, EyeOff, Loader2 } from "lucide-react"
import Link from "next/link"

// Component that handles search params
function LoginFormWithParams() {
  const searchParams = useSearchParams()
  const message = searchParams.get('message')
  
  return <LoginFormContent initialMessage={message} />
}

// Main form component
function LoginFormContent({ initialMessage }: { initialMessage: string | null }) {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [successMessage, setSuccessMessage] = useState(initialMessage || "")
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccessMessage("")
    setLoading(true)

    try {
      const response = await userAPI.login(
        new URLSearchParams({
          username: email.toLowerCase(),
          password: password,
        })
      );

      const { access_token, refresh_token } = response.data;

      // Store the tokens in local storage for further API requests
      setTokens(access_token, refresh_token);

      // Redirect to the dashboard
      router.push("/dashboard");
    } catch (err: any) {
      console.error("Login error:", err)

      if (err.message === "API URL is not defined") {
        setError("Server configuration error. Please contact support.")
      } else if (err.response) {
        const backendMessage = err.response.data?.detail

        if (backendMessage === "Incorrect email or password") {
          setError("Incorrect email or password.")
        } else if (backendMessage === "Inactive user") {
          setError("Your account is inactive. Please contact support.")
        } else if (backendMessage) {
          setError(backendMessage)
        } else if (err.response.status === 401) {
          setError("Invalid credentials.")
        } else {
          setError("An error occurred. Please try again.")
        }
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
        <CardTitle className="text-2xl font-bold">Sign in to Envision HR</CardTitle>
        <CardDescription>Enter your credentials to access your HR platform.</CardDescription>
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
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-gray-400" />
                ) : (
                  <Eye className="h-4 w-4 text-gray-400" />
                )}
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Link href="/auth/forgot-password" className="text-sm text-primary hover:text-primary/80 hover:underline">
              Forgot password?
            </Link>
          </div>

          <Button type="submit" className="w-full bg-primary hover:bg-primary/90" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing In...
              </>
            ) : (
              "Sign In"
            )}
          </Button>
        </form>

        <Separator className="my-6" />

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <Link href="/auth/signup" className="text-primary hover:text-primary/80 hover:underline font-medium">
              Sign up
            </Link>
          </p>
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

// Main export component with Suspense boundary
export function LoginForm() {
  return (
    <Suspense fallback={
      <Card className="w-full max-w-md shadow-xl border-0">
        <CardHeader className="text-center pb-6">
          <div className="flex justify-center mb-4">
            <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
              <ShieldCheck className="h-6 w-6 text-primary-foreground" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Sign in to SecurRoom AI</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
      </Card>
    }>
      <LoginFormWithParams />
    </Suspense>
  )
}
