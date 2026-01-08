'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import Image from 'next/image';

// Spinner Component
const Spinner = () => (
  <svg
    className="animate-spin h-5 w-5 mr-2 text-white"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"
    ></circle>
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8v8H4z"
    ></path>
  </svg>
);

export default function AdminLoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (localStorage.getItem('admin_token')) {
      router.push('/admin/dashboard'); // Frontend path remains /admin/dashboard
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('API URL is not defined');
      }

      const response = await axios.post(
        `${apiUrl}/admin/login/access-token`, // Updated API endpoint
        new URLSearchParams({
          username: email.toLowerCase(), 
          password: password,
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      const { access_token } = response.data;
      localStorage.setItem('admin_token', access_token);
      router.push('/admin/dashboard'); // Frontend path remains /admin/dashboard
    } catch (err: any) {
      console.error('Admin login error:', err);
      if (err.message === 'API URL is not defined') {
        setError('Server configuration error. Please contact support.');
      } else if (err.response) {
        const backendMessage = err.response.data?.detail;
        if (backendMessage === 'Incorrect username or password') {
          setError('Incorrect username or password.');
        } else if (backendMessage === 'User does not have superuser privileges') {
          setError('Access denied. Superuser privileges required.');
        } else if (backendMessage) {
          setError(backendMessage);
        } else if (err.response.status === 401 || err.response.status === 403) {
          setError('Invalid credentials or insufficient permissions.');
        } else {
          setError('An error occurred. Please try again.');
        }
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-200 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/">
          <Image
            src="/logo.png" 
            alt="Scale8UP Admin"
            width={180}
            height={48}
            className="mx-auto"
            priority
          />
        </Link>
      </div>

      <Card className="sm:mx-auto sm:w-full sm:max-w-md mt-8">
        <CardHeader>
          <CardTitle className="text-center text-2xl font-bold text-slate-900">
            Admin Panel Login
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-1">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full"
                placeholder="admin@example.com"
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full"
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-slate-800 hover:bg-slate-900 text-white flex items-center justify-center"
            >
              {loading && <Spinner />}
              Log in
            </Button>
          </form>
        </CardContent>
        <CardFooter className="text-center text-sm">
          <p>Access to this panel is restricted to authorized personnel only.</p>
        </CardFooter>
      </Card>
    </div>
  );
} 