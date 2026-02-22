"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Upload,
  Loader2,
  X,
} from "lucide-react";
import { extractionApi } from "@/lib/api";
import type { IngestResponse } from "@/types/plans";

const PROCESSING_MESSAGES = [
  "Analyzing document structure...",
  "Extracting data points...",
  "Validating coverage details...",
  "Processing multiple files in parallel...",
  "Combining extracted data...",
  "Formatting output...",
  "Saving plans to database...",
  "Almost there...",
];

interface UploadTabProps {
  onIngestionComplete: () => void;
}

export function UploadTab({ onIngestionComplete }: UploadTabProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [quarter, setQuarter] = useState<string>("");
  const [status, setStatus] = useState<
    "IDLE" | "PROCESSING" | "SUCCESS" | "ERROR"
  >("IDLE");
  const [loadingMessage, setLoadingMessage] = useState("");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (status === "PROCESSING") {
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            setLoadingMessage("Finalizing...");
            return 90;
          }
          return prev + Math.random() * 1.5;
        });

        if (progress < 90 && Math.random() > 0.7) {
          setLoadingMessage(
            PROCESSING_MESSAGES[
              Math.floor(Math.random() * PROCESSING_MESSAGES.length)
            ]
          );
        }
      }, 500);
      return () => clearInterval(interval);
    }
  }, [status, progress]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFiles = Array.from(e.target.files);
      const validFiles: File[] = [];
      const errors: string[] = [];

      selectedFiles.forEach((file) => {
        if (file.name.split(".").pop()?.toLowerCase() !== "pdf") {
          errors.push(`${file.name}: Only PDF files are supported`);
        } else {
          validFiles.push(file);
        }
      });

      if (errors.length > 0) setError(errors.join(". "));
      else setError(null);

      if (validFiles.length > 0) {
        setFiles((prev) => [...prev, ...validFiles]);
        setStatus("IDLE");
        setResult(null);
      }
    }
    if (e.target) e.target.value = "";
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProcess = async () => {
    if (files.length === 0) return;

    setStatus("PROCESSING");
    setProgress(0);
    setLoadingMessage("Starting extraction...");
    setError(null);

    try {
      const { data } = await extractionApi.ingest(
        files,
        quarter || undefined
      );
      setResult(data);
      setStatus("SUCCESS");
      setProgress(100);
      onIngestionComplete();
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        "An error occurred during processing.";
      setError(message);
      setStatus("ERROR");
    }
  };

  const handleReset = () => {
    setFiles([]);
    setStatus("IDLE");
    setResult(null);
    setQuarter("");
    setProgress(0);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label>Quarter (Optional)</Label>
          <Select
            value={quarter}
            onValueChange={setQuarter}
            disabled={status === "PROCESSING"}
          >
            <SelectTrigger>
              <SelectValue placeholder="Auto-detect" />
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
            files.length > 0
              ? "border-blue-500 bg-blue-50/50"
              : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
          } ${status === "PROCESSING" ? "opacity-50 cursor-not-allowed" : ""}`}
          onClick={() =>
            status !== "PROCESSING" && fileInputRef.current?.click()
          }
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
              {files.length > 0
                ? "Click to add more PDFs"
                : "Click to upload PDF files"}
            </span>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <Label className="text-sm text-slate-600">
            {files.length} file{files.length > 1 ? "s" : ""} selected
          </Label>
          <div className="max-h-[200px] overflow-y-auto space-y-2">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="border rounded-lg p-3 flex items-center gap-3 bg-white border-slate-200"
              >
                <FileText className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-700 text-sm truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
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

      {/* Error */}
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-md flex items-center gap-2 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Processing */}
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
            Processing {files.length} file{files.length > 1 ? "s" : ""} in
            parallel...
          </p>
        </div>
      )}

      {/* Results */}
      {status === "SUCCESS" && result && (
        <div className="space-y-4">
          <div className="bg-green-50 text-green-700 p-4 rounded-md flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5" />
            <div>
              <p className="font-medium">Ingestion Complete</p>
              <p className="text-sm opacity-90">
                {result.total_plans_ingested} plan
                {result.total_plans_ingested !== 1 ? "s" : ""} ingested from{" "}
                {result.total_files} file{result.total_files !== 1 ? "s" : ""}
              </p>
            </div>
          </div>

          {/* Per-file breakdown */}
          {result.files.map((fileResult) => (
            <Card key={fileResult.file}>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-500" />
                    <span className="font-medium text-sm">
                      {fileResult.file}
                    </span>
                  </div>
                  <Badge
                    variant={
                      fileResult.status === "success"
                        ? "default"
                        : "destructive"
                    }
                  >
                    {fileResult.status}
                  </Badge>
                </div>

                {fileResult.status === "error" && fileResult.detail && (
                  <p className="text-sm text-red-600">{fileResult.detail}</p>
                )}

                {fileResult.status === "success" && (
                  <div className="space-y-2">
                    <div className="flex gap-2 flex-wrap">
                      {fileResult.detected_quarters?.map((q) => (
                        <Badge key={q} variant="outline">
                          {q}
                        </Badge>
                      ))}
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-xs text-slate-600">
                      <div className="bg-slate-50 rounded p-2 text-center">
                        <p className="font-semibold text-base text-slate-800">
                          {fileResult.inserted}
                        </p>
                        <p>Inserted</p>
                      </div>
                      <div className="bg-slate-50 rounded p-2 text-center">
                        <p className="font-semibold text-base text-slate-800">
                          {fileResult.updated_exact}
                        </p>
                        <p>Updated</p>
                      </div>
                      <div className="bg-slate-50 rounded p-2 text-center">
                        <p className="font-semibold text-base text-slate-800">
                          {fileResult.updated_fuzzy}
                        </p>
                        <p>Fuzzy Matched</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <Button
          variant="ghost"
          onClick={handleReset}
          disabled={status === "PROCESSING"}
        >
          Reset
        </Button>
        <Button
          onClick={handleProcess}
          disabled={files.length === 0 || status === "PROCESSING"}
          className="gap-2 bg-blue-600 hover:bg-blue-700"
        >
          {status === "PROCESSING"
            ? "Processing..."
            : `Process ${files.length > 0 ? files.length : ""} File${files.length !== 1 ? "s" : ""}`}
        </Button>
      </div>
    </div>
  );
}
