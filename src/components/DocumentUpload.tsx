'use client';

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, FileText, X, AlertCircle, CheckCircle2, Zap, Layers, ArrowRight } from 'lucide-react';
import { AnalysisMode } from '@/types/analysis';
import { formatBytes } from '@/lib/utils';

interface DocumentUploadProps {
  onStartAnalysis: (file: File, mode: AnalysisMode) => void;
  isLoading: boolean;
}

export default function DocumentUpload({ onStartAnalysis, isLoading }: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedMode, setSelectedMode] = useState<AnalysisMode>('detailed');
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE = 8 * 1024 * 1024; // 8 MB

  const validateAndSetFile = (file: File) => {
    setValidationError(null);

    // MIME and extension check
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setValidationError('Only PDF documents are supported. Please select a valid .pdf file.');
      return;
    }

    if (file.size === 0) {
      setValidationError('The selected file is empty (0 bytes). Please choose a valid PDF document.');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setValidationError(
        `File size (${formatBytes(file.size)}) exceeds the 8 MB limit. Please split the document into smaller parts or compress it before uploading.`
      );
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setValidationError('Please select a PDF document to begin analysis.');
      return;
    }
    onStartAnalysis(selectedFile, selectedMode);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Dropzone Card */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`relative rounded-xl border-2 border-dashed p-8 text-center transition-all ${
            dragActive
              ? 'border-primary bg-primary-light/40 shadow-md scale-[1.005]'
              : selectedFile
              ? 'border-primary/50 bg-white shadow-sm'
              : 'border-surface-border bg-white hover:border-slate-300 hover:bg-slate-50/50 shadow-sm'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            className="hidden"
            id="pdf-upload-input"
            disabled={isLoading}
          />

          {!selectedFile ? (
            <div className="py-4 space-y-4">
              <div className="mx-auto w-14 h-14 rounded-full bg-primary-light flex items-center justify-center text-primary">
                <UploadCloud className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <p className="text-base font-semibold text-navy-900">
                  Drag and drop your legal PDF here, or{' '}
                  <label
                    htmlFor="pdf-upload-input"
                    className="text-primary hover:text-primary-hover underline cursor-pointer font-bold inline-block"
                  >
                    browse files
                  </label>
                </p>
                <p className="text-xs text-ink-muted">
                  Supports text-based PDF documents up to 8 MB (maximum 50 pages)
                </p>
              </div>

              <div className="pt-2 flex flex-wrap items-center justify-center gap-3 text-xs text-ink-muted">
                <span className="inline-flex items-center gap-1 bg-surface-bg px-2.5 py-1 rounded-md border border-surface-border">
                  <CheckCircle2 className="w-3.5 h-3.5 text-status-success" /> Confidential in-memory processing
                </span>
                <span className="inline-flex items-center gap-1 bg-surface-bg px-2.5 py-1 rounded-md border border-surface-border">
                  <CheckCircle2 className="w-3.5 h-3.5 text-status-success" /> Verbatim citation verification
                </span>
                <span className="inline-flex items-center gap-1 bg-surface-bg px-2.5 py-1 rounded-md border border-surface-border">
                  <CheckCircle2 className="w-3.5 h-3.5 text-status-success" /> No permanent storage
                </span>
              </div>
            </div>
          ) : (
            <div className="py-2">
              <div className="flex items-center justify-between p-4 rounded-lg bg-surface-bg border border-surface-border max-w-xl mx-auto">
                <div className="flex items-center space-x-3 text-left overflow-hidden">
                  <div className="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center text-primary flex-shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="truncate">
                    <p className="text-sm font-semibold text-navy-900 truncate">{selectedFile.name}</p>
                    <p className="text-xs text-ink-muted">{formatBytes(selectedFile.size)}</p>
                  </div>
                </div>
                {!isLoading && (
                  <button
                    type="button"
                    onClick={handleRemoveFile}
                    className="p-1.5 text-ink-muted hover:text-status-error hover:bg-red-50 rounded-md transition-colors flex-shrink-0"
                    title="Remove file"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Validation Error Alert */}
        {validationError && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 flex items-start space-x-3 text-left animate-in fade-in">
            <AlertCircle className="w-5 h-5 text-status-error flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-status-error">Document Error</h4>
              <p className="text-xs text-red-700 mt-0.5">{validationError}</p>
            </div>
          </div>
        )}

        {/* Analysis Mode Selector */}
        <div className="bg-white rounded-xl border border-surface-border p-5 shadow-sm space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-ink-muted block">
            Select Analysis Mode
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Quick Review */}
            <div
              onClick={() => setSelectedMode('quick')}
              className={`cursor-pointer rounded-lg border p-4 text-left transition-all ${
                selectedMode === 'quick'
                  ? 'border-primary bg-primary-light/30 ring-1 ring-primary'
                  : 'border-surface-border bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center space-x-2 text-navy-900 font-semibold text-sm">
                <Zap className="w-4 h-4 text-amber-500" />
                <span>Quick Review</span>
              </div>
              <p className="text-xs text-ink-muted mt-1 leading-relaxed">
                Rapid triage focusing on document summary, primary factual statements, high-level clues, and unanswered questions.
              </p>
            </div>

            {/* Detailed Review */}
            <div
              onClick={() => setSelectedMode('detailed')}
              className={`cursor-pointer rounded-lg border p-4 text-left transition-all ${
                selectedMode === 'detailed'
                  ? 'border-primary bg-primary-light/30 ring-1 ring-primary'
                  : 'border-surface-border bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center space-x-2 text-navy-900 font-semibold text-sm">
                <Layers className="w-4 h-4 text-primary" />
                <span>Detailed Comprehensive Review</span>
              </div>
              <p className="text-xs text-ink-muted mt-1 leading-relaxed">
                In-depth cross-examination including internal inconsistencies, alternative explanations, information gaps, and tactical deposition questions.
              </p>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <p className="text-xs text-ink-muted text-center sm:text-left">
            By proceeding, the document will be extracted in-memory and analyzed via Groq AI. No permanent copies are saved.
          </p>
          <button
            type="submit"
            disabled={!selectedFile || isLoading}
            className={`w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold text-white shadow-sm transition-all ${
              !selectedFile || isLoading
                ? 'bg-slate-300 cursor-not-allowed'
                : 'bg-primary hover:bg-primary-hover active:scale-[0.99]'
            }`}
          >
            <span>{isLoading ? 'Analyzing Document...' : 'Begin AI Legal Analysis'}</span>
            {!isLoading && <ArrowRight className="w-4 h-4" />}
          </button>
        </div>
      </form>
    </div>
  );
}
