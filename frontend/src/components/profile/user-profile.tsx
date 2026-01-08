"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/hooks/use-toast"
import {
  User,
  Mail,
  Building,
  Calendar,
  Shield,
  Bell,
  CreditCard,
  Eye,
  EyeOff,
  Save,
  ArrowLeft,
  Loader2,
} from "lucide-react"
import Link from "next/link"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { userAPI } from "@/lib/api"

interface UserData {
  id: number
  name: string
  email: string
  organization: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string | null
}

export function UserProfile() {
  const { toast } = useToast()
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)

  const [userData, setUserData] = useState<UserData | null>(null)
  const [profileData, setProfileData] = useState({
    name: "",
    organization: "",
  })

  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  })

  const [notifications, setNotifications] = useState({
    hrUpdates: true,
    complianceAlerts: true,
    supportResponses: true,
    hrReports: false,
  })

  // Fetch current user data on component mount
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await userAPI.getCurrentUser()
        const user = response.data
        setUserData(user)
        setProfileData({
          name: user.name || "",
          organization: user.organization || "",
        })
      } catch (error) {
        console.error("Error fetching user data:", error)
        toast({
          title: "Error",
          description: "Failed to load user data. Please try again.",
          variant: "destructive",
        })
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [toast])

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setUpdating(true)

    try {
      const response = await userAPI.updateCurrentUser(profileData)
      const updatedUser = response.data
      setUserData(updatedUser)
      toast({
        title: "Success",
        description: "Profile updated successfully!",
      })
    } catch (error: any) {
      console.error("Profile update error:", error)
      const errorMessage = error.response?.data?.detail || "Failed to update profile. Please try again."
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setUpdating(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast({
        title: "Error",
        description: "New passwords do not match.",
        variant: "destructive",
      })
      return
    }

    if (passwordData.newPassword.length < 8) {
      toast({
        title: "Error", 
        description: "Password must be at least 8 characters long.",
        variant: "destructive",
      })
      return
    }

    setChangingPassword(true)

    try {
      await userAPI.updateCurrentUser({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
      })
      
      setPasswordData({ currentPassword: "", newPassword: "", confirmPassword: "" })
      toast({
        title: "Success",
        description: "Password changed successfully!",
      })
    } catch (error: any) {
      console.error("Password change error:", error)
      const errorMessage = error.response?.data?.detail || "Failed to change password. Please try again."
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setChangingPassword(false)
    }
  }

  const handleNotificationChange = (key: string, value: boolean) => {
    setNotifications((prev) => ({ ...prev, [key]: value }))
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A"
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-gray-600">Loading profile...</p>
        </div>
      </div>
    )
  }

  if (!userData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Failed to load user data.</p>
          <Button onClick={() => window.location.reload()} className="mt-4 bg-primary hover:bg-primary/90">
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader />
      
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Button asChild variant="ghost" size="sm" className="mb-4 hover:bg-primary/10 transition-colors">
            <Link href="/dashboard">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Dashboard
            </Link>
          </Button>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Account Settings</h1>
          <p className="text-gray-600">Manage your profile, security, and notification preferences.</p>
        </div>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px] bg-white shadow-sm">
            <TabsTrigger
              value="profile"
              className="transition-all duration-200 hover:bg-primary/5 data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
            >
              <User className="h-4 w-4 mr-2" />
              Profile
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className="transition-all duration-200 hover:bg-primary/5 data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
            >
              <Shield className="h-4 w-4 mr-2" />
              Security
            </TabsTrigger>
            <TabsTrigger
              value="notifications"
              className="transition-all duration-200 hover:bg-primary/5 data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
            >
              <Bell className="h-4 w-4 mr-2" />
              Notifications
            </TabsTrigger>
            <TabsTrigger
              value="billing"
              className="transition-all duration-200 hover:bg-primary/5 data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
            >
              <CreditCard className="h-4 w-4 mr-2" />
              Billing
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>Update your personal details here.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProfileUpdate} className="space-y-6 max-w-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center">
                      <User className="h-10 w-10 text-gray-500" />
                    </div>
                    <Button type="button" variant="outline">Change Photo</Button>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      value={profileData.name}
                      onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                      disabled={updating}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input id="email" value={userData.email} disabled />
                  </div>
                   <div className="space-y-2">
                    <Label htmlFor="organization">Organization</Label>
                    <Input
                      id="organization"
                      value={profileData.organization}
                      onChange={(e) => setProfileData({ ...profileData, organization: e.target.value })}
                      placeholder="Your Company, Inc."
                      disabled={updating}
                    />
                  </div>
                  <div className="flex items-center pt-4">
                    <Button type="submit" className="bg-primary hover:bg-primary/90" disabled={updating}>
                      {updating ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="mr-2 h-4 w-4" />
                          Save Changes
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
                <CardDescription>
                  For your security, we recommend choosing a strong password that you don't use elsewhere.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordChange} className="space-y-6 max-w-lg">
                  <div className="space-y-2">
                    <Label htmlFor="currentPassword">Current Password</Label>
                    <div className="relative">
                      <Input
                        id="currentPassword"
                        type={showCurrentPassword ? "text" : "password"}
                        value={passwordData.currentPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                        disabled={changingPassword}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        disabled={changingPassword}
                      >
                        {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                     <div className="relative">
                      <Input
                        id="newPassword"
                        type={showNewPassword ? "text" : "password"}
                        value={passwordData.newPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                        disabled={changingPassword}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        disabled={changingPassword}
                      >
                        {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <div className="relative">
                       <Input
                        id="confirmPassword"
                        type={showConfirmPassword ? "text" : "password"}
                        value={passwordData.confirmPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                        disabled={changingPassword}
                      />
                       <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        disabled={changingPassword}
                      >
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center pt-4">
                    <Button type="submit" className="bg-primary hover:bg-primary/90" disabled={changingPassword}>
                      {changingPassword ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Changing Password...
                        </>
                      ) : (
                        <>
                          <Shield className="mr-2 h-4 w-4" />
                          Change Password
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>Notification Settings</CardTitle>
                <CardDescription>
                  Choose how you want to be notified about activity in your HR platform.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="hrUpdates">HR Updates</Label>
                      <p className="text-sm text-gray-500">
                        Receive emails about new HR documents, policy updates, and platform notifications.
                      </p>
                    </div>
                  <Switch
                    id="hrUpdates"
                    checked={notifications.hrUpdates}
                    onCheckedChange={(checked) => handleNotificationChange("hrUpdates", checked)}
                  />
                </div>
                                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="complianceAlerts">Compliance Alerts</Label>
                      <p className="text-sm text-gray-500">
                        Get notified about compliance deadlines, legal updates, and regulatory changes.
                      </p>
                    </div>
                  <Switch
                    id="complianceAlerts"
                    checked={notifications.complianceAlerts}
                    onCheckedChange={(checked) => handleNotificationChange("complianceAlerts", checked)}
                  />
                </div>
                                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="supportResponses">Support Responses</Label>
                      <p className="text-sm text-gray-500">
                        Be alerted when HR experts respond to your support tickets and inquiries.
                      </p>
                    </div>
                  <Switch
                    id="supportResponses"
                    checked={notifications.supportResponses}
                    onCheckedChange={(checked) => handleNotificationChange("supportResponses", checked)}
                  />
                </div>
                                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="hrReports">HR Reports</Label>
                      <p className="text-sm text-gray-500">
                        Receive weekly summary reports about your HR activities and consultation usage.
                      </p>
                    </div>
                  <Switch
                    id="hrReports"
                    checked={notifications.hrReports}
                    onCheckedChange={(checked) => handleNotificationChange("hrReports", checked)}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="billing">
            <Card>
              <CardHeader>
                <CardTitle>Billing & Subscription</CardTitle>
                <CardDescription>
                  Manage your subscription plan and view payment history.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="p-4 border rounded-lg flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold">Current Plan</h4>
                    <p className="text-2xl font-bold mt-1">Growth Plan</p>
                    <p className="text-sm text-gray-500">Your plan renews on November 26, 2025.</p>
                  </div>
                  <Button variant="outline">Manage Subscription</Button>
                </div>
                 <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-2">Payment Method</h4>
                  <div className="flex items-center">
                    <CreditCard className="h-8 w-8 mr-4" />
                    <div>
                      <p>Visa ending in 1234</p>
                      <p className="text-sm text-gray-500">Expires 12/2025</p>
                    </div>
                    <Button variant="outline" className="ml-auto">Update</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
