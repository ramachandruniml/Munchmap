"use client";

import { BrowserMultiFormatReader } from "@zxing/browser";
import type { IScannerControls } from "@zxing/browser";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";

interface BarcodeScannerProps {
  onScan: (barcode: string) => void;
  onClose: () => void;
}

export function BarcodeScanner({ onScan, onClose }: BarcodeScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const reader = new BrowserMultiFormatReader();

    reader
      .decodeFromVideoDevice(undefined, videoRef.current ?? undefined, (result, err) => {
        if (cancelled) return;
        if (result) {
          controlsRef.current?.stop();
          onScan(result.getText());
        }
        // A per-frame "not found" error is normal while the camera is still searching -
        // only real (non-decode) errors are worth surfacing, and even those we just log.
        if (err && err.message && !err.message.includes("No MultiFormat Readers")) {
          // no-op: transient per-frame decode misses are expected and not user-facing
        }
      })
      .then((controls) => {
        if (cancelled) {
          controls.stop();
          return;
        }
        controlsRef.current = controls;
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Could not access the camera");
      });

    return () => {
      cancelled = true;
      controlsRef.current?.stop();
    };
  }, [onScan]);

  return (
    <div className="flex flex-col gap-3">
      {error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : (
        <video
          ref={videoRef}
          className="w-full max-w-sm rounded-lg border border-border"
          muted
          playsInline
        />
      )}
      <Button type="button" variant="outline" onClick={onClose} className="self-start">
        Cancel
      </Button>
    </div>
  );
}
