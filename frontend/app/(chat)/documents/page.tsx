"use client";

import { ChangeEvent, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Trash2, UploadCloud } from "lucide-react";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api/documents";

export default function DocumentsPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    event.target.value = "";
  };

  return (
    <div className="flex-1 overflow-y-auto bg-bg">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
          <div>
            <h1 className="font-display text-2xl text-text">Documents</h1>
            <p className="mt-1 text-sm text-text-muted">Upload files for retrieval-augmented answers.</p>
          </div>
          <button
            onClick={() => inputRef.current?.click()}
            className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-2 text-sm font-medium text-bg hover:bg-accent-hover"
          >
            <UploadCloud size={16} /> Upload
          </button>
          <input ref={inputRef} type="file" className="hidden" onChange={handleFileChange} accept=".pdf,.docx,.txt,.md" />
        </div>

        {uploadMutation.error && <p className="text-sm text-red-400">Upload failed. Check file type, size, and API keys.</p>}

        <div className="overflow-hidden rounded-md border border-border bg-surface">
          <div className="grid grid-cols-[1fr_120px_150px_48px] gap-3 border-b border-border px-4 py-2 text-xs uppercase text-text-muted">
            <span>Name</span>
            <span>Status</span>
            <span>Uploaded</span>
            <span />
          </div>
          {isLoading && <div className="px-4 py-6 text-sm text-text-muted">Loading documents...</div>}
          {!isLoading && documents.length === 0 && (
            <div className="px-4 py-8 text-sm text-text-muted">No documents uploaded yet.</div>
          )}
          {documents.map((document) => (
            <div
              key={document.id}
              className="grid grid-cols-[1fr_120px_150px_48px] items-center gap-3 border-b border-border px-4 py-3 last:border-b-0"
            >
              <div className="flex min-w-0 items-center gap-3">
                <FileText size={18} className="shrink-0 text-highlight" />
                <div className="min-w-0">
                  <p className="truncate text-sm text-text">{document.filename}</p>
                  <p className="text-xs text-text-muted">{document.file_type.toUpperCase()}</p>
                </div>
              </div>
              <span className="text-sm capitalize text-text-muted">{document.status}</span>
              <span className="text-sm text-text-muted">{new Date(document.uploaded_at).toLocaleDateString()}</span>
              <button
                onClick={() => deleteMutation.mutate(document.id)}
                className="text-text-muted hover:text-red-400"
                aria-label="Delete document"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
