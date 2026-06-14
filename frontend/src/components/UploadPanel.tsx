import { format } from "date-fns";
import {
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import { api } from "../api/client";
import type { AgentInput } from "../types";

type Mode = "text" | "file";
type TextInputType = Extract<AgentInput["input_type"], "log" | "json" | "email">;
type ToastKind = "success" | "error";

type Toast = {
  id: number;
  message: string;
  kind: ToastKind;
  visible: boolean;
};

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_FILES = ".log,.txt,.json,.pdf,.png,.jpg,.eml";

const inputTypeOptions: Array<{ value: TextInputType; label: string }> = [
  { value: "log", label: "Log" },
  { value: "json", label: "JSON" },
  { value: "email", label: "Email" },
];

export function UploadPanel() {
  const [mode, setMode] = useState<Mode>("text");
  const [inputType, setInputType] = useState<TextInputType>("log");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [lastSubmittedAt, setLastSubmittedAt] = useState<Date | null>(null);
  const toastIdRef = useRef(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const pushToast = (message: string, kind: ToastKind) => {
    const id = toastIdRef.current + 1;
    toastIdRef.current = id;

    setToasts((prev) => [...prev, { id, message, kind, visible: false }]);

    window.setTimeout(() => {
      setToasts((prev) =>
        prev.map((toast) =>
          toast.id === id ? { ...toast, visible: true } : toast,
        ),
      );
    }, 10);
  };

  useEffect(() => {
    if (toasts.length === 0) return;

    const timers = toasts.flatMap((toast) => [
      window.setTimeout(() => {
        setToasts((prev) =>
          prev.map((item) =>
            item.id === toast.id ? { ...item, visible: false } : item,
          ),
        );
      }, 3000),
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((item) => item.id !== toast.id));
      }, 3300),
    ]);

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [toasts]);

  const validateAndSetFile = (selectedFile?: File) => {
    if (!selectedFile) return;

    if (selectedFile.size > MAX_FILE_SIZE) {
      pushToast("File too large (max 10 MB)", "error");
      return;
    }

    setFile(selectedFile);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    validateAndSetFile(event.target.files?.[0]);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    validateAndSetFile(event.dataTransfer.files[0]);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (isSubmitting) return;
    if (mode === "text" && content.trim().length === 0) return;
    if (mode === "file" && !file) return;

    setIsSubmitting(true);

    try {
      if (mode === "text") {
        await api.analyze({ input_type: inputType, content: content.trim() });
      } else if (file) {
        const result = await api.upload(file);
        await api.analyze(result.data);
      }

      setContent("");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setLastSubmittedAt(new Date());
      pushToast("✅ Incident submitted for analysis", "success");
    } catch (error) {
      console.error("[UploadPanel] Submission failed", error);
      pushToast("❌ Submission failed — check console", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitDisabled =
    isSubmitting ||
    (mode === "text" && content.trim().length === 0) ||
    (mode === "file" && !file);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5 inline-flex rounded-md border border-slate-200 bg-slate-50 p-1">
        <button
          type="button"
          className={`rounded px-3 py-1.5 text-sm font-medium transition ${
            mode === "text"
              ? "bg-white text-slate-950 shadow-sm"
              : "text-slate-600 hover:text-slate-950"
          }`}
          onClick={() => setMode("text")}
        >
          Text / Log
        </button>
        <button
          type="button"
          className={`rounded px-3 py-1.5 text-sm font-medium transition ${
            mode === "file"
              ? "bg-white text-slate-950 shadow-sm"
              : "text-slate-600 hover:text-slate-950"
          }`}
          onClick={() => setMode("file")}
        >
          File upload
        </button>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        {mode === "text" ? (
          <>
            <textarea
              className="min-h-80 w-full resize-y rounded-md border border-slate-300 px-3 py-2 font-mono text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
              rows={20}
              placeholder="Paste SIEM alert, syslog, or incident description here..."
              value={content}
              onChange={(event) => setContent(event.target.value)}
            />
            <label className="block text-sm font-medium text-slate-700">
              Input type
              <select
                className="mt-1 block w-44 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
                value={inputType}
                onChange={(event) =>
                  setInputType(event.target.value as TextInputType)
                }
              >
                {inputTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : (
          <div
            className="flex min-h-60 cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center transition hover:border-sky-400 hover:bg-sky-50"
            role="button"
            tabIndex={0}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(event) => event.preventDefault()}
            onDrop={handleDrop}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                fileInputRef.current?.click();
              }
            }}
          >
            <input
              ref={fileInputRef}
              className="sr-only"
              type="file"
              accept={ACCEPTED_FILES}
              onChange={handleFileChange}
            />
            <svg
              className="mb-3 h-10 w-10 text-slate-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 16V4" />
              <path d="m7 9 5-5 5 5" />
              <path d="M20 16.5V19a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-2.5" />
            </svg>
            <p className="text-sm font-medium text-slate-700">
              Drop a file here, or click to browse
            </p>
            <p className="mt-1 text-xs text-slate-500">
              .log .txt .json .pdf .png .jpg .eml
            </p>
            {file ? (
              <p className="mt-4 max-w-full truncate rounded bg-white px-3 py-1.5 text-sm font-medium text-slate-900 shadow-sm">
                {file.name}
              </p>
            ) : null}
          </div>
        )}

        <div className="space-y-2">
          <button
            type="submit"
            className="inline-flex min-w-40 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={submitDisabled}
          >
            {isSubmitting ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            ) : null}
            {mode === "text" ? "Analyze" : "Upload & Analyze"}
          </button>

          {lastSubmittedAt ? (
            <p className="text-sm text-slate-500">
              Last submitted: {format(lastSubmittedAt, "HH:mm:ss dd MMM yyyy")}
            </p>
          ) : null}
        </div>
      </form>

      <div className="fixed bottom-4 right-4 z-50 flex max-w-sm flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-md px-4 py-3 text-sm font-medium shadow-lg transition-all duration-300 ${
              toast.visible
                ? "translate-y-0 opacity-100"
                : "translate-y-2 opacity-0"
            } ${
              toast.kind === "success"
                ? "bg-emerald-600 text-white"
                : "bg-red-600 text-white"
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}
