"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { 
  FileText, 
  MessageCircle, 
  Calendar, 
  Users, 
  Download, 
  Send, 
  Clock, 
  CheckCircle,
  AlertCircle,
  BookOpen,
  Headphones,
  TrendingUp,
  Shield,
  HelpCircle,
  ExternalLink,
  Upload,
  FolderOpen,
  Bot
} from "lucide-react"
import { DashboardHeader } from "./dashboard-header"
import { userAPI } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface UserData {
  id: number
  name: string
  email: string
  organization: string | null
  is_active: boolean
  created_at: string | null
}

interface HRDocument {
  id: string
  title: string
  category: string
  description: string
  downloadCount: number
}

interface Ticket {
  id: string
  subject: string
  status: "open" | "in-progress" | "closed"
  created_at: string
}

// Mock data for MVP prototype
const mockHRDocuments: HRDocument[] = [
  {
    id: "1",
    title: "Employee Handbook Template",
    category: "Policies",
    description: "Comprehensive employee handbook template for small businesses",
    downloadCount: 245
  },
  {
    id: "2", 
    title: "Termination Checklist",
    category: "HR Forms",
    description: "Step-by-step checklist for employee termination process",
    downloadCount: 189
  },
  {
    id: "3",
    title: "Job Description Templates",
    category: "Recruitment",
    description: "Pre-built job descriptions for common positions",
    downloadCount: 167
  },
  {
    id: "4",
    title: "Performance Review Forms",
    category: "Performance",
    description: "Annual and quarterly performance evaluation forms",
    downloadCount: 134
  }
]

const mockRecentTickets: Ticket[] = [
  {
    id: "1",
    subject: "Question about overtime policies",
    status: "in-progress", 
    created_at: "2024-01-15T10:30:00Z"
  },
  {
    id: "2",
    subject: "Need help with hiring process",
    status: "closed",
    created_at: "2024-01-12T14:22:00Z"
  }
]

