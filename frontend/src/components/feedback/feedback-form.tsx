"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Search, Star, MessageSquarePlus, CheckCircle, XCircle, Loader2, AlertCircle } from "lucide-react"
import { feedbackAPI } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

// Types for the form data
interface PropertyOption {
  property_address: string
  county: string
  state: string
}

interface FeedbackFormData {
  used_platform_for_bidding: boolean
  property_address: string
  county: string
  state: string
  description: string
  bid_outcome: string
  rating: number | null
}

interface FeedbackFormProps {
  onSubmitSuccess?: () => void
  className?: string
}

export function FeedbackForm({ onSubmitSuccess, className = "" }: FeedbackFormProps) {
  const { toast } = useToast()
  
  // Form state
  const [formData, setFormData] = useState<FeedbackFormData>({
    used_platform_for_bidding: false,
    property_address: "",
    county: "",
    state: "",
    description: "",
    bid_outcome: "",
    rating: null
  })
  
  // UI state
  const [propertyOptions, setPropertyOptions] = useState<PropertyOption[]>([])
  const [propertySearch, setPropertySearch] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingProperties, setIsLoadingProperties] = useState(false)
  const [showPropertySearch, setShowPropertySearch] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Fetch property options for dropdown
  const fetchPropertyOptions = async (search: string = "") => {
    try {
      setIsLoadingProperties(true)
      const response = await feedbackAPI.getPropertyOptions(search, 50)
      setPropertyOptions(response.data.properties || [])
    } catch (error) {
      console.error("Error fetching property options:", error)
      toast({
        title: "Error",
        description: "Failed to load property options.",
        variant: "destructive",
      })
    } finally {
      setIsLoadingProperties(false)
    }
  }

  // Handle property search
  useEffect(() => {
    if (showPropertySearch) {
      const timeoutId = setTimeout(() => {
        fetchPropertyOptions(propertySearch)
      }, 300)
      return () => clearTimeout(timeoutId)
    }
  }, [propertySearch, showPropertySearch])

  // Initialize property options
  useEffect(() => {
    fetchPropertyOptions()
  }, [])

  // Handle form field changes
  const handleFieldChange = (field: keyof FeedbackFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error when field is updated
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: "" }))
    }
  }

  // Handle property selection
  const handlePropertySelect = (property: PropertyOption) => {
    setFormData(prev => ({
      ...prev,
      property_address: property.property_address,
      county: property.county,
      state: property.state
    }))
    setPropertySearch(property.property_address)
    setShowPropertySearch(false)
  }

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (formData.used_platform_for_bidding && !formData.property_address.trim()) {
      newErrors.property_address = "Property address is required when you used our platform for bidding"
    }

    if (formData.used_platform_for_bidding && formData.bid_outcome && !formData.rating) {
      newErrors.rating = "Please provide a rating for your experience"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return

    try {
      setIsSubmitting(true)

      const submitData = {
        used_platform_for_bidding: formData.used_platform_for_bidding,
        property_address: formData.property_address || null,
        county: formData.county || null,
        state: formData.state || null,
        description: formData.description || null,
        bid_outcome: formData.bid_outcome || null,
        rating: formData.rating
      }

      await feedbackAPI.createFeedback(submitData)

      toast({
        title: "Feedback Submitted!",
        description: "Thank you for sharing your experience with us.",
        duration: 5000,
      })

      // Reset form
      setFormData({
        used_platform_for_bidding: false,
        property_address: "",
        county: "",
        state: "",
        description: "",
        bid_outcome: "",
        rating: null
      })
      setPropertySearch("")
      setShowPropertySearch(false)

      onSubmitSuccess?.()
    } catch (error: any) {
      console.error("Error submitting feedback:", error)
      toast({
        title: "Submission Failed",
        description: error.response?.data?.detail || "Failed to submit feedback. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className={`w-full max-w-2xl mx-auto shadow-lg border-2 border-blue-100 ${className}`}>
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <MessageSquarePlus className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <CardTitle className="text-xl text-blue-900">Share Your Experience</CardTitle>
            <CardDescription className="text-blue-700">
              Help us improve by sharing feedback about your property bidding experience
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-6 p-6">
          {/* Primary Question */}
          <div className="space-y-4">
            <Label className="text-base font-semibold text-gray-800">
              Did you use our property rankings to bid on a property? *
            </Label>
            <RadioGroup
              value={formData.used_platform_for_bidding.toString()}
              onValueChange={(value) => handleFieldChange("used_platform_for_bidding", value === "true")}
              className="flex gap-6"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="true" id="yes" />
                <Label htmlFor="yes" className="text-green-700 font-medium">Yes, I used your rankings</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="false" id="no" />
                <Label htmlFor="no" className="text-gray-700 font-medium">No, I haven't bid yet</Label>
              </div>
            </RadioGroup>
          </div>

          {/* Property Details (conditional) */}
          {formData.used_platform_for_bidding && (
            <div className="space-y-4 p-4 bg-green-50 border border-green-200 rounded-lg animate-fadeIn">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <Label className="text-base font-semibold text-green-800">
                  Tell us about the property you bid on
                </Label>
              </div>

              {/* Property Search */}
              <div className="space-y-2 relative">
                <Label htmlFor="property-search" className="text-sm font-medium text-gray-700">
                  Property Address *
                </Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 z-10" />
                  <Input
                    id="property-search"
                    placeholder="Search for the property address..."
                    value={propertySearch}
                    onChange={(e) => {
                      setPropertySearch(e.target.value)
                      setShowPropertySearch(true)
                    }}
                    onFocus={() => setShowPropertySearch(true)}
                    onBlur={() => {
                      // Delay hiding to allow for clicks on dropdown items
                      setTimeout(() => setShowPropertySearch(false), 150)
                    }}
                    className={`pl-10 ${errors.property_address ? 'border-red-500' : ''}`}
                  />
                  {isLoadingProperties && (
                    <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-gray-400 z-10" />
                  )}
                  
                  {/* Property Options Dropdown */}
                  {showPropertySearch && propertyOptions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-white border border-gray-300 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                      {propertyOptions
                        .filter(prop => 
                          !propertySearch || 
                          prop.property_address.toLowerCase().includes(propertySearch.toLowerCase())
                        )
                        .slice(0, 10)
                        .map((property, index) => (
                          <div
                            key={index}
                            className="p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors duration-150"
                            onMouseDown={(e) => {
                              // Prevent input blur when clicking on dropdown
                              e.preventDefault()
                              handlePropertySelect(property)
                            }}
                          >
                            <div className="font-medium text-gray-900 truncate">{property.property_address}</div>
                            <div className="text-sm text-gray-500">{property.county}, {property.state}</div>
                          </div>
                        ))
                      }
                      {propertyOptions.filter(prop => 
                        !propertySearch || 
                        prop.property_address.toLowerCase().includes(propertySearch.toLowerCase())
                      ).length === 0 && (
                        <div className="p-3 text-gray-500 text-center">
                          No properties found matching "{propertySearch}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {errors.property_address && (
                  <p className="text-sm text-red-600">{errors.property_address}</p>
                )}
              </div>

              {/* Bid Outcome */}
              <div className="space-y-2">
                <Label htmlFor="bid-outcome" className="text-sm font-medium text-gray-700">
                  What was the outcome of your bid?
                </Label>
                <Select
                  value={formData.bid_outcome}
                  onValueChange={(value) => handleFieldChange("bid_outcome", value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select bid outcome..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="successful">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        Successful - I won the bid
                      </div>
                    </SelectItem>
                    <SelectItem value="unsuccessful">
                      <div className="flex items-center gap-2">
                        <XCircle className="h-4 w-4 text-red-600" />
                        Unsuccessful - Someone else won
                      </div>
                    </SelectItem>
                    <SelectItem value="pending">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 text-yellow-600" />
                        Pending - Auction hasn't happened yet
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Rating (conditional) */}
              {formData.bid_outcome && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-700">
                    How would you rate our property ranking accuracy? *
                  </Label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Button
                        key={star}
                        type="button"
                        variant="ghost"
                        size="sm"
                        className={`p-1 ${
                          formData.rating && formData.rating >= star
                            ? "text-yellow-500 hover:text-yellow-600"
                            : "text-gray-300 hover:text-yellow-400"
                        }`}
                        onClick={() => handleFieldChange("rating", star)}
                      >
                        <Star className="h-6 w-6 fill-current" />
                      </Button>
                    ))}
                    {formData.rating && (
                      <Badge variant="outline" className="ml-2">
                        {formData.rating} star{formData.rating > 1 ? 's' : ''}
                      </Badge>
                    )}
                  </div>
                  {errors.rating && (
                    <p className="text-sm text-red-600">{errors.rating}</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-sm font-medium text-gray-700">
              Additional Comments
            </Label>
            <Textarea
              id="description"
              placeholder="Tell us more about your experience, suggestions for improvement, or any other feedback..."
              value={formData.description}
              onChange={(e) => handleFieldChange("description", e.target.value)}
              rows={4}
              className="resize-none"
            />
          </div>

          {/* Info Alert */}
          <Alert className="bg-blue-50 border-blue-200">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              Your feedback helps us improve our property ranking algorithm and provide better investment opportunities.
            </AlertDescription>
          </Alert>
        </CardContent>

        <CardFooter className="bg-gray-50 border-t">
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200 hover:scale-105"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting Feedback...
              </>
            ) : (
              <>
                <MessageSquarePlus className="mr-2 h-4 w-4" />
                Submit Feedback
              </>
            )}
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
} 