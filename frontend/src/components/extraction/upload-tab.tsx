"use client";

import { useState, useRef, useEffect, DragEvent } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Upload,
  Loader2,
  ClipboardList,
  X,
  Brain,
  DatabaseZap,
  ShieldCheck,
  CloudUpload,
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

const INFO_CARDS = [
  {
    icon: Brain,
    title: "AI-Powered Extraction",
    description:
      "GPT-4 reads your PDFs and automatically pulls out plan names, rates, copays, deductibles, and more.",
  },
  {
    icon: ShieldCheck,
    title: "Smart Deduplication",
    description:
      "Plans are matched by carrier, name, and period — existing records are updated, not duplicated.",
  },
  {
    icon: DatabaseZap,
    title: "Instant Database Sync",
    description:
      "Extracted plans are immediately available in Edit Data and Comparison as soon as processing finishes.",
  },
];

interface UploadTabProps {
  onIngestionComplete: () => void;
}

export function UploadTab({ onIngestionComplete }: UploadTabProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [quarter, setQuarter] = useState<string>("");
  const [status, setStatus] = useState<"IDLE" | "PROCESSING" | "SUCCESS" | "ERROR">("IDLE");
  const [loadingMessage, setLoadingMessage] = useState("");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
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
            PROCESSING_MESSAGES[Math.floor(Math.random() * PROCESSING_MESSAGES.length)]
          );
        }
      }, 500);
      return () => clearInterval(interval);
    }
  }, [status, progress]);

  const addFiles = (incoming: FileList | File[]) => {
    const arr = Array.from(incoming);
    const valid: File[] = [];
    const errors: string[] = [];
    arr.forEach((f) => {
      if (f.name.split(".").pop()?.toLowerCase() !== "pdf") {
        errors.push(`${f.name}: Only PDF files are supported`);
      } else {
        valid.push(f);
      }
    });
    if (errors.length) setError(errors.join(". "));
    else setError(null);
    if (valid.length) {
      setFiles((prev) => [...prev, ...valid]);
      setStatus("IDLE");
      setResult(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) addFiles(e.target.files);
    if (e.target) e.target.value = "";
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (status === "PROCESSING") return;
    const dropped = e.dataTransfer.files;
    if (dropped && dropped.length > 0) addFiles(dropped);
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
      const { data } = await extractionApi.ingest(files, quarter || undefined);
      setResult(data);
      setStatus("SUCCESS");
      setProgress(100);
      onIngestionComplete();
    } catch (err: any) {
      const message =
        err.response?.data?.detail || err.message || "An error occurred during processing.";
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

  const isIdle = status === "IDLE" && files.length === 0 && !result;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">

      {/* ── Drop Zone ─────────────────────────────────────────────── */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => status !== "PROCESSING" && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl transition-all cursor-pointer select-none
          ${status === "PROCESSING" ? "opacity-50 cursor-not-allowed pointer-events-none" : ""}
          ${isDragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : files.length > 0
            ? "border-blue-400 bg-blue-50/40 hover:bg-blue-50/60"
            : "border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50/60"
          }`}
        style={{ minHeight: 200 }}
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
        <div className="flex flex-col items-center justify-center py-14 gap-3 text-center px-6">
          <div className={`rounded-full p-4 transition-colors ${
            isDragging ? "bg-primary/15" : files.length > 0 ? "bg-blue-100" : "bg-gray-100"
          }`}>
            <CloudUpload className={`w-8 h-8 ${
              isDragging ? "text-primary" : files.length > 0 ? "text-blue-500" : "text-gray-400"
            }`} />
          </div>
          <div>
            <p className={`text-base font-semibold ${isDragging ? "text-primary" : "text-gray-700"}`}>
              {isDragging
                ? "Drop your PDFs here"
                : files.length > 0
                ? `${files.length} file${files.length > 1 ? "s" : ""} selected — click to add more`
                : "Drag & drop PDFs here"}
            </p>
            <p className="text-sm text-gray-400 mt-0.5">
              {files.length === 0 && !isDragging && "or click to browse — PDF files only"}
            </p>
          </div>
        </div>
      </div>

      {/* ── Quarter selector ──────────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-gray-600 whitespace-nowrap">Quarter override:</span>
        <Select value={quarter} onValueChange={setQuarter} disabled={status === "PROCESSING"}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Auto-detect" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Q1">Q1</SelectItem>
            <SelectItem value="Q2">Q2</SelectItem>
            <SelectItem value="Q3">Q3</SelectItem>
            <SelectItem value="Q4">Q4</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-xs text-gray-400">Leave blank to let the AI detect it from the PDF</span>
      </div>

      {/* ── File list ─────────────────────────────────────────────── */}
      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-600">
            {files.length} file{files.length > 1 ? "s" : ""} queued
          </p>
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg px-4 py-2.5 shadow-sm"
              >
                <FileText className="w-4 h-4 text-red-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700 truncate">{file.name}</p>
                  <p className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                {status !== "PROCESSING" && (
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                    className="text-gray-300 hover:text-gray-500 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Error ─────────────────────────────────────────────────── */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ── Processing ────────────────────────────────────────────── */}
      {status === "PROCESSING" && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3 shadow-sm">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
              {loadingMessage}
            </span>
            <span className="font-medium">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-gray-400 text-center">
            Processing {files.length} file{files.length > 1 ? "s" : ""} in parallel
          </p>
        </div>
      )}

      {/* ── Success ───────────────────────────────────────────────── */}
      {status === "SUCCESS" && result && (
        <div className="space-y-3">
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <div>
              <p className="font-semibold">Ingestion Complete</p>
              <p className="text-sm opacity-90">
                {result.total_plans_ingested} plan{result.total_plans_ingested !== 1 ? "s" : ""} ingested from{" "}
                {result.total_files} file{result.total_files !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          {result.files.map((fileResult) => (
            <Card key={fileResult.file} className="shadow-sm">
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-4 h-4 text-gray-400 shrink-0" />
                    <span className="font-medium text-sm truncate">{fileResult.file}</span>
                  </div>
                  <Badge variant={fileResult.status === "success" ? "default" : "destructive"}>
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
                        <Badge key={q} variant="outline">{q}</Badge>
                      ))}
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-xs text-gray-500">
                      {[
                        ["Inserted", fileResult.inserted],
                        ["Updated", fileResult.updated_exact],
                        ["Fuzzy Matched", fileResult.updated_fuzzy],
                      ].map(([label, val]) => (
                        <div key={label as string} className="bg-gray-50 rounded-lg p-2 text-center">
                          <p className="font-bold text-lg text-gray-800">{val}</p>
                          <p>{label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ── Actions ───────────────────────────────────────────────── */}
      <div className="flex justify-between items-center">
        <Button variant="ghost" onClick={handleReset} disabled={status === "PROCESSING"}>
          Reset
        </Button>
        <Button
          onClick={handleProcess}
          disabled={files.length === 0 || status === "PROCESSING"}
          className="gap-2 px-6"
        >
          {status === "PROCESSING" ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Process {files.length > 0 ? files.length : ""} File{files.length !== 1 ? "s" : ""}
            </>
          )}
        </Button>
      </div>

      {/* ── Info cards (shown when idle + no files) ───────────────── */}
      {isIdle && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          {INFO_CARDS.map(({ icon: Icon, title, description }) => (
            <div key={title} className="bg-white border border-gray-200 rounded-xl p-4 space-y-2 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="bg-primary/10 rounded-lg p-1.5">
                  <Icon className="w-4 h-4 text-primary" />
                </div>
                <p className="text-sm font-semibold text-gray-800">{title}</p>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── Benefit Summary Upload Section ────────────────────────── */}
      <BenefitSummaryUpload />
    </div>
  );
}

function BenefitSummaryUpload() {
  const [files, setFiles] = useState<File[]>([]);
  const [year, setYear] = useState<string>("");
  const [status, setStatus] = useState<"IDLE" | "PROCESSING" | "SUCCESS" | "ERROR">("IDLE");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = (incoming: FileList | File[]) => {
    const valid = Array.from(incoming).filter(f => f.name.toLowerCase().endsWith(".pdf"));
    if (valid.length) { setFiles(prev => [...prev, ...valid]); setStatus("IDLE"); setResult(null); }
  };

  const [benefitProgress, setBenefitProgress] = useState(0);

  const handleProcess = async () => {
    if (files.length === 0 || !year) return;
    setStatus("PROCESSING"); setError(null); setResult(null); setBenefitProgress(0);

    const allResults: any[] = [];

    try {
      // Process one file at a time to avoid proxy timeouts on large batches
      for (let i = 0; i < files.length; i++) {
        const { data } = await extractionApi.ingestBenefits([files[i]], year);
        if (data.files) allResults.push(...data.files);
        setBenefitProgress(Math.round(((i + 1) / files.length) * 100));
      }
      setResult({ total_files: files.length, files: allResults });
      setStatus("SUCCESS");
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "An error occurred.");
      setStatus("ERROR");
    }
  };

  const currentYear = new Date().getFullYear();
  const years = [String(currentYear - 1), String(currentYear), String(currentYear + 1)];

  return (
    <div className="mt-8 border-t border-gray-200 pt-8 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-1.5">
          <ClipboardList className="w-4 h-4 text-amber-600" />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-800">Upload Benefit Summaries</p>
          <p className="text-xs text-gray-500">Updates benefit details (deductibles, copays, Rx, Medicare Part D) across all quarters for the selected year</p>
        </div>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
        onDrop={(e) => { e.preventDefault(); setIsDragging(false); if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files); }}
        onClick={() => status !== "PROCESSING" && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl cursor-pointer transition-all
          ${isDragging ? "border-amber-400 bg-amber-50/40" : files.length > 0 ? "border-amber-300 bg-amber-50/20" : "border-gray-200 bg-gray-50/40 hover:border-gray-300"}`}
        style={{ minHeight: 120 }}
      >
        <input ref={fileInputRef} type="file" accept=".pdf" multiple className="hidden" onChange={(e) => { if (e.target.files) addFiles(e.target.files); }} />
        <div className="flex flex-col items-center justify-center py-8 gap-2 text-center px-6">
          <ClipboardList className={`w-6 h-6 ${files.length > 0 ? "text-amber-500" : "text-gray-300"}`} />
          <p className="text-sm font-medium text-gray-600">
            {files.length > 0 ? `${files.length} benefit summary file${files.length > 1 ? "s" : ""} selected` : "Drop benefit summary PDFs here"}
          </p>
          {files.length === 0 && <p className="text-xs text-gray-400">or click to browse</p>}
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-gray-600 bg-white border border-gray-100 rounded-lg px-3 py-1.5">
              <FileText className="w-3 h-3 text-amber-400 shrink-0" />
              <span className="truncate">{f.name}</span>
              <button onClick={(e) => { e.stopPropagation(); setFiles(prev => prev.filter((_, j) => j !== i)); }} className="ml-auto text-gray-300 hover:text-gray-500">✕</button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <Select value={year} onValueChange={setYear} disabled={status === "PROCESSING"}>
          <SelectTrigger className={`w-36 ${!year && files.length > 0 ? "border-amber-400 ring-1 ring-amber-300" : ""}`}>
            <SelectValue placeholder="Select year *" />
          </SelectTrigger>
          <SelectContent>
            {years.map(y => <SelectItem key={y} value={y}>{y}</SelectItem>)}
          </SelectContent>
        </Select>
        <span className="text-xs text-gray-400">
          {year ? "Benefits apply to all quarters for this year" : <span className="text-amber-600 font-medium">Year is required</span>}
        </span>
      </div>

      {status === "PROCESSING" && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 space-y-2">
          <div className="flex items-center justify-between text-xs text-amber-700">
            <span className="flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" />
              Processing benefit summaries...
            </span>
            <span className="font-medium">{benefitProgress}%</span>
          </div>
          <div className="w-full bg-amber-100 rounded-full h-1.5">
            <div className="bg-amber-500 h-1.5 rounded-full transition-all duration-300" style={{ width: `${benefitProgress}%` }} />
          </div>
          <p className="text-xs text-amber-600 text-center">
            Do not close this tab — processing {files.length} file{files.length !== 1 ? "s" : ""} one at a time
          </p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-3 py-2 rounded-lg flex items-center gap-2 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />{error}
        </div>
      )}

      {status === "SUCCESS" && result && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-4 h-4" />
            <p className="font-semibold text-sm">Benefit summaries processed</p>
          </div>
          <div className="space-y-1">
            {result.files?.map((f: any, i: number) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <span className="truncate max-w-xs">{f.file}</span>
                <Badge variant={f.status === "success" ? "default" : "destructive"} className="ml-2 shrink-0">
                  {f.status === "success" ? `${f.plans_updated} plan${f.plans_updated !== 1 ? "s" : ""} updated` : f.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-between">
        <Button variant="ghost" size="sm" onClick={() => { setFiles([]); setStatus("IDLE"); setResult(null); setError(null); }} disabled={status === "PROCESSING"}>
          Reset
        </Button>
        <div className="flex items-center gap-2">
          {!year && files.length > 0 && (
            <span className="text-xs text-amber-600 font-medium">Select a year to continue</span>
          )}
          <Button onClick={handleProcess} disabled={files.length === 0 || !year || status === "PROCESSING"} size="sm" className="gap-2 bg-amber-600 hover:bg-amber-700">
            {status === "PROCESSING" ? <><Loader2 className="w-3 h-3 animate-spin" />Processing...</> : <><ClipboardList className="w-3 h-3" />Update Benefits</>}
          </Button>
        </div>
      </div>
    </div>
  );
}