export function Dashboard() {
  const { toast } = useToast()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<Array<{type: 'user' | 'bot', message: string}>>([
    { type: 'bot', message: 'Hello! I\'m your AI HR Assistant. How can I help you today?' }
  ])
  const [chatInput, setChatInput] = useState("")
  const [chatLoading, setChatLoading] = useState(false)
  
  // Support ticket state
  const [ticketSubject, setTicketSubject] = useState("")
  const [ticketDescription, setTicketDescription] = useState("")
  const [ticketPriority, setTicketPriority] = useState("medium")
  const [ticketSubmitting, setTicketSubmitting] = useState(false)

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await userAPI.getCurrentUser()
        setUserData(response.data)
      } catch (error) {
        console.error("Error fetching user data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [])

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return

    const userMessage = chatInput.trim()
    setChatInput("")
    setChatMessages(prev => [...prev, { type: 'user', message: userMessage }])
    setChatLoading(true)

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        "Based on labor law requirements, I recommend reviewing your current policy. Would you like me to provide specific guidance?",
        "For compliance purposes, you should document this process. I can help you create the necessary forms.",
        "This is a common HR challenge. Let me provide you with some best practices and templates.",
        "I'd recommend consulting with our HR experts for this specific situation. Would you like to schedule a call?"
      ]
      const randomResponse = responses[Math.floor(Math.random() * responses.length)]
      
      setChatMessages(prev => [...prev, { type: 'bot', message: randomResponse }])
      setChatLoading(false)
    }, 1500)
  }

  const handleTicketSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ticketSubject.trim() || !ticketDescription.trim()) {
      toast({
        title: "Error",
        description: "Please fill in all required fields.",
        variant: "destructive"
      })
      return
    }

    setTicketSubmitting(true)
    
    // Simulate ticket submission
    setTimeout(() => {
      toast({
        title: "Support Ticket Submitted",
        description: "Our HR experts will respond within 24 hours.",
      })
      setTicketSubject("")
      setTicketDescription("")
      setTicketPriority("medium")
      setTicketSubmitting(false)
    }, 1000)
  }

  const handleDocumentDownload = (doc: HRDocument) => {
    toast({
      title: "Download Started",
      description: `Downloading ${doc.title}...`
    })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <DashboardHeader />
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Loading your dashboard...</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {userData?.name?.split(' ')[0] || 'there'}!
          </h1>
          <p className="text-gray-600">
            Your HR command center for {userData?.organization || 'your organization'}
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Documents Downloaded</p>
                  <p className="text-2xl font-bold text-gray-900">12</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Download className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Support Tickets</p>
                  <p className="text-2xl font-bold text-gray-900">3</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <Headphones className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">AI Queries</p>
                  <p className="text-2xl font-bold text-gray-900">47</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Bot className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Consultations</p>
                  <p className="text-2xl font-bold text-gray-900">2</p>
                </div>
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Calendar className="h-6 w-6 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Digital HR Vault */}
          <Card className="lg:col-span-2 hover:shadow-md transition-shadow duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderOpen className="h-5 w-5 text-primary" />
                Digital HR Vault
              </CardTitle>
              <CardDescription>
                Access essential HR templates and documents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {mockHRDocuments.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => handleDocumentDownload(doc)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <FileText className="h-5 w-5 text-primary mt-1" />
                      <Badge variant="secondary" className="text-xs">
                        {doc.category}
                      </Badge>
                    </div>
                    <h4 className="font-medium text-gray-900 mb-1">{doc.title}</h4>
                    <p className="text-sm text-gray-600 mb-2">{doc.description}</p>
                    <div className="flex items-center text-xs text-gray-500">
                      <Download className="h-3 w-3 mr-1" />
                      {doc.downloadCount} downloads
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Document
                </Button>
                <Button variant="outline" className="flex-1">
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Browse All
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* AI HR Assistant */}
          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                AI HR Assistant
              </CardTitle>
              <CardDescription>
                Get instant answers to HR questions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 mb-4 max-h-64 overflow-y-auto">
                {chatMessages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-3 rounded-lg text-sm ${
                        msg.type === 'user'
                          ? 'bg-primary text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      {msg.message}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 p-3 rounded-lg text-sm">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <form onSubmit={handleChatSubmit} className="flex gap-2">
                <Input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask an HR question..."
                  disabled={chatLoading}
                />
                <Button type="submit" size="icon" disabled={chatLoading || !chatInput.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </form>
              <p className="text-xs text-gray-500 mt-2">
                <AlertCircle className="h-3 w-3 inline mr-1" />
                AI responses are for guidance only. Consult HR experts for specific situations.
              </p>
            </CardContent>
          </Card>

          {/* Support Ticket System */}
          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Headphones className="h-5 w-5 text-primary" />
                HR Support
              </CardTitle>
              <CardDescription>
                Submit tickets to our HR experts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleTicketSubmit} className="space-y-4">
                <div>
                  <Input
                    value={ticketSubject}
                    onChange={(e) => setTicketSubject(e.target.value)}
                    placeholder="Subject"
                    required
                  />
                </div>
                <div>
                  <Select value={ticketPriority} onValueChange={setTicketPriority}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low Priority</SelectItem>
                      <SelectItem value="medium">Medium Priority</SelectItem>
                      <SelectItem value="high">High Priority</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Textarea
                    value={ticketDescription}
                    onChange={(e) => setTicketDescription(e.target.value)}
                    placeholder="Describe your HR question or issue..."
                    rows={3}
                    required
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={ticketSubmitting}
                >
                  {ticketSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Submit Ticket
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Schedule Consultation */}
          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                Schedule Consultation
              </CardTitle>
              <CardDescription>
                Book time with HR experts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Available Services</h4>
                  <ul className="space-y-1 text-sm text-blue-800">
                    <li>• HR Policy Review</li>
                    <li>• Compliance Consultation</li>
                    <li>• Employee Relations</li>
                    <li>• Performance Management</li>
                  </ul>
                </div>
                <Button 
                  className="w-full"
                  onClick={() => window.open('https://calendly.com/envision-hr', '_blank')}
                >
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Meeting
                  <ExternalLink className="h-4 w-4 ml-2" />
                </Button>
                <p className="text-xs text-gray-500">
                  Opens Microsoft Bookings in a new tab
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-primary" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockRecentTickets.map((ticket) => (
                  <div key={ticket.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div className={`w-3 h-3 rounded-full mt-1 ${
                      ticket.status === 'closed' ? 'bg-green-500' : 
                      ticket.status === 'in-progress' ? 'bg-yellow-500' : 'bg-blue-500'
                    }`}></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {ticket.subject}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(ticket.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
                <div className="text-center pt-2">
                  <Button variant="ghost" size="sm">
                    View All Activity
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col space-y-2 hover:bg-primary/5">
              <BookOpen className="h-6 w-6" />
              <span className="text-sm">Training Library</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2 hover:bg-primary/5">
              <Shield className="h-6 w-6" />
              <span className="text-sm">Compliance Check</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2 hover:bg-primary/5">
              <Users className="h-6 w-6" />
              <span className="text-sm">Employee Portal</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2 hover:bg-primary/5">
              <HelpCircle className="h-6 w-6" />
              <span className="text-sm">Help Center</span>
            </Button>
          </div>
        </div>

      </main>
    </div>
  )
}
