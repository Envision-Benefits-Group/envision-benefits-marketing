"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertCircle, CheckCircle2, Download, FileText, Upload, Eye, Loader2, Lock } from "lucide-react"

const PROCESSING_MESSAGES = [
  "Analyzing document structure...",
  "Extracting data points...",
  "Validating coverage details...",
  "Formatting output...",
  "Generating Excel report...",
  "Double checking extraction...",
  "Almost there...",
]

export default function TestUploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [quarter, setQuarter] = useState<string>("")
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [status, setStatus] = useState<"IDLE" | "PROCESSING" | "SUCCESS" | "ERROR">("IDLE")
  const [loadingMessage, setLoadingMessage] = useState("")
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string>("extraction_result.xlsx")
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (status === "PROCESSING") {
      // Logic for ~60 seconds to reach 90%
      // 90% / 60s = 1.5% per second
      // Updating every 500ms -> 0.75% per tick
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            setLoadingMessage("Finalizing file...")
            return 90
          }
          const increment = Math.random() * 1.5 // Random increment to simulate work, avg ~0.75
          return prev + increment
        })

        // Randomly change messages only if below 90%
        if (progress < 90 && Math.random() > 0.7) {
          setLoadingMessage(PROCESSING_MESSAGES[Math.floor(Math.random() * PROCESSING_MESSAGES.length)])
        }
      }, 500)
      return () => clearInterval(interval)
    }
  }, [status, progress])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      const fileType = selectedFile.name.split('.').pop()?.toLowerCase()

      if (fileType !== 'pdf' && fileType !== 'docx') {
        setError("Unsupported file type. Please upload a PDF or DOCX.")
        setFile(null)
        setPreviewUrl(null)
        return
      }

      setFile(selectedFile)
      setError(null)
      setStatus("IDLE")
      setDownloadUrl(null)

      if (fileType === 'pdf') {
        const url = URL.createObjectURL(selectedFile)
        setPreviewUrl(url)
      } else {
        setPreviewUrl(null)
      }
    }
  }

  const handleProcess = async () => {
    if (!file) return

    setStatus("PROCESSING")
    setProgress(0)
    setLoadingMessage("Starting extraction...")
    setError(null)

    const formData = new FormData()
    formData.append("file", file)
    if (quarter) {
      formData.append("quarter", quarter)
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(`${apiUrl}/extraction/process-pdf`, {
        method: "POST",
        headers: {
          "x-api-key": "test-secret-key",
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Error: ${response.statusText}`)
      }

      // Try to get filename from content-disposition
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

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-3xl shadow-xl border-slate-200">
        <CardHeader className="bg-white rounded-t-xl border-b pb-6">
          <CardTitle className="text-2xl font-semibold text-slate-800 flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" />
            Document Extraction Test
          </CardTitle>
          <CardDescription>
            Upload insurance documents (PDF/DOCX) to extract data into Excel.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">

          {/* Controls: Quarter Selection & File Upload */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Quarter (Optional)</Label>
              <Select value={quarter} onValueChange={setQuarter}>
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
              className={`md:col-span-2 border-2 border-dashed rounded-lg p-4 flex flex-col items-center justify-center text-center transition-colors cursor-pointer ${file ? "border-blue-500 bg-blue-50/50" : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
                }`}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={handleFileChange}
              />
              {file ? (
                <div className="flex items-center gap-2">
                  <FileText className="w-8 h-8 text-blue-600" />
                  <div className="text-left">
                    <p className="font-medium text-slate-700 text-sm">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <Button variant="ghost" size="sm" className="ml-2 text-blue-600 h-auto p-1" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click() }}>
                    Change
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-slate-500">
                  <Upload className="w-6 h-6" />
                  <span className="text-sm font-medium">Click to upload PDF/DOCX</span>
                </div>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-md flex items-center gap-2 text-sm">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          {/* Preview Section */}
          {previewUrl && file?.type === 'application/pdf' && (
            <div className="mt-4 border rounded-lg overflow-hidden h-[300px] bg-slate-100 relative group">
              <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button variant="secondary" size="sm" asChild>
                  <a href={previewUrl} target="_blank" rel="noopener noreferrer">
                    <Eye className="w-4 h-4 mr-2" /> Open Full
                  </a>
                </Button>
              </div>
              <iframe src={previewUrl} className="w-full h-full" title="PDF Preview" />
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
            </div>
          )}

          {/* Success State */}
          {status === "SUCCESS" && (
            <div className="bg-green-50 text-green-700 p-4 rounded-md flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5" />
              <div className="flex-1">
                <p className="font-medium">Extraction Complete!</p>
                <p className="text-sm opacity-90">Your Excel report is ready.</p>
              </div>
            </div>
          )}

        </CardContent>
        <CardFooter className="flex justify-between border-t pt-6 bg-slate-50/50 rounded-b-xl">
          <Button variant="ghost" onClick={() => { setFile(null); setStatus("IDLE"); setPreviewUrl(null); setDownloadUrl(null); setQuarter(""); setProgress(0); }} disabled={status === "PROCESSING"}>
            Reset
          </Button>

          {status === "SUCCESS" && downloadUrl ? (
            <Button className="bg-green-600 hover:bg-green-700 gap-2" asChild>
              <a href={downloadUrl} download={fileName}>
                <Download className="w-4 h-4" /> Download Excel
              </a>
            </Button>
          ) : (
            <Button onClick={handleProcess} disabled={!file || status === "PROCESSING"} className="gap-2 bg-blue-600 hover:bg-blue-700">
              {status === "PROCESSING" ? "Processing..." : "Start Processing"}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}
