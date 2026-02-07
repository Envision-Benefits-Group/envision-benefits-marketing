"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertCircle, CheckCircle2, Download, FileText, Upload, Loader2, X } from "lucide-react"

const PROCESSING_MESSAGES = [
  "Analyzing document structure...",
  "Extracting data points...",
  "Validating coverage details...",
  "Processing multiple files in parallel...",
  "Combining extracted data...",
  "Formatting output...",
  "Generating Excel report...",
  "Almost there...",
]

export default function TestUploadPage() {
  const [files, setFiles] = useState<File[]>([])
  const [quarter, setQuarter] = useState<string>("")
  const [status, setStatus] = useState<"IDLE" | "PROCESSING" | "SUCCESS" | "ERROR">("IDLE")
  const [loadingMessage, setLoadingMessage] = useState("")
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string>("extraction_result.xlsx")
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (status === "PROCESSING") {
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            setLoadingMessage("Finalizing report...")
            return 90
          }
          const increment = Math.random() * 1.5
          return prev + increment
        })

        if (progress < 90 && Math.random() > 0.7) {
          setLoadingMessage(PROCESSING_MESSAGES[Math.floor(Math.random() * PROCESSING_MESSAGES.length)])
        }
      }, 500)
      return () => clearInterval(interval)
    }
  }, [status, progress])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFiles = Array.from(e.target.files)
      const validFiles: File[] = []
      const errors: string[] = []

      selectedFiles.forEach(file => {
        const fileType = file.name.split('.').pop()?.toLowerCase()
        if (fileType !== 'pdf') {
          errors.push(`${file.name}: Only PDF files are supported`)
          return
        }
        validFiles.push(file)
      })

      if (errors.length > 0) {
        setError(errors.join('. '))
      } else {
        setError(null)
      }

      if (validFiles.length > 0) {
        setFiles(prev => [...prev, ...validFiles])
        setStatus("IDLE")
        setDownloadUrl(null)
      }
    }
    if (e.target) e.target.value = ''
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleProcess = async () => {
    if (files.length === 0) return

    setStatus("PROCESSING")
    setProgress(0)
    setLoadingMessage("Starting extraction...")
    setError(null)

    const formData = new FormData()
    files.forEach(file => {
      formData.append("files", file)
    })
    if (quarter) {
      formData.append("quarter", quarter)
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(`${apiUrl}/extraction/process-pdfs`, {
        method: "POST",
        headers: {
          "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "test-secret-key",
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Error: ${response.statusText}`)
      }

      const contentDisposition = response.headers.get('Content-Disposition')
      let extractedFileName = "extraction_result.xlsx"
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (fileNameMatch && fileNameMatch.length === 2) {
          extractedFileName = fileNameMatch[1]
        }
      }
      setFileName(extractedFileName)

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      setDownloadUrl(url)
      setStatus("SUCCESS")
      setProgress(100)
    } catch (err: any) {
      setError(err.message || "An error occurred during processing.")
      setStatus("ERROR")
    }
  }

  const handleReset = () => {
    setFiles([])
    setStatus("IDLE")
    setDownloadUrl(null)
    setQuarter("")
    setProgress(0)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-3xl shadow-xl border-slate-200">
        <CardHeader className="bg-white rounded-t-xl border-b pb-6">
          <CardTitle className="text-2xl font-semibold text-slate-800 flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" />
            Document Extraction
          </CardTitle>
          <CardDescription>
            Upload multiple insurance PDFs to extract and combine data into a single Excel file.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">

          {/* Controls: Quarter Selection & File Upload */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Quarter (Optional)</Label>
              <Select value={quarter} onValueChange={setQuarter} disabled={status === "PROCESSING"}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Quarter" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Q1">Q1</SelectItem>
                  <SelectItem value="Q2">Q2</SelectItem>
                  <SelectItem value="Q3">Q3</SelectItem>
                  <SelectItem value="Q4">Q4</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div
              className={`md:col-span-2 border-2 border-dashed rounded-lg p-4 flex flex-col items-center justify-center text-center transition-colors cursor-pointer ${
                files.length > 0 ? "border-blue-500 bg-blue-50/50" : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
              } ${status === "PROCESSING" ? "opacity-50 cursor-not-allowed" : ""}`}
              onClick={() => status !== "PROCESSING" && fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                multiple
                className="hidden"
                onChange={handleFileChange}
                disabled={status === "PROCESSING"}
              />
              <div className="flex items-center gap-2 text-slate-500">
                <Upload className="w-6 h-6" />
                <span className="text-sm font-medium">
                  {files.length > 0 ? "Click to add more PDFs" : "Click to upload PDF files"}
                </span>
              </div>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm text-slate-600">
                {files.length} file{files.length > 1 ? 's' : ''} selected
              </Label>
              <div className="max-h-[200px] overflow-y-auto space-y-2">
                {files.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="border rounded-lg p-3 flex items-center gap-3 bg-white border-slate-200"
                  >
                    <FileText className="w-5 h-5 text-slate-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-700 text-sm truncate">{file.name}</p>
                      <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    {status !== "PROCESSING" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-slate-400 hover:text-slate-600 flex-shrink-0"
                        onClick={() => removeFile(index)}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-md flex items-center gap-2 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Processing State */}
          {status === "PROCESSING" && (
            <div className="space-y-2 py-4">
              <div className="flex justify-between text-sm text-slate-600">
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  {loadingMessage}
                </span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              <p className="text-xs text-slate-500 text-center">
                Processing {files.length} file{files.length > 1 ? 's' : ''} in parallel...
              </p>
            </div>
          )}

          {/* Success State */}
          {status === "SUCCESS" && (
            <div className="bg-green-50 text-green-700 p-4 rounded-md flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5" />
              <div className="flex-1">
                <p className="font-medium">Extraction Complete!</p>
                <p className="text-sm opacity-90">
                  Combined data from {files.length} file{files.length > 1 ? 's' : ''} into a single Excel report.
                </p>
              </div>
            </div>
          )}

        </CardContent>
        <CardFooter className="flex justify-between border-t pt-6 bg-slate-50/50 rounded-b-xl">
          <Button variant="ghost" onClick={handleReset} disabled={status === "PROCESSING"}>
            Reset
          </Button>

          {status === "SUCCESS" && downloadUrl ? (
            <Button className="bg-green-600 hover:bg-green-700 gap-2" asChild>
              <a href={downloadUrl} download={fileName}>
                <Download className="w-4 h-4" /> Download Excel
              </a>
            </Button>
          ) : (
            <Button
              onClick={handleProcess}
              disabled={files.length === 0 || status === "PROCESSING"}
              className="gap-2 bg-blue-600 hover:bg-blue-700"
            >
              {status === "PROCESSING"
                ? "Processing..."
                : `Process ${files.length > 0 ? files.length : ''} File${files.length !== 1 ? 's' : ''}`
              }
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}
